"""
日志管理模块
捕获系统日志，同时存储在内存和文件中，供后台查看。
"""
import logging
import threading
import os
from datetime import datetime
from collections import deque
from logging.handlers import RotatingFileHandler


class MemoryLogHandler(logging.Handler):
    """内存日志处理器，将日志存储在内存队列中"""

    def __init__(self, max_logs=500):
        super().__init__()
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)
        self._lock = threading.Lock()

    def emit(self, record):
        try:
            log_entry = {
                'time': datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
                'level': record.levelname,
                'message': self.format(record),
                'module': record.module,
            }
            with self._lock:
                self.logs.append(log_entry)
        except Exception:
            # 忽略日志记录错误，不影响主程序
            pass

    def get_logs(self, level=None, keyword=None, limit=200):
        """获取日志列表"""
        with self._lock:
            logs = list(self.logs)

        # 按级别过滤
        if level and level != 'all':
            logs = [l for l in logs if l['level'] == level]

        # 按关键词过滤
        if keyword:
            keyword = keyword.lower()
            logs = [l for l in logs if keyword in l['message'].lower()]

        # 返回最近的日志
        return logs[-limit:]

    def clear(self):
        """清空日志"""
        with self._lock:
            self.logs.clear()


# 全局日志管理器
_log_handler = None
_file_handler = None


def get_log_dir():
    """获取日志目录"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def init_log_handler():
    """初始化日志处理器（内存+文件）"""
    global _log_handler, _file_handler
    if _log_handler is None:
        _log_handler = MemoryLogHandler(max_logs=500)
        _log_handler.setFormatter(logging.Formatter('%(message)s'))

        # 添加到 root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(_log_handler)

    # 初始化文件日志处理器
    if _file_handler is None:
        try:
            log_dir = get_log_dir()
            log_file = os.path.join(log_dir, 'app.log')
            _file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            _file_handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            ))
            _file_handler.setLevel(logging.INFO)

            # 添加到 root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(_file_handler)
        except Exception as e:
            print(f"初始化文件日志失败: {e}")

    return _log_handler


def get_log_handler():
    """获取日志处理器"""
    global _log_handler
    if _log_handler is None:
        init_log_handler()
    return _log_handler


def get_log_files():
    """获取日志文件列表"""
    log_dir = get_log_dir()
    files = []
    for f in os.listdir(log_dir):
        if f.endswith('.log'):
            filepath = os.path.join(log_dir, f)
            stat = os.stat(filepath)
            files.append({
                'name': f,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    return sorted(files, key=lambda x: x['modified'], reverse=True)
