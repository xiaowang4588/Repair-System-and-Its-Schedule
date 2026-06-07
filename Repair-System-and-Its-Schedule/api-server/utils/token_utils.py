"""
管理员 Token 工具模块
使用 HMAC-SHA256 签名的令牌替代 Base64 编码凭据。

Token 格式: base64url(json_payload).hmac_sha256_signature
Payload: {"user": "username", "role": "admin", "exp": unix_timestamp,
          "iat": unix_timestamp, "jti": "unique_id"}
"""
import hmac
import hashlib
import json
import time
import base64
import uuid
import logging

logger = logging.getLogger(__name__)

# Token 有效期（小时），可通过环境变量配置
ADMIN_TOKEN_EXPIRE_HOURS = 720  # 30天

# Token 自动刷新阈值（距过期不足7天时自动刷新）
TOKEN_REFRESH_THRESHOLD_HOURS = 168  # 7天


def generate_admin_token(username: str, secret_key: str, expire_hours: int = None) -> str:
    """
    生成管理员 Token

    Args:
        username: 管理员用户名
        secret_key: 签名密钥（app.secret_key）
        expire_hours: 有效期（小时），默认使用 ADMIN_TOKEN_EXPIRE_HOURS

    Returns:
        格式为 base64url(payload).signature 的 token 字符串
    """
    if expire_hours is None:
        expire_hours = ADMIN_TOKEN_EXPIRE_HOURS

    now = int(time.time())
    payload = json.dumps({
        'user': username,
        'role': 'admin',
        'exp': now + expire_hours * 3600,
        'iat': now,
        'jti': uuid.uuid4().hex,
    }, ensure_ascii=False)

    payload_b64 = base64.urlsafe_b64encode(payload.encode('utf-8')).decode().rstrip('=')

    secret = secret_key if isinstance(secret_key, str) else secret_key.decode()
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return f"{payload_b64}.{signature}"


def verify_admin_token(token: str, secret_key: str) -> dict:
    """
    验证管理员 Token

    Args:
        token: token 字符串
        secret_key: 签名密钥（app.secret_key）

    Returns:
        验证成功: {'valid': True, 'username': str, 'iat': int, 'jti': str, 'needs_refresh': bool}
        验证失败: {'valid': False, 'error': str}
    """
    try:
        if not token or '.' not in token:
            return {'valid': False, 'error': 'token格式无效'}

        payload_b64, signature = token.split('.', 1)

        # 还原 Base64 padding
        pad_len = (4 - len(payload_b64) % 4) % 4
        padded = payload_b64 + '=' * pad_len
        payload_str = base64.urlsafe_b64decode(padded).decode('utf-8')
        payload = json.loads(payload_str)

        # 检查过期时间（60秒容差）
        if payload.get('exp', 0) < time.time() - 60:
            return {'valid': False, 'error': 'token已过期'}

        # 验证签名
        secret = secret_key if isinstance(secret_key, str) else secret_key.decode()
        expected_sig = hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return {'valid': False, 'error': 'token签名无效'}

        # 检查Token是否已被吊销（密码修改后批量失效）
        iat = payload.get('iat', 0)
        jti = payload.get('jti', '')
        username = payload.get('user', '')

        if _is_token_revoked('admin', username, iat, jti):
            return {'valid': False, 'error': 'token已失效（密码已修改）'}

        # 判断是否需要自动刷新
        needs_refresh = _check_needs_refresh(payload)

        return {
            'valid': True,
            'username': username,
            'iat': iat,
            'jti': jti,
            'needs_refresh': needs_refresh,
        }
    except Exception as e:
        return {'valid': False, 'error': f'token验证失败: {str(e)}'}


def _check_needs_refresh(payload: dict) -> bool:
    """检查Token是否需要刷新（距过期不足阈值时间）"""
    exp = payload.get('exp', 0)
    remaining = exp - time.time()
    return 0 < remaining < TOKEN_REFRESH_THRESHOLD_HOURS * 3600


def _is_token_revoked(user_type: str, user_id: str, iat: int, jti: str = '') -> bool:
    """
    检查Token是否已被吊销
    逻辑：如果用户在Token签发之后修改过密码，则Token失效
    """
    try:
        from models import TokenRevocation
        # 查找该用户在Token签发时间之后的吊销记录
        revocations = TokenRevocation.select().where(
            (TokenRevocation.user_type == user_type) &
            (TokenRevocation.user_id == user_id) &
            (TokenRevocation.revoked_at >= str(iat))
        )
        return revocations.exists()
    except Exception:
        # 数据库异常时，不阻止访问（降级策略）
        logger.warning("Token吊销检查异常，降级放行")
        return False


def revoke_tokens_for_user(user_type: str, user_id: str, reason: str = 'password_change'):
    """
    吊销指定用户的所有Token（通过记录吊销时间戳实现）
    密码修改后调用此函数
    """
    try:
        from models import TokenRevocation
        now = str(int(time.time()))
        TokenRevocation.create(
            user_type=user_type,
            user_id=user_id,
            revoked_at=now,
            reason=reason,
            created_at=now,
        )
        logger.info(f"已吊销用户 {user_type}/{user_id} 的所有旧Token，原因: {reason}")

        # 清理7天前的旧吊销记录（已无实际意义，Token已过期）
        _cleanup_old_revocations()
    except Exception as e:
        logger.error(f"吊销Token失败: {e}")


def _cleanup_old_revocations():
    """清理过期的吊销记录（Token已过期的记录无需保留）"""
    try:
        from models import TokenRevocation
        cutoff = str(int(time.time()) - ADMIN_TOKEN_EXPIRE_HOURS * 3600 - 86400)
        deleted = TokenRevocation.delete().where(
            TokenRevocation.revoked_at < cutoff
        ).execute()
        if deleted > 0:
            logger.info(f"已清理 {deleted} 条过期Token吊销记录")
    except Exception as e:
        logger.warning(f"清理吊销记录异常: {e}")


def refresh_admin_token(token: str, secret_key: str) -> dict:
    """
    刷新管理员Token（需验证旧Token有效）

    Returns:
        成功: {'success': True, 'token': new_token}
        失败: {'success': False, 'error': str}
    """
    result = verify_admin_token(token, secret_key)
    if not result.get('valid'):
        return {'success': False, 'error': result.get('error', '旧Token无效')}

    new_token = generate_admin_token(result['username'], secret_key)
    return {'success': True, 'token': new_token}
