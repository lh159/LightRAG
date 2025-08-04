#!/usr/bin/env python3
"""
测试前端显示修复
"""

import sys
import os
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.tag_extractor import TagExtractor
from app.core.tag_manager import TagManager

def test_frontend_display():
    """测试前端显示修复"""
    print("🚀 开始测试前端显示修复...")
    
    user_id = "test_user_frontend"
    
    try:
        # 1. 提取标签（使用与用户相同的输入）
        extractor = TagExtractor(user_id)
        test_text = "我喜欢看电影"
        
        print(f"📝 测试文本: {test_text}")
        extracted_tags = extractor.extract_tags_from_text(test_text)
        
        if extracted_tags:
            print("✅ 标签提取成功:")
            for category, tags in extracted_tags.items():
                for tag in tags:
                    print(f"   - {tag.name} -> {tag.category}.{tag.subcategory} (置信度: {tag.confidence:.2f})")
        
        # 2. 更新标签
        tag_manager = TagManager(user_id)
        updated_tags = tag_manager.update_tags(extracted_tags)
        
        print("\n📊 更新后的标签结构:")
        tag_dimensions = updated_tags.get('tag_dimensions', {})
        
        for dim_key, dim_data in tag_dimensions.items():
            print(f"\n📋 维度: {dim_data.get('dimension_name', dim_key)}")
            
            if 'subcategories' in dim_data:
                for sub_key, sub_data in dim_data['subcategories'].items():
                    active_tags = sub_data.get('active_tags', [])
                    if active_tags:
                        print(f"   📂 子分类: {sub_data.get('subcategory_name', sub_key)}")
                        for tag in active_tags:
                            print(f"      ✅ {tag.get('tag_name', '')} (置信度: {tag.get('avg_confidence', 0):.2f})")
        
        # 3. 模拟前端数据结构
        print("\n🔍 模拟前端数据结构:")
        frontend_data = {
            'tag_dimensions': tag_dimensions,
            'active_dimensions': [],  # 向后兼容
            'emotional_health_index': updated_tags.get('emotional_health_index', 0.5)
        }
        
        print("✅ 前端数据结构已准备就绪")
        print(f"   - tag_dimensions: {len(tag_dimensions)} 个维度")
        
        # 检查是否有影视欣赏类标签
        interests_hobbies = tag_dimensions.get('interests_hobbies', {})
        film_tv = interests_hobbies.get('subcategories', {}).get('film_tv_appreciation', {})
        film_tags = film_tv.get('active_tags', [])
        
        if film_tags:
            print(f"   ✅ 影视欣赏类标签: {len(film_tags)} 个")
            for tag in film_tags:
                print(f"      - {tag.get('tag_name', '')} (置信度: {tag.get('avg_confidence', 0):.2f})")
        else:
            print("   ❌ 未找到影视欣赏类标签")
        
        return frontend_data
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_frontend_display() 