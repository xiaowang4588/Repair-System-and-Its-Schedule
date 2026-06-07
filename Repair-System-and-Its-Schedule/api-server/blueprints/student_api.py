"""
学生API Blueprint
包含学生登录、个人信息、修改密码等接口
"""
from flask import Blueprint, request, jsonify
import hmac
import hashlib
import time
import json
import base64
import uuid
import logging
from functools import wraps
from utils.security_monitor import security_monitor

logger = logging.getLogger(__name__)

# 创建Blueprint
student_bp = Blueprint('student', __name__)

# 这些变量会在注册时从app传入
student_manager = None
repair_manager = None
app_secret_key = None

# Token自动刷新阈值（距过期不足7天时标记需要刷新）
STUDENT_TOKEN_REFRESH_THRESHOLD = 7 * 86400  # 7天（秒）


def init_blueprint(student_mgr, repair_mgr, secret_key):
    """初始化Blueprint的依赖"""
    global student_manager, repair_manager, app_secret_key
    student_manager = student_mgr
    repair_manager = repair_mgr
    app_secret_key = secret_key


def verify_student_token(token: str) -> dict:
    """
    验证学生token（兼容新旧两种格式）
    新格式: base64({sid,name,role:"student",exp,iat,jti}).full_hmac_sha256
    旧格式: base64({sid,name,exp}).hmac_sha256[:32]
    返回: {'valid': True, 'student_id': ..., 'name': ..., 'iat': ..., 'needs_refresh': ...}
          或 {'valid': False, 'error': ...}
    """
    try:
        if not token or '.' not in token:
            return {'valid': False, 'error': 'token格式无效'}

        payload_b64, signature = token.split('.', 1)

        # 解码payload（修复padding问题）
        payload_b64_clean = payload_b64.rstrip('=')
        pad_len = (4 - len(payload_b64_clean) % 4) % 4
        padded = payload_b64_clean + '=' * pad_len
        payload_str = base64.urlsafe_b64decode(padded).decode('utf-8')
        payload = json.loads(payload_str)

        # 检查过期时间（60秒容差，兼容客户端/服务端时钟偏差）
        if payload.get('exp', 0) < time.time() - 60:
            return {'valid': False, 'error': 'token已过期'}

        # 验证签名：先尝试完整签名（新格式），再尝试截断签名（旧格式兼容）
        secret = app_secret_key if isinstance(app_secret_key, str) else app_secret_key.decode()
        full_sig = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        is_valid = (
            hmac.compare_digest(signature, full_sig) or           # 新格式：完整签名
            hmac.compare_digest(signature, full_sig[:32])         # 旧格式：截断签名（向后兼容）
        )

        if not is_valid:
            return {'valid': False, 'error': 'token签名无效'}

        # 检查Token是否已被吊销（密码修改后批量失效）
        iat = payload.get('iat', 0)
        jti = payload.get('jti', '')
        student_id = payload.get('sid', '')

        if iat and student_id:
            if _is_student_token_revoked(student_id, iat, jti):
                return {'valid': False, 'error': 'token已失效（密码已修改）'}

        # 判断是否需要自动刷新
        needs_refresh = False
        exp = payload.get('exp', 0)
        remaining = exp - time.time()
        if 0 < remaining < STUDENT_TOKEN_REFRESH_THRESHOLD:
            needs_refresh = True

        return {
            'valid': True,
            'student_id': payload.get('sid'),
            'name': payload.get('name'),
            'iat': iat,
            'jti': jti,
            'needs_refresh': needs_refresh,
        }
    except Exception as e:
        return {'valid': False, 'error': f'token验证失败: {str(e)}'}


def _is_student_token_revoked(student_id: str, iat: int, jti: str = '') -> bool:
    """检查学生Token是否已被吊销"""
    try:
        from models import TokenRevocation
        revocations = TokenRevocation.select().where(
            (TokenRevocation.user_type == 'student') &
            (TokenRevocation.user_id == student_id) &
            (TokenRevocation.revoked_at >= str(iat))
        )
        return revocations.exists()
    except Exception:
        logger.warning("学生Token吊销检查异常，降级放行")
        return False


def revoke_student_tokens(student_id: str, reason: str = 'password_change'):
    """吊销指定学生的所有Token"""
    try:
        from models import TokenRevocation
        now = str(int(time.time()))
        TokenRevocation.create(
            user_type='student',
            user_id=student_id,
            revoked_at=now,
            reason=reason,
            created_at=now,
        )
        logger.info(f"已吊销学生 {student_id} 的所有旧Token，原因: {reason}")
    except Exception as e:
        logger.error(f"吊销学生Token失败: {e}")


def student_required(f):
    """学生登录验证装饰器（支持Token自动刷新）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'status': 'error', 'message': '未登录'}), 401

        token = auth[7:]  # 去掉 "Bearer " 前缀（7个字符）
        result = verify_student_token(token)

        if not result.get('valid'):
            return jsonify({'status': 'error', 'message': result.get('error', '认证失败')}), 401

        # 将学生信息存入request上下文
        request.student_id = result['student_id']
        request.student_name = result['name']

        # 如果Token需要刷新，在响应头中返回新Token
        response = f(*args, **kwargs)

        if result.get('needs_refresh'):
            # 生成新Token
            new_token = _generate_student_token(result['student_id'], result['name'])
            if isinstance(response, tuple):
                resp = jsonify(response[0].get_json() if hasattr(response[0], 'get_json') else response[0])
                resp.headers['X-New-Token'] = new_token
                return resp, response[1] if len(response) > 1 else 200
            else:
                if hasattr(response, 'headers'):
                    response.headers['X-New-Token'] = new_token

        return response

    return decorated


def _generate_student_token(student_id: str, name: str) -> str:
    """生成学生Token（内部使用）"""
    now = int(time.time())
    expire_time = now + 30 * 86400  # 30天过期
    payload = json.dumps({
        'sid': student_id,
        'name': name,
        'role': 'student',
        'exp': expire_time,
        'iat': now,
        'jti': uuid.uuid4().hex,
    }, ensure_ascii=False)

    secret = app_secret_key if isinstance(app_secret_key, str) else app_secret_key.decode()
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    token = f"{base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')}.{signature}"
    return token


@student_bp.route('/api/student/login', methods=['POST'])
def api_student_login():
    """学生登录（集成入侵检测）"""
    try:
        ip = request.remote_addr or 'unknown'
        data = request.get_json() or {}
        student_id = data.get('student_id', '').strip()
        password = data.get('password', '')
        if not student_id or not password:
            return jsonify({'status': 'error', 'message': '请输入学号和密码'}), 400

        # 检查IP是否被锁定
        if security_monitor.is_ip_locked(ip):
            remaining = security_monitor.get_lockout_remaining(ip)
            return jsonify({
                'status': 'error',
                'message': f'登录尝试过多，IP已被锁定，请{remaining}秒后重试'
            }), 429

        result = student_manager.verify_student(student_id, password)
        if 'error' in result:
            # 登录失败，记录并检查是否需要锁定
            lock_result = security_monitor.record_login_failure(ip, student_id, 'student')
            if lock_result['locked']:
                return jsonify({
                    'status': 'error',
                    'message': f'登录失败次数过多，IP已被锁定10分钟'
                }), 429
            return jsonify({'status': 'error', 'message': result['error']}), 401

        # 登录成功，清除失败计数
        security_monitor.record_login_success(ip, student_id, 'student')

        # 生成安全 token（HMAC签名 + 过期时间 + role字段，含iat和jti）
        now = int(time.time())
        expire_time = now + 30 * 86400  # 30天过期
        payload = json.dumps({
            'sid': result['student_id'],
            'name': result['name'],
            'role': 'student',
            'exp': expire_time,
            'iat': now,
            'jti': uuid.uuid4().hex,
        }, ensure_ascii=False)

        # 使用完整HMAC-SHA256签名（与管理员token一致，不再截断）
        secret = app_secret_key if isinstance(app_secret_key, str) else app_secret_key.decode()
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        # token格式: base64(payload).signature（去掉padding）
        token = f"{base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')}.{signature}"

        return jsonify({
            'status': 'ok',
            'data': {
                'token': token,
                'student_id': result['student_id'],
                'name': result['name'],
                'expire': expire_time,
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@student_bp.route('/api/student/change-password', methods=['POST'])
@student_required
def api_student_change_password():
    """学生修改密码（从token获取学生信息，修改后吊销旧Token）"""
    try:
        data = request.get_json() or {}
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        if not old_password or not new_password:
            return jsonify({'status': 'error', 'message': '参数不完整'}), 400

        # 从token获取学生ID
        student_id = request.student_id

        result = student_manager.change_password(student_id, old_password, new_password)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 400

        # 密码修改成功，吊销该学生的所有旧Token
        revoke_student_tokens(student_id, 'password_change')

        # 生成新Token返回
        new_token = _generate_student_token(student_id, request.student_name)

        return jsonify({
            'status': 'ok',
            'message': '密码修改成功，请使用新Token',
            'data': {'token': new_token}
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@student_bp.route('/api/student/token-refresh', methods=['POST'])
@student_required
def api_student_token_refresh():
    """学生Token刷新接口"""
    try:
        student_id = request.student_id
        student_name = request.student_name
        new_token = _generate_student_token(student_id, student_name)
        return jsonify({
            'status': 'ok',
            'data': {'token': new_token}
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@student_bp.route('/api/repair/student-update', methods=['POST'])
@student_required
def api_repair_student_update():
    """学生编辑自己的报修记录（从token获取学生信息）"""
    try:
        data = request.get_json() or {}
        repair_id = data.get('id')
        if not repair_id:
            return jsonify({'status': 'error', 'message': '参数不完整'}), 400

        # 从token获取学生信息
        student_id = request.student_id
        student_name = request.student_name

        result = repair_manager.student_update_repair(int(repair_id), student_id, data, student_name)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 400

        return jsonify({'status': 'ok', 'data': result, 'message': '修改成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@student_bp.route('/api/repair/student-delete', methods=['POST'])
@student_required
def api_repair_student_delete():
    """学生删除自己的报修记录（从token获取学生信息）"""
    try:
        data = request.get_json() or {}
        repair_id = data.get('id')
        if not repair_id:
            return jsonify({'status': 'error', 'message': '参数不完整'}), 400

        # 从token获取学生信息
        student_id = request.student_id
        student_name = request.student_name

        result = repair_manager.student_delete_repair(int(repair_id), student_id, student_name)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 400

        return jsonify({'status': 'ok', 'message': '删除成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@student_bp.route('/api/student/info', methods=['GET'])
@student_required
def api_student_info():
    """获取学生个人信息和报修统计（仅返回自己的信息）"""
    try:
        # 从token获取学生ID（@student_required 已验证token有效性）
        student_id = request.student_id

        # 获取学生信息
        student = student_manager.get_student_by_id(student_id)
        if not student:
            return jsonify({'status': 'error', 'message': '学生不存在'}), 404

        # 获取该学生的报修统计
        from models import Repair
        student_name = student.get('name', '')
        total_repairs = Repair.select().where(
            Repair.handler_name == student_name
        ).count()

        pending_repairs = Repair.select().where(
            (Repair.handler_name == student_name) &
            (Repair.status.in_(['未处理', '处理中']))
        ).count()

        return jsonify({
            'status': 'ok',
            'data': {
                **student,
                'stats': {
                    'total': total_repairs,
                    'pending': pending_repairs,
                    'resolved': total_repairs - pending_repairs
                }
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
