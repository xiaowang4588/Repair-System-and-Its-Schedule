"""
公共API Blueprint
包含学生端和教师端共用的接口
"""
from flask import Blueprint, request, jsonify
import base64
import json
import re
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# 创建Blueprint
public_bp = Blueprint('public', __name__)

# 这些变量会在注册时从app传入
cache = None
admin_config = None
_admin_required = None
_student_required = None


def init_blueprint(cache_manager, admin_config_module, admin_req=None, student_req=None):
    """初始化Blueprint的依赖"""
    global cache, admin_config, _admin_required, _student_required
    cache = cache_manager
    admin_config = admin_config_module
    _admin_required = admin_req
    _student_required = student_req


def _login_required(f):
    """懒加载装饰器：需要登录（管理员或学生均可）
    优化：先解析 role，再按角色一次性完成验证，避免双重解析 token。"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'status': 'error', 'message': '未登录'}), 401

        token = auth[7:]

        # 先解析 role 字段，决定走哪条验证路径
        role = ''
        try:
            payload_b64 = token.split('.', 1)[0]
            pad_len = (4 - len(payload_b64) % 4) % 4
            payload = json.loads(base64.urlsafe_b64decode(payload_b64 + '=' * pad_len))
            role = payload.get('role', '')
        except Exception:
            pass

        if role == 'admin' and _admin_required:
            # 管理员：委托给 admin_required（它会完整验证签名 + 设置 request 属性）
            return _admin_required(f)(*args, **kwargs)
        else:
            # 学生（或 role 缺失的旧 token）：一次性完成验证，避免再套一层装饰器
            from blueprints.student_api import verify_student_token
            result = verify_student_token(token)
            if not result.get('valid'):
                return jsonify({'status': 'error', 'message': result.get('error', '认证失败')}), 401
            request.student_id = result['student_id']
            request.student_name = result['name']
            return f(*args, **kwargs)

    return decorated


@public_bp.route('/api/config', methods=['GET'])
def api_config():
    """
    获取客户端配置（学生端启动时调用）
    学生端根据此接口动态获取 API 地址，无需在前端硬编码服务器 IP。
    换服务器时只需修改 .env 中的 API_BASE_URL，学生端自动生效，无需重新构建。
    """
    import os
    # API_BASE_URL: 客户端访问后端的完整地址
    # 优先从 .env 读取，未设置则返回空（学生端将使用当前页面地址）
    api_base = os.environ.get('API_BASE_URL', '').strip()
    return jsonify({
        'status': 'ok',
        'data': {
            'api_base_url': api_base,
        }
    })


@public_bp.route('/api/time', methods=['GET'])
@_login_required
def api_time():
    """获取当前时间和节次信息"""
    from utils.time_helper import get_auto_time_info
    return jsonify({'status': 'ok', 'data': get_auto_time_info()})


@public_bp.route('/api/current-week', methods=['GET'])
@_login_required
def api_current_week():
    """获取当前教学周（根据学期开始日期自动计算）"""
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


@public_bp.route('/api/query', methods=['GET'])
@_login_required
def api_query():
    """
    按条件查询课程
    参数：
      - day_of_week: 星期几 (1-7)
      - section: 节次 (如 "1-2节")
      - classroom: 教室关键词
    """
    from utils.time_helper import get_auto_time_info
    try:
        df = cache.get_df()
        day = request.args.get('day_of_week', '').strip()
        section = request.args.get('section', '').strip()
        classroom = request.args.get('classroom', '').strip()

        if not day:
            auto = get_auto_time_info()
            day = str(auto['weekday'])

        mask = df["_weekday_str"] == day
        if section:
            escaped = re.escape(section.lower())
            mask = mask & df["_section_lower"].str.contains(escaped, na=False, regex=True)
        if classroom:
            escaped = re.escape(classroom.lower())
            mask = mask & df["_classroom_lower"].str.contains(escaped, na=False, regex=True)

        filtered = df[mask]
        results = []
        for row in filtered.itertuples(index=False):
            results.append({
                "course_name": row.课程名称,
                "teacher": row.姓名,
                "teacher_id": row.教工号,
                "college": row.开课学院,
                "class": row.教学班组成,
                "time": row.上课时间,
                "classroom": row.上课地点
            })

        return jsonify({'status': 'ok', 'data': results, 'total': len(results)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def _query_by_keyword(filter_col: str, keyword: str, error_msg: str):
    """按关键词查询课程的公共逻辑"""
    if not keyword:
        return jsonify({'status': 'error', 'message': error_msg}), 400

    df = cache.get_df()
    escaped = re.escape(keyword.lower())
    mask = df[filter_col].str.contains(escaped, na=False, regex=True)
    filtered = df[mask]

    results = []
    for row in filtered.itertuples(index=False):
        results.append({
            "course_name": row.课程名称,
            "teacher": row.姓名,
            "teacher_id": row.教工号,
            "college": row.开课学院,
            "class": row.教学班组成,
            "time": row.上课时间,
            "classroom": row.上课地点,
            "day_of_week": row.星期几,
            "section": row.上课节次
        })

    return jsonify({'status': 'ok', 'data': results, 'total': len(results)})


@public_bp.route('/api/query/course', methods=['GET'])
@_login_required
def api_query_course():
    """按课程名称查询"""
    try:
        return _query_by_keyword("_course_lower", request.args.get('keyword', '').strip(), '请输入课程名称')
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@public_bp.route('/api/query/teacher', methods=['GET'])
@_login_required
def api_query_teacher():
    """按教师姓名查询"""
    try:
        return _query_by_keyword("_teacher_lower", request.args.get('keyword', '').strip(), '请输入教师姓名')
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@public_bp.route('/api/query/weekly', methods=['GET'])
@_login_required
def api_query_weekly():
    """
    获取一周课表
    参数：
      - keyword: 班级名称或教师姓名
      - type: class（按班级）或 teacher（按教师）
    返回格式：
      - weekly_data: {1: {"1-2节": [...], "3-4节": [...]}, 2: {...}, ...}
      - sections: ["1-2节", "3-4节", ...]
    """
    try:
        keyword = request.args.get('keyword', '').strip()
        query_type = request.args.get('type', 'class')

        if not keyword:
            return jsonify({'status': 'error', 'message': '请输入查询关键词'}), 400

        df = cache.get_df()
        if query_type == 'class':
            escaped = re.escape(keyword.lower())
            mask = df["教学班组成"].str.lower().str.contains(escaped, na=False, regex=True)
        else:
            escaped = re.escape(keyword.lower())
            mask = df["_teacher_lower"].str.contains(escaped, na=False, regex=True)

        filtered_df = df[mask].copy()
        if len(filtered_df) == 0:
            label = '班级' if query_type == 'class' else '教师'
            return jsonify({'status': 'ok', 'data': {'weekly_data': {}, 'sections': []}, 'message': f'未找到{label}: {keyword}'})

        # 收集所有出现的节次（去重、排序）
        raw_sections = filtered_df["上课节次"].dropna().unique().tolist()
        # 按起始数字排序：提取 "1-2节" 中的 1 作为排序键
        def _section_sort_key(s):
            m = re.match(r'(\d+)', str(s))
            return int(m.group(1)) if m else 999
        all_sections = sorted(set(s.strip() for s in raw_sections if s.strip()), key=_section_sort_key)

        # 构建一周课表数据：{day_number: {section_str: [courses]}}
        weekly_data = {}
        for day in range(1, 8):
            day_data = filtered_df[filtered_df['星期几'] == str(day)]
            section_map = {}
            for row in day_data.itertuples(index=False):
                section = str(row.上课节次).strip()
                if not section:
                    continue
                if section not in section_map:
                    section_map[section] = []
                section_map[section].append({
                    'course_name': row.课程名称,
                    'teacher': row.姓名,
                    'classroom': row.上课地点,
                })
            weekly_data[day] = section_map

        return jsonify({
            'status': 'ok',
            'data': {
                'weekly_data': weekly_data,
                'sections': all_sections,
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@public_bp.route('/api/empty-rooms', methods=['GET'])
@_login_required
def api_empty_rooms():
    """查询空教室"""
    from datasource.empty_classroom_query import create_query_system, ClassroomType
    from utils.time_helper import get_auto_time_info
    try:
        weekday = request.args.get('weekday', '').strip()
        sections_str = request.args.get('sections', '').strip()
        building = request.args.get('building', '').strip()
        classroom_type = request.args.get('classroom_type', 'all').strip()
        keyword = request.args.get('keyword', '').strip()
        exclude_special = request.args.get('exclude_special', 'true').lower() == 'true'

        if not weekday:
            auto = get_auto_time_info()
            weekday = str(auto['weekday'])

        if not sections_str:
            return jsonify({'status': 'error', 'message': '请选择节次'}), 400

        # 前端发送的是节次起始数字（如 "1,3,5" 代表 1-2节、3-4节、5-6节）
        # 需要展开为完整的节次列表 [1,2,3,4,5,6]
        raw_sections = [int(s.strip()) for s in sections_str.split(',') if s.strip()]
        expanded_sections = []
        for s in raw_sections:
            if s not in expanded_sections:
                expanded_sections.append(s)
            # 奇数起始节次自动包含下一节（1→[1,2], 3→[3,4], 5→[5,6]）
            if s % 2 == 1 and (s + 1) not in expanded_sections:
                expanded_sections.append(s + 1)
        sections = sorted(expanded_sections)

        # 获取缓存的查询系统
        query_system = cache.get_query_system()

        # 构建查询条件
        type_map = {
            'all': ClassroomType.ALL,
            'regular': ClassroomType.REGULAR,
            'lab': ClassroomType.LAB,
            'library': ClassroomType.LIBRARY,
            'special': ClassroomType.SPECIAL
        }

        # 模糊匹配楼栋名称（去除首尾空格，处理可能的编码差异）
        matched_building = None
        if building:
            building_stripped = building.strip()
            available_buildings = query_system.get_buildings()
            # 精确匹配
            if building_stripped in available_buildings:
                matched_building = building_stripped
            else:
                # 模糊匹配：前端传的值包含在楼栋名中，或反之
                for b in available_buildings:
                    if building_stripped in b or b in building_stripped:
                        matched_building = b
                        break

        from datasource.empty_classroom_query import QueryCondition
        condition = QueryCondition(
            weekday=int(weekday),
            sections=sections,
            building=matched_building,
            classroom_type=type_map.get(classroom_type, ClassroomType.ALL),
            keyword=keyword if keyword else None,
            exclude_special=exclude_special
        )

        result = query_system.query_empty_classrooms(condition)

        # 转换为可序列化的字典列表
        result_list = []
        for room in result:
            result_list.append({
                'classroom': room.classroom,
                'building': room.building,
                'classroom_type': room.classroom_type.value,
                'sections_available': room.sections_available,
                'sections_occupied': room.sections_occupied,
            })

        return jsonify({'status': 'ok', 'data': result_list})
    except Exception as e:
        logger.error(f"查询空教室失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@public_bp.route('/api/buildings', methods=['GET'])
@_login_required
def api_buildings():
    """获取所有楼栋列表"""
    try:
        # 优先从查询系统获取（与空教室查询使用相同提取逻辑）
        buildings = []
        try:
            query_system = cache.get_query_system()
            if query_system:
                buildings = query_system.get_buildings()
                logger.info(f"[BUILDINGS] 查询系统返回 {len(buildings)} 个楼栋: {buildings[:5]}")
        except Exception as e:
            logger.warning(f"[BUILDINGS] 从查询系统获取楼栋失败: {e}")

        # 兜底：如果查询系统没有数据，从原始 DataFrame 提取
        if not buildings:
            from datasource.data_cleaning import extract_building_name
            df = cache.get_df()
            logger.info(f"[BUILDINGS] DataFrame 行数: {len(df)}, 列: {list(df.columns)}")
            buildings = sorted(set(
                extract_building_name(str(row.上课地点))
                for row in df.itertuples(index=False)
                if row.上课地点 and str(row.上课地点).strip()
            ))
            logger.info(f"[BUILDINGS] DataFrame 兜底返回 {len(buildings)} 个楼栋: {buildings[:5]}")

        return jsonify({'status': 'ok', 'data': buildings})
    except Exception as e:
        logger.error(f"[BUILDINGS] 接口异常: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@public_bp.route('/api/stats', methods=['GET'])
@_login_required
def api_stats():
    """获取统计数据"""
    try:
        df = cache.get_df()
        stats = {
            'total_courses': len(df),
            'total_teachers': df['姓名'].nunique(),
            'total_classrooms': df['上课地点'].nunique(),
            'total_colleges': df['开课学院'].nunique(),
        }
        return jsonify({'status': 'ok', 'data': stats})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@public_bp.route('/api/building-usage', methods=['GET'])
@_login_required
def api_building_usage():
    """各楼栋各楼层教室实时使用情况"""
    from utils.time_helper import get_auto_time_info
    try:
        df = cache.get_df()
        auto = get_auto_time_info()
        weekday = str(auto['weekday'])
        current_section = auto.get('current_section') or ''

        # 获取当前正在上课的课程
        if current_section:
            mask = (df['_weekday_str'] == weekday) & (df['上课节次'].str.contains(current_section, na=False))
            active_courses = df[mask]
        else:
            # 非上课时间，返回空结果
            active_courses = df.iloc[0:0]

        # 统计各楼栋使用情况（使用唯一教室数）
        usage = {}
        for row in active_courses.itertuples(index=False):
            room = str(row.上课地点)
            building = re.sub(r'\d+$', '', room).strip()
            if building:
                if building not in usage:
                    usage[building] = {'total': 0, 'used_rooms': set()}
                usage[building]['used_rooms'].add(room)

        # 统计各楼栋总教室数
        all_rooms = df['上课地点'].unique()
        for room in all_rooms:
            if room and str(room).strip():
                building = re.sub(r'\d+$', '', str(room)).strip()
                if building:
                    if building not in usage:
                        usage[building] = {'total': 0, 'used_rooms': set()}
                    usage[building]['total'] += 1

        # 转换为列表
        result = []
        for building, data in usage.items():
            used_count = len(data['used_rooms'])
            result.append({
                'building': building,
                'total_rooms': data['total'],
                'used_rooms': used_count,
                'available_rooms': data['total'] - used_count,
                'usage_rate': round(used_count / data['total'] * 100, 1) if data['total'] > 0 else 0
            })

        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
