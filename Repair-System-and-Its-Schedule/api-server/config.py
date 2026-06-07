"""
集中配置模块
通过环境变量或 .env 文件切换数据源类型，支持 Excel 和 API 两种模式。

配置优先级：环境变量 > .env 文件 > 默认值
"""
import os

# ============================================================
# 加载 .env 文件（如果存在）
# ============================================================
def _load_env_file():
    """从 .env 文件加载配置到环境变量"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                # 环境变量优先级更高，不覆盖已有的
                if key not in os.environ:
                    os.environ[key] = value

_load_env_file()


# ============================================================
# 数据源类型: "excel" 或 "api"
# 修改 .env 文件中的 DATA_SOURCE_TYPE 即可切换
# ============================================================
DATA_SOURCE_TYPE = os.environ.get("DATA_SOURCE_TYPE", "excel")

# ============================================================
# Excel 数据源配置
# ============================================================
EXCEL_PATH = os.environ.get("EXCEL_PATH", "全校课表.xlsx")
EXCEL_SHEET = os.environ.get("EXCEL_SHEET", "Sheet1")

# ============================================================
# 青果教务系统 API 配置
# ============================================================
QINGGUO_BASE_URL = os.environ.get("QINGGUO_BASE_URL", "https://http-10-252-6-31-80.vpn.cqytxy.edu.cn")

# 【推荐】账号密码登录（申请专用账号后填写）
QINGGUO_USERNAME = os.environ.get("QINGGUO_USERNAME", "")
QINGGUO_PASSWORD = os.environ.get("QINGGUO_PASSWORD", "")

# 【备用】手动提供 Cookie（从浏览器获取，有效期较短）
QINGGUO_WEBVPN_TOKEN = os.environ.get("QINGGUO_WEBVPN_TOKEN", "")
QINGGUO_JSESSIONID = os.environ.get("QINGGUO_JSESSIONID", "")

# 学期配置
QINGGUO_XNM = os.environ.get("QINGGUO_XNM", "2025")      # 学年：如 2025 表示 2025-2026 学年
QINGGUO_XQM = os.environ.get("QINGGUO_XQM", "12")         # 学期：12=春季，3=秋季
QINGGUO_XQH_ID = os.environ.get("QINGGUO_XQH_ID", "C67E548C4B4553FFE0530100007F06AD")  # 校区ID

# ============================================================
# 爬虫配置（当没有正式 API 时使用）
# ============================================================
SCRAPER_ENABLED = os.environ.get("SCRAPER_ENABLED", "false").lower() == "true"
SCRAPER_INTERVAL_MINUTES = int(os.environ.get("SCRAPER_INTERVAL_MINUTES", "30"))
SCRAPER_HEADLESS = os.environ.get("SCRAPER_HEADLESS", "true").lower() == "true"

# ============================================================
# 缓存配置
# ============================================================
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "1800"))  # 默认30分钟
CACHE_BACKGROUND_REFRESH = os.environ.get("CACHE_BACKGROUND_REFRESH", "true").lower() == "true"
CACHE_FALLBACK_TO_STALE = os.environ.get("CACHE_FALLBACK_TO_STALE", "true").lower() == "true"

# ============================================================
# 客户端 API 地址（学生端自动获取，无需在前端硬编码）
# ============================================================
# 设置后，学生端启动时会自动获取此地址作为 API 基础 URL
# 格式: https://your-domain.com 或 http://IP:端口
# 留空则学生端使用当前页面地址（适用于同域部署）
API_BASE_URL = os.environ.get("API_BASE_URL", "")

# ============================================================
# HTTPS / SSL 配置
# ============================================================
# 设置证书路径后自动启用 HTTPS（开发环境留空则使用 HTTP）
SSL_CERTFILE = os.environ.get("SSL_CERTFILE", "")  # 如: /path/to/cert.pem
SSL_KEYFILE = os.environ.get("SSL_KEYFILE", "")    # 如: /path/to/key.pem

# ============================================================
# QQ机器人对接配置
# ============================================================
# 机器人调用报修接口时使用的密钥（提供给机器人开发者）
QQ_BOT_API_KEY = os.environ.get("QQ_BOT_API_KEY", "repair-bot-2026-secret-key")
