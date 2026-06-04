"""
后台管理配置模块
管理管理员账号、数据源配置、系统设置等。
配置存储在 config.json 文件中。
"""
import os
import json
import hashlib
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

# 默认密码从环境变量读取，如果未设置则生成随机密码
DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', secrets.token_urlsafe(12))

# 默认配置
DEFAULT_CONFIG = {
    "admin": {
        "username": "wxzx",
        "password_hash": hashlib.sha256(DEFAULT_ADMIN_PASSWORD.encode()).hexdigest()
    },
    "datasource": {
        "type": "excel",
        "current_excel": "",
        "api": {
            "base_url": "https://http-10-252-6-31-80.vpn.cqytxy.edu.cn",
            "username": "",
            "password": "",
            "xnm": "2025",
            "xqm": "12",
            "xqh_id": "C67E548C4B4553FFE0530100007F06AD"
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
    """加载配置文件，不存在则创建默认配置"""
    _ensure_dirs()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    # 创建默认配置
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """保存配置到文件"""
    _ensure_dirs()
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def verify_admin(username: str, password: str) -> bool:
    """验证管理员账号密码"""
    config = load_config()
    admin = config.get("admin", {})
    if username != admin.get("username", ""):
        return False
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == admin.get("password_hash", "")


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
    _ensure_dirs()
    excel_dir = os.path.join(UPLOADS_DIR, "excel")
    os.makedirs(excel_dir, exist_ok=True)

    # 生成文件名
    filename = file.filename
    if year and semester:
        name, ext = os.path.splitext(filename)
        filename = f"{year}-{semester}_{name}{ext}"

    filepath = os.path.join(excel_dir, filename)

    # 保存文件
    file.save(filepath)

    # 设置为当前文件
    rel_path = os.path.relpath(filepath, BASE_DIR)
    set_current_excel(rel_path)

    return {'filename': filename, 'path': rel_path}


def switch_excel(file_path: str):
    """切换当前使用的 Excel 文件"""
    set_current_excel(file_path)


def delete_excel(file_path: str):
    """删除 Excel 文件"""
    full_path = os.path.join(BASE_DIR, file_path)
    if os.path.exists(full_path):
        os.remove(full_path)

        # 如果删除的是当前文件，清空当前文件设置
        config = load_config()
        if config.get("datasource", {}).get("current_excel") == file_path:
            config["datasource"]["current_excel"] = ""
            save_config(config)


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

    # 验证旧密码
    old_hash = hashlib.sha256(old_password.encode()).hexdigest()
    if old_hash != admin.get("password_hash", ""):
        return {'error': '旧密码错误'}

    # 验证新密码长度
    if len(new_password) < 6:
        return {'error': '新密码长度不能少于6位'}

    # 更新密码
    config["admin"]["password_hash"] = hashlib.sha256(new_password.encode()).hexdigest()
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
