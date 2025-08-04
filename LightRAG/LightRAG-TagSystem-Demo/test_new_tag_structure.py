#!/usr/bin/env python3
"""
测试新的二级标签结构
"""

import sys
import os
import json
from datetime import datetime

# 添加路径以便导入
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.tag_extractor import TagExtractor, TagInfo
from core.tag_manager import TagManager

def test_new_tag_structure():
    """测试新的二级标签结构"""
    print("🧪 开始测试新的二级标签结构...")
    
    # 创建测试用户
    test_user_id = "test_user_new_structure"
    
    # 初始化标签提取器和管理器
    extractor = TagExtractor(test_user_id)
    manager = TagManager(test_user_id)
    
    print("\n📋 测试标签类别定义...")
    print("标签类别结构:")
    for category_key, category_info in extractor.tag_categories.items():
        print(f"  {category_key}: {category_info['name']}")
        for sub_key, sub_name in category_info['subcategories'].items():
            print(f"    - {sub_key}: {sub_name}")
    
    # 测试用例
    test_cases = [
        {
            "text": "我是一个90后程序员，平时喜欢看电影和打篮球",
            "expected_categories": ["demographic_info", "interests_hobbies"]
        },
        {
            "text": "最近心情不太好，工作压力很大，希望有人能听我倾诉",
            "expected_categories": ["emotional_state"]
        },
        {
            "text": "我来自北京，是个女生，喜欢听音乐和健身",
            "expected_categories": ["demographic_info", "interests_hobbies"]
        }
    ]
    
    print("\n🔍 开始提取标签测试...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i} ---")
        print(f"输入文本: {test_case['text']}")
        
        # 提取标签
        extracted_tags = extractor.extract_tags_from_text(test_case['text'])
        
        print("提取结果:")
        for category, tags in extracted_tags.items():
            if tags:
                print(f"  {category}:")
                for tag in tags:
                    print(f"    - {tag.name} (置信度: {tag.confidence:.2f})")
                    print(f"      类别: {tag.category} -> {tag.subcategory}")
                    print(f"      证据: {tag.evidence}")
        
        # 更新标签管理器
        print("\n📝 更新标签管理器...")
        try:
            result = manager.update_tags(extracted_tags)
            print("✅ 标签更新成功")
        except Exception as e:
            print(f"❌ 标签更新失败: {e}")
    
    # 检查生成的标签文件
    print("\n📄 检查生成的标签文件...")
    tags_file = f"user_data/{test_user_id}/user_tags.json"
    
    if os.path.exists(tags_file):
        with open(tags_file, 'r', encoding='utf-8') as f:
            tags_data = json.load(f)
        
        print("标签文件结构:")
        print(f"  用户ID: {tags_data.get('user_id')}")
        print(f"  创建时间: {tags_data.get('created_at')}")
        print(f"  最后更新: {tags_data.get('last_updated')}")
        
        print("\n标签维度:")
        for dim_key, dim_data in tags_data.get('tag_dimensions', {}).items():
            print(f"  {dim_key}: {dim_data.get('dimension_name')}")
            
            if 'subcategories' in dim_data:
                for sub_key, sub_data in dim_data['subcategories'].items():
                    print(f"    - {sub_key}: {sub_data.get('subcategory_name')}")
                    active_tags = sub_data.get('active_tags', [])
                    print(f"      活跃标签数量: {len(active_tags)}")
                    
                    for tag in active_tags[:3]:  # 只显示前3个
                        print(f"        * {tag.get('tag_name')} (置信度: {tag.get('avg_confidence', 0):.2f})")
    else:
        print("❌ 标签文件未生成")
    
    print("\n🎉 测试完成！")

def test_tag_info_creation():
    """测试TagInfo类的创建"""
    print("\n🧪 测试TagInfo类创建...")
    
    try:
        # 测试新的TagInfo结构
        tag = TagInfo(
            name="年轻用户",
            confidence=0.8,
            evidence="使用了年轻人常用的网络用语",
            category="demographic_info",
            subcategory="age"
        )
        
        print(f"✅ TagInfo创建成功:")
        print(f"  名称: {tag.name}")
        print(f"  置信度: {tag.confidence}")
        print(f"  证据: {tag.evidence}")
        print(f"  一级分类: {tag.category}")
        print(f"  二级分类: {tag.subcategory}")
        
    except Exception as e:
        print(f"❌ TagInfo创建失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("新的二级标签结构测试")
    print("=" * 60)
    
    test_tag_info_creation()
    test_new_tag_structure()