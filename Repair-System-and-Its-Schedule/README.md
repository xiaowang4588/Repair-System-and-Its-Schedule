# 📚 课程查询系统

## 项目架构

本系统采用**前后端分离**架构，后端只提供 JSON API，前端独立部署。

```
course_query/
├── api-server/           # 后端 API 服务（Python Flask）
├── teacher-app/          # 教师端（纯 HTML/JS 网页）
├── student-app/          # 学生端（Uni-app，待开发）
└── docs/                 # 项目文档
```

## 快速开始

### 1. 启动后端 API 服务

```bash
cd api-server
pip install -r requirements.txt
python app.py
```

API 服务将在 `http://localhost:5000` 启动。

### 2. 打开教师端

用浏览器打开 `teacher-app/index.html`，登录后即可管理。

默认账号：`wxzx`
默认密码：`123456`

### 3. 学生端（待开发）

学生端将使用 Uni-app 开发，支持网页和微信小程序。

---

## 后端 API 接口

### 公共接口（学生端 + 教师端共用）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/time` | GET | 获取当前时间和节次 |
| `/api/query` | GET | 按条件查询课程 |
| `/api/query/course` | GET | 按课程名称查询 |
| `/api/query/teacher` | GET | 按教师姓名查询 |
| `/api/query/weekly` | GET | 获取一周课表 |
| `/api/empty-rooms` | GET | 查询空教室 |
| `/api/buildings` | GET | 获取楼栋列表 |
| `/api/stats` | GET | 获取统计数据 |

### 管理员接口（教师端用，需登录）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/admin/login` | POST | 管理员登录 |
| `/admin/status` | GET | 获取系统状态 |
| `/admin/refresh` | POST | 刷新数据缓存 |
| `/admin/datasource` | GET | 获取数据源配置 |
| `/admin/datasource/switch` | POST | 切换数据源 |
| `/admin/datasource/api` | POST | 保存 API 配置 |
| `/admin/excel/list` | GET | 获取文件列表 |
| `/admin/excel/upload` | POST | 上传 Excel 文件 |
| `/admin/excel/switch` | POST | 切换文件 |
| `/admin/excel/delete` | POST | 删除文件 |
| `/admin/week` | GET | 获取周次信息 |
| `/admin/week/set-start` | POST | 设置学期开始日期 |
| `/admin/week/confirm` | POST | 确认当前周次 |
| `/admin/settings/cache` | POST | 保存缓存设置 |
| `/admin/settings/password` | POST | 修改密码 |
| `/admin/logs` | GET | 获取系统日志 |
| `/admin/test-connection` | POST | 测试连接 |

---

## 文件说明

### api-server/（后端 API 服务）

| 文件 | 说明 |
|------|------|
| `app.py` | API 服务入口，定义所有接口 |
| `config.py` | 环境变量配置 |
| `admin_config.py` | 后台管理配置（config.json） |
| `data_source.py` | 数据源抽象层（Excel/API） |
| `api_adapter.py` | 青果教务系统适配器 |
| `cache_manager.py` | 缓存管理器 |
| `empty_classroom_query.py` | 空教室查询 |
| `data_cleaning.py` | 数据清洗 |
| `log_manager.py` | 日志管理 |
| `requirements.txt` | Python 依赖 |
| `.env` | 运行时配置 |
| `uploads/` | 上传的课表文件 |

### teacher-app/（教师端网页）

| 文件 | 说明 |
|------|------|
| `index.html` | 教师管理后台（单文件，包含 HTML/CSS/JS） |

### student-app/（学生端，待开发）

将使用 Uni-app 开发，支持：
- 网页版（H5）
- 微信小程序
- APP（可选）

---

## 技术栈

| 层 | 技术 | 说明 |
|------|------|------|
| 后端 | Python + Flask | API 服务、Excel 处理、数据缓存 |
| 教师端 | HTML + CSS + JavaScript | 纯静态网页，调用后端 API |
| 学生端 | Uni-app（Vue.js） | 网页 + 微信小程序 |

---

## 部署说明

### 后端部署

```bash
# 使用 Gunicorn 部署
cd api-server
gunicorn -c deploy/gunicorn_conf.py app:app

# 或使用 uWSGI
uwsgi deploy/uwsgi.ini
```

### 前端部署

- **教师端**：将 `teacher-app/` 目录放到任意 Web 服务器即可
- **学生端**：Uni-app 编译后部署到相应平台
