#!/usr/bin/env python3
"""
测试增强版标签提取功能
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.tag_extractor import TagExtractor

def test_enhanced_extraction():
    """测试增强版标签提取"""
    print("🚀 开始测试增强版标签提取...")
    
    user_id = "test_user"
    extractor = TagExtractor(user_id)
    
    # 测试用例
    test_cases = [
        "我喜欢踢足球",
        "我喜欢看电影，你有没有看最近的院线电影",
        "我经常听音乐，特别是流行歌曲",
        "我会弹吉他，还学过钢琴",
        "我喜欢做手工，最近在学编织",
        "我经常健身，每天跑步",
        "我养了一只猫，很可爱",
        "我喜欢做饭，特别是家常菜",
        "我经常和朋友聚会，喜欢社交",
        "我喜欢旅行，去过很多地方"
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}: {test_text}")
        print(f"{'='*60}")
        
        try:
            # 提取标签
            extracted_tags = extractor.extract_tags_from_text(test_text)
            
            if extracted_tags:
                for category, tags in extracted_tags.items():
                    print(f"\n📊 分类 [{category}]:")
                    for tag in tags:
                        print(f"   ✅ {tag.name} -> {tag.category}.{tag.subcategory} (置信度: {tag.confidence:.2f})")
                        print(f"      证据: {tag.evidence}")
            else:
                print("❌ 未提取到任何标签")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_extraction() 