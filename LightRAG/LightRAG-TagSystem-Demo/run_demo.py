#!/usr/bin/env python3
"""
LightRAG标签体系演示Demo启动脚本 - DeepSeek版本
"""
import os
import sys
from pathlib import Path

def load_config():
    """加载配置文件"""
    try:
        import yaml
    except ImportError:
        print("错误: 缺少yaml模块，请运行: pip install pyyaml")
        sys.exit(1)
        
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("错误: 配置文件 config.yaml 不存在")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def setup_environment():
    """设置环境变量"""
    config = load_config()
    
    # 设置API Key（DeepSeek）
    api_key = config.get('llm', {}).get('api_key')
    if not api_key:
        print("错误: 配置文件中未找到API Key")
        sys.exit(1)
    
    # 将DeepSeek API Key设置为OPENAI_API_KEY环境变量（兼容性）
    os.environ['OPENAI_API_KEY'] = api_key
    
    print(f"✅ DeepSeek API配置完成")
    print(f"🔑 API Key: {api_key[:8]}...{api_key[-8:]}")
    
    return config

def create_directories():
    """创建必要的目录"""
    directories = [
        "user_data",
        "user_data/global", 
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ 目录结构创建完成")

def check_dependencies():
    """检查依赖包"""
    required_modules = [
        ("lightrag", "lightrag"),
        ("openai", "openai"),
        ("flask", "flask"),
        ("pydantic", "pydantic"),
        ("yaml", "pyyaml")
    ]
    
    missing_packages = []
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"错误: 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ 依赖包检查通过")

def main():
    """主函数"""
    print("🚀 启动 LightRAG标签体系演示Demo (DeepSeek版本)...")
    
    # 检查依赖
    check_dependencies()
    
    # 设置环境
    config = setup_environment()
    
    # 创建目录
    create_directories()
    
    # 启动Web应用
    try:
        from web.app import app
        
        host = config.get('web', {}).get('host', '127.0.0.1')
        port = config.get('web', {}).get('port', 5000)
        debug = config.get('app', {}).get('debug', True)
        
        print(f"✅ Demo启动成功!")
        print(f"📱 访问地址: http://{host}:{port}")
        print("💡 使用说明:")
        print("   1. 在聊天界面与助手对话")
        print("   2. 观察右侧用户画像的实时更新")
        print("   3. 可以添加知识到个人知识库")
        print("   4. 重置按钮可以清除会话数据")
        print("\n🔥 DeepSeek驱动的个性化情感陪伴体验!")
        
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print(f"💡 建议: 请检查DeepSeek API Key是否有效")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
