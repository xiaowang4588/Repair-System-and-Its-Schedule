"""
管理员API Blueprint
包含管理员登录、数据源管理、课表管理、学生管理、系统设置等接口
"""
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

# 创建Blueprint
admin_bp = Blueprint('admin', __name__)

# 这些变量会在注册时从app传入
admin_config = None
cache = None
repair_manager = None
student_manager = None


def init_blueprint(admin_cfg, cache_mgr, repair_mgr, student_mgr):
    """初始化Blueprint的依赖"""
    global admin_config, cache, repair_manager, student_manager
    admin_config = admin_cfg
    cache = cache_mgr
    repair_manager = repair_mgr
    student_manager = student_mgr


def admin_required(f):
    """管理员认证装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Basic '):
            return jsonify({'status': 'error', 'message': '未登录'}), 401

        try:
            import base64
            decoded = base64.b64decode(auth[6:]).decode('utf-8')
            username, password = decoded.split(':', 1)
            if not admin_config.verify_admin(username, password):
                return jsonify({'status': 'error', 'message': '账号或密码错误'}), 401
        except Exception:
            return jsonify({'status': 'error', 'message': '认证失败'}), 401

        return f(*args, **kwargs)

    return decorated


@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """管理员登录"""
    import base64
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')

    if admin_config.verify_admin(username, password):
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        return jsonify({'status': 'ok', 'token': token, 'username': username})
    else:
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
    """修改管理员密码"""
    try:
        data = request.get_json() or {}
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        if not old_password or not new_password:
            return jsonify({'status': 'error', 'message': '参数不完整'}), 400

        result = admin_config.change_password(old_password, new_password)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 400

        return jsonify({'status': 'ok', 'message': '密码修改成功'})
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
        from log_manager import get_log_handler
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
        from log_manager import get_log_handler
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
    """上传Excel文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': '没有选择文件'}), 400

        file = request.files['file']
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'status': 'error', 'message': '只支持Excel文件'}), 400

        year = request.form.get('year', '')
        semester = request.form.get('semester', '')

        result = admin_config.upload_excel(file, year, semester)

        # Bug6 修复: reload() 现在返回实际加载结果
        success = cache.reload()
        if success:
            return jsonify({'status': 'ok', 'message': f'上传成功：{file.filename}'})
        else:
            return jsonify({
                'status': 'warning',
                'message': f'文件已上传，但加载数据失败，请稍后点击"刷新数据"重试',
                'data': result
            })
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/excel/switch', methods=['POST'])
@admin_required
def admin_excel_switch():
    """切换Excel文件"""
    try:
        data = request.get_json() or {}
        path = data.get('path', '')
        if not path:
            return jsonify({'status': 'error', 'message': '缺少文件路径'}), 400

        admin_config.switch_excel(path)
        success = cache.reload()
        if success:
            return jsonify({'status': 'ok', 'message': '已切换文件'})
        else:
            return jsonify({
                'status': 'warning',
                'message': '文件已切换，但加载数据失败，请稍后点击"刷新数据"重试'
            })
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
        cache.reload()
        return jsonify({
            'status': 'ok',
            'message': f'已清除所有数据（删除 {result["deleted_count"]} 个文件）',
            'data': result
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
