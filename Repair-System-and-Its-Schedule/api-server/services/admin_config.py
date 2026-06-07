"""
后台管理配置模块
管理管理员账号、数据源配置、系统设置等。
配置存储在 config.json 文件中。
"""
import os
import json
import hashlib
import secrets
import threading
import tempfile
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

# Bug2 修复: 配置文件读写锁，防止并发读写导致配置损坏
_config_lock = threading.Lock()

# 内存缓存配置，避免每次读磁盘
_cached_config = None

# 管理员密码从 .env 文件读取，如果未设置则生成随机密码并在终端打印
_default_pwd = os.environ.get('ADMIN_PASSWORD', '').strip()
if not _default_pwd:
    _default_pwd = secrets.token_urlsafe(12)
    print(f"[WARN] ADMIN_PASSWORD not configured. Generated random password: {_default_pwd}")
    print(f"       Set ADMIN_PASSWORD in .env file to use a fixed password.")
DEFAULT_ADMIN_PASSWORD = _default_pwd


# ============ 密码哈希工具函数（必须在 DEFAULT_CONFIG 和 sync_admin_password 之前定义） ============

def _hash_admin_password(password: str, salt: str = '') -> str:
    """
    管理员密码哈希（带盐，与学生密码安全级别一致）
    格式: salt$hash_value
    """
    if not salt:
        salt = secrets.token_hex(16)
    hash_value = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${hash_value}"


def _verify_admin_password(password: str, stored_hash: str) -> bool:
    """
    验证管理员密码（兼容新旧两种格式）
    新格式: salt$hash_value
    旧格式: 纯SHA-256哈希（64位十六进制，无$分隔符）
    """
    if '$' in stored_hash:
        # 新格式：带盐SHA-256
        return _hash_admin_password(password, stored_hash.split('$', 1)[0]) == stored_hash
    # 兼容旧格式：无盐SHA-256
    return hashlib.sha256(password.encode()).hexdigest() == stored_hash


def _needs_rehash(stored_hash: str) -> bool:
    """检查密码哈希是否需要升级（旧格式→新格式）"""
    return '$' not in stored_hash


def sync_admin_password():
    """
    启动时检查 config.json 中的管理员密码是否与 .env 中的 ADMIN_PASSWORD 一致。
    如果 .env 设了密码但 config.json 中的哈希不匹配，自动更新 config.json。
    使用带盐哈希格式，兼容旧的无盐格式自动升级。
    """
    env_pwd = os.environ.get('ADMIN_PASSWORD', '').strip()
    if not env_pwd:
        return  # .env 没设密码，不需要同步

    config = load_config()
    stored_hash = config.get("admin", {}).get("password_hash", "")

    # 使用新的验证函数（兼容新旧格式）
    if not _verify_admin_password(env_pwd, stored_hash):
        # 密码不匹配，用.env的密码更新（带盐哈希）
        config["admin"]["password_hash"] = _hash_admin_password(env_pwd)
        save_config(config)
        print(f"[INFO] Admin password synced from .env file (upgraded to salted hash).")
    elif _needs_rehash(stored_hash):
        # 密码匹配但哈希格式旧，升级为新格式
        config["admin"]["password_hash"] = _hash_admin_password(env_pwd)
        save_config(config)
        print(f"[INFO] Admin password hash upgraded to salted format.")

# 默认配置
DEFAULT_CONFIG = {
    "admin": {
        "username": "wxzx",
        "password_hash": _hash_admin_password(DEFAULT_ADMIN_PASSWORD)
    },
    "datasource": {
        "type": "excel",
        "current_excel": "",
        "api": {
            "base_url": os.environ.get("QINGGUO_BASE_URL", ""),
            "username": os.environ.get("QINGGUO_USERNAME", ""),
            "password": os.environ.get("QINGGUO_PASSWORD", ""),
            "xnm": os.environ.get("QINGGUO_XNM", "2025"),
            "xqm": os.environ.get("QINGGUO_XQM", "12"),
            "xqh_id": os.environ.get("QINGGUO_XQH_ID", "")
        }
    },
    "semester": {
        "start_date": "",       # 学期开始日期（第1周的周一），如 "2026-02-24"
    },
    "cache": {
        "ttl_seconds": 1800,
        "background_refresh": True,
        "fallback_to_stale": True
    }
}


def _ensure_dirs():
    """确保必要的目录存在"""
    os.makedirs(UPLOADS_DIR, exist_ok=True)


def load_config() -> dict:
    """
    加载配置文件，不存在则创建默认配置。
    Bug2 修复: 加读锁，并发安全。
    Bug8 修复: 读取失败时用内存缓存兜底，不覆盖配置文件。
    """
    global _cached_config
    _ensure_dirs()

    with _config_lock:
        if os.path.exists(CONFIG_PATH):
            for attempt in range(3):
                try:
                    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                    _cached_config = cfg  # 更新内存缓存
                    return cfg
                except (json.JSONDecodeError, IOError, OSError):
                    if attempt < 2:
                        import time
                        time.sleep(0.05)  # 短暂等待后重试
                    continue

        # 读取失败，用内存缓存兜底（Bug8: 不覆盖配置文件）
        if _cached_config is not None:
            return _cached_config.copy()

        # 真正的首次启动，创建默认配置
        _write_config_file(DEFAULT_CONFIG)
        _cached_config = DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """
    保存配置到文件。
    Bug2 修复: 加写锁 + 原子写入（先写临时文件再 rename），防止并发写入损坏。
    """
    global _cached_config
    _ensure_dirs()
    with _config_lock:
        _write_config_file(config)
        _cached_config = config.copy()


def _write_config_file(config: dict):
    """原子写入配置文件：先写临时文件，再原子替换，避免写入中途被读到半截"""
    dir_name = os.path.dirname(CONFIG_PATH)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        # os.replace() 是原子操作，不会出现文件不存在的瞬间
        os.replace(tmp_path, CONFIG_PATH)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


def verify_admin(username: str, password: str) -> bool:
    """验证管理员账号密码（自动迁移旧格式哈希）"""
    config = load_config()
    admin = config.get("admin", {})
    if username != admin.get("username", ""):
        return False
    stored_hash = admin.get("password_hash", "")

    if not _verify_admin_password(password, stored_hash):
        return False

    # 自动迁移：旧格式哈希验证成功后，升级为新格式
    if _needs_rehash(stored_hash):
        config["admin"]["password_hash"] = _hash_admin_password(password)
        save_config(config)
        logger.info("管理员密码哈希已自动升级为带盐格式")

    return True


def get_datasource_config() -> dict:
    """获取数据源配置"""
    config = load_config()
    return config.get("datasource", DEFAULT_CONFIG["datasource"])


def set_datasource_type(ds_type: str):
    """切换数据源类型"""
    config = load_config()
    config["datasource"]["type"] = ds_type
    save_config(config)


def set_current_excel(file_path: str):
    """设置当前使用的 Excel 文件"""
    config = load_config()
    config["datasource"]["current_excel"] = file_path
    save_config(config)


def get_current_excel_path() -> str:
    """获取当前使用的 Excel 文件完整路径"""
    config = load_config()
    rel_path = config["datasource"].get("current_excel", "")
    if rel_path:
        return os.path.join(BASE_DIR, rel_path)
    return ""


def get_uploads_dir() -> str:
    """获取上传目录路径"""
    _ensure_dirs()
    return UPLOADS_DIR


def get_semester_config() -> dict:
    """获取学期配置"""
    config = load_config()
    return config.get("semester", DEFAULT_CONFIG["semester"])


def set_semester_start(start_date: str):
    """设置学期开始日期"""
    config = load_config()
    if "semester" not in config:
        config["semester"] = DEFAULT_CONFIG["semester"].copy()
    config["semester"]["start_date"] = start_date
    save_config(config)


def get_excel_files() -> list:
    """获取已上传的 Excel 文件列表"""
    _ensure_dirs()
    files = []
    excel_dir = os.path.join(UPLOADS_DIR, "excel")
    os.makedirs(excel_dir, exist_ok=True)

    config = load_config()
    current_excel = config.get("datasource", {}).get("current_excel", "")

    for f in os.listdir(excel_dir):
        if f.endswith(('.xlsx', '.xls')):
            filepath = os.path.join(excel_dir, f)
            rel_path = os.path.relpath(filepath, BASE_DIR)
            files.append({
                'name': f,
                'path': rel_path,
                'size': os.path.getsize(filepath),
                'is_current': rel_path == current_excel,
            })

    # 按修改时间排序
    files.sort(key=lambda x: os.path.getmtime(os.path.join(BASE_DIR, x['path'])), reverse=True)
    return files


def upload_excel(file, year: str = '', semester: str = '') -> dict:
    """上传 Excel 文件"""
    import time as _time
    from werkzeug.utils import secure_filename

    _ensure_dirs()
    excel_dir = os.path.join(UPLOADS_DIR, "excel")
    os.makedirs(excel_dir, exist_ok=True)

    # 限制文件大小（最大 50MB）
    MAX_SIZE = 50 * 1024 * 1024
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_SIZE:
        raise ValueError(f"文件大小 {size / 1024 / 1024:.1f}MB 超过限制 50MB")

    # 安全过滤文件名（防路径穿越）
    safe_name = secure_filename(file.filename)
    if not safe_name:
        safe_name = 'upload.xlsx'
    # secure_filename 可能去掉中文，保留原扩展名
    _, ext = os.path.splitext(file.filename)
    if ext.lower() in ('.xlsx', '.xls'):
        _, safe_ext = os.path.splitext(safe_name)
        if safe_ext.lower() not in ('.xlsx', '.xls'):
            safe_name = safe_name + ext

    filename = safe_name
    if year and semester:
        name, ext = os.path.splitext(filename)
        filename = f"{year}-{semester}_{name}{ext}"

    filepath = os.path.join(excel_dir, filename)

    file.save(filepath)
    # 确保文件完全写入磁盘（Linux 缓存 / Windows 文件锁）
    try:
        with open(filepath, 'rb') as f:
            os.fsync(f.fileno())
    except Exception:
        pass
    _time.sleep(0.5)

    rel_path = os.path.relpath(filepath, BASE_DIR)
    set_current_excel(rel_path)

    return {'filename': filename, 'path': rel_path}


def _validate_excel_path(file_path: str) -> str:
    """
    验证文件路径是否在 uploads/excel 目录内，防止路径穿越。
    返回验证后的完整路径，失败抛出 ValueError。
    """
    excel_dir = os.path.join(UPLOADS_DIR, "excel")
    # 用 realpath 解析 .. 和符号链接
    full_path = os.path.realpath(os.path.join(BASE_DIR, file_path))
    allowed_prefix = os.path.realpath(excel_dir)
    if not full_path.startswith(allowed_prefix + os.sep) and full_path != allowed_prefix:
        raise ValueError(f"路径不允许: {file_path}")
    return full_path


def switch_excel(file_path: str):
    """切换当前使用的 Excel 文件"""
    _validate_excel_path(file_path)  # 验证路径合法性
    set_current_excel(file_path)


def delete_excel(file_path: str):
    """删除 Excel 文件"""
    full_path = _validate_excel_path(file_path)  # 验证路径合法性
    if os.path.exists(full_path):
        os.remove(full_path)

        # 如果删除的是当前文件，清空当前文件设置
        config = load_config()
        if config.get("datasource", {}).get("current_excel") == file_path:
            config["datasource"]["current_excel"] = ""
            save_config(config)


def clear_all_excel() -> dict:
    """
    清除所有 Excel 数据：删除所有上传的文件 + 重置配置中的 Excel 路径。
    返回删除的文件数量。
    """
    _ensure_dirs()
    excel_dir = os.path.join(UPLOADS_DIR, "excel")
    deleted_count = 0

    # 删除所有 Excel 文件
    if os.path.exists(excel_dir):
        for f in os.listdir(excel_dir):
            if f.endswith(('.xlsx', '.xls')):
                filepath = os.path.join(excel_dir, f)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except OSError as e:
                    logger.warning(f"删除文件失败 {filepath}: {e}")

    # 重置配置中的 Excel 路径
    config = load_config()
    config["datasource"]["current_excel"] = ""
    save_config(config)

    logger.info(f"已清除所有 Excel 数据，删除 {deleted_count} 个文件")
    return {'deleted_count': deleted_count}


def save_api_config(data: dict):
    """保存 API 数据源配置"""
    config = load_config()
    if "datasource" not in config:
        config["datasource"] = DEFAULT_CONFIG["datasource"].copy()
    if "api" not in config["datasource"]:
        config["datasource"]["api"] = DEFAULT_CONFIG["datasource"]["api"].copy()

    # 更新 API 配置字段
    api_config = config["datasource"]["api"]
    for key in ['base_url', 'username', 'password', 'xnm', 'xqm', 'xqh_id']:
        if key in data:
            api_config[key] = data[key]

    save_config(config)


def save_cache_settings(data: dict):
    """保存缓存配置"""
    config = load_config()
    if "cache" not in config:
        config["cache"] = DEFAULT_CONFIG["cache"].copy()

    # 更新缓存配置字段
    cache_config = config["cache"]
    for key in ['ttl_seconds', 'background_refresh', 'fallback_to_stale']:
        if key in data:
            cache_config[key] = data[key]

    save_config(config)


def change_password(old_password: str, new_password: str) -> dict:
    """修改管理员密码"""
    config = load_config()
    admin = config.get("admin", {})

    # 验证旧密码（兼容新旧格式）
    stored_hash = admin.get("password_hash", "")
    if not _verify_admin_password(old_password, stored_hash):
        return {'error': '旧密码错误'}

    # 验证新密码长度
    if len(new_password) < 6:
        return {'error': '新密码长度不能少于6位'}

    # 更新密码（使用带盐哈希）
    config["admin"]["password_hash"] = _hash_admin_password(new_password)
    save_config(config)

    return {'success': True}


def get_current_week() -> int:
    """
    获取当前周次（根据学期开始日期自动计算）
    学期开始日期为第1周的周一
    """
    from datetime import datetime
    config = load_config()
    semester = config.get("semester", DEFAULT_CONFIG["semester"])

    start_date_str = semester.get("start_date", "")
    if not start_date_str:
        return 0  # 未设置学期开始日期

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        days_diff = (today - start_date).days
        if days_diff < 0:
            return 0  # 学期还没开始
        current_week = days_diff // 7 + 1
        return min(current_week, 30)  # 最多30周
    except ValueError:
        return 0
