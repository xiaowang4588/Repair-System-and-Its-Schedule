"""
Peewee ORM 模型定义
替代 JSON 文件存储，提供事务保障和并发安全。
"""
import os
import json
import time
import logging
from datetime import datetime
from peewee import (
    Model, SqliteDatabase, AutoField, CharField, IntegerField,
    BooleanField, TextField, ForeignKeyField, DateField
)

logger = logging.getLogger(__name__)

# 数据库路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'repair.db')


class RetrySqliteDatabase(SqliteDatabase):
    """支持自动重试的 SQLite 数据库连接
    当遇到 'database is locked' 错误时自动重试，解决 Gunicorn 多 worker 并发写入问题。"""

    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 0.1  # 100ms 基础延迟，指数退避

    def execute_sql(self, sql, params=None, commit=None):
        """执行 SQL，遇到锁定错误时自动重试"""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                if commit is not None:
                    return super().execute_sql(sql, params, commit)
                return super().execute_sql(sql, params)
            except Exception as e:
                err_str = str(e).lower()
                if ('locked' in err_str or 'busy' in err_str) and attempt < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"[DB] 数据库锁定，第 {attempt + 1} 次重试，等待 {delay:.1f}s: {sql[:80]}")
                    time.sleep(delay)
                    continue
                raise


# 数据库连接（使用支持重试的自定义数据库类）
db = RetrySqliteDatabase(DB_PATH, pragmas={
    'journal_mode': 'wal',       # WAL模式，提升并发读写性能
    'busy_timeout': 15000,       # 忙等待15秒（原5秒在高并发下不够）
    'foreign_keys': 1,           # 启用外键约束
    'synchronous': 'normal',     # WAL模式下用NORMAL即可，减少fsync开销
})


class BaseModel(Model):
    """基础模型类"""
    class Meta:
        database = db


class Repair(BaseModel):
    """报修记录表"""
    id = AutoField(primary_key=True)
    student_id = CharField(default='')
    student_name = CharField(default='')
    semester = CharField(default='')
    classroom = CharField(default='')
    report_time = CharField(default='')
    week_number = IntegerField(default=0)
    fault_type = CharField(default='')
    reporter_name = CharField(default='')
    reporter_college = CharField(default='')
    is_external_teacher = BooleanField(default=False)
    report_method = CharField(default='')
    handler_name = CharField(default='')
    is_device_replaced = BooleanField(default=False)
    device_replace_note = CharField(default='')
    status = CharField(default='未处理')
    fault_cause = CharField(default='')
    solution = CharField(default='')
    completion_time = CharField(default='')
    final_status = CharField(default='')
    photo_url = CharField(default='')
    new_classroom = CharField(default='')
    notes = CharField(default='')
    note_images = TextField(default='[]')  # JSON字符串
    created_at = CharField(default='')
    updated_at = CharField(default='')

    class Meta:
        table_name = 'repairs'
        indexes = (
            (('status',), False),
            (('report_time',), False),
            (('student_id',), False),
            (('semester',), False),
            (('handler_name',), False),
            (('reporter_college',), False),
            (('fault_type',), False),
        )

    def to_dict(self) -> dict:
        """转换为字典（兼容旧的JSON格式，含修改日志）"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'semester': self.semester,
            'classroom': self.classroom,
            'report_time': self.report_time,
            'week_number': self.week_number,
            'fault_type': self.fault_type,
            'reporter_name': self.reporter_name,
            'reporter_college': self.reporter_college,
            'is_external_teacher': self.is_external_teacher,
            'report_method': self.report_method,
            'handler_name': self.handler_name,
            'is_device_replaced': self.is_device_replaced,
            'device_replace_note': self.device_replace_note,
            'status': self.status,
            'fault_cause': self.fault_cause,
            'solution': self.solution,
            'completion_time': self.completion_time,
            'final_status': self.final_status,
            'photo_url': self.photo_url,
            'new_classroom': self.new_classroom,
            'notes': self.notes,
            'note_images': self.get_note_images(),
            'modification_log': [log.to_dict() for log in self.logs.order_by(ModificationLog.id)],
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    def to_dict_light(self) -> dict:
        """轻量版字典（不含修改日志，用于批量查询避免 N+1）"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'semester': self.semester,
            'classroom': self.classroom,
            'report_time': self.report_time,
            'week_number': self.week_number,
            'fault_type': self.fault_type,
            'reporter_name': self.reporter_name,
            'reporter_college': self.reporter_college,
            'is_external_teacher': self.is_external_teacher,
            'report_method': self.report_method,
            'handler_name': self.handler_name,
            'is_device_replaced': self.is_device_replaced,
            'device_replace_note': self.device_replace_note,
            'status': self.status,
            'fault_cause': self.fault_cause,
            'solution': self.solution,
            'completion_time': self.completion_time,
            'final_status': self.final_status,
            'photo_url': self.photo_url,
            'new_classroom': self.new_classroom,
            'notes': self.notes,
            'note_images': self.get_note_images(),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    def get_note_images(self) -> list:
        """获取备注图片列表"""
        try:
            return json.loads(self.note_images)
        except (json.JSONDecodeError, TypeError):
            return []


class ModificationLog(BaseModel):
    """修改日志表"""
    id = AutoField(primary_key=True)
    repair = ForeignKeyField(Repair, backref='logs', on_delete='CASCADE')
    change_time = CharField()
    changes = TextField()  # JSON字符串

    class Meta:
        table_name = 'modification_logs'

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'time': self.change_time,
            'changes': json.loads(self.changes) if self.changes else [],
        }


class Config(BaseModel):
    """系统配置表"""
    key = CharField(primary_key=True)
    value = TextField()

    class Meta:
        table_name = 'config'


class Student(BaseModel):
    """学生账号表"""
    id = AutoField(primary_key=True)
    student_id = CharField(unique=True, index=True)  # 学号
    name = CharField(default='')                       # 姓名
    college = CharField(default='')                    # 学院
    password_hash = CharField(default='')              # 密码哈希
    created_at = CharField(default='')

    class Meta:
        table_name = 'students'

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'created_at': self.created_at,
        }


class GuidePost(BaseModel):
    """防坑指南动态表"""
    id = AutoField(primary_key=True)
    student_id = CharField(max_length=50, index=True)       # 发布者学号
    student_name = CharField(max_length=50, default='')     # 发布者姓名
    content = TextField(default='')                         # 文字内容
    images = TextField(default='[]')                        # 图片路径列表（JSON数组）
    video_url = CharField(max_length=500, default='')       # 视频路径
    video_duration = IntegerField(default=0)                # 视频时长（秒）
    device_tags = CharField(max_length=200, default='[]')   # 设备标签（JSON数组）
    location_tag = CharField(max_length=50, default='')     # 地点标签
    like_count = IntegerField(default=0)                    # 点赞数
    comment_count = IntegerField(default=0)                 # 评论数
    favorite_count = IntegerField(default=0)                # 收藏数
    is_deleted = BooleanField(default=False)                # 软删除
    created_at = CharField(default='')                      # 发布时间
    updated_at = CharField(default='')                      # 更新时间

    class Meta:
        table_name = 'guide_posts'
        order_by = ('-id',)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'content': self.content,
            'images': self._parse_json(self.images, []),
            'video_url': self.video_url,
            'video_duration': self.video_duration,
            'device_tags': self._parse_json(self.device_tags, []),
            'location_tag': self.location_tag,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'favorite_count': self.favorite_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    @staticmethod
    def _parse_json(text, default):
        try:
            return json.loads(text) if text else default
        except (json.JSONDecodeError, TypeError):
            return default


class GuideLike(BaseModel):
    """防坑指南点赞表"""
    id = AutoField(primary_key=True)
    post = ForeignKeyField(GuidePost, backref='likes', on_delete='CASCADE')  # 关联动态
    student_id = CharField(max_length=50, index=True)       # 点赞者学号
    created_at = CharField(default='')

    class Meta:
        table_name = 'guide_likes'
        indexes = (
            (('post_id', 'student_id'), True),  # 唯一索引
        )


class GuideComment(BaseModel):
    """防坑指南评论表"""
    id = AutoField(primary_key=True)
    post = ForeignKeyField(GuidePost, backref='comments', on_delete='CASCADE')  # 关联动态
    student_id = CharField(max_length=50)                   # 评论者学号
    student_name = CharField(max_length=50, default='')     # 评论者姓名
    content = TextField(default='')                         # 评论内容
    reply_to_id = IntegerField(null=True)                   # 回复的评论ID
    reply_to_name = CharField(max_length=50, default='')    # 被回复者姓名
    is_deleted = BooleanField(default=False)                # 软删除
    created_at = CharField(default='')

    class Meta:
        table_name = 'guide_comments'
        order_by = ('id',)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'post_id': self.post_id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'content': self.content,
            'reply_to_id': self.reply_to_id,
            'reply_to_name': self.reply_to_name,
            'created_at': self.created_at,
        }


class GuideFavorite(BaseModel):
    """防坑指南收藏表"""
    id = AutoField(primary_key=True)
    post = ForeignKeyField(GuidePost, backref='favorites', on_delete='CASCADE')  # 关联动态
    student_id = CharField(max_length=50, index=True)       # 收藏者学号
    created_at = CharField(default='')

    class Meta:
        table_name = 'guide_favorites'
        indexes = (
            (('post_id', 'student_id'), True),  # 唯一索引
        )


class TokenRevocation(BaseModel):
    """Token吊销记录表（密码修改后批量失效旧Token）"""
    id = AutoField(primary_key=True)
    user_type = CharField(max_length=20)   # 'admin' 或 'student'
    user_id = CharField(max_length=100)    # 管理员用户名 或 学生学号
    revoked_at = CharField()               # 吊销时间戳（Unix秒）
    reason = CharField(default='')          # 吊销原因（如 'password_change'）
    created_at = CharField(default='')      # 记录创建时间

    class Meta:
        table_name = 'token_revocations'
        indexes = (
            (('user_type', 'user_id'), False),
        )


class SecurityEvent(BaseModel):
    """安全事件日志表（入侵检测、异常行为记录）"""
    id = AutoField(primary_key=True)
    event_type = CharField(max_length=50)   # 事件类型：login_failure, ip_lockout, off_hours_access, bulk_export, abnormal_ua
    severity = CharField(max_length=20)     # 严重级别：INFO, WARNING, CRITICAL
    source_ip = CharField(max_length=50)    # 来源IP
    user_type = CharField(max_length=20, default='')  # admin / student
    user_id = CharField(max_length=100, default='')    # 用户标识
    detail = TextField(default='')          # 事件详情（JSON）
    created_at = CharField(default='')      # 事件时间

    class Meta:
        table_name = 'security_events'
        indexes = (
            (('event_type',), False),
            (('severity',), False),
            (('source_ip',), False),
            (('created_at',), False),
        )


def init_db():
    """初始化数据库（创建表）"""
    db.connect(reuse_if_open=True)
    db.create_tables([Repair, ModificationLog, Config, Student,
                      GuidePost, GuideLike, GuideComment, GuideFavorite,
                      TokenRevocation, SecurityEvent])
    db.close()


def get_db():
    """获取数据库连接"""
    if db.is_closed():
        db.connect(reuse_if_open=True)
    return db
