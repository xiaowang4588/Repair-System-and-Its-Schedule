"""
管理员API Blueprint
包含管理员登录、数据源管理、课表管理、学生管理、系统设置等接口
"""
from flask import Blueprint, request, jsonify
from utils.token_utils import generate_admin_token, verify_admin_token, revoke_tokens_for_user, refresh_admin_token
from utils.security_monitor import security_monitor, IP_LOCKOUT_DURATION
import logging

logger = logging.getLogger(__name__)

# 创建Blueprint
admin_bp = Blueprint('admin', __name__)

# 这些变量会在注册时从app传入
admin_config = None
cache = None
repair_manager = None
student_manager = None
_app_secret_key = None


def init_blueprint(admin_cfg, cache_mgr, repair_mgr, student_mgr, secret_key=None):
    """初始化Blueprint的依赖"""
    global admin_config, cache, repair_manager, student_manager, _app_secret_key
    admin_config = admin_cfg
    cache = cache_mgr
    repair_manager = repair_mgr
    student_manager = student_mgr
    _app_secret_key = secret_key


def admin_required(f):
    """管理员认证装饰器（HMAC Token 验证，支持Token自动刷新）"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'status': 'error', 'message': '未登录'}), 401

        token = auth[7:]
        result = verify_admin_token(token, _app_secret_key)

        if not result.get('valid'):
            return jsonify({'status': 'error', 'message': result.get('error', '认证失败')}), 401

        # 将管理员用户名存入 request 上下文
        request.admin_username = result['username']

        # 执行原函数
        response = f(*args, **kwargs)

        # 如果Token需要刷新，在响应头中返回新Token
        if result.get('needs_refresh'):
            new_token = generate_admin_token(result['username'], _app_secret_key)
            if isinstance(response, tuple):
                resp = jsonify(response[0].get_json() if hasattr(response[0], 'get_json') else response[0])
                resp.headers['X-New-Token'] = new_token
                return resp, response[1] if len(response) > 1 else 200
            else:
                if hasattr(response, 'headers'):
                    response.headers['X-New-Token'] = new_token

        return response

    return decorated


@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """管理员登录（集成入侵检测）"""
    ip = request.remote_addr or 'unknown'
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')

    # 检查IP是否被锁定
    if security_monitor.is_ip_locked(ip):
        remaining = security_monitor.get_lockout_remaining(ip)
        return jsonify({
            'status': 'error',
            'message': f'登录尝试过多，IP已被锁定，请{remaining}秒后重试'
        }), 429

    if admin_config.verify_admin(username, password):
        # 登录成功，清除失败计数
        security_monitor.record_login_success(ip, username, 'admin')
        token = generate_admin_token(username, _app_secret_key)
        return jsonify({'status': 'ok', 'token': token, 'username': username})
    else:
        # 登录失败，记录并检查是否需要锁定
        lock_result = security_monitor.record_login_failure(ip, username, 'admin')
        if lock_result['locked']:
            return jsonify({
                'status': 'error',
                'message': f'登录失败次数过多，IP已被锁定{IP_LOCKOUT_DURATION}秒'
            }), 429
        return jsonify({'status': 'error', 'message': '账号或密码错误'}), 401


@admin_bp.route('/admin/status', methods=['GET'])
@admin_required
def admin_status():
    """获取系统状态"""
    try:
        cache_info = cache.get_status() if cache else {}
        datasource_info = admin_config.get_datasource_config()
        return jsonify({
            'status': 'ok',
            'cache': cache_info,
            'datasource': datasource_info
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/refresh', methods=['POST'])
@admin_required
def admin_refresh():
    """刷新缓存"""
    try:
        cache.reload()
        return jsonify({'status': 'ok', 'message': '缓存已刷新'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/datasource', methods=['GET'])
@admin_required
def admin_datasource():
    """获取数据源配置"""
    try:
        config = admin_config.get_datasource_config()
        return jsonify({'status': 'ok', 'data': config})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/datasource/switch', methods=['POST'])
@admin_required
def admin_datasource_switch():
    """切换数据源"""
    try:
        data = request.get_json() or {}
        ds_type = data.get('type', '')
        if ds_type not in ['excel', 'api']:
            return jsonify({'status': 'error', 'message': '无效的数据源类型'}), 400

        admin_config.set_datasource_type(ds_type)
        cache.reload()
        return jsonify({'status': 'ok', 'message': f'已切换到{ds_type}数据源'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/datasource/api', methods=['POST'])
@admin_required
def admin_datasource_api():
    """保存API配置"""
    try:
        data = request.get_json() or {}
        admin_config.save_api_config(data)
        return jsonify({'status': 'ok', 'message': 'API配置已保存'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/test-connection', methods=['POST'])
@admin_required
def admin_test_connection():
    """测试连接"""
    try:
        result = cache.test_connection()
        return jsonify({'status': 'ok', 'message': '连接成功' if result else '连接失败'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/week', methods=['GET'])
@admin_required
def admin_week():
    """获取周次信息"""
    try:
        current_week = admin_config.get_current_week()
        semester = admin_config.get_semester_config()
        return jsonify({
            'status': 'ok',
            'data': {
                'current_week': current_week,
                'start_date': semester.get('start_date', ''),
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/week/set-start', methods=['POST'])
@admin_required
def admin_week_set_start():
    """设置学期开始日期"""
    try:
        data = request.get_json() or {}
        start_date = data.get('start_date', '')
        if not start_date:
            return jsonify({'status': 'error', 'message': '请选择日期'}), 400

        admin_config.set_semester_start(start_date)
        return jsonify({'status': 'ok', 'message': '学期开始日期已设置'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/settings/cache', methods=['POST'])
@admin_required
def admin_settings_cache():
    """保存缓存设置"""
    try:
        data = request.get_json() or {}
        admin_config.save_cache_settings(data)
        return jsonify({'status': 'ok', 'message': '缓存设置已保存'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/settings/password', methods=['POST'])
@admin_required
def admin_settings_password():
    """修改管理员密码（修改后吊销所有旧Token）"""
    try:
        data = request.get_json() or {}
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        if not old_password or not new_password:
            return jsonify({'status': 'error', 'message': '参数不完整'}), 400

        result = admin_config.change_password(old_password, new_password)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 400

        # 密码修改成功，吊销管理员的所有旧Token
        username = request.admin_username
        revoke_tokens_for_user('admin', username, 'password_change')

        # 生成新Token返回
        new_token = generate_admin_token(username, _app_secret_key)

        return jsonify({
            'status': 'ok',
            'message': '密码修改成功，请使用新Token',
            'data': {'token': new_token}
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/token-refresh', methods=['POST'])
@admin_required
def admin_token_refresh():
    """管理员Token刷新接口"""
    try:
        username = request.admin_username
        new_token = generate_admin_token(username, _app_secret_key)
        return jsonify({
            'status': 'ok',
            'data': {'token': new_token}
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/students', methods=['GET'])
@admin_required
def admin_students():
    """获取学生列表"""
    try:
        keyword = request.args.get('keyword', '')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        result = student_manager.get_student_list(keyword, page, page_size)
        return jsonify({'status': 'ok', **result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/students/create', methods=['POST'])
@admin_required
def admin_students_create():
    """创建学生"""
    try:
        data = request.get_json() or {}
        student_id = data.get('student_id', '').strip()
        name = data.get('name', '').strip()
        password = data.get('password', '')

        if not student_id or not name:
            return jsonify({'status': 'error', 'message': '学号和姓名不能为空'}), 400

        result = student_manager.create_student(student_id, name, password)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 400

        return jsonify({'status': 'ok', 'data': result, 'message': '创建成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/students/batch-create', methods=['POST'])
@admin_required
def admin_students_batch_create():
    """批量创建学生"""
    try:
        data = request.get_json() or {}
        students = data.get('students', [])
        if not students:
            return jsonify({'status': 'error', 'message': '没有学生数据'}), 400

        result = student_manager.batch_create_students(students)
        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/students/update', methods=['POST'])
@admin_required
def admin_students_update():
    """更新学生信息"""
    try:
        data = request.get_json() or {}
        student_id = data.get('student_id', '').strip()
        if not student_id:
            return jsonify({'status': 'error', 'message': '缺少学号'}), 400

        result = student_manager.update_student(student_id, data)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 400

        return jsonify({'status': 'ok', 'data': result, 'message': '更新成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/students/delete', methods=['POST'])
@admin_required
def admin_students_delete():
    """删除学生"""
    try:
        data = request.get_json() or {}
        student_id = data.get('student_id', '').strip()
        if not student_id:
            return jsonify({'status': 'error', 'message': '缺少学号'}), 400

        result = student_manager.delete_student(student_id)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 400

        return jsonify({'status': 'ok', 'message': '删除成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/students/reset-password', methods=['POST'])
@admin_required
def admin_students_reset_password():
    """重置学生密码"""
    try:
        data = request.get_json() or {}
        student_id = data.get('student_id', '').strip()
        new_password = data.get('new_password', '')
        if not student_id:
            return jsonify({'status': 'error', 'message': '缺少学号'}), 400

        result = student_manager.admin_reset_password(student_id, new_password)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 400

        return jsonify({'status': 'ok', 'message': result.get('message', '密码已重置')})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/students/stats', methods=['GET'])
@admin_required
def admin_students_stats():
    """获取学生账号统计"""
    try:
        stats = student_manager.get_student_stats()
        return jsonify({'status': 'ok', 'data': stats})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/logs', methods=['GET'])
@admin_required
def admin_logs():
    """获取系统日志"""
    try:
        from utils.log_manager import get_log_handler
        handler = get_log_handler()
        level = request.args.get('level', '')
        keyword = request.args.get('keyword', '')
        logs = handler.get_logs(level=level, keyword=keyword)
        return jsonify({'status': 'ok', 'data': logs})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/logs/clear', methods=['POST'])
@admin_required
def admin_logs_clear():
    """清空系统日志"""
    try:
        from utils.log_manager import get_log_handler
        handler = get_log_handler()
        handler.clear()
        return jsonify({'status': 'ok', 'message': '日志已清空'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/excel/list', methods=['GET'])
@admin_required
def admin_excel_list():
    """获取已上传的Excel文件列表"""
    try:
        files = admin_config.get_excel_files()
        return jsonify({'status': 'ok', 'data': files})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/excel/upload', methods=['POST'])
@admin_required
def admin_excel_upload():
    """上传Excel文件（后台异步处理，不阻塞响应）"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': '没有选择文件'}), 400

        file = request.files['file']
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'status': 'error', 'message': '只支持Excel文件'}), 400

        year = request.form.get('year', '')
        semester = request.form.get('semester', '')

        result = admin_config.upload_excel(file, year, semester)

        # 移到后台线程处理，立即返回响应
        cache.reload_async()
        return jsonify({
            'status': 'ok',
            'message': f'文件已上传：{file.filename}，正在后台加载数据...',
            'data': result
        })
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/excel/switch', methods=['POST'])
@admin_required
def admin_excel_switch():
    """切换Excel文件（后台异步处理）"""
    try:
        data = request.get_json() or {}
        path = data.get('path', '')
        if not path:
            return jsonify({'status': 'error', 'message': '缺少文件路径'}), 400

        admin_config.switch_excel(path)
        cache.reload_async()
        return jsonify({'status': 'ok', 'message': '已切换文件，正在后台加载数据...'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/excel/delete', methods=['POST'])
@admin_required
def admin_excel_delete():
    """删除Excel文件"""
    try:
        data = request.get_json() or {}
        path = data.get('path', '')
        if not path:
            return jsonify({'status': 'error', 'message': '缺少文件路径'}), 400

        admin_config.delete_excel(path)
        return jsonify({'status': 'ok', 'message': '已删除文件'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/excel/clear-all', methods=['POST'])
@admin_required
def admin_excel_clear_all():
    """清除所有 Excel 数据（删除全部文件 + 重置配置 + 清缓存）"""
    try:
        result = admin_config.clear_all_excel()
        cache.reload()  # 清空是快速操作，同步即可
        return jsonify({
            'status': 'ok',
            'message': f'已清除所有数据（删除 {result["deleted_count"]} 个文件）',
            'data': result
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/cache/status', methods=['GET'])
@admin_required
def admin_cache_status():
    """查询缓存后台处理状态（供前端轮询）"""
    try:
        status = cache.get_processing_status()
        return jsonify({'status': 'ok', 'data': status})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============ 安全监控端点 ============

@admin_bp.route('/admin/security/events', methods=['GET'])
@admin_required
def admin_security_events():
    """查询安全事件"""
    try:
        event_type = request.args.get('event_type', '')
        severity = request.args.get('severity', '')
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)

        events = security_monitor.get_security_events(
            event_type=event_type,
            severity=severity,
            hours=hours,
            limit=limit,
        )
        return jsonify({'status': 'ok', 'data': events})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/security/summary', methods=['GET'])
@admin_required
def admin_security_summary():
    """获取安全事件摘要"""
    try:
        hours = request.args.get('hours', 24, type=int)
        summary = security_monitor.get_security_summary(hours=hours)
        return jsonify({'status': 'ok', 'data': summary})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/security/locked-ips', methods=['GET'])
@admin_required
def admin_security_locked_ips():
    """查看当前被锁定的IP列表"""
    try:
        summary = security_monitor.get_security_summary(hours=1)
        return jsonify({'status': 'ok', 'data': summary.get('locked_ips', [])})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/security/unlock-ip', methods=['POST'])
@admin_required
def admin_security_unlock_ip():
    """手动解锁IP"""
    try:
        data = request.get_json() or {}
        ip = data.get('ip', '').strip()
        if not ip:
            return jsonify({'status': 'error', 'message': '缺少IP地址'}), 400

        # 从锁定列表中移除
        with security_monitor._data_lock:
            if ip in security_monitor._ip_lockouts:
                del security_monitor._ip_lockouts[ip]
                return jsonify({'status': 'ok', 'message': f'IP {ip} 已解锁'})
            else:
                return jsonify({'status': 'ok', 'message': f'IP {ip} 未被锁定'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
