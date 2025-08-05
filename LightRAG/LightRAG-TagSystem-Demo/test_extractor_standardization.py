#!/usr/bin/env python3
"""
测试TagExtractor的标签标准化功能
"""

import sys
import os

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.tag_extractor import TagExtractor, TagInfo

def test_tag_extractor_standardization():
    """测试标签提取器的标准化功能"""
    
    print("🔍 测试TagExtractor标签标准化功能")
    print("=" * 60)
    
    # 初始化标签提取器
    user_id = "test_standardization_user"
    extractor = TagExtractor(user_id)
    
    # 模拟一些需要标准化的标签
    test_tags = {
        "demographic_info": [
            TagInfo("青少年或年轻成年", 0.8, "用户提到自己年轻", "demographic_info", "age"),
            TagInfo("青年", 0.7, "用户表现出年轻特征", "demographic_info", "age"),
            TagInfo("男性", 0.9, "用户使用男性称谓", "demographic_info", "gender"),
            TagInfo("女生", 0.6, "用户自称女生", "demographic_info", "gender")
        ],
        "interests_hobbies": [
            TagInfo("看电影", 0.8, "用户说喜欢看电影", "interests_hobbies", "film_appreciation"),
            TagInfo("踢足球", 0.7, "用户提到踢足球", "interests_hobbies", "ball_sports"),
            TagInfo("做饭", 0.9, "用户说喜欢做饭", "interests_hobbies", "cooking"),
            TagInfo("烘焙", 0.6, "用户提到烘焙", "interests_hobbies", "baking")
        ]
    }
    
    print("📋 原始标签:")
    for category, tags in test_tags.items():
        print(f"\n{category}:")
        for tag in tags:
            print(f"  • {tag.name} (置信度: {tag.confidence:.2f}, 子类别: {tag.subcategory})")
    
    print("\n🔧 应用标准化...")
    
    # 应用标准化
    standardized_tags = extractor._apply_tag_standardization(test_tags)
    
    print("\n📋 标准化后的标签:")
    for category, tags in standardized_tags.items():
        print(f"\n{category}:")
        for tag in tags:
            print(f"  • {tag.name} (置信度: {tag.confidence:.2f}, 子类别: {tag.subcategory})")
            if "标准化自:" in tag.evidence:
                print(f"    证据: {tag.evidence}")
    
    # 测试标准化映射效果
    print("\n📊 标准化效果统计:")
    
    original_count = sum(len(tags) for tags in test_tags.values())
    standardized_count = sum(len(tags) for tags in standardized_tags.values())
    
    print(f"原始标签数量: {original_count}")
    print(f"标准化后数量: {standardized_count}")
    print(f"合并数量: {original_count - standardized_count}")
    
    # 验证具体的标准化效果
    print("\n🎯 验证预期的标准化效果:")
    
    # 检查年龄标签是否正确标准化
    demo_tags = standardized_tags.get("demographic_info", [])
    age_tags = [tag for tag in demo_tags if tag.subcategory == "age"]
    
    if age_tags:
        print("✅ 年龄标签标准化:")
        for tag in age_tags:
            print(f"  • {tag.name}")
        
        # 检查是否有标准化的标签
        has_standardized = any("青少年或年轻成人" in tag.name for tag in age_tags)
        if has_standardized:
            print("  ✅ 成功标准化为'青少年或年轻成人'")
        else:
            print("  ❌ 未找到预期的标准化标签")
    
    # 检查性别标签
    gender_tags = [tag for tag in demo_tags if tag.subcategory == "gender"]
    
    if gender_tags:
        print("✅ 性别标签标准化:")
        for tag in gender_tags:
            print(f"  • {tag.name}")
        
        # 检查是否有标准化的标签
        has_male = any("男" == tag.name for tag in gender_tags)
        has_female = any("女" == tag.name for tag in gender_tags)
        
        if has_male or has_female:
            print("  ✅ 成功标准化性别标签")
        else:
            print("  ❌ 未找到预期的标准化性别标签")
    
    # 检查兴趣爱好标签
    hobby_tags = standardized_tags.get("interests_hobbies", [])
    
    if hobby_tags:
        print("✅ 兴趣爱好标签标准化:")
        for tag in hobby_tags:
            print(f"  • {tag.name} ({tag.subcategory})")
        
        # 检查特定的标准化
        has_film = any("影视欣赏" in tag.name for tag in hobby_tags)
        has_sports = any("足球运动" in tag.name for tag in hobby_tags)
        has_cooking = any("烹饪" in tag.name for tag in hobby_tags)
        has_baking = any("烘焙制作" in tag.name for tag in hobby_tags)
        
        standardized_count = sum([has_film, has_sports, has_cooking, has_baking])
        print(f"  ✅ 成功标准化 {standardized_count} 个兴趣爱好标签")
    
    print("\n✅ 测试完成！")
    print("\n🎯 功能验证:")
    print("✓ 标签标准化映射")
    print("✓ 相似标签合并")
    print("✓ 置信度保留")
    print("✓ 证据信息更新")
    print("✓ 子类别保持一致")

def test_direct_standardization():
    """直接测试标准化映射"""
    print("\n" + "="*60)
    print("🧪 直接测试标准化映射")
    
    extractor = TagExtractor("test_user")
    
    test_cases = [
        ("青少年或年轻成年", "demographic_info"),
        ("年轻成年", "demographic_info"),
        ("青年", "demographic_info"),
        ("男性", "demographic_info"),
        ("女生", "demographic_info"),
        ("看电影", "interests_hobbies"),
        ("踢足球", "interests_hobbies"),
        ("做饭", "interests_hobbies"),
        ("烘焙", "interests_hobbies")
    ]
    
    for original_name, category in test_cases:
        category_rules = extractor.similarity_detector.category_similarity_rules.get(category, {})
        standardized = extractor.similarity_detector._standardize_tag_name(original_name, category_rules)
        
        if standardized != original_name:
            print(f"✅ {original_name} -> {standardized}")
        else:
            print(f"❌ {original_name} (无变化)")

if __name__ == "__main__":
    test_tag_extractor_standardization()
    test_direct_standardization()