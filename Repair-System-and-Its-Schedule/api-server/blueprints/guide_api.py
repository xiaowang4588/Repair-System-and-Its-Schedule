"""
防坑指南API Blueprint
包含动态发布、点赞、评论、收藏、搜索等接口
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from functools import wraps
import json
import logging
import os
import uuid
import subprocess

logger = logging.getLogger(__name__)

# 创建Blueprint
guide_bp = Blueprint('guide', __name__)

# 这些变量会在注册时从app传入
_student_required = None


def init_blueprint(student_req_decorator=None):
    """初始化Blueprint的依赖"""
    global _student_required
    _student_required = student_req_decorator


def student_required(f):
    """懒加载装饰器，在请求时才解析真实的student_required"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if _student_required:
            return _student_required(f)(*args, **kwargs)
        # 如果未初始化，直接调用（不应发生）
        return f(*args, **kwargs)
    return decorated


def _now():
    """获取当前时间字符串"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _get_optional_student_id():
    """从token中尝试获取学生ID（可选认证）"""
    try:
        from blueprints.student_api import verify_student_token
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth[7:]
            result = verify_student_token(token)
            if result.get('valid'):
                return result['student_id']
    except Exception:
        pass
    return None


def _get_video_duration(filepath):
    """获取视频时长（秒），失败返回0（ffprobe未安装时不影响上传）"""
    try:
        # 先检查ffprobe是否可用
        check = subprocess.run(
            ['where', 'ffprobe'] if os.name == 'nt' else ['which', 'ffprobe'],
            capture_output=True, timeout=3
        )
        if check.returncode != 0:
            return 0  # ffprobe未安装，跳过时长检测

        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json',
             '-show_format', filepath],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            info = json.loads(result.stdout)
            return int(float(info.get('format', {}).get('duration', 0)))
    except FileNotFoundError:
        pass  # ffprobe未安装
    except Exception as e:
        logger.warning(f"获取视频时长失败: {e}")
    return 0


# ============================================================
# 动态 CRUD
# ============================================================

@guide_bp.route('/api/guide/create', methods=['POST'])
@student_required
def api_guide_create():
    """发布防坑指南"""
    try:
        from models import GuidePost

        data = request.get_json() or {}
        content = (data.get('content') or '').strip()
        images = data.get('images', [])
        video_url = (data.get('video_url') or '').strip()
        video_duration = data.get('video_duration', 0)
        device_tags = data.get('device_tags', [])
        location_tag = (data.get('location_tag') or '').strip()

        # 参数校验
        if not content or not content.strip():
            return jsonify({'status': 'error', 'message': '请输入内容'}), 400
        if not isinstance(images, list):
            return jsonify({'status': 'error', 'message': '图片格式错误'}), 400
        if len(images) > 9:
            return jsonify({'status': 'error', 'message': '图片最多上传9张'}), 400
        if len(device_tags) > 3:
            return jsonify({'status': 'error', 'message': '设备标签最多选3个'}), 400

        # 内容安全：去除HTML标签
        import re
        content = re.sub(r'<[^>]+>', '', content)

        now = _now()
        post = GuidePost.create(
            student_id=request.student_id,
            student_name=request.student_name,
            content=content,
            images=json.dumps(images, ensure_ascii=False),
            video_url=video_url,
            video_duration=int(video_duration) if video_duration else 0,
            device_tags=json.dumps(device_tags, ensure_ascii=False),
            location_tag=location_tag,
            created_at=now,
            updated_at=now,
        )

        return jsonify({'status': 'ok', 'data': {'id': post.id}})
    except Exception as e:
        logger.error(f"发布防坑指南失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@guide_bp.route('/api/guide/list', methods=['GET'])
@student_required
def api_guide_list():
    """获取动态列表（信息流）"""
    try:
        from models import GuidePost, GuideLike, GuideFavorite

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        page_size = min(page_size, 50)
        device_tag = request.args.get('device_tag', '').strip()
        location_tag = request.args.get('location_tag', '').strip()
        keyword = request.args.get('keyword', '').strip()

        query = GuidePost.select().where(GuidePost.is_deleted == False)

        # 标签筛选（精确匹配 JSON 数组元素，避免子串误匹配）
        if device_tag:
            exact_tag = f'"{device_tag}"'
            query = query.where(
                GuidePost.device_tags.contains(exact_tag + ',') |
                GuidePost.device_tags.contains(exact_tag + ']')
            )
        if location_tag:
            query = query.where(GuidePost.location_tag == location_tag)

        # 关键词搜索
        if keyword:
            query = query.where(
                (GuidePost.content.contains(keyword)) |
                (GuidePost.device_tags.contains(keyword)) |
                (GuidePost.location_tag.contains(keyword)) |
                (GuidePost.student_name.contains(keyword))
            )

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))

        posts = query.order_by(GuidePost.id.desc()).paginate(page, page_size)

        # 获取当前用户的点赞和收藏状态（仅查询当前页的 post_id，避免全表扫描）
        current_student_id = _get_optional_student_id()
        liked_ids = set()
        favorited_ids = set()
        if current_student_id:
            page_post_ids = [p.id for p in posts]
            liked_ids = {l.post_id for l in
                         GuideLike.select(GuideLike.post_id).where(
                             (GuideLike.post_id.in_(page_post_ids)) &
                             (GuideLike.student_id == current_student_id))}
            favorited_ids = {f.post_id for f in
                             GuideFavorite.select(GuideFavorite.post_id).where(
                                 (GuideFavorite.post_id.in_(page_post_ids)) &
                                 (GuideFavorite.student_id == current_student_id))}

        result_records = []
        for post in posts:
            d = post.to_dict()
            d['is_liked'] = post.id in liked_ids
            d['is_favorited'] = post.id in favorited_ids
            result_records.append(d)

        return jsonify({
            'status': 'ok',
            'records': result_records,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        })
    except Exception as e:
        logger.error(f"获取动态列表失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@guide_bp.route('/api/guide/detail', methods=['GET'])
@student_required
def api_guide_detail():
    """获取动态详情"""
    try:
        from models import GuidePost, GuideLike, GuideFavorite

        post_id = request.args.get('id', type=int)
        if not post_id:
            return jsonify({'status': 'error', 'message': '缺少动态ID'}), 400

        try:
            post = GuidePost.get(
                (GuidePost.id == post_id) & (GuidePost.is_deleted == False))
        except GuidePost.DoesNotExist:
            return jsonify({'status': 'error', 'message': '动态不存在'}), 404

        d = post.to_dict()

        current_student_id = _get_optional_student_id()
        d['is_liked'] = False
        d['is_favorited'] = False
        if current_student_id:
            d['is_liked'] = GuideLike.select().where(
                (GuideLike.post_id == post_id) &
                (GuideLike.student_id == current_student_id)
            ).exists()
            d['is_favorited'] = GuideFavorite.select().where(
                (GuideFavorite.post_id == post_id) &
                (GuideFavorite.student_id == current_student_id)
            ).exists()

        return jsonify({'status': 'ok', 'data': d})
    except Exception as e:
        logger.error(f"获取动态详情失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@guide_bp.route('/api/guide/update', methods=['POST'])
@student_required
def api_guide_update():
    """编辑自己的动态"""
    try:
        from models import GuidePost

        data = request.get_json() or {}
        post_id = data.get('id')
        if not post_id:
            return jsonify({'status': 'error', 'message': '缺少动态ID'}), 400

        try:
            post = GuidePost.get(
                (GuidePost.id == post_id) & (GuidePost.is_deleted == False))
        except GuidePost.DoesNotExist:
            return jsonify({'status': 'error', 'message': '动态不存在'}), 404

        if post.student_id != request.student_id:
            return jsonify({'status': 'error', 'message': '只能编辑自己的动态'}), 403

        content = (data.get('content') or '').strip()
        if content:
            import re
            content = re.sub(r'<[^>]+>', '', content)
            post.content = content

        if 'images' in data:
            images = data['images']
            if not isinstance(images, list) or len(images) > 9:
                return jsonify({'status': 'error', 'message': '图片格式错误或超过9张'}), 400
            # 删除被替换掉的旧图片
            _cleanup_removed_media(post.images, json.dumps(images, ensure_ascii=False), is_video=False)
            post.images = json.dumps(images, ensure_ascii=False)

        if 'video_url' in data:
            new_video = (data['video_url'] or '').strip()
            # 删除被替换掉的旧视频
            if new_video != post.video_url:
                _cleanup_removed_media(post.video_url, new_video, is_video=True)
            post.video_url = new_video
        if 'video_duration' in data:
            post.video_duration = int(data['video_duration'] or 0)

        if 'device_tags' in data:
            tags = data['device_tags']
            if not isinstance(tags, list):
                return jsonify({'status': 'error', 'message': '标签格式错误'}), 400
            if len(tags) > 3:
                return jsonify({'status': 'error', 'message': '设备标签最多选3个'}), 400
            post.device_tags = json.dumps(tags, ensure_ascii=False)

        if 'location_tag' in data:
            post.location_tag = (data['location_tag'] or '').strip()

        post.updated_at = _now()
        post.save()

        return jsonify({'status': 'ok', 'message': '修改成功'})
    except Exception as e:
        logger.error(f"编辑动态失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def _delete_file(path):
    """删除单个文件"""
    if not path or not path.startswith('/uploads/'):
        return
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, path.lstrip('/'))
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"已删除文件: {full_path}")
    except Exception as e:
        logger.warning(f"删除文件失败 {full_path}: {e}")


def _delete_media_files(post):
    """删除动态关联的所有图片和视频文件"""
    # 删除图片
    try:
        images = json.loads(post.images) if post.images else []
        for img_path in images:
            _delete_file(img_path)
    except Exception as e:
        logger.warning(f"删除图片失败: {e}")

    # 删除视频
    _delete_file(post.video_url)


def _cleanup_removed_media(old_val, new_val, is_video=False):
    """编辑时清理被移除的媒体文件"""
    if is_video:
        # 视频：旧值不为空且与新值不同则删除
        if old_val and old_val != new_val and old_val.startswith('/uploads/'):
            _delete_file(old_val)
    else:
        # 图片：找出旧有但新列表中没有的，删除
        try:
            old_list = json.loads(old_val) if old_val else []
            new_list = json.loads(new_val) if new_val else []
            for img in old_list:
                if img not in new_list:
                    _delete_file(img)
        except Exception:
            pass


@guide_bp.route('/api/guide/delete', methods=['POST'])
@student_required
def api_guide_delete():
    """删除自己的动态（软删除 + 清理媒体文件）"""
    try:
        from models import GuidePost

        data = request.get_json() or {}
        post_id = data.get('id')
        if not post_id:
            return jsonify({'status': 'error', 'message': '缺少动态ID'}), 400

        try:
            post = GuidePost.get(GuidePost.id == post_id)
        except GuidePost.DoesNotExist:
            return jsonify({'status': 'error', 'message': '动态不存在'}), 404

        if post.student_id != request.student_id:
            return jsonify({'status': 'error', 'message': '只能删除自己的动态'}), 403

        # 先删除媒体文件，再软删除记录
        _delete_media_files(post)

        post.is_deleted = True
        post.save()

        return jsonify({'status': 'ok', 'message': '删除成功'})
    except Exception as e:
        logger.error(f"删除动态失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================
# 搜索与标签
# ============================================================

@guide_bp.route('/api/guide/search', methods=['GET'])
@student_required
def api_guide_search():
    """搜索动态"""
    try:
        from models import GuidePost, GuideLike, GuideFavorite

        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return jsonify({'status': 'error', 'message': '请输入搜索关键词'}), 400

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        query = GuidePost.select().where(
            (GuidePost.is_deleted == False) & (
                (GuidePost.content.contains(keyword)) |
                (GuidePost.device_tags.contains(keyword)) |
                (GuidePost.location_tag.contains(keyword)) |
                (GuidePost.student_name.contains(keyword))
            )
        )

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))

        posts = query.order_by(GuidePost.id.desc()).paginate(page, page_size)

        # 获取当前用户的点赞和收藏状态（仅查询当前页的 post_id，避免全表扫描）
        current_student_id = _get_optional_student_id()
        liked_ids = set()
        favorited_ids = set()
        if current_student_id:
            page_post_ids = [p.id for p in posts]
            if page_post_ids:
                liked_ids = {l.post_id for l in
                             GuideLike.select(GuideLike.post_id).where(
                                 (GuideLike.post_id.in_(page_post_ids)) &
                                 (GuideLike.student_id == current_student_id))}
                favorited_ids = {f.post_id for f in
                                 GuideFavorite.select(GuideFavorite.post_id).where(
                                     (GuideFavorite.post_id.in_(page_post_ids)) &
                                     (GuideFavorite.student_id == current_student_id))}

        records = []
        for post in posts:
            d = post.to_dict()
            d['is_liked'] = post.id in liked_ids
            d['is_favorited'] = post.id in favorited_ids
            records.append(d)

        return jsonify({
            'status': 'ok',
            'records': records,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        })
    except Exception as e:
        logger.error(f"搜索动态失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@guide_bp.route('/api/guide/available-tags', methods=['GET'])
@student_required
def api_guide_available_tags():
    """获取系统中所有可用的设备标签和地点标签（与项目数据联动）"""
    try:
        from models import Repair

        # 设备标签：从报修记录中提取所有使用过的故障类型 + 预设列表
        preset_device_tags = ['中控', '电脑', '投影仪', '音响', '麦克风', '展台', '幕布', '网络', '软件', '其他']
        used_types = set()
        for r in Repair.select(Repair.fault_type).distinct():
            if r.fault_type and r.fault_type.strip():
                used_types.add(r.fault_type.strip())
        # 合并：预设 + 数据库中出现过的（去重，保持顺序）
        all_device_tags = list(preset_device_tags)
        for t in used_types:
            if t not in all_device_tags:
                all_device_tags.append(t)

        # 地点标签：从报修记录中提取楼栋名
        used_buildings = set()
        for r in Repair.select(Repair.classroom).distinct():
            if r.classroom:
                # 从教室名提取楼栋（去掉数字部分）
                import re
                building = re.sub(r'[\d]+.*$', '', r.classroom.strip())
                if building:
                    used_buildings.add(building)

        # 也从防坑指南中提取已使用的地点标签
        from models import GuidePost
        for p in GuidePost.select(GuidePost.location_tag).distinct():
            if p.location_tag and p.location_tag.strip():
                used_buildings.add(p.location_tag.strip())

        location_tags = sorted(used_buildings) if used_buildings else ['行者楼', '达者楼', '智者楼', '仁者楼']

        return jsonify({
            'status': 'ok',
            'data': {
                'device_tags': all_device_tags,
                'location_tags': location_tags,
            }
        })
    except Exception as e:
        logger.error(f"获取可用标签失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@guide_bp.route('/api/guide/tags', methods=['GET'])
@student_required
def api_guide_tags():
    """获取所有标签及数量"""
    try:
        from models import GuidePost

        posts = GuidePost.select(
            GuidePost.device_tags, GuidePost.location_tag
        ).where(GuidePost.is_deleted == False)

        device_counts = {}
        location_counts = {}

        for post in posts:
            # 统计设备标签
            try:
                tags = json.loads(post.device_tags) if post.device_tags else []
                for tag in tags:
                    device_counts[tag] = device_counts.get(tag, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass
            # 统计地点标签
            if post.location_tag:
                location_counts[post.location_tag] = location_counts.get(
                    post.location_tag, 0) + 1

        device_tags = [{'name': k, 'count': v} for k, v in
                       sorted(device_counts.items(), key=lambda x: -x[1])]
        location_tags = [{'name': k, 'count': v} for k, v in
                         sorted(location_counts.items(), key=lambda x: -x[1])]

        return jsonify({
            'status': 'ok',
            'data': {
                'device_tags': device_tags,
                'location_tags': location_tags,
            }
        })
    except Exception as e:
        logger.error(f"获取标签失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================
# 点赞
# ============================================================

@guide_bp.route('/api/guide/like', methods=['POST'])
@student_required
def api_guide_like():
    """点赞/取消点赞（使用原子计数器，避免并发竞态）"""
    try:
        from models import GuidePost, GuideLike
        from peewee import fn as pw_fn

        data = request.get_json() or {}
        post_id = data.get('id')
        if not post_id:
            return jsonify({'status': 'error', 'message': '缺少动态ID'}), 400

        try:
            post = GuidePost.get(
                (GuidePost.id == post_id) & (GuidePost.is_deleted == False))
        except GuidePost.DoesNotExist:
            return jsonify({'status': 'error', 'message': '动态不存在'}), 404

        student_id = request.student_id

        # 检查是否已点赞
        existing = GuideLike.select().where(
            (GuideLike.post_id == post_id) &
            (GuideLike.student_id == student_id)
        ).first()

        if existing:
            # 取消点赞：原子减1
            existing.delete_instance()
            GuidePost.update(
                like_count=pw_fn.MAX(0, GuidePost.like_count - 1)
            ).where(GuidePost.id == post_id).execute()
            is_liked = False
        else:
            # 点赞：原子加1
            GuideLike.create(
                post_id=post_id,
                student_id=student_id,
                created_at=_now(),
            )
            GuidePost.update(
                like_count=GuidePost.like_count + 1
            ).where(GuidePost.id == post_id).execute()
            is_liked = True

        # 读取最新计数返回给前端
        post = GuidePost.get(GuidePost.id == post_id)

        return jsonify({
            'status': 'ok',
            'data': {
                'is_liked': is_liked,
                'like_count': post.like_count,
            }
        })
    except Exception as e:
        logger.error(f"点赞操作失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================
# 评论
# ============================================================

@guide_bp.route('/api/guide/comment', methods=['POST'])
@student_required
def api_guide_comment():
    """发表评论"""
    try:
        from models import GuidePost, GuideComment

        data = request.get_json() or {}
        post_id = data.get('post_id')
        content = (data.get('content') or '').strip()
        reply_to_id = data.get('reply_to_id')

        if not post_id:
            return jsonify({'status': 'error', 'message': '缺少动态ID'}), 400
        if not content:
            return jsonify({'status': 'error', 'message': '请输入评论内容'}), 400
        if len(content) > 200:
            return jsonify({'status': 'error', 'message': '评论内容最多200字'}), 400

        try:
            post = GuidePost.get(
                (GuidePost.id == post_id) & (GuidePost.is_deleted == False))
        except GuidePost.DoesNotExist:
            return jsonify({'status': 'error', 'message': '动态不存在'}), 404

        # 内容安全
        import re
        content = re.sub(r'<[^>]+>', '', content)

        # 获取被回复者姓名
        reply_to_name = ''
        if reply_to_id:
            try:
                reply_comment = GuideComment.get(GuideComment.id == reply_to_id)
                reply_to_name = reply_comment.student_name
            except GuideComment.DoesNotExist:
                pass

        comment = GuideComment.create(
            post_id=post_id,
            student_id=request.student_id,
            student_name=request.student_name,
            content=content,
            reply_to_id=reply_to_id,
            reply_to_name=reply_to_name,
            created_at=_now(),
        )

        # 更新评论计数（原子操作，避免并发丢失）
        from peewee import fn as pw_fn
        GuidePost.update(
            comment_count=GuidePost.comment_count + 1
        ).where(GuidePost.id == post_id).execute()

        return jsonify({'status': 'ok', 'data': {'id': comment.id}})
    except Exception as e:
        logger.error(f"发表评论失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@guide_bp.route('/api/guide/comment/list', methods=['GET'])
@student_required
def api_guide_comment_list():
    """获取评论列表"""
    try:
        from models import GuideComment

        post_id = request.args.get('post_id', type=int)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        if not post_id:
            return jsonify({'status': 'error', 'message': '缺少动态ID'}), 400

        query = GuideComment.select().where(
            (GuideComment.post_id == post_id) &
            (GuideComment.is_deleted == False)
        )

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))

        comments = query.paginate(page, page_size)
        records = [c.to_dict() for c in comments]

        return jsonify({
            'status': 'ok',
            'records': records,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        })
    except Exception as e:
        logger.error(f"获取评论列表失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@guide_bp.route('/api/guide/comment/delete', methods=['POST'])
@student_required
def api_guide_comment_delete():
    """删除自己的评论（软删除）"""
    try:
        from models import GuidePost, GuideComment

        data = request.get_json() or {}
        comment_id = data.get('id')
        if not comment_id:
            return jsonify({'status': 'error', 'message': '缺少评论ID'}), 400

        try:
            comment = GuideComment.get(GuideComment.id == comment_id)
        except GuideComment.DoesNotExist:
            return jsonify({'status': 'error', 'message': '评论不存在'}), 404

        if comment.student_id != request.student_id:
            return jsonify({'status': 'error', 'message': '只能删除自己的评论'}), 403

        comment.is_deleted = True
        comment.save()

        # 原子更新评论计数
        from peewee import fn as pw_fn
        GuidePost.update(
            comment_count=pw_fn.MAX(0, GuidePost.comment_count - 1)
        ).where(GuidePost.id == comment.post_id).execute()

        return jsonify({'status': 'ok', 'message': '删除成功'})
    except Exception as e:
        logger.error(f"删除评论失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================
# 收藏
# ============================================================

@guide_bp.route('/api/guide/favorite', methods=['POST'])
@student_required
def api_guide_favorite():
    """收藏/取消收藏（使用原子计数器，避免并发竞态）"""
    try:
        from models import GuidePost, GuideFavorite
        from peewee import fn as pw_fn

        data = request.get_json() or {}
        post_id = data.get('id')
        if not post_id:
            return jsonify({'status': 'error', 'message': '缺少动态ID'}), 400

        try:
            post = GuidePost.get(
                (GuidePost.id == post_id) & (GuidePost.is_deleted == False))
        except GuidePost.DoesNotExist:
            return jsonify({'status': 'error', 'message': '动态不存在'}), 404

        student_id = request.student_id

        existing = GuideFavorite.select().where(
            (GuideFavorite.post_id == post_id) &
            (GuideFavorite.student_id == student_id)
        ).first()

        if existing:
            # 取消收藏：原子减1
            existing.delete_instance()
            GuidePost.update(
                favorite_count=pw_fn.MAX(0, GuidePost.favorite_count - 1)
            ).where(GuidePost.id == post_id).execute()
            is_favorited = False
        else:
            # 收藏：原子加1
            GuideFavorite.create(
                post_id=post_id,
                student_id=student_id,
                created_at=_now(),
            )
            GuidePost.update(
                favorite_count=GuidePost.favorite_count + 1
            ).where(GuidePost.id == post_id).execute()
            is_favorited = True

        # 读取最新计数返回给前端
        post = GuidePost.get(GuidePost.id == post_id)

        return jsonify({
            'status': 'ok',
            'data': {
                'is_favorited': is_favorited,
                'favorite_count': post.favorite_count,
            }
        })
    except Exception as e:
        logger.error(f"收藏操作失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================
# 个人中心
# ============================================================

@guide_bp.route('/api/guide/my-posts', methods=['GET'])
@student_required
def api_guide_my_posts():
    """获取我的发布"""
    try:
        from models import GuidePost

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        query = GuidePost.select().where(
            (GuidePost.student_id == request.student_id) &
            (GuidePost.is_deleted == False)
        )

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))

        posts = query.order_by(GuidePost.id.desc()).paginate(page, page_size)
        records = [p.to_dict() for p in posts]

        return jsonify({
            'status': 'ok',
            'records': records,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        })
    except Exception as e:
        logger.error(f"获取我的发布失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@guide_bp.route('/api/guide/my-favorites', methods=['GET'])
@student_required
def api_guide_my_favorites():
    """获取我的收藏（批量查询优化，消除 N+1 问题）"""
    try:
        from models import GuidePost, GuideFavorite, GuideLike

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        # 获取收藏的动态ID列表
        fav_query = GuideFavorite.select().where(
            GuideFavorite.student_id == request.student_id
        ).order_by(GuideFavorite.id.desc())

        total = fav_query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))

        favs = fav_query.paginate(page, page_size)
        post_ids = [f.post_id for f in favs]

        if not post_ids:
            return jsonify({
                'status': 'ok',
                'records': [],
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
            })

        # 批量查询动态详情（一条 SQL 替代 N 条）
        posts = GuidePost.select().where(
            (GuidePost.id.in_(post_ids)) & (GuidePost.is_deleted == False)
        )
        post_map = {p.id: p for p in posts}

        # 批量查询当前用户的点赞状态
        liked_ids = set()
        if post_ids:
            liked_ids = {l.post_id for l in
                         GuideLike.select(GuideLike.post_id).where(
                             (GuideLike.post_id.in_(post_ids)) &
                             (GuideLike.student_id == request.student_id))}

        # 按收藏顺序组装结果（保持分页排序）
        records = []
        for pid in post_ids:
            post = post_map.get(pid)
            if not post:
                continue
            d = post.to_dict()
            d['is_liked'] = pid in liked_ids
            d['is_favorited'] = True
            records.append(d)

        return jsonify({
            'status': 'ok',
            'records': records,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        })
    except Exception as e:
        logger.error(f"获取我的收藏失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@guide_bp.route('/api/guide/stats', methods=['GET'])
@student_required
def api_guide_stats():
    """获取个人防坑指南统计（@student_required 已验证 token，直接用 request.student_id）"""
    try:
        from models import GuidePost, GuideFavorite

        # @student_required 已验证 token 有效性并设置 request.student_id
        # 无需再次解析 token，直接使用 request 上下文中的已验证信息
        student_id = request.student_id

        post_count = GuidePost.select().where(
            (GuidePost.student_id == student_id) &
            (GuidePost.is_deleted == False)
        ).count()

        favorite_count = GuideFavorite.select().where(
            GuideFavorite.student_id == student_id
        ).count()

        return jsonify({
            'status': 'ok',
            'data': {
                'post_count': post_count,
                'favorite_count': favorite_count,
            }
        })
    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================
# 视频上传
# ============================================================

@guide_bp.route('/api/guide/upload-video', methods=['POST'])
@student_required
def api_guide_upload_video():
    """上传视频（≤60秒，≤50MB）"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': '没有选择文件'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'status': 'error', 'message': '文件名为空'}), 400

        # 解析扩展名（兼容无扩展名和各种格式）
        ext = os.path.splitext(file.filename)[1].lower()
        if not ext:
            ext = '.mp4'  # 默认mp4
        # 清理扩展名中的查询参数等
        if '?' in ext:
            ext = ext.split('?')[0]
        if ext not in ('.mp4', '.mov', '.avi', '.3gp', '.m4v'):
            ext = '.mp4'  # 不认识的格式默认按mp4处理

        # 读取文件内容
        file_data = file.read()

        # 校验文件大小（≤50MB）
        if len(file_data) > 50 * 1024 * 1024:
            return jsonify({'status': 'error', 'message': '视频大小不能超过50MB'}), 400

        # 保存文件
        filename = f"{uuid.uuid4().hex}{ext}"
        upload_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'uploads', 'guide_videos')
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(file_data)

        # 获取视频时长（ffprobe未安装时返回0，不影响上传）
        duration = _get_video_duration(filepath)
        if duration > 60:
            os.remove(filepath)
            return jsonify({'status': 'error', 'message': '视频时长不能超过60秒'}), 400

        logger.info(f"视频上传成功: {filename}, 时长: {duration}秒, 大小: {len(file_data)}字节")

        return jsonify({
            'status': 'ok',
            'data': {
                'url': f'/uploads/guide_videos/{filename}',
                'duration': duration,
            }
        })
    except Exception as e:
        logger.error(f"上传视频失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
