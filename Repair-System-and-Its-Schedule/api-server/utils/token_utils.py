"""
管理员 Token 工具模块
使用 HMAC-SHA256 签名的令牌替代 Base64 编码凭据。

Token 格式: base64url(json_payload).hmac_sha256_signature
Payload: {"user": "username", "role": "admin", "exp": unix_timestamp}
"""
import hmac
import hashlib
import json
import time
import base64
import logging

logger = logging.getLogger(__name__)

# Token 有效期（小时），可通过环境变量配置
ADMIN_TOKEN_EXPIRE_HOURS = 720  # 30天


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

    payload = json.dumps({
        'user': username,
        'role': 'admin',
        'exp': int(time.time()) + expire_hours * 3600,
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
        验证成功: {'valid': True, 'username': str}
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

        return {
            'valid': True,
            'username': payload.get('user', ''),
        }
    except Exception as e:
        return {'valid': False, 'error': f'token验证失败: {str(e)}'}
