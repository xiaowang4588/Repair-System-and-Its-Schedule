"""
管理员密码重置工具
用法: python reset_password.py [新密码]
不传参数则交互式输入
"""
import sys
import os
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from admin_config import load_config, save_config

def reset_admin_password(new_password=None):
    if not new_password:
        new_password = input("请输入新的管理员密码: ").strip()
        if not new_password:
            print("密码不能为空")
            return False
        confirm = input("请再次输入密码: ").strip()
        if new_password != confirm:
            print("两次密码不一致")
            return False

    if len(new_password) < 6:
        print("密码长度不能少于6位")
        return False

    config = load_config()
    config["admin"]["password_hash"] = hashlib.sha256(new_password.encode()).hexdigest()
    save_config(config)
    print(f"管理员密码已重置成功")
    return True

if __name__ == '__main__':
    if len(sys.argv) > 1:
        reset_admin_password(sys.argv[1])
    else:
        reset_admin_password()
