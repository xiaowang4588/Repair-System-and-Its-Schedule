"""
报修API Blueprint
包含报修记录的CRUD、统计、导入导出等接口
"""
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
from functools import wraps
import logging
import os

logger = logging.getLogger(__name__)

# 创建Blueprint
repair_bp = Blueprint('repair', __name__)

# 这些变量会在注册时从app传入
repair_manager = None
admin_config = None
student_required = None
admin_required = None
_cache = None


def init_blueprint(repair_mgr, admin_cfg, student_req_decorator=None, cache=None, admin_req_decorator=None):
    """初始化Blueprint的依赖"""
    global repair_manager, admin_config, student_required, admin_required, _cache
    repair_manager = repair_mgr
    admin_config = admin_cfg
    _cache = cache
    if student_req_decorator:
        student_required = student_req_decorator
    if admin_req_decorator:
        admin_required = admin_req_decorator


def _admin_required(f):
    """懒加载装饰器：需要管理员权限"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if admin_required:
            return admin_required(f)(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated


def _student_required(f):
    """懒加载装饰器：需要学生登录"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if student_required:
            return student_required(f)(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated


def _login_required(f):
    """懒加载装饰器：需要登录（管理员或学生均可）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import request as req
        auth = req.headers.get('Authorization', '')

        if not auth.startswith('Bearer '):
            return jsonify({'status': 'error', 'message': '未登录'}), 401

        token = auth[7:]

        # 通过 payload 中的 role 字段判断是管理员还是学生 token
        try:
            import base64, json
            payload_b64 = token.split('.', 1)[0]
            pad_len = (4 - len(payload_b64) % 4) % 4
            payload = json.loads(base64.urlsafe_b64decode(payload_b64 + '=' * pad_len))

            if payload.get('role') == 'admin':
                # 管理员 token
                if admin_required:
                    return admin_required(f)(*args, **kwargs)
                return f(*args, **kwargs)
            else:
                # 学生 token
                if student_required:
                    return student_required(f)(*args, **kwargs)
                return f(*args, **kwargs)
        except Exception:
            # payload 解析失败，尝试学生验证
            if student_required:
                return student_required(f)(*args, **kwargs)
            return jsonify({'status': 'error', 'message': '认证失败'}), 401

    return decorated


@repair_bp.route('/api/repair/auto-fill', methods=['GET'])
@_login_required
def api_repair_auto_fill():
    """根据教室自动填充报修信息（需要登录）"""
    try:
        classroom = request.args.get('classroom', '').strip()
        weekday = request.args.get('weekday', '').strip()
        section = request.args.get('section', '').strip()

        if not classroom:
            return jsonify({'status': 'error', 'message': '请输入教室名称'}), 400

        result = repair_manager.auto_fill(classroom, _cache, weekday, section)
        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/nearby-rooms', methods=['GET'])
@_login_required
def api_repair_nearby_rooms():
    """获取同楼栋空教室推荐（需要登录）"""
    try:
        classroom = request.args.get('classroom', '').strip()
        weekday = request.args.get('weekday', '0').strip()
        section = request.args.get('section', '').strip()

        if not classroom:
            return jsonify({'status': 'error', 'message': '请输入教室名称'}), 400

        # 转换 weekday 为 int
        try:
            weekday_int = int(weekday)
        except ValueError:
            weekday_int = 0

        result = repair_manager.get_nearby_rooms(classroom, weekday_int, section, _cache)
        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/list', methods=['GET'])
@_login_required
def api_repair_list():
    """获取报修记录列表（教师端+学生端共用，支持多条件筛选和分页）"""
    try:
        params = {
            'status': request.args.get('status', 'all'),
            'semester': request.args.get('semester', ''),
            'start_date': request.args.get('start_date', ''),
            'end_date': request.args.get('end_date', ''),
            'keyword': request.args.get('keyword', ''),
            'classroom': request.args.get('classroom', ''),
            'week_number': request.args.get('week_number', ''),
            'fault_type': request.args.get('fault_type', ''),
            'reporter_name': request.args.get('reporter_name', ''),
            'reporter_college': request.args.get('reporter_college', ''),
            'is_external_teacher': request.args.get('is_external_teacher', ''),
            'handler_name': request.args.get('handler_name', ''),
            'fault_cause': request.args.get('fault_cause', ''),
            'page': request.args.get('page', 1, type=int),
            'page_size': request.args.get('page_size', 50, type=int),
        }

        result = repair_manager.get_repair_list(**params)
        return jsonify({'status': 'ok', **result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/my-list', methods=['GET'])
def api_repair_my_list():
    """获取学生的报修记录（从token获取学生信息）"""
    # 手动验证学生token
    from blueprints.student_api import verify_student_token
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    token = auth[7:]
    result = verify_student_token(token)
    if not result.get('valid'):
        return jsonify({'status': 'error', 'message': result.get('error', '认证失败')}), 401
    request.student_id = result['student_id']
    request.student_name = result['name']
    try:
        # 从token中获取学生信息
        student_id = request.student_id
        student_name = request.student_name

        result = repair_manager.get_student_repairs(
            student_id=student_id,
            student_name=student_name,
            status=request.args.get('status', 'all'),
            keyword=request.args.get('keyword', ''),
            page=request.args.get('page', 1, type=int),
            page_size=request.args.get('page_size', 20, type=int),
        )
        return jsonify({'status': 'ok', **result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/filter-options', methods=['GET'])
@_admin_required
def api_repair_filter_options():
    """获取所有筛选选项（需要管理员登录）"""
    try:
        options = repair_manager.get_filter_options()
        return jsonify({'status': 'ok', 'data': options})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/create', methods=['POST'])
@_student_required
def api_repair_create():
    """创建报修记录（需要学生登录）"""
    try:
        data = request.get_json() or {}
        if not data.get('classroom'):
            return jsonify({'status': 'error', 'message': '请输入故障教室'}), 400

        result = repair_manager.create_repair(data)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 400

        return jsonify({'status': 'ok', 'data': result, 'message': '创建成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/update', methods=['POST'])
@_admin_required
def api_repair_update():
    """更新报修记录"""
    try:
        data = request.get_json() or {}
        repair_id = data.get('id')
        if not repair_id:
            return jsonify({'status': 'error', 'message': '缺少记录ID'}), 400

        result = repair_manager.update_repair(int(repair_id), data)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 400

        return jsonify({'status': 'ok', 'data': result, 'message': '更新成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/delete', methods=['POST'])
@_admin_required
def api_repair_delete():
    """删除报修记录"""
    try:
        data = request.get_json() or {}
        repair_id = data.get('id')
        if not repair_id:
            return jsonify({'status': 'error', 'message': '缺少记录ID'}), 400

        result = repair_manager.delete_repair(int(repair_id))
        if not result:
            return jsonify({'status': 'error', 'message': '删除失败，记录不存在'}), 400

        return jsonify({'status': 'ok', 'message': '删除成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/batch-update-status', methods=['POST'])
@_admin_required
def api_repair_batch_update_status():
    """批量更新处理状态"""
    try:
        data = request.get_json() or {}
        ids = data.get('ids', [])
        status = data.get('status', '')

        if not ids or not status:
            return jsonify({'status': 'error', 'message': '参数不完整'}), 400

        result = repair_manager.batch_update_status(ids, status)
        return jsonify({'status': 'ok', **result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/batch-update-handler', methods=['POST'])
@_admin_required
def api_repair_batch_update_handler():
    """批量分配处理人"""
    try:
        data = request.get_json() or {}
        ids = data.get('ids', [])
        handler_name = data.get('handler_name', '')

        if not ids or not handler_name:
            return jsonify({'status': 'error', 'message': '参数不完整'}), 400

        result = repair_manager.batch_update_handler(ids, handler_name)
        return jsonify({'status': 'ok', **result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/batch-delete', methods=['POST'])
@_admin_required
def api_repair_batch_delete():
    """批量删除"""
    try:
        data = request.get_json() or {}
        ids = data.get('ids', [])

        if not ids:
            return jsonify({'status': 'error', 'message': '缺少记录ID'}), 400

        result = repair_manager.batch_delete(ids)
        return jsonify({'status': 'ok', **result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/stats', methods=['GET'])
@_login_required
def api_repair_stats():
    """获取报修统计数据（需要登录）"""
    try:
        stats = repair_manager.get_repair_stats()
        return jsonify({'status': 'ok', 'data': stats})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/dashboard-stats', methods=['GET'])
@_admin_required
def api_repair_dashboard_stats():
    """获取大屏综合统计数据（需要管理员登录）"""
    try:
        range_type = request.args.get('range', 'semester')
        stats = repair_manager.get_dashboard_stats(range_type)
        return jsonify({'status': 'ok', 'data': stats})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/drill/building', methods=['GET'])
@_admin_required
def api_repair_drill_building():
    """楼栋下钻统计（需要管理员登录）"""
    try:
        building = request.args.get('building', '')
        range_type = request.args.get('range', 'semester')
        result = repair_manager.get_building_drill(building, range_type)
        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/drill/college', methods=['GET'])
@_admin_required
def api_repair_drill_college():
    """学院下钻统计（需要管理员登录）"""
    try:
        college = request.args.get('college', '')
        range_type = request.args.get('range', 'semester')
        result = repair_manager.get_college_drill(college, range_type)
        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/drill/handler', methods=['GET'])
@_admin_required
def api_repair_drill_handler():
    """处理人下钻统计（需要管理员登录）"""
    try:
        handler = request.args.get('handler', '')
        range_type = request.args.get('range', 'semester')
        result = repair_manager.get_handler_drill(handler, range_type)
        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/drill/fault-type', methods=['GET'])
@_admin_required
def api_repair_drill_fault_type():
    """故障类型下钻统计（需要管理员登录）"""
    try:
        fault_type = request.args.get('fault_type', '')
        range_type = request.args.get('range', 'semester')
        result = repair_manager.get_fault_type_drill(fault_type, range_type)
        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/drill/repair', methods=['GET'])
@_admin_required
def api_repair_drill_repair():
    """单条报修详情（需要管理员登录）"""
    try:
        repair_id = request.args.get('id', type=int)
        if not repair_id:
            return jsonify({'status': 'error', 'message': '缺少记录ID'}), 400

        result = repair_manager.get_repair_detail(repair_id)
        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 404

        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/drill/pending', methods=['GET'])
@_admin_required
def api_repair_drill_pending():
    """待处理工单列表（需要管理员登录）"""
    try:
        range_type = request.args.get('range', 'semester')
        result = repair_manager.get_pending_list(range_type)
        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/drill/classroom', methods=['GET'])
@_admin_required
def api_repair_drill_classroom():
    """教室下钻统计（需要管理员登录）"""
    try:
        classroom = request.args.get('classroom', '')
        range_type = request.args.get('range', 'semester')
        result = repair_manager.get_classroom_drill(classroom, range_type)
        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/export', methods=['GET'])
@_admin_required
def api_repair_export():
    """导出报修记录为Excel（需要管理员登录）"""
    try:
        params = {
            'range_type': request.args.get('range', ''),
            'semester': request.args.get('semester', ''),
            'start_date': request.args.get('start_date', ''),
            'end_date': request.args.get('end_date', ''),
            'status': request.args.get('status', ''),
        }

        buffer, filename = repair_manager.export_to_excel(**params)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/import', methods=['POST'])
@_admin_required
def api_repair_import():
    """导入报修记录"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': '没有选择文件'}), 400

        file = request.files['file']
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'status': 'error', 'message': '只支持Excel文件'}), 400

        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            result = repair_manager.import_from_excel(tmp_path)
        finally:
            # 删除临时文件
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/import-template', methods=['GET'])
@_login_required
def api_repair_import_template():
    """下载导入模板（需要登录）"""
    try:
        buffer = repair_manager.get_import_template_path()

        return send_file(
            buffer,
            as_attachment=True,
            download_name='报修记录导入模板.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/semesters', methods=['GET'])
@_login_required
def api_repair_semesters():
    """获取学期列表（需要登录）"""
    try:
        semesters = repair_manager.get_semester_list()
        return jsonify({'status': 'ok', 'data': semesters})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@repair_bp.route('/api/repair/upload-image', methods=['POST'])
@_student_required
def api_repair_upload_image():
    """上传备注图片（需要学生登录，限制文件类型和大小）"""
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    MAX_SIZE = 10 * 1024 * 1024  # 10MB

    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': '没有选择文件'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'status': 'error', 'message': '文件名为空'}), 400

        # 校验扩展名白名单
        import uuid
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({'status': 'error', 'message': f'不支持的文件格式{ext}，仅支持 jpg/png/gif/webp'}), 400

        # 校验文件大小
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_SIZE:
            return jsonify({'status': 'error', 'message': f'文件大小 {size/1024/1024:.1f}MB 超过限制 10MB'}), 400

        filename = f"{uuid.uuid4().hex}{ext}"

        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads', 'repair_images')
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        return jsonify({'status': 'ok', 'data': {'url': f'/uploads/repair_images/{filename}', 'filename': filename}})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
