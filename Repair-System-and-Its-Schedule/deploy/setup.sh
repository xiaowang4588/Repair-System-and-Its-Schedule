#!/bin/bash
# ============================================================
# 多媒体报修系统 - 服务器初始化 / 迁移脚本
#
# 使用方式：
#   1. 将项目上传到新服务器
#   2. 修改下方 CONFIG 区域的变量
#   3. chmod +x deploy/setup.sh && ./deploy/setup.sh
#
# 此脚本会：
#   - 创建 .env 配置文件
#   - 更新 Gunicorn / uWSGI / Nginx 配置中的路径
#   - 安装 Python 依赖
#   - 初始化数据库
# ============================================================

set -e

# ============================================================
# 【必填】请修改以下配置
# ============================================================

# 项目部署路径（代码放在哪里）
PROJECT_DIR="/www/wwwroot/course_query"

# 服务器域名或 IP（用于 CORS 和 Nginx）
SERVER_DOMAIN="your-domain.com"

# 管理员密码（首次部署后请立即在管理后台修改）
ADMIN_PASSWORD="CHANGE_ME_IMMEDIATELY"

# 学生默认密码
STUDENT_DEFAULT_PASSWORD="CHANGE_ME_IMMEDIATELY"

# SSL 证书路径（留空则不启用 HTTPS，建议用宝塔面板申请后再填）
SSL_CERTFILE=""
SSL_KEYFILE=""

# ============================================================
# 【可选】以下配置一般不需要修改
# ============================================================

# 绑定端口
PORT=5000

# 日志目录
LOG_DIR="/www/wwwlogs/python/course_query"

# Nginx 用户（宝塔默认为 www）
NGINX_USER="www"

# ============================================================
# 脚本主体（以下不需要修改）
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  多媒体报修系统 - 服务器部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}建议使用 root 权限运行此脚本${NC}"
fi

# 进入项目目录
cd "$PROJECT_DIR/api-server"

# ============================================================
# 1. 创建 .env 文件
# ============================================================
echo -e "${GREEN}[1/5] 创建 .env 配置文件...${NC}"

if [ -f ".env" ]; then
    echo -e "${YELLOW}  .env 已存在，跳过（如需重新生成，请先删除 .env）${NC}"
else
    # 生成随机 SECRET_KEY
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)

    # 构建 ALLOWED_ORIGINS
    if [ -n "$SSL_CERTFILE" ]; then
        ALLOWED_ORIGINS="https://${SERVER_DOMAIN},http://localhost:8080"
    else
        ALLOWED_ORIGINS="http://${SERVER_DOMAIN}:${PORT},http://localhost:8080"
    fi

    cat > .env << EOF
# ============================================================
# 由 deploy/setup.sh 自动生成于 $(date '+%Y-%m-%d %H:%M:%S')
# 如需修改，请直接编辑此文件
# ============================================================

# 安全配置
ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
SECRET_KEY=${SECRET_KEY}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
STUDENT_DEFAULT_PASSWORD=${STUDENT_DEFAULT_PASSWORD}

# 数据源配置
DATA_SOURCE_TYPE=excel
EXCEL_SHEET=Sheet1

# 青果教务系统（如不使用 API 数据源，留空即可）
QINGGUO_USERNAME=
QINGGUO_PASSWORD=
QINGGUO_WEBVPN_TOKEN=
QINGGUO_JSESSIONID=
QINGGUO_XNM=2025
QINGGUO_XQM=12
QINGGUO_XQH_ID=

# SSL 证书（留空则使用 HTTP，建议用宝塔申请 Let's Encrypt）
SSL_CERTFILE=${SSL_CERTFILE}
SSL_KEYFILE=${SSL_KEYFILE}

# 缓存配置
CACHE_TTL_SECONDS=1800
CACHE_BACKGROUND_REFRESH=true
CACHE_FALLBACK_TO_STALE=true
EOF

    echo -e "  ${GREEN}✓ .env 已生成${NC}"
    echo -e "  ${YELLOW}SECRET_KEY: ${SECRET_KEY:0:16}...${NC}"
fi

# ============================================================
# 2. 更新 Gunicorn 配置
# ============================================================
echo -e "${GREEN}[2/5] 更新 Gunicorn 配置...${NC}"

GUNICORN_CONF="$PROJECT_DIR/deploy/gunicorn_conf.py"
sed -i "s|chdir = '.*'|chdir = '${PROJECT_DIR}'|g" "$GUNICORN_CONF"
sed -i "s|pidfile = '.*'|pidfile = '${PROJECT_DIR}/gunicorn.pid'|g" "$GUNICORN_CONF"
sed -i "s|accesslog = '.*'|accesslog = '${LOG_DIR}/gunicorn_access.log'|g" "$GUNICORN_CONF"
sed -i "s|errorlog = '.*'|errorlog = '${LOG_DIR}/gunicorn_error.log'|g" "$GUNICORN_CONF"
echo -e "  ${GREEN}✓ gunicorn_conf.py 已更新${NC}"

# ============================================================
# 3. 更新 uWSGI 配置
# ============================================================
echo -e "${GREEN}[3/5] 更新 uWSGI 配置...${NC}"

UWSGI_INI="$PROJECT_DIR/deploy/uwsgi.ini"
sed -i "s|chdir=.*|chdir=${PROJECT_DIR}|g" "$UWSGI_INI"
sed -i "s|wsgi-file=.*|wsgi-file=${PROJECT_DIR}/app.py|g" "$UWSGI_INI"
sed -i "s|pidfile=.*|pidfile=${PROJECT_DIR}/uwsgi.pid|g" "$UWSGI_INI"
sed -i "s|daemonize = .*|daemonize = ${LOG_DIR}/uwsgi.log|g" "$UWSGI_INI"
echo -e "  ${GREEN}✓ uwsgi.ini 已更新${NC}"

# ============================================================
# 4. 更新 Nginx 配置
# ============================================================
echo -e "${GREEN}[4/5] 更新 Nginx 配置...${NC}"

NGINX_CONF="$PROJECT_DIR/deploy/nginx.conf"
sed -i "s|server_name .*;|server_name ${SERVER_DOMAIN};|g" "$NGINX_CONF"
sed -i "s|root .*;|root ${PROJECT_DIR};|g" "$NGINX_CONF"
sed -i "s|alias .*;|alias ${PROJECT_DIR}/api-server/uploads/;|g" "$NGINX_CONF"

if [ -n "$SSL_CERTFILE" ]; then
    sed -i "s|ssl_certificate .*;|ssl_certificate     ${SSL_CERTFILE};|g" "$NGINX_CONF"
    sed -i "s|ssl_certificate_key .*;|ssl_certificate_key ${SSL_KEYFILE};|g" "$NGINX_CONF"
fi

echo -e "  ${GREEN}✓ nginx.conf 已更新${NC}"
echo -e "  ${YELLOW}请将 nginx.conf 内容复制到 Nginx 站点配置中${NC}"

# ============================================================
# 5. 安装依赖 & 初始化
# ============================================================
echo -e "${GREEN}[5/5] 安装 Python 依赖...${NC}"

if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt -q 2>/dev/null || pip install -r requirements.txt -q
    echo -e "  ${GREEN}✓ 依赖安装完成${NC}"
fi

# 创建必要目录
mkdir -p "$PROJECT_DIR/api-server/data"
mkdir -p "$PROJECT_DIR/api-server/uploads/repair_images"
mkdir -p "$PROJECT_DIR/api-server/uploads/guide_videos"
mkdir -p "$PROJECT_DIR/api-server/uploads/excel"
mkdir -p "$LOG_DIR"
echo -e "  ${GREEN}✓ 目录结构已创建${NC}"

# ============================================================
# 完成
# ============================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "后续步骤："
echo -e "  1. 确认 .env 配置无误"
echo -e "  2. 启动后端: cd ${PROJECT_DIR} && gunicorn -c deploy/gunicorn_conf.py app:app"
echo -e "  3. 配置 Nginx: 将 deploy/nginx.conf 内容粘贴到站点配置"
echo -e "  4. 如用宝塔面板，在 SSL 页签申请 Let's Encrypt 证书"
echo -e "  5. 学生端修改 config/index.js 中的 API_BASE 后重新构建"
echo ""
echo -e "${YELLOW}管理员账号: wxzx${NC}"
echo -e "${YELLOW}管理后台: http(s)://${SERVER_DOMAIN}/ ${NC}"
