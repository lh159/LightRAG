#!/usr/bin/env python3
"""
用户系统部署脚本
"""
import os
import sys
import shutil
import time
from pathlib import Path

def create_directories():
    """创建必要的目录"""
    directories = [
        "app/models",
        "app/auth", 
        "app/api",
        "app/utils",
        "web/static/css",
        "web/static/js",
        "web/static/images",
        "database",
        "database/backups",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {directory}")

def install_dependencies():
    """安装依赖"""
    print("📦 安装依赖包...")
    os.system("pip install -r requirements.txt")

def setup_database():
    """设置数据库"""
    print("🗄️ 初始化数据库...")
    try:
        from app.utils.database import DatabaseManager
        
        db_manager = DatabaseManager()
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")

def create_admin_user():
    """创建管理员用户"""
    print("👤 创建管理员用户...")
    try:
        from app.utils.database import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # 创建默认管理员账户
        admin_result = db_manager.create_user(
            username="admin",
            password="admin123",
            email="admin@lightrag.com"
        )
        
        if admin_result["success"]:
            print("✅ 管理员用户创建成功")
            print("   用户名: admin")
            print("   密码: admin123")
            print("   ⚠️  请在生产环境中修改默认密码！")
        else:
            print("❌ 管理员用户创建失败:", admin_result["error"])
    except Exception as e:
        print(f"❌ 创建管理员用户失败: {e}")

def backup_existing_data():
    """备份现有数据"""
    print("💾 备份现有数据...")
    
    if os.path.exists("user_data"):
        backup_dir = f"backup_{int(time.time())}"
        shutil.copytree("user_data", backup_dir)
        print(f"✅ 数据已备份到: {backup_dir}")

def main():
    """主部署流程"""
    print("🚀 开始部署LightRAG用户系统...")
    
    # 1. 创建目录结构
    create_directories()
    
    # 2. 安装依赖
    install_dependencies()
    
    # 3. 设置数据库
    setup_database()
    
    # 4. 创建管理员用户
    create_admin_user()
    
    # 5. 备份现有数据
    backup_existing_data()
    
    print("\n🎉 用户系统部署完成！")
    print("\n📋 下一步操作:")
    print("1. 启动应用: python run_demo.py")
    print("2. 访问: http://127.0.0.1:5000")
    print("3. 使用管理员账户登录")
    print("4. 根据需要修改配置文件")

if __name__ == "__main__":
    main() 