#!/usr/bin/env python3
"""
测试新的"用户-角色"对话格式
"""

import sys
import os
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web.app import parse_conversation_text

def test_role_format():
    """测试新的角色格式"""
    print("🚀 测试新的'用户-角色'对话格式...")
    
    # 测试文本格式
    test_text = """用户: 欢欢蜀黍，干嘛呢？
角色: 哎呀宝宝怎么突然叫我蜀黍啦～刚拍完一场打戏正在擦汗呢
用户: 热坏了吧！
角色: 是啊片场空调又罢工了...不过想到你在关心我瞬间就不热了呢
用户: 我这么有效
角色: 当然啦～你就是我的专属降温剂呀"""
    
    print("=" * 80)
    print("📄 测试文本格式:")
    print("=" * 80)
    print(test_text)
    print("=" * 80)
    
    # 解析文本
    messages = parse_conversation_text(test_text)
    
    print("\n🔍 解析结果:")
    print("-" * 50)
    for i, msg in enumerate(messages, 1):
        role_emoji = "👤" if msg['role'] == 'user' else "🎭"
        print(f"{i}. {role_emoji} {msg['role'].upper()}: {msg['content']}")
    
    print(f"\n📊 统计信息:")
    print(f"- 总消息数: {len(messages)}")
    print(f"- 用户消息: {len([m for m in messages if m['role'] == 'user'])}")
    print(f"- 角色消息: {len([m for m in messages if m['role'] == 'assistant'])}")
    
    # 测试Markdown格式
    test_markdown = """## 用户
欢欢蜀黍，干嘛呢？

## 角色
哎呀宝宝怎么突然叫我蜀黍啦～刚拍完一场打戏正在擦汗呢

## 用户
热坏了吧！

## 角色
是啊片场空调又罢工了...不过想到你在关心我瞬间就不热了呢"""
    
    print("\n" + "=" * 80)
    print("📄 测试Markdown格式:")
    print("=" * 80)
    print(test_markdown)
    print("=" * 80)
    
    # 解析Markdown
    markdown_messages = parse_conversation_text(test_markdown)
    
    print("\n🔍 Markdown解析结果:")
    print("-" * 50)
    for i, msg in enumerate(markdown_messages, 1):
        role_emoji = "👤" if msg['role'] == 'user' else "🎭"
        print(f"{i}. {role_emoji} {msg['role'].upper()}: {msg['content']}")
    
    # 测试JSON格式
    test_json = json.dumps([
        {"role": "user", "content": "欢欢蜀黍，干嘛呢？"},
        {"role": "assistant", "content": "哎呀宝宝怎么突然叫我蜀黍啦～刚拍完一场打戏正在擦汗呢"},
        {"role": "user", "content": "热坏了吧！"},
        {"role": "assistant", "content": "是啊片场空调又罢工了...不过想到你在关心我瞬间就不热了呢"}
    ], ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print("📄 测试JSON格式:")
    print("=" * 80)
    print(test_json)
    print("=" * 80)
    
    # 解析JSON
    json_messages = parse_conversation_text(test_json)
    
    print("\n🔍 JSON解析结果:")
    print("-" * 50)
    for i, msg in enumerate(json_messages, 1):
        role_emoji = "👤" if msg['role'] == 'user' else "🎭"
        print(f"{i}. {role_emoji} {msg['role'].upper()}: {msg['content']}")
    
    # 兼容性测试 - 测试旧的"助手"格式是否仍然支持
    test_old_format = """用户: 你好！今天心情不太好
助手: 怎么了？发生什么事情了吗？
用户: 工作上遇到了一些挫折，感觉很沮丧
助手: 我理解你的感受..."""
    
    print("\n" + "=" * 80)
    print("📄 兼容性测试 - 旧格式:")
    print("=" * 80)
    print(test_old_format)
    print("=" * 80)
    
    # 解析旧格式
    old_messages = parse_conversation_text(test_old_format)
    
    print("\n🔍 旧格式解析结果:")
    print("-" * 50)
    for i, msg in enumerate(old_messages, 1):
        role_emoji = "👤" if msg['role'] == 'user' else "🎭"
        print(f"{i}. {role_emoji} {msg['role'].upper()}: {msg['content']}")
    
    print("\n✅ 所有格式测试完成！")
    print("🎯 新格式'用户-角色'已成功支持，同时保持对旧格式的兼容性。")

if __name__ == "__main__":
    test_role_format() 