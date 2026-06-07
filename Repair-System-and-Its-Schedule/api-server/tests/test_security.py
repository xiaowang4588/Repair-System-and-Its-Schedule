"""
安全功能测试模块
覆盖：管理员密码哈希、Token吊销机制、入侵检测、安全事件记录
"""
import unittest
import hashlib
import secrets
import time
import json
import os
import sys

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.admin_config import (
    _hash_admin_password, _verify_admin_password, _needs_rehash
)
from utils.token_utils import (
    generate_admin_token, verify_admin_token, revoke_tokens_for_user,
    refresh_admin_token, TOKEN_REFRESH_THRESHOLD_HOURS, ADMIN_TOKEN_EXPIRE_HOURS
)
from utils.security_monitor import SecurityMonitor, security_monitor


class TestAdminPasswordHash(unittest.TestCase):
    """管理员密码哈希安全测试"""

    def test_salted_hash_format(self):
        """带盐哈希应生成 salt$hash 格式"""
        result = _hash_admin_password("test123")
        self.assertIn('$', result)
        parts = result.split('$', 1)
        self.assertEqual(len(parts), 2)
        self.assertEqual(len(parts[0]), 32)  # 16字节 = 32个十六进制字符
        self.assertEqual(len(parts[1]), 64)  # SHA-256 = 64个十六进制字符

    def test_salted_hash_deterministic_with_salt(self):
        """指定盐值时哈希应确定性"""
        salt = "abcdef0123456789"
        h1 = _hash_admin_password("test123", salt)
        h2 = _hash_admin_password("test123", salt)
        self.assertEqual(h1, h2)

    def test_different_salts_different_hashes(self):
        """不同盐值应产生不同哈希"""
        h1 = _hash_admin_password("test123")
        h2 = _hash_admin_password("test123")
        self.assertNotEqual(h1, h2)

    def test_verify_new_format(self):
        """验证新格式密码（带盐）"""
        hashed = _hash_admin_password("mypassword")
        self.assertTrue(_verify_admin_password("mypassword", hashed))
        self.assertFalse(_verify_admin_password("wrongpassword", hashed))

    def test_verify_old_format_compatibility(self):
        """验证旧格式密码（无盐SHA-256）兼容性"""
        old_hash = hashlib.sha256("123456".encode()).hexdigest()
        self.assertTrue(_verify_admin_password("123456", old_hash))
        self.assertFalse(_verify_admin_password("wrong", old_hash))

    def test_needs_rehash(self):
        """旧格式哈希应标记为需要升级"""
        old_hash = hashlib.sha256("123456".encode()).hexdigest()
        self.assertTrue(_needs_rehash(old_hash))

        new_hash = _hash_admin_password("123456")
        self.assertFalse(_needs_rehash(new_hash))


class TestTokenRevocation(unittest.TestCase):
    """Token吊销机制测试"""

    def setUp(self):
        self.secret_key = secrets.token_hex(32)
        self.username = "testadmin"

    def test_generate_token_contains_iat_jti(self):
        """生成的Token应包含iat和jti字段"""
        token = generate_admin_token(self.username, self.secret_key)
        import base64
        payload_b64 = token.split('.')[0]
        pad_len = (4 - len(payload_b64) % 4) % 4
        padded = payload_b64 + '=' * pad_len
        payload_str = base64.urlsafe_b64decode(padded).decode('utf-8')
        payload = json.loads(payload_str)

        self.assertIn('iat', payload)
        self.assertIn('jti', payload)
        self.assertIn('exp', payload)
        self.assertEqual(payload['user'], self.username)
        self.assertEqual(payload['role'], 'admin')

    def test_verify_valid_token(self):
        """验证有效Token"""
        token = generate_admin_token(self.username, self.secret_key)
        result = verify_admin_token(token, self.secret_key)
        self.assertTrue(result['valid'])
        self.assertEqual(result['username'], self.username)

    def test_verify_expired_token(self):
        """验证过期Token"""
        token = generate_admin_token(self.username, self.secret_key, expire_hours=-1)
        result = verify_admin_token(token, self.secret_key)
        self.assertFalse(result['valid'])
        self.assertIn('过期', result['error'])

    def test_verify_invalid_signature(self):
        """验证签名无效的Token"""
        token = generate_admin_token(self.username, self.secret_key)
        # 篡改Token
        tampered = token[:-5] + "xxxxx"
        result = verify_admin_token(tampered, self.secret_key)
        self.assertFalse(result['valid'])

    def test_needs_refresh_flag(self):
        """Token临近过期时应标记needs_refresh"""
        # 生成一个3天后过期的Token（在7天刷新阈值内）
        token = generate_admin_token(self.username, self.secret_key, expire_hours=72)
        result = verify_admin_token(token, self.secret_key)
        self.assertTrue(result['valid'])
        self.assertTrue(result.get('needs_refresh', False))

    def test_no_refresh_when_far_from_expiry(self):
        """Token远离过期时不应标记needs_refresh"""
        # 生成一个20天后过期的Token（在7天刷新阈值外）
        token = generate_admin_token(self.username, self.secret_key, expire_hours=480)
        result = verify_admin_token(token, self.secret_key)
        self.assertTrue(result['valid'])
        self.assertFalse(result.get('needs_refresh', False))

    def test_refresh_token(self):
        """刷新Token应返回新的有效Token"""
        token = generate_admin_token(self.username, self.secret_key)
        result = refresh_admin_token(token, self.secret_key)
        self.assertTrue(result['success'])
        self.assertNotEqual(result['token'], token)

        # 验证新Token有效
        new_result = verify_admin_token(result['token'], self.secret_key)
        self.assertTrue(new_result['valid'])


class TestSecurityMonitor(unittest.TestCase):
    """入侵检测与安全监控测试"""

    def setUp(self):
        self.monitor = SecurityMonitor()
        # 清理测试数据
        with self.monitor._data_lock:
            self.monitor._login_failures.clear()
            self.monitor._ip_lockouts.clear()
            self.monitor._export_counts.clear()

    def test_login_failure_recording(self):
        """登录失败应被正确记录"""
        result = self.monitor.record_login_failure("192.168.1.1", "admin", "admin")
        self.assertFalse(result['locked'])
        self.assertEqual(result['failure_count'], 1)

    def test_ip_lockout_after_max_failures(self):
        """超过最大失败次数后IP应被锁定"""
        ip = "192.168.1.2"
        for i in range(30):
            result = self.monitor.record_login_failure(ip, "admin", "admin")

        self.assertTrue(result['locked'])
        self.assertTrue(self.monitor.is_ip_locked(ip))
        self.assertGreater(self.monitor.get_lockout_remaining(ip), 0)

    def test_ip_not_locked_below_threshold(self):
        """未达到阈值时IP不应被锁定"""
        ip = "192.168.1.3"
        for i in range(29):
            self.monitor.record_login_failure(ip, "admin", "admin")

        self.assertFalse(self.monitor.is_ip_locked(ip))

    def test_login_success_clears_failures(self):
        """登录成功应清除失败计数"""
        ip = "192.168.1.4"
        self.monitor.record_login_failure(ip, "admin", "admin")
        self.monitor.record_login_success(ip, "admin", "admin")

        # 再次失败应从1开始计数
        result = self.monitor.record_login_failure(ip, "admin", "admin")
        self.assertEqual(result['failure_count'], 1)

    def test_off_hours_detection(self):
        """非正常工作时间检测"""
        # 此测试依赖当前时间，仅验证函数可正常调用
        result = self.monitor.check_off_hours_access('admin')
        self.assertIsInstance(result, bool)

    def test_off_hours_not_triggered_for_student(self):
        """学生账户不应触发非正常时间检测"""
        result = self.monitor.check_off_hours_access('student')
        self.assertFalse(result)

    def test_abnormal_ua_empty(self):
        """空User-Agent应被检测为异常"""
        result = self.monitor.check_user_agent('')
        self.assertTrue(result['abnormal'])

    def test_abnormal_ua_attack_tool(self):
        """攻击工具User-Agent应被检测为异常"""
        result = self.monitor.check_user_agent('sqlmap/1.0')
        self.assertTrue(result['abnormal'])

    def test_normal_ua(self):
        """正常User-Agent不应被检测为异常"""
        result = self.monitor.check_user_agent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.assertFalse(result['abnormal'])

    def test_export_monitoring(self):
        """导出操作应被正确监控"""
        ip = "192.168.1.5"
        result = self.monitor.record_export(ip, record_count=1)
        self.assertFalse(result['abnormal'])

    def test_bulk_export_detection(self):
        """批量导出应触发告警"""
        ip = "192.168.1.6"
        # 模拟大量导出
        result = self.monitor.record_export(ip, record_count=100)
        self.assertTrue(result['abnormal'])

    def test_security_summary(self):
        """安全摘要应正确返回"""
        summary = self.monitor.get_security_summary(hours=24)
        self.assertIn('total', summary)
        self.assertIn('by_severity', summary)
        self.assertIn('by_type', summary)
        self.assertIn('locked_ips', summary)


class TestBackwardCompatibility(unittest.TestCase):
    """向后兼容性测试"""

    def test_old_token_without_iat_still_works(self):
        """不含iat字段的旧Token仍应能验证"""
        import base64
        import hmac as hmac_mod
        import json as json_mod

        secret = secrets.token_hex(32)
        # 构造旧格式Token（不含iat和jti）
        payload = json_mod.dumps({
            'user': 'testadmin',
            'role': 'admin',
            'exp': int(time.time()) + 3600,
        }, ensure_ascii=False)

        payload_b64 = base64.urlsafe_b64encode(payload.encode('utf-8')).decode().rstrip('=')
        signature = hmac_mod.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        old_token = f"{payload_b64}.{signature}"
        result = verify_admin_token(old_token, secret)
        self.assertTrue(result['valid'])
        self.assertEqual(result['username'], 'testadmin')


if __name__ == '__main__':
    unittest.main(verbosity=2)
