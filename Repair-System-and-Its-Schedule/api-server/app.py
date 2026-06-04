"""
课程查询系统 - 后端 API 服务（Blueprint版本）

纯 JSON API 服务，不返回任何 HTML 页面。
前端（学生端/教师端）通过调用这些 API 获取数据。

启动方式：python app_new.py
访问地址：http://localhost:5000
"""
from flask import Flask, send_file, send_from_directory
from flask_cors import CORS
import os
import logging

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

from log_manager import init_log_handler
init_log_handler()

from models import init_db
init_db()

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())

# 获取项目根目录（course_query目录）
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
init_repair(repair_manager, admin_config, student_required, cache)
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
    # 上传保存在 api-server/uploads/ 目录下（与 repair_api.py 的保存路径一致）
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'repair_images')
    return send_from_directory(upload_dir, filename)

@app.route('/uploads/guide_videos/<filename>')
def uploaded_video(filename):
    """访问上传的视频"""
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'guide_videos')
    return send_from_directory(upload_dir, filename)

# 启动服务
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
