# 📚 多媒体设备报修系统

> 重庆移通学院綦江校区 — 多媒体设备报修与课表查询系统

## 项目简介

本系统是一套前后端分离的多媒体设备报修管理平台，包含以下核心功能：

| 模块 | 功能 |
|------|------|
| **报修管理** | 学生提交报修、管理员处理工单、批量操作、统计分析 |
| **课表查询** | 按教室/教师/课程查询课表、空教室查询、周课表 |
| **防坑指南** | 学生社区发布设备使用经验、点赞评论收藏 |
| **运维报告** | 自动生成周报/月报/学期报告（含 AI 建议） |
| **数据大屏** | 实时报修数据可视化展示 |

---

## 技术架构

```
┌─────────────┐     HTTPS      ┌─────────────┐     HTTP      ┌─────────────┐
│  学生端      │ ─────────────→ │    Nginx     │ ────────────→ │   Gunicorn  │
│  (Uni-app)   │ ←───────────── │  (反向代理)   │ ←──────────── │   (Flask)   │
└─────────────┘                └─────────────┘               └─────────────┘
                                                                      │
┌─────────────┐     同源请求     │                                     │
│  教师端      │ ─────────────→ │                                     ▼
│  (HTML/JS)   │ ←───────────── │                              ┌─────────────┐
└─────────────┘                │                              │   SQLite    │
                               │                              │  (repair.db)│
                               │                              └─────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 - 学生端 | Uni-app (Vue.js) | H5 网页 + 微信小程序 |
| 前端 - 教师端 | 原生 HTML/CSS/JS | 单文件应用，无需构建 |
| 后端 | Python 3 + Flask | RESTful API，Blueprint 分模块 |
| 数据库 | SQLite (Peewee ORM) | 轻量级，零配置 |
| 部署 | Nginx + Gunicorn | HTTPS 反向代理，多 worker |

---

## 项目目录结构

```
Repair-System-and-Its-Schedule/
│
├── api-server/                          # 后端 API 服务
│   ├── app.py                           # Flask 入口（启动文件）
│   ├── config.py                        # 配置加载（读取 .env）
│   ├── config.json                      # 运行时配置（自动生成）
│   ├── models.py                        # 数据库模型定义
│   ├── requirements.txt                 # Python 依赖清单
│   ├── .env.example                     # 环境变量模板
│   │
│   ├── blueprints/                      # API 路由层（各模块接口）
│   │   ├── admin_api.py                 #   管理员接口（登录、学生管理、系统设置）
│   │   ├── student_api.py               #   学生接口（登录、个人信息、改密）
│   │   ├── repair_api.py                #   报修接口（CRUD、统计、导入导出）
│   │   ├── public_api.py                #   公共接口（课表查询、空教室、配置）
│   │   ├── report_api.py                #   报告接口（周报/月报/学期报告）
│   │   └── guide_api.py                 #   防坑指南接口（帖子、评论、点赞）
│   │
│   ├── services/                        # 业务逻辑层
│   │   ├── admin_config.py              #   管理员账号、数据源、系统配置
│   │   ├── student_manager.py           #   学生账号 CRUD、密码管理
│   │   ├── repair_manager.py            #   报修记录 CRUD、统计分析
│   │   └── report/                      #   运维报告模块
│   │       ├── analyzer.py              #     数据分析（周/月/学期维度）
│   │       ├── advisor.py               #     AI 建议生成
│   │       ├── renderer.py              #     Excel/Word 报告渲染
│   │       └── html_template.py         #     HTML 报告模板
│   │
│   ├── datasource/                      # 数据访问层
│   │   ├── data_source.py               #   数据源抽象（Excel/API 切换）
│   │   ├── cache_manager.py             #   DataFrame 缓存（TTL、后台刷新）
│   │   ├── data_cleaning.py             #   课表数据清洗
│   │   ├── api_adapter.py               #   青果教务系统 API 适配器
│   │   └── empty_classroom_query.py     #   空教室查询引擎
│   │
│   ├── utils/                           # 工具层
│   │   ├── log_manager.py               #   日志管理（内存 + 文件）
│   │   ├── token_utils.py               #   管理员 HMAC Token 工具
│   │   ├── stats_helper.py              #   统计辅助函数
│   │   └── time_helper.py               #   时间/节次辅助函数
│   │
│   ├── data/                            # SQLite 数据库（运行时生成）
│   ├── uploads/                         # 上传文件（图片、视频、Excel）
│   └── logs/                            # 运行日志
│
├── teacher-app/                         # 教师管理端
│   ├── index.html                       #   管理后台（单文件应用）
│   ├── screen.html                      #   全屏数据大屏
│   └── report.html                      #   运维报告页面
│
├── student-app/                         # 学生端（Uni-app）
│   ├── config/index.js                  #   API 地址配置（动态获取）
│   ├── api/index.js                     #   API 服务封装
│   ├── pages/                           #   页面组件
│   │   ├── login/login.vue              #     登录页
│   │   ├── index/index.vue              #     首页
│   │   ├── repair/repair.vue            #     报修表单
│   │   ├── repair/list.vue              #     报修记录列表
│   │   ├── profile/profile.vue          #     个人中心
│   │   ├── course/schedule.vue          #     课表查询
│   │   ├── empty/empty.vue              #     空教室查询
│   │   └── guide/                       #     防坑指南
│   └── manifest.json                    #   Uni-app 配置
│
├── deploy/                              # 部署配置
│   ├── nginx.conf                       #   Nginx 反向代理 + HTTPS 配置
│   ├── gunicorn_conf.py                 #   Gunicorn 多进程配置
│   ├── uwsgi.ini                        #   uWSGI 配置（备选）
│   └── setup.sh                         #   服务器初始化脚本
│
└── docs/                                # 项目文档
    ├── API接口文档.md
    ├── 需求文档.md
    ├── 项目使用说明文档.md
    └── ...
```

---

## 快速开始（本地开发）

### 环境要求

- Python 3.9+
- pip

### 1. 安装依赖

```bash
cd api-server
pip install -r requirements.txt
```

### 2. 创建配置文件

```bash
cp .env.example .env
```

编辑 `.env`，至少修改以下项：

```bash
SECRET_KEY=你的随机密钥        # python -c "import secrets; print(secrets.token_hex(32))"
ADMIN_PASSWORD=你的管理员密码
STUDENT_DEFAULT_PASSWORD=学生默认密码
```

### 3. 启动后端

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动。

### 4. 访问前端

- **教师管理端**：浏览器打开 `http://localhost:5000/`
- **数据大屏**：`http://localhost:5000/screen.html`
- **学生端**：需单独启动 Uni-app 开发服务器

### 5. 默认管理员账号

| 项目 | 值 |
|------|---|
| 用户名 | `wxzx` |
| 密码 | `.env` 中设置的 `ADMIN_PASSWORD` |

> ⚠️ 首次登录后请立即修改密码。

---

## 配置说明（.env 文件）

所有服务器相关配置集中在 `api-server/.env` 一个文件中，**换服务器只需改这一个文件**。

```bash
# ============================================================
# 安全配置
# ============================================================

# 客户端 API 地址（学生端启动时自动获取）
# 留空则学生端使用当前页面地址（同域部署时）
API_BASE_URL=https://your-domain.com

# 允许的前端域名（CORS 限制，逗号分隔）
ALLOWED_ORIGINS=https://your-domain.com,http://localhost:8080

# Token 签名密钥（必须修改！）
SECRET_KEY=随机生成的32字节十六进制字符串

# 管理员密码
ADMIN_PASSWORD=你的密码

# 学生默认密码（新创建学生的初始密码）
STUDENT_DEFAULT_PASSWORD=123456

# ============================================================
# 数据源配置
# ============================================================

# 数据源类型：excel（上传课表）或 api（对接教务系统）
DATA_SOURCE_TYPE=excel

# 青果教务系统（DATA_SOURCE_TYPE=api 时需要）
QINGGUO_USERNAME=
QINGGUO_PASSWORD=

# ============================================================
# HTTPS 配置
# ============================================================

# SSL 证书路径（留空则使用 HTTP，建议用 Nginx + Let's Encrypt）
SSL_CERTFILE=
SSL_KEYFILE=

# ============================================================
# 缓存配置
# ============================================================

CACHE_TTL_SECONDS=1800         # 缓存过期时间（秒）
CACHE_BACKGROUND_REFRESH=true  # 后台自动刷新
CACHE_FALLBACK_TO_STALE=true   # 过期缓存兜底
```

---

## 生产环境部署

### 方案一：宝塔面板（推荐）

#### 1. 上传项目

将整个项目上传到服务器，例如 `/www/wwwroot/course_query`。

#### 2. 配置 .env

```bash
cd /www/wwwroot/course_query/api-server
cp .env.example .env
vim .env   # 编辑配置
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 启动后端

```bash
cd /www/wwwroot/course_query
gunicorn -c deploy/gunicorn_conf.py app:app
```

#### 5. 配置 Nginx

在宝塔面板中：
1. **网站** → 添加站点 → 填写域名
2. **SSL** → 申请 Let's Encrypt 免费证书
3. 将 `deploy/nginx.conf` 的内容粘贴到站点的 Nginx 配置中
4. 重启 Nginx

#### 6. 设置开机自启

在宝塔面板 → **Python 项目管理器** 中添加项目，或使用 systemd：

```bash
# 创建 systemd 服务
cat > /etc/systemd/system/repair-system.service << 'EOF'
[Unit]
Description=Multimedia Repair System
After=network.target

[Service]
Type=notify
User=www
WorkingDirectory=/www/wwwroot/course_query
ExecStart=/usr/local/bin/gunicorn -c deploy/gunicorn_conf.py app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl enable repair-system
systemctl start repair-system
```

### 方案二：Docker（可选）

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY api-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api-server/ ./api-server/
COPY teacher-app/ ./teacher-app/
EXPOSE 5000
CMD ["gunicorn", "-c", "api-server/../deploy/gunicorn_conf.py", "app:app"]
```

---

## 换服务器迁移指南

**只需改一个文件：`api-server/.env`**

```
1. 将项目复制到新服务器
2. cd api-server && cp .env.example .env
3. 编辑 .env：
   - API_BASE_URL → 新服务器地址
   - ALLOWED_ORIGINS → 新服务器域名/IP
   - SECRET_KEY → 重新生成
   - ADMIN_PASSWORD → 设置密码
4. pip install -r requirements.txt
5. gunicorn -c deploy/gunicorn_conf.py app:app
6. 配置 Nginx + SSL（参考 deploy/nginx.conf）
```

> 学生端会自动从后端 `/api/config` 接口获取 API 地址，**无需重新构建**。

---

## 安全机制

本系统已实施以下安全措施：

| 类别 | 措施 |
|------|------|
| **认证** | 管理员 HMAC-SHA256 Token（30天有效）；学生 HMAC Token（30天有效） |
| **密码** | 学生密码 SHA-256 + 随机盐；管理员密码 SHA-256（建议升级 bcrypt） |
| **传输** | 支持 HTTPS（Nginx SSL 终结）；HSTS 强制加密 |
| **防护** | CSP 响应头；X-Frame-Options；请求频率限制（120次/分钟） |
| **输入** | HTML 标签过滤；文件上传扩展名白名单；路径穿越防护 |
| **配置** | 敏感信息统一在 .env（已 gitignore）；密钥不硬编码 |

---

## API 接口一览

### 公共接口（无需登录）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/config` | GET | 获取客户端配置（API 地址） |
| `/api/time` | GET | 当前时间和节次 |
| `/api/current-week` | GET | 当前教学周 |
| `/api/query` | GET | 按条件查询课程 |
| `/api/query/course` | GET | 按课程名查询 |
| `/api/query/teacher` | GET | 按教师名查询 |
| `/api/query/weekly` | GET | 一周课表 |
| `/api/empty-rooms` | GET | 空教室查询 |
| `/api/buildings` | GET | 楼栋列表 |
| `/api/stats` | GET | 课表统计 |
| `/api/building-usage` | GET | 楼栋实时使用率 |
| `/api/repair/auto-fill` | GET | 报修表单自动填充 |
| `/api/repair/nearby-rooms` | GET | 同楼栋空教室推荐 |
| `/api/repair/semesters` | GET | 学期列表 |
| `/api/repair/import-template` | GET | 下载导入模板 |
| `/api/guide/list` | GET | 防坑指南列表 |
| `/api/guide/detail` | GET | 帖子详情 |
| `/api/guide/search` | GET | 搜索帖子 |
| `/api/guide/tags` | GET | 标签列表 |
| `/api/guide/comment/list` | GET | 评论列表 |

### 学生接口（需 Bearer Token）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/student/login` | POST | 学生登录 |
| `/api/student/change-password` | POST | 修改密码 |
| `/api/student/info` | GET | 个人信息 + 报修统计 |
| `/api/repair/create` | POST | 提交报修 |
| `/api/repair/student-update` | POST | 编辑自己的报修 |
| `/api/repair/student-delete` | POST | 删除自己的报修 |
| `/api/repair/my-list` | GET | 我的报修记录 |
| `/api/repair/upload-image` | POST | 上传报修图片 |
| `/api/guide/create` | POST | 发布帖子 |
| `/api/guide/update` | POST | 编辑帖子 |
| `/api/guide/delete` | POST | 删除帖子 |
| `/api/guide/like` | POST | 点赞/取消 |
| `/api/guide/comment` | POST | 发表评论 |
| `/api/guide/comment/delete` | POST | 删除评论 |
| `/api/guide/favorite` | POST | 收藏/取消 |
| `/api/guide/upload-video` | POST | 上传视频（≤50MB） |

### 管理员接口（需 Bearer Token）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/admin/login` | POST | 管理员登录 |
| `/admin/status` | GET | 系统状态 |
| `/admin/refresh` | POST | 刷新缓存 |
| `/admin/datasource` | GET | 数据源配置 |
| `/admin/datasource/switch` | POST | 切换数据源 |
| `/admin/datasource/api` | POST | 保存 API 配置 |
| `/admin/test-connection` | POST | 测试教务系统连接 |
| `/admin/week` | GET | 周次信息 |
| `/admin/week/set-start` | POST | 设置学期开始日期 |
| `/admin/settings/cache` | POST | 保存缓存设置 |
| `/admin/settings/password` | POST | 修改管理员密码 |
| `/admin/students` | GET | 学生列表 |
| `/admin/students/create` | POST | 创建学生 |
| `/admin/students/batch-create` | POST | 批量创建学生 |
| `/admin/students/update` | POST | 更新学生 |
| `/admin/students/delete` | POST | 删除学生 |
| `/admin/students/reset-password` | POST | 重置学生密码 |
| `/admin/students/stats` | GET | 学生统计 |
| `/admin/logs` | GET | 系统日志 |
| `/admin/logs/clear` | POST | 清空日志 |
| `/admin/excel/list` | GET | Excel 文件列表 |
| `/admin/excel/upload` | POST | 上传课表 Excel |
| `/admin/excel/switch` | POST | 切换 Excel |
| `/admin/excel/delete` | POST | 删除 Excel |
| `/admin/excel/clear-all` | POST | 清除所有 Excel |
| `/api/repair/list` | GET | 全部报修记录 |
| `/api/repair/stats` | GET | 报修统计 |
| `/api/repair/filter-options` | GET | 筛选选项 |
| `/api/repair/update` | POST | 更新报修记录 |
| `/api/repair/delete` | POST | 删除报修记录 |
| `/api/repair/batch-update-status` | POST | 批量更新状态 |
| `/api/repair/batch-update-handler` | POST | 批量分配处理人 |
| `/api/repair/batch-delete` | POST | 批量删除 |
| `/api/repair/dashboard-stats` | GET | 大屏统计数据 |
| `/api/repair/drill/*` | GET | 各维度下钻统计 |
| `/api/repair/export` | GET | 导出 Excel |
| `/api/repair/import` | POST | 导入 Excel |
| `/api/report/weekly` | GET | 周报数据 |
| `/api/report/monthly` | GET | 月报数据 |
| `/api/report/semester` | GET | 学期报告 |
| `/api/report/preview` | GET | 报告预览（HTML） |
| `/api/report/export/excel` | GET | 导出 Excel 报告 |
| `/api/report/export/word` | GET | 导出 Word 报告 |

---

## 常见运维问题

### Q: 忘记管理员密码怎么办？

```bash
cd api-server
# 方法1：修改 .env 中的 ADMIN_PASSWORD，重启服务
# 方法2：直接修改 config.json 中的 password_hash
python -c "import hashlib; print(hashlib.sha256('新密码'.encode()).hexdigest())"
# 将输出的哈希值替换 config.json 中的 password_hash
```

### Q: 学生端无法连接后端？

1. 检查 `.env` 中 `API_BASE_URL` 是否正确
2. 检查 `ALLOWED_ORIGINS` 是否包含学生端的访问地址
3. 检查 Nginx 是否正常运行：`nginx -t && systemctl status nginx`
4. 检查后端是否正常：`curl http://127.0.0.1:5000/api/time`

### Q: 上传课表后数据不显示？

1. 确认 Excel 格式正确（参考 `docs/需求文档.md`）
2. 在管理后台点击"刷新数据"
3. 检查日志：`cat api-server/logs/app.log | tail -50`

### Q: 如何备份数据？

```bash
# 备份数据库和配置
cp api-server/data/repair.db backup/repair_$(date +%Y%m%d).db
cp api-server/config.json backup/config_$(date +%Y%m%d).json
cp api-server/.env backup/.env_$(date +%Y%m%d)

# 备份上传文件
tar -czf backup/uploads_$(date +%Y%m%d).tar.gz api-server/uploads/
```

### Q: 如何查看系统日志？

```bash
# 应用日志
tail -f api-server/logs/app.log

# Gunicorn 日志
tail -f /www/wwwlogs/python/course_query/gunicorn_error.log

# Nginx 日志
tail -f /www/wwwlogs/access.log
```

---

## 依赖说明

| 包 | 版本 | 用途 |
|---|---|---|
| Flask | ≥3.0 | Web 框架 |
| Flask-CORS | ≥4.0 | 跨域支持 |
| Peewee | ≥4.0 | SQLite ORM |
| Pandas | ≥2.2 | 数据处理 |
| openpyxl | ≥3.1 | Excel 读写 |
| python-docx | ≥1.1 | Word 报告生成 |
| requests | ≥2.31 | HTTP 请求 |
| beautifulsoup4 | ≥4.12 | HTML 解析 |
| pytz | ≥2024.1 | 时区处理 |

---

## 许可证

本项目为竞赛作品，仅供学习交流使用。
