"""
多媒体设备报修系统 - 后端 API 服务（Blueprint版本）

纯 JSON API 服务，不返回任何 HTML 页面。
前端（学生端/教师端）通过调用这些 API 获取数据。

启动方式：python app.py
访问地址：http://localhost:5000
"""
from flask import Flask, send_file, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import time
import logging

# 最先加载 .env 文件，确保后续所有 os.environ.get() 能读到配置
import config as _config  # config.py 会自动加载 .env 文件到 os.environ

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

from log_manager import init_log_handler
init_log_handler()

from models import init_db
init_db()

# 启动诊断
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
_env_exists = os.path.exists(_env_path)
_env_secret = os.environ.get('SECRET_KEY', '')
logger.info("=" * 50)
logger.info("[STARTUP] .env file exists: %s (path: %s)", _env_exists, _env_path)
logger.info("[STARTUP] SECRET_KEY from env: %s", ('SET (' + _env_secret[:8] + '...)' if _env_secret else 'NOT SET - will generate random!'))
logger.info("[STARTUP] ALLOWED_ORIGINS: %s", os.environ.get('ALLOWED_ORIGINS', 'NOT SET'))
logger.info("[STARTUP] STUDENT_DEFAULT_PASSWORD: %s", 'SET' if os.environ.get('STUDENT_DEFAULT_PASSWORD') else 'NOT SET (using 123456)')
logger.info("[STARTUP] ADMIN_PASSWORD: %s", 'SET' if os.environ.get('ADMIN_PASSWORD') else 'NOT SET (will generate random)')
logger.info("=" * 50)

# 创建 Flask 应用
app = Flask(__name__)

# ============================================================
# 安全配置
# ============================================================

# 从 .env 读取允许的前端域名（逗号分隔）
_allowed_origins = os.environ.get('ALLOWED_ORIGINS', '').strip()
if _allowed_origins:
    origins = [o.strip() for o in _allowed_origins.split(',') if o.strip()]
else:
    # 默认允许本机和常见开发地址
    origins = [
        'http://localhost:5000',
        'http://127.0.0.1:5000',
        'http://localhost:8080',
        'http://127.0.0.1:8080',
    ]
    logger.info("[INFO] ALLOWED_ORIGINS not set, using defaults. Set in .env for production.")

CORS(app, origins=origins, supports_credentials=True)

# 安全响应头
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # 不暴露服务器信息
    response.headers.pop('Server', None)
    return response

# 简易请求频率限制（内存计数器）
_request_counts = {}
_RATE_LIMIT_WINDOW = 60  # 秒
_RATE_LIMIT_MAX = 120    # 每窗口最大请求数（通用）
_RATE_LIMIT_LOGIN = 10   # 登录接口每窗口最大次数

def _check_rate_limit(key, max_requests):
    """检查频率限制，返回 True 表示被限流"""
    now = time.time()
    window_start = now - _RATE_LIMIT_WINDOW

    # 清理过期记录
    if key in _request_counts:
        _request_counts[key] = [t for t in _request_counts[key] if t > window_start]
    else:
        _request_counts[key] = []

    if len(_request_counts[key]) >= max_requests:
        return True

    _request_counts[key].append(now)
    return False

@app.before_request
def global_rate_limit():
    """全局请求频率限制"""
    # 静态文件不限流
    if request.path.startswith('/uploads/'):
        return None

    client_ip = request.remote_addr or 'unknown'

    # 登录接口更严格的限制
    if request.path in ('/api/student/login', '/admin/login'):
        if _check_rate_limit(f"login:{client_ip}", _RATE_LIMIT_LOGIN):
            logger.warning(f"[RATE_LIMIT] Login rate limit hit: {client_ip}")
            return jsonify({'status': 'error', 'message': '请求过于频繁，请稍后再试'}), 429
    else:
        if _check_rate_limit(f"global:{client_ip}", _RATE_LIMIT_MAX):
            return jsonify({'status': 'error', 'message': '请求过于频繁，请稍后再试'}), 429

    # 拦截明显的扫描/攻击请求
    ua = request.headers.get('User-Agent', '').lower()
    blocked_agents = ['sqlmap', 'nikto', 'nmap', 'masscan', 'dirbuster', 'gobuster']
    if any(agent in ua for agent in blocked_agents):
        logger.warning(f"[BLOCKED] Suspicious User-Agent: {ua} from {client_ip}")
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403

    return None

# 从 .env 或环境变量读取 SECRET_KEY
_secret = os.environ.get('SECRET_KEY', '').strip()
if not _secret:
    import secrets as _secrets
    _secret = _secrets.token_hex(32)
    logger.warning(
        "[WARN] SECRET_KEY not configured! Generated random key. "
        "All tokens will be invalidated on restart. "
        "Set SECRET_KEY in .env file to fix this."
    )
app.secret_key = _secret

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 初始化数据缓存
from data_source import create_data_source
from cache_manager import CacheManager
import admin_config
import student_manager
import repair_manager

try:
    data_source = create_data_source()
    cache = CacheManager(data_source=data_source)
    logger.info(f"数据源初始化完成: {data_source.get_source_name()}")
except Exception as e:
    logger.warning(f"数据源初始化失败: {e}，系统将在首次上传课表后可用")
    from data_source import ExcelDataSource
    data_source = ExcelDataSource("", "Sheet1")
    cache = CacheManager(data_source=data_source)

# 注册Blueprint
from blueprints.public_api import public_bp, init_blueprint as init_public
from blueprints.student_api import student_bp, init_blueprint as init_student, student_required
from blueprints.repair_api import repair_bp, init_blueprint as init_repair
from blueprints.admin_api import admin_bp, init_blueprint as init_admin, admin_required
from blueprints.report_api import report_bp, init_blueprint as init_report
from blueprints.guide_api import guide_bp, init_blueprint as init_guide

# 初始化Blueprint依赖
init_public(cache, admin_config)
init_student(student_manager, repair_manager, app.secret_key)
init_repair(repair_manager, admin_config, student_required, cache, admin_required)
init_admin(admin_config, cache, repair_manager, student_manager)
init_report(admin_required)
init_guide(student_required)

# 注册Blueprint
app.register_blueprint(public_bp)
app.register_blueprint(student_bp)
app.register_blueprint(repair_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(report_bp)
app.register_blueprint(guide_bp)

# 静态文件服务
@app.route('/')
def index():
    """教师管理端首页"""
    teacher_app_dir = os.path.join(BASE_DIR, 'teacher-app')
    return send_from_directory(teacher_app_dir, 'index.html')

@app.route('/screen.html')
def screen():
    """全屏数据大屏"""
    teacher_app_dir = os.path.join(BASE_DIR, 'teacher-app')
    return send_from_directory(teacher_app_dir, 'screen.html')

@app.route('/report.html')
def report():
    """运维报告页面"""
    teacher_app_dir = os.path.join(BASE_DIR, 'teacher-app')
    return send_from_directory(teacher_app_dir, 'report.html')

@app.route('/uploads/repair_images/<filename>')
def uploaded_file(filename):
    """访问上传的图片"""
    # 安全检查：拒绝路径穿越
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'status': 'error', 'message': 'Invalid filename'}), 400
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'repair_images')
    return send_from_directory(upload_dir, filename)

@app.route('/uploads/guide_videos/<filename>')
def uploaded_video(filename):
    """访问上传的视频"""
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'status': 'error', 'message': 'Invalid filename'}), 400
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'guide_videos')
    return send_from_directory(upload_dir, filename)

# 启动服务
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    if debug:
        logger.warning("[WARN] Flask debug mode is ON. Disable in production!")
    app.run(host='0.0.0.0', port=port, debug=debug)
