#!/usr/bin/env python3
"""
用户系统测试脚本
"""
import requests
import json
import time

class UserSystemTester:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_registration(self):
        """测试用户注册"""
        print("🧪 测试用户注册...")
        
        data = {
            "username": "testuser",
            "password": "testpass123",
            "email": "test@example.com"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/auth/register",
            json=data
        )
        
        result = response.json()
        
        if result.get("success"):
            print("✅ 注册测试通过")
            return True
        else:
            print("❌ 注册测试失败:", result.get("error"))
            return False
    
    def test_login(self):
        """测试用户登录"""
        print("🧪 测试用户登录...")
        
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json=data
        )
        
        result = response.json()
        
        if result.get("success"):
            print("✅ 登录测试通过")
            return True
        else:
            print("❌ 登录测试失败:", result.get("error"))
            return False
    
    def test_chat_functionality(self):
        """测试聊天功能"""
        print("🧪 测试聊天功能...")
        
        data = {
            "message": "你好，我是一个测试用户"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=data
        )
        
        result = response.json()
        
        if result.get("success"):
            print("✅ 聊天功能测试通过")
            return True
        else:
            print("❌ 聊天功能测试失败:", result.get("error"))
            return False
    
    def test_profile_access(self):
        """测试用户资料访问"""
        print("🧪 测试用户资料访问...")
        
        response = self.session.get(f"{self.base_url}/api/auth/profile")
        
        result = response.json()
        
        if result.get("success"):
            print("✅ 用户资料访问测试通过")
            return True
        else:
            print("❌ 用户资料访问测试失败:", result.get("error"))
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始用户系统测试...")
        
        tests = [
            self.test_registration,
            self.test_login,
            self.test_chat_functionality,
            self.test_profile_access
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ 测试异常: {e}")
        
        print(f"\n📊 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！用户系统运行正常。")
        else:
            print("⚠️  部分测试失败，请检查系统配置。")

if __name__ == "__main__":
    tester = UserSystemTester()
    tester.run_all_tests() 