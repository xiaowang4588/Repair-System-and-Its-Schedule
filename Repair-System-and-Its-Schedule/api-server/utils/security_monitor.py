"""
安全监控模块 - 入侵检测与告警
功能：
1. 登录失败次数检测与IP锁定
2. 异常行为检测（非正常时间访问、批量导出、异常User-Agent）
3. 分级告警机制（INFO / WARNING / CRITICAL）
4. 安全事件集中管理
"""
import time
import json
import re
import logging
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)

# ============ 配置常量 ============

# 登录失败检测
MAX_LOGIN_FAILURES_PER_DAY = 30       # 单IP单日最大登录失败次数
IP_LOCKOUT_DURATION = 600             # IP锁定时长（秒），10分钟
LOGIN_FAILURE_WINDOW = 86400          # 登录失败统计窗口（秒），24小时

# 非正常工作时间（凌晨2点-5点）
OFF_HOURS_START = 2
OFF_HOURS_END = 5

# 批量导出检测
EXPORT_COUNT_THRESHOLD = 10           # 单次导出超过正常量10倍触发告警
EXPORT_WINDOW = 3600                  # 导出统计窗口（秒），1小时
NORMAL_EXPORT_COUNT = 5               # 正常1小时导出次数基线

# 异常User-Agent检测
ABNORMAL_UA_PATTERNS = [
    r'^$',                             # 空User-Agent
    r'^.{0,5}$',                       # 极短User-Agent（少于5字符）
    r'(?:sqlmap|nikto|nmap|masscan|dirbuster|gobuster|wfuzz|hydra|metasploit)',  # 攻击工具
    r'(?:python-requests|curl|wget)\s*/',  # 自动化脚本（带版本号的除外正常API调用）
]

# 告警级别
SEVERITY_INFO = 'INFO'
SEVERITY_WARNING = 'WARNING'
SEVERITY_CRITICAL = 'CRITICAL'


class SecurityMonitor:
    """安全监控器（单例模式）"""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 登录失败计数 {ip: [(timestamp, username, user_type), ...]}
        self._login_failures = {}
        # IP锁定记录 {ip: lockout_until_timestamp}
        self._ip_lockouts = {}
        # 导出计数 {ip: [(timestamp, count), ...]}
        self._export_counts = {}
        # 数据锁
        self._data_lock = Lock()

    # ============ 登录失败检测 ============

    def record_login_failure(self, ip: str, username: str = '', user_type: str = ''):
        """
        记录登录失败事件
        返回: {'locked': bool, 'failure_count': int, 'lockout_remaining': int}
        """
        now = time.time()

        with self._data_lock:
            if ip not in self._login_failures:
                self._login_failures[ip] = []

            # 清理过期记录
            self._login_failures[ip] = [
                (ts, u, t) for ts, u, t in self._login_failures[ip]
                if now - ts < LOGIN_FAILURE_WINDOW
            ]

            # 记录本次失败
            self._login_failures[ip].append((now, username, user_type))
            failure_count = len(self._login_failures[ip])

        # 记录安全事件
        self._log_security_event(
            event_type='login_failure',
            severity=SEVERITY_INFO if failure_count < 10 else SEVERITY_WARNING,
            source_ip=ip,
            user_type=user_type,
            user_id=username,
            detail=json.dumps({
                'failure_count': failure_count,
                'username': username,
            }, ensure_ascii=False)
        )

        # 检查是否需要锁定
        if failure_count >= MAX_LOGIN_FAILURES_PER_DAY:
            lockout_until = now + IP_LOCKOUT_DURATION
            with self._data_lock:
                self._ip_lockouts[ip] = lockout_until

            # 记录锁定事件（高级别告警）
            self._log_security_event(
                event_type='ip_lockout',
                severity=SEVERITY_CRITICAL,
                source_ip=ip,
                user_type=user_type,
                user_id=username,
                detail=json.dumps({
                    'failure_count': failure_count,
                    'lockout_duration': IP_LOCKOUT_DURATION,
                    'lockout_until': lockout_until,
                }, ensure_ascii=False)
            )
            logger.warning(f"[安全告警] IP {ip} 已被锁定 {IP_LOCKOUT_DURATION}秒，"
                          f"原因：登录失败 {failure_count} 次")

            return {
                'locked': True,
                'failure_count': failure_count,
                'lockout_remaining': IP_LOCKOUT_DURATION,
            }

        return {
            'locked': False,
            'failure_count': failure_count,
            'lockout_remaining': 0,
        }

    def is_ip_locked(self, ip: str) -> bool:
        """检查IP是否被锁定"""
        now = time.time()
        with self._data_lock:
            if ip in self._ip_lockouts:
                if now < self._ip_lockouts[ip]:
                    return True
                else:
                    # 锁定已过期，移除记录
                    del self._ip_lockouts[ip]
        return False

    def get_lockout_remaining(self, ip: str) -> int:
        """获取IP锁定剩余时间（秒）"""
        now = time.time()
        with self._data_lock:
            if ip in self._ip_lockouts:
                remaining = int(self._ip_lockouts[ip] - now)
                return max(0, remaining)
        return 0

    def record_login_success(self, ip: str, username: str = '', user_type: str = ''):
        """记录登录成功（清除该IP的失败计数）"""
        with self._data_lock:
            if ip in self._login_failures:
                del self._login_failures[ip]

    # ============ 异常行为检测 ============

    def check_off_hours_access(self, user_type: str = 'admin') -> bool:
        """检查当前是否为非正常工作时间"""
        now = datetime.now()
        hour = now.hour
        if OFF_HOURS_START <= hour < OFF_HOURS_END and user_type == 'admin':
            return True
        return False

    def record_export(self, ip: str, record_count: int = 1, user_type: str = '', user_id: str = ''):
        """
        记录数据导出操作
        返回: {'abnormal': bool, 'export_count': int}
        """
        now = time.time()

        with self._data_lock:
            if ip not in self._export_counts:
                self._export_counts[ip] = []

            # 清理过期记录
            self._export_counts[ip] = [
                (ts, c) for ts, c in self._export_counts[ip]
                if now - ts < EXPORT_WINDOW
            ]

            # 记录本次导出
            self._export_counts[ip].append((now, record_count))

            # 计算窗口内总导出量
            total_exports = sum(c for _, c in self._export_counts[ip])
            export_operations = len(self._export_counts[ip])

        # 检查是否超过正常量10倍
        is_abnormal = (
            total_exports > NORMAL_EXPORT_COUNT * EXPORT_COUNT_THRESHOLD or
            record_count > NORMAL_EXPORT_COUNT * EXPORT_COUNT_THRESHOLD
        )

        if is_abnormal:
            self._log_security_event(
                event_type='bulk_export',
                severity=SEVERITY_WARNING,
                source_ip=ip,
                user_type=user_type,
                user_id=user_id,
                detail=json.dumps({
                    'total_exports': total_exports,
                    'this_batch': record_count,
                    'operations_count': export_operations,
                    'threshold': NORMAL_EXPORT_COUNT * EXPORT_COUNT_THRESHOLD,
                }, ensure_ascii=False)
            )
            logger.warning(f"[安全告警] IP {ip} 疑似批量导出，"
                          f"窗口内导出 {total_exports} 条，本次 {record_count} 条")

        return {
            'abnormal': is_abnormal,
            'export_count': total_exports,
        }

    def check_user_agent(self, ua: str) -> dict:
        """
        检查User-Agent是否异常
        返回: {'abnormal': bool, 'reason': str}
        """
        if not ua:
            return {'abnormal': True, 'reason': 'User-Agent为空'}

        for pattern in ABNORMAL_UA_PATTERNS:
            if re.search(pattern, ua, re.IGNORECASE):
                return {'abnormal': True, 'reason': f'匹配异常模式: {pattern}'}

        return {'abnormal': False, 'reason': ''}

    # ============ 安全事件日志 ============

    def _log_security_event(self, event_type: str, severity: str,
                            source_ip: str = '', user_type: str = '',
                            user_id: str = '', detail: str = ''):
        """记录安全事件到数据库"""
        try:
            from models import SecurityEvent
            now_str = str(int(time.time()))
            SecurityEvent.create(
                event_type=event_type,
                severity=severity,
                source_ip=source_ip,
                user_type=user_type,
                user_id=user_id,
                detail=detail,
                created_at=now_str,
            )
        except Exception as e:
            logger.error(f"记录安全事件失败: {e}")

    def log_off_hours_access(self, ip: str, user_type: str = 'admin',
                             user_id: str = '', endpoint: str = ''):
        """记录非正常工作时间访问事件"""
        self._log_security_event(
            event_type='off_hours_access',
            severity=SEVERITY_WARNING,
            source_ip=ip,
            user_type=user_type,
            user_id=user_id,
            detail=json.dumps({
                'hour': datetime.now().hour,
                'endpoint': endpoint,
            }, ensure_ascii=False)
        )
        logger.warning(f"[安全告警] 非正常时间访问: IP={ip}, 用户={user_id}, "
                      f"时间={datetime.now().strftime('%H:%M')}, 端点={endpoint}")

    def log_abnormal_ua(self, ip: str, ua: str, endpoint: str = ''):
        """记录异常User-Agent访问事件"""
        self._log_security_event(
            event_type='abnormal_ua',
            severity=SEVERITY_WARNING,
            source_ip=ip,
            detail=json.dumps({
                'user_agent': ua[:200],  # 截断防止过长
                'endpoint': endpoint,
            }, ensure_ascii=False)
        )
        logger.warning(f"[安全告警] 异常User-Agent: IP={ip}, UA={ua[:100]}")

    # ============ 查询接口 ============

    def get_security_events(self, event_type: str = '', severity: str = '',
                            hours: int = 24, limit: int = 100) -> list:
        """查询安全事件"""
        try:
            from models import SecurityEvent
            cutoff = str(int(time.time()) - hours * 3600)
            query = SecurityEvent.select().where(
                SecurityEvent.created_at >= cutoff
            )

            if event_type:
                query = query.where(SecurityEvent.event_type == event_type)
            if severity:
                query = query.where(SecurityEvent.severity == severity)

            query = query.order_by(SecurityEvent.id.desc()).limit(limit)

            return [{
                'id': e.id,
                'event_type': e.event_type,
                'severity': e.severity,
                'source_ip': e.source_ip,
                'user_type': e.user_type,
                'user_id': e.user_id,
                'detail': e.detail,
                'created_at': e.created_at,
            } for e in query]
        except Exception as e:
            logger.error(f"查询安全事件失败: {e}")
            return []

    def get_security_summary(self, hours: int = 24) -> dict:
        """获取安全事件摘要"""
        try:
            from models import SecurityEvent
            cutoff = str(int(time.time()) - hours * 3600)
            events = SecurityEvent.select().where(
                SecurityEvent.created_at >= cutoff
            )

            summary = {
                'total': 0,
                'by_severity': {'INFO': 0, 'WARNING': 0, 'CRITICAL': 0},
                'by_type': {},
                'locked_ips': [],
            }

            for e in events:
                summary['total'] += 1
                summary['by_severity'][e.severity] = summary['by_severity'].get(e.severity, 0) + 1
                summary['by_type'][e.event_type] = summary['by_type'].get(e.event_type, 0) + 1

            # 当前锁定的IP
            now = time.time()
            with self._data_lock:
                for ip, lockout_until in self._ip_lockouts.items():
                    if now < lockout_until:
                        summary['locked_ips'].append({
                            'ip': ip,
                            'remaining': int(lockout_until - now),
                        })

            return summary
        except Exception as e:
            logger.error(f"获取安全摘要失败: {e}")
            return {'total': 0, 'by_severity': {}, 'by_type': {}, 'locked_ips': []}

    def cleanup_old_events(self, days: int = 30):
        """清理过期安全事件（默认保留30天）"""
        try:
            from models import SecurityEvent
            cutoff = str(int(time.time()) - days * 86400)
            deleted = SecurityEvent.delete().where(
                SecurityEvent.created_at < cutoff
            ).execute()
            if deleted > 0:
                logger.info(f"已清理 {deleted} 条过期安全事件（{days}天前）")
        except Exception as e:
            logger.error(f"清理安全事件失败: {e}")


# 全局安全监控器实例
security_monitor = SecurityMonitor()
