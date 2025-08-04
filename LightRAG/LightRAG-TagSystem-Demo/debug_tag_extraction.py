#!/usr/bin/env python3
"""
标签提取调试脚本
用于全流程检查标签提取、应用和显示的问题
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.tag_extractor import TagExtractor
from app.core.enhanced_tag_extractor import EnhancedTagExtractor
from app.core.tag_manager import TagManager
from app.utils.llm_client import LLMClient

def test_basic_tag_extraction():
    """测试基础标签提取"""
    print("🔍 [调试] 开始基础标签提取测试...")
    
    user_id = "debug_user"
    test_text = "你，我喜欢踢足球"
    
    try:
        # 1. 测试基础标签提取器
        print(f"📝 测试文本: '{test_text}'")
        
        extractor = TagExtractor(user_id)
        print(f"✅ 标签提取器初始化完成")
        
        # 显示标签类别定义
        print(f"📋 兴趣爱好标签子类别:")
        interests_subcategories = extractor.tag_categories["interests_hobbies"]["subcategories"]
        for key, name in interests_subcategories.items():
            print(f"   - {key}: {name}")
        
        # 提取标签
        extracted_tags = extractor.extract_tags_from_text(test_text)
        print(f"🎯 提取结果: {extracted_tags}")
        
        # 详细分析结果
        if extracted_tags:
            for category, tags in extracted_tags.items():
                print(f"📊 分类 [{category}]:")
                for tag in tags:
                    print(f"   - 标签名: {tag.name}")
                    print(f"   - 置信度: {tag.confidence}")
                    print(f"   - 证据: {tag.evidence}")
                    print(f"   - 主分类: {tag.category}")
                    print(f"   - 子分类: {tag.subcategory}")
                    print()
        else:
            print("❌ 未提取到任何标签！")
            
        return extracted_tags
        
    except Exception as e:
        print(f"❌ 基础标签提取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_enhanced_tag_extraction():
    """测试增强标签提取"""
    print("\n🔍 [调试] 开始增强标签提取测试...")
    
    user_id = "debug_user" 
    test_text = "你，我喜欢踢足球"
    
    try:
        enhanced_extractor = EnhancedTagExtractor(user_id)
        print(f"✅ 增强标签提取器初始化完成")
        
        # 提取标签并记录溯源
        extracted_tags, triggers = enhanced_extractor.extract_tags_with_tracing(
            text=test_text,
            context={"source": "debug"},
            session_id="debug_session",
            message_id="debug_message"
        )
        
        print(f"🎯 增强提取结果: {extracted_tags}")
        print(f"📊 触发记录数量: {len(triggers) if triggers else 0}")
        
        if triggers:
            for trigger in triggers:
                print(f"⚡ 触发记录:")
                print(f"   - 标签: {trigger.tag_name}")
                print(f"   - 分类: {trigger.tag_category}")
                print(f"   - 动作: {trigger.action_type}")
                print(f"   - 置信度变化: {trigger.confidence_before} -> {trigger.confidence_after}")
                
        return extracted_tags, triggers
        
    except Exception as e:
        print(f"❌ 增强标签提取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_tag_manager_update():
    """测试标签管理器更新"""
    print("\n🔍 [调试] 开始标签管理器更新测试...")
    
    user_id = "debug_user"
    
    try:
        # 创建测试标签
        from app.core.tag_extractor import TagInfo
        test_tags = {
            "interests_hobbies": [
                TagInfo(
                    name="足球爱好者",
                    confidence=0.8,
                    evidence="喜欢踢足球",
                    category="interests_hobbies",
                    subcategory="ball_sports"
                )
            ]
        }
        
        tag_manager = TagManager(user_id)
        print(f"✅ 标签管理器初始化完成")
        
        # 更新标签
        updated_tags = tag_manager.update_tags(test_tags)
        print(f"✅ 标签更新完成")
        
        # 显示更新后的标签结构
        print(f"📋 更新后的标签结构:")
        interests_hobbies = updated_tags.get("tag_dimensions", {}).get("interests_hobbies", {})
        
        if "subcategories" in interests_hobbies:
            for sub_key, sub_data in interests_hobbies["subcategories"].items():
                active_tags = sub_data.get("active_tags", [])
                if active_tags:
                    print(f"   子分类 [{sub_key}] ({sub_data.get('subcategory_name', '')}):")
                    for tag in active_tags:
                        print(f"     - {tag.get('tag_name', '')} (置信度: {tag.get('avg_confidence', 0):.2f})")
        
        # 获取用户标签用于前端显示测试
        user_tags = tag_manager.get_user_tags()
        print(f"📊 用户标签文件内容:")
        print(json.dumps(user_tags, ensure_ascii=False, indent=2)[:500] + "...")
        
        return updated_tags
        
    except Exception as e:
        print(f"❌ 标签管理器更新测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_frontend_compatibility():
    """测试前端兼容性"""
    print("\n🔍 [调试] 开始前端兼容性测试...")
    
    user_id = "debug_user"
    
    try:
        # 模拟 /api/profile 接口逻辑
        tag_manager = TagManager(user_id)
        user_tags = tag_manager.get_user_tags()
        
        # 检查数据结构
        dimensions = user_tags.get('tag_dimensions', {})
        interests_hobbies = dimensions.get('interests_hobbies', {})
        
        print(f"📋 兴趣爱好标签结构检查:")
        print(f"   维度名称: {interests_hobbies.get('dimension_name', '未找到')}")
        
        subcategories = interests_hobbies.get('subcategories', {})
        print(f"   子分类数量: {len(subcategories)}")
        
        expected_subcategories = [
            "art_creation", "handcraft_diy", "music_appreciation", "music_performance",
            "film_tv_appreciation", "ball_sports", "sports_watching", "extreme_sports",
            "health_fitness", "pet_keeping", "home_cooking", "baking",
            "food_exploration", "offline_socializing", "home_design", "knowledge_learning",
            "collecting_appreciation", "life_experience"
        ]
        
        print(f"   预期子分类: {len(expected_subcategories)}个")
        
        for expected in expected_subcategories:
            if expected in subcategories:
                sub_data = subcategories[expected]
                active_tags = sub_data.get("active_tags", [])
                print(f"   ✅ {expected} ({sub_data.get('subcategory_name', '')}): {len(active_tags)}个标签")
            else:
                print(f"   ❌ 缺失子分类: {expected}")
        
        # 检查ball_sports子分类
        ball_sports = subcategories.get("ball_sports", {})
        if ball_sports:
            print(f"\n🏈 球类运动类详细检查:")
            print(f"   名称: {ball_sports.get('subcategory_name', '')}")
            print(f"   活跃标签: {len(ball_sports.get('active_tags', []))}个")
            
            for tag in ball_sports.get('active_tags', []):
                print(f"     - {tag.get('tag_name', '')} (置信度: {tag.get('avg_confidence', 0):.2f})")
        
        return user_tags
        
    except Exception as e:
        print(f"❌ 前端兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_llm_prompt():
    """测试LLM prompt内容"""
    print("\n🔍 [调试] 开始LLM prompt测试...")
    
    user_id = "debug_user"
    test_text = "你，我喜欢踢足球"
    
    try:
        extractor = TagExtractor(user_id)
        
        # 构建prompt
        prompt = extractor._build_extraction_prompt(test_text)
        
        print("📝 生成的LLM Prompt:")
        print("=" * 50)
        print(prompt)
        print("=" * 50)
        
        # 检查prompt中是否包含新的子标签
        if "球类运动类" in prompt:
            print("✅ Prompt包含'球类运动类'")
        else:
            print("❌ Prompt未包含'球类运动类'")
            
        return prompt
        
    except Exception as e:
        print(f"❌ LLM prompt测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    print("🚀 开始标签提取调试...")
    print(f"⏰ 时间: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # 1. 测试LLM prompt
    test_llm_prompt()
    
    # 2. 测试基础标签提取
    extracted_tags = test_basic_tag_extraction()
    
    # 3. 测试增强标签提取 
    enhanced_tags, triggers = test_enhanced_tag_extraction()
    
    # 4. 测试标签管理器更新
    updated_tags = test_tag_manager_update()
    
    # 5. 测试前端兼容性
    frontend_data = test_frontend_compatibility()
    
    print("\n" + "=" * 80)
    print("🏁 调试完成")
    
    # 总结
    print("\n📊 问题总结:")
    if not extracted_tags:
        print("❌ 基础标签提取失败")
    elif "interests_hobbies" not in extracted_tags:
        print("❌ 未提取到兴趣爱好标签")
    elif not any(tag.subcategory == "ball_sports" for tag in extracted_tags.get("interests_hobbies", [])):
        print("❌ 未将足球归类到球类运动类")
    else:
        print("✅ 标签提取正常")
        
    if not updated_tags:
        print("❌ 标签管理器更新失败")
    else:
        print("✅ 标签管理器更新正常")
        
    if not frontend_data:
        print("❌ 前端数据获取失败")
    else:
        print("✅ 前端数据获取正常")

if __name__ == "__main__":
    main()