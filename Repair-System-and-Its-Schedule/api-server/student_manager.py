"""
学生账号管理模块
负责学生账号的增删改查、登录验证。
"""
import hashlib
import logging
import secrets
import os
from datetime import datetime
from models import Student

logger = logging.getLogger(__name__)

# 默认密码从环境变量读取，如果未设置则使用随机密码
DEFAULT_PASSWORD = os.environ.get('STUDENT_DEFAULT_PASSWORD', '123456')


def _hash_password(password: str, salt: str = '') -> str:
    """
    密码哈希（带盐）
    使用SHA-256 + 随机盐，提高安全性
    """
    if not salt:
        salt = secrets.token_hex(16)
    # 将盐和密码组合后哈希
    hash_value = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${hash_value}"


def _verify_password(password: str, stored_hash: str) -> bool:
    """
    验证密码
    stored_hash格式: salt$hash_value
    """
    if '$' in stored_hash:
        salt, hash_value = stored_hash.split('$', 1)
        return _hash_password(password, salt) == stored_hash
    # 兼容旧格式（纯SHA-256无盐）
    return hashlib.sha256(password.encode()).hexdigest() == stored_hash


def create_student(student_id: str, name: str, password: str = '') -> dict:
    """创建学生账号"""
    if not student_id or not name:
        return {'error': '学号和姓名不能为空'}

    # 检查学号是否已存在
    if Student.select().where(Student.student_id == student_id).exists():
        return {'error': f'学号 {student_id} 已存在'}

    pwd = password if password else DEFAULT_PASSWORD
    student = Student.create(
        student_id=student_id,
        name=name,
        password_hash=_hash_password(pwd),
        created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    )
    logger.info(f"创建学生账号: {student_id} - {name}")
    return student.to_dict()


def batch_create_students(students: list) -> dict:
    """批量创建学生账号"""
    success = 0
    errors = []
    duplicates = []

    for s in students:
        sid = str(s.get('student_id', '')).strip()
        name = str(s.get('name', '')).strip()

        if not sid or not name:
            errors.append({'student_id': sid, 'message': '学号或姓名为空'})
            continue

        if Student.select().where(Student.student_id == sid).exists():
            duplicates.append({'student_id': sid, 'name': name})
            continue

        Student.create(
            student_id=sid,
            name=name,
            password_hash=_hash_password(DEFAULT_PASSWORD),
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
        success += 1

    return {
        'success_count': success,
        'error_count': len(errors),
        'duplicate_count': len(duplicates),
        'errors': errors[:20],
        'duplicates': duplicates[:20],
    }


def get_student_list(keyword: str = '', page: int = 1, page_size: int = 50) -> dict:
    """获取学生列表"""
    query = Student.select()

    if keyword:
        query = query.where(
            (Student.student_id.contains(keyword)) |
            (Student.name.contains(keyword))
        )

    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))

    students = query.order_by(Student.student_id).paginate(page, page_size)
    return {
        'records': [s.to_dict() for s in students],
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    }


def update_student(student_id: str, data: dict) -> dict:
    """更新学生信息"""
    try:
        student = Student.get(Student.student_id == student_id)
    except Student.DoesNotExist:
        return {'error': '学生不存在'}

    if 'name' in data:
        student.name = data['name']
    student.save()

    logger.info(f"更新学生信息: {student_id}")
    return student.to_dict()


def change_password(student_id: str, old_password: str, new_password: str) -> dict:
    """修改密码（学生自助）"""
    try:
        student = Student.get(Student.student_id == student_id)
    except Student.DoesNotExist:
        return {'error': '学生不存在'}

    if not _verify_password(old_password, student.password_hash):
        return {'error': '原密码错误'}

    student.password_hash = _hash_password(new_password)
    student.save()
    logger.info(f"学生修改密码: {student_id}")
    return {'success': True}


def admin_reset_password(student_id: str, new_password: str = '') -> dict:
    """管理员重置密码"""
    try:
        student = Student.get(Student.student_id == student_id)
    except Student.DoesNotExist:
        return {'error': '学生不存在'}

    pwd = new_password if new_password else DEFAULT_PASSWORD
    student.password_hash = _hash_password(pwd)
    student.save()
    logger.info(f"管理员重置密码: {student_id}")
    return {'success': True, 'message': f'密码已重置为 {pwd}'}


def delete_student(student_id: str) -> dict:
    """删除学生账号"""
    deleted = Student.delete().where(Student.student_id == student_id).execute()
    if deleted > 0:
        logger.info(f"删除学生账号: {student_id}")
        return {'success': True}
    return {'error': '学生不存在'}


def verify_student(student_id: str, password: str) -> dict:
    """验证学生登录"""
    try:
        student = Student.get(Student.student_id == student_id)
    except Student.DoesNotExist:
        return {'error': '学号不存在'}

    if not _verify_password(password, student.password_hash):
        return {'error': '密码错误'}

    return {
        'success': True,
        'student_id': student.student_id,
        'name': student.name,
    }


def get_student_by_id(student_id: str) -> dict:
    """根据学号获取学生信息"""
    try:
        student = Student.get(Student.student_id == student_id)
        return student.to_dict()
    except Student.DoesNotExist:
        return {}


def get_student_stats() -> dict:
    """学生账号统计"""
    total = Student.select().count()
    return {
        'total': total,
    }
