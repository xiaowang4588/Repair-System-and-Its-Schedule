# 项目目录
chdir = '/www/wwwroot/course_query'

# 指定进程数
workers = 4

# 指定每个进程开启的线程数
threads = 2

#启动用户
user = 'www'

# 启动模式
worker_class = 'sync'

# 绑定的ip与端口
# 生产环境绑定 127.0.0.1，仅允许 Nginx 反向代理访问（不要暴露到公网）
# 开发环境可改为 0.0.0.0:5000
bind = '127.0.0.1:5000'

# ============================================================
# SSL 证书（不推荐直接由 Gunicorn 提供 SSL）
# 生产环境请使用 Nginx 反向代理 + SSL（参见 deploy/nginx.conf）
# ============================================================
# certfile = '/path/to/cert.pem'
# keyfile = '/path/to/key.pem'

# 设置进程文件目录（用于停止服务和重启服务，请勿删除）
pidfile = '/www/wwwroot/course_query/gunicorn.pid'

# 设置访问日志和错误信息日志路径
accesslog = '/www/wwwlogs/python/course_query/gunicorn_acess.log'
errorlog = '/www/wwwlogs/python/course_query/gunicorn_error.log'

# 日志级别，这个日志级别指的是错误日志的级别，而访问日志的级别无法设置
# debug:调试级别，记录的信息最多；
# info:普通级别；
# warning:警告消息；
# error:错误消息；
# critical:严重错误消息；
loglevel = 'info' 

# 自定义设置项请写到该处
# 最好以上面相同的格式 <注释 + 换行 + key = value> 进行书写， 
# PS: gunicorn 的配置文件是python扩展形式，即".py"文件，需要注意遵从python语法，
# 如：loglevel的等级是字符串作为配置的，需要用引号包裹起来