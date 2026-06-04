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
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# 创建Blueprint
student_bp = Blueprint('student', __name__)

# 这些变量会在注册时从app传入
student_manager = None
repair_manager = None
app_secret_key = None


def init_blueprint(student_mgr, repair_mgr, secret_key):
    """初始化Blueprint的依赖"""
    global student_manager, repair_manager, app_secret_key
    student_manager = student_mgr
    repair_manager = repair_mgr
    app_secret_key = secret_key


def verify_student_token(token: str) -> dict:
    """
    验证学生token
    返回: {'valid': True, 'student_id': ..., 'name': ...} 或 {'valid': False, 'error': ...}
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

        # 验证签名
        secret = app_secret_key if isinstance(app_secret_key, str) else app_secret_key.decode()
        expected_sig = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()[:32]

        if not hmac.compare_digest(signature, expected_sig):
            return {'valid': False, 'error': 'token签名无效'}

        return {
            'valid': True,
            'student_id': payload.get('sid'),
            'name': payload.get('name')
        }
    except Exception as e:
        return {'valid': False, 'error': f'token验证失败: {str(e)}'}


def student_required(f):
    """学生登录验证装饰器"""
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

        return f(*args, **kwargs)

    return decorated


@student_bp.route('/api/student/login', methods=['POST'])
def api_student_login():
    """学生登录"""
    try:
        data = request.get_json() or {}
        student_id = data.get('student_id', '').strip()
        password = data.get('password', '')
        if not student_id or not password:
            return jsonify({'status': 'error', 'message': '请输入学号和密码'}), 400

        result = student_manager.verify_student(student_id, password)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 401

        # 生成安全 token（HMAC签名 + 过期时间）
        expire_time = int(time.time()) + 30 * 86400  # 30天过期
        payload = json.dumps({
            'sid': result['student_id'],
            'name': result['name'],
            'exp': expire_time
        }, ensure_ascii=False)

        # 使用HMAC-SHA256签名
        secret = app_secret_key if isinstance(app_secret_key, str) else app_secret_key.decode()
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()[:32]

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
    """学生修改密码（从token获取学生信息）"""
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

        return jsonify({'status': 'ok', 'message': '密码修改成功'})
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
def api_student_info():
    """获取学生个人信息和报修统计"""
    try:
        # 优先从token获取学生ID，其次从参数获取
        student_id = None
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            from blueprints.student_api import verify_student_token
            token = auth[7:]
            result = verify_student_token(token)
            if result.get('valid'):
                student_id = result['student_id']

        # 如果token验证失败，尝试从参数获取
        if not student_id:
            student_id = request.args.get('student_id', '').strip()

        if not student_id:
            return jsonify({'status': 'error', 'message': '请提供学号或登录'}), 400

        # 获取学生信息
        student = student_manager.get_student_by_id(student_id)
        if not student:
            return jsonify({'status': 'error', 'message': '学生不存在'}), 404

        # 获取该学生的报修统计（按 student_id 或 handler_name 匹配）
        from models import Repair
        total_repairs = Repair.select().where(
            (Repair.student_id == student_id) |
            (Repair.handler_name == student.get('name', ''))
        ).count()

        pending_repairs = Repair.select().where(
            ((Repair.student_id == student_id) | (Repair.handler_name == student.get('name', ''))) &
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
