"""
Peewee ORM 模型定义
替代 JSON 文件存储，提供事务保障和并发安全。
"""
import os
import json
from datetime import datetime
from peewee import (
    Model, SqliteDatabase, AutoField, CharField, IntegerField,
    BooleanField, TextField, ForeignKeyField, DateField
)

# 数据库路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'repair.db')

# 数据库连接
db = SqliteDatabase(DB_PATH, pragmas={
    'journal_mode': 'wal',      # WAL模式，提升并发读写性能
    'busy_timeout': 5000,       # 忙等待5秒，避免锁冲突
    'foreign_keys': 1,          # 启用外键约束
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

    def to_dict(self) -> dict:
        """转换为字典（兼容旧的JSON格式）"""
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
    post_id = IntegerField(index=True)                      # 关联动态ID
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
    post_id = IntegerField(index=True)                      # 关联动态ID
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
    post_id = IntegerField(index=True)                      # 关联动态ID
    student_id = CharField(max_length=50, index=True)       # 收藏者学号
    created_at = CharField(default='')

    class Meta:
        table_name = 'guide_favorites'
        indexes = (
            (('post_id', 'student_id'), True),  # 唯一索引
        )


def init_db():
    """初始化数据库（创建表）"""
    db.connect(reuse_if_open=True)
    db.create_tables([Repair, ModificationLog, Config, Student,
                      GuidePost, GuideLike, GuideComment, GuideFavorite])
    db.close()


def get_db():
    """获取数据库连接"""
    if db.is_closed():
        db.connect(reuse_if_open=True)
    return db
