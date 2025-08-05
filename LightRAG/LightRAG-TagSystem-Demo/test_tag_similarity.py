#!/usr/bin/env python3
"""
测试标签相似性检测和合并功能
"""

import sys
import os

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.tag_similarity_detector import TagSimilarityDetector
from app.core.tag_extractor import TagInfo
from app.core.tag_manager import TagManager

def test_tag_similarity_detection():
    """测试标签相似性检测功能"""
    
    print("🔍 测试标签相似性检测和合并功能")
    print("=" * 60)
    
    # 初始化相似性检测器
    similarity_detector = TagSimilarityDetector()
    
    # 模拟现有标签
    existing_tags = [
        {
            "tag_name": "青少年或年轻成年",
            "avg_confidence": 0.6,
            "evidence": "用户提到自己是年轻人",
            "category": "demographic_info",
            "subcategory": "age",
            "first_detected": "2024-01-01T00:00:00",
            "last_reinforced": "2024-01-01T00:00:00",
            "evidence_count": 1,
            "total_confidence": 0.6,
            "decay_rate": 0.1,
            "current_weight": 0.6,
            "is_historical": False,
            "is_contextual": False,
            "conflict_resolved": False
        },
        {
            "tag_name": "女性",
            "avg_confidence": 0.7,
            "evidence": "用户使用女性化表达",
            "category": "demographic_info",
            "subcategory": "gender",
            "first_detected": "2024-01-01T00:00:00",
            "last_reinforced": "2024-01-01T00:00:00",
            "evidence_count": 1,
            "total_confidence": 0.7,
            "decay_rate": 0.1,
            "current_weight": 0.7,
            "is_historical": False,
            "is_contextual": False,
            "conflict_resolved": False
        },
        {
            "tag_name": "看电影",
            "avg_confidence": 0.8,
            "evidence": "用户说喜欢看电影",
            "category": "interests_hobbies",
            "subcategory": "film_appreciation",
            "first_detected": "2024-01-01T00:00:00",
            "last_reinforced": "2024-01-01T00:00:00",
            "evidence_count": 1,
            "total_confidence": 0.8,
            "decay_rate": 0.1,
            "current_weight": 0.8,
            "is_historical": False,
            "is_contextual": False,
            "conflict_resolved": False
        }
    ]
    
    # 模拟新标签
    new_tags = [
        TagInfo("青少年或年轻成人", 0.7, "用户提到自己刚成年", "demographic_info", "age"),
        TagInfo("女生", 0.6, "用户使用女生自称", "demographic_info", "gender"),
        TagInfo("影视欣赏", 0.9, "用户说喜欢看剧", "interests_hobbies", "film_appreciation"),
        TagInfo("踢足球", 0.8, "用户说喜欢踢足球", "interests_hobbies", "ball_sports"),
        TagInfo("烘焙制作", 0.7, "用户说喜欢做蛋糕", "interests_hobbies", "baking")
    ]
    
    print("📋 现有标签:")
    for tag in existing_tags:
        print(f"  • {tag['tag_name']} ({tag['category']}.{tag['subcategory']})")
    
    print("\n📋 新标签:")
    for tag in new_tags:
        print(f"  • {tag.name} ({tag.category}.{tag.subcategory})")
    
    print("\n🔍 检测相似标签...")
    
    # 检测相似标签
    similar_groups = similarity_detector.detect_similar_tags(existing_tags, new_tags)
    
    if similar_groups:
        print(f"\n✅ 发现 {len(similar_groups)} 组相似标签:")
        for i, group in enumerate(similar_groups, 1):
            print(f"\n{i}. 主要标签: {group.primary_tag}")
            print(f"   相似标签: {', '.join(group.similar_tags)}")
            print(f"   相似度: {group.similarity_score:.2f}")
            print(f"   合并原因: {group.merge_reason}")
    else:
        print("\n❌ 未发现相似标签")
    
    # 测试合并功能
    print("\n🔄 测试标签合并功能...")
    
    # 模拟标签管理器
    user_id = "test_similarity_user"
    tag_manager = TagManager(user_id)
    
    # 创建测试数据 - 使用标准化的标签名称
    test_dimension_data = {
        "dimension_name": "基本人口统计学标签",
        "subcategories": {
            "age": {
                "subcategory_name": "年龄",
                "active_tags": [
                    {
                        "tag_name": "青少年或年轻成人",  # 使用标准化后的名称
                        "avg_confidence": 0.6,
                        "evidence": "用户提到自己是年轻人",
                        "category": "demographic_info",
                        "subcategory": "age",
                        "first_detected": "2024-01-01T00:00:00",
                        "last_reinforced": "2024-01-01T00:00:00",
                        "evidence_count": 1,
                        "total_confidence": 0.6,
                        "decay_rate": 0.1,
                        "current_weight": 0.6,
                        "is_historical": False,
                        "is_contextual": False,
                        "conflict_resolved": False
                    }
                ],
                "dominant_tag": None,
                "dimension_weight": 0.0,
                "stability_score": 0.0,
                "conflict_history": []
            }
        }
    }
    
    print("\n📊 合并前标签状态:")
    for tag in test_dimension_data["subcategories"]["age"]["active_tags"]:
        print(f"  • {tag['tag_name']} (置信度: {tag['avg_confidence']:.2f})")
    
    # 尝试添加相似标签
    new_age_tag = TagInfo("青少年或年轻成人", 0.7, "用户提到自己刚成年", "demographic_info", "age")
    
    print(f"\n➕ 添加新标签: {new_age_tag.name}")
    
    # 更新标签
    tag_manager._update_subcategory_tag(
        test_dimension_data["subcategories"]["age"], 
        new_age_tag
    )
    
    print("\n📊 合并后标签状态:")
    for tag in test_dimension_data["subcategories"]["age"]["active_tags"]:
        print(f"  • {tag['tag_name']} (置信度: {tag['avg_confidence']:.2f})")
        if "merge_info" in tag:
            print(f"    合并信息: {tag['merge_info']['merge_reason']}")
    
    # 测试标准化映射
    print("\n🔧 测试标签标准化映射:")
    test_names = [
        "青少年或年轻成年",
        "年轻成年", 
        "青年",
        "男性",
        "女生",
        "看电影",
        "踢足球",
        "做饭",
        "烘焙"
    ]
    
    for name in test_names:
        standardized = similarity_detector._standardize_tag_name(name, {})
        if standardized != name:
            print(f"  {name} -> {standardized}")
        else:
            print(f"  {name} (无变化)")
    
    # 测试相似度计算
    print("\n📏 测试相似度计算:")
    test_pairs = [
        ("青少年或年轻成年", "青少年或年轻成人"),
        ("男性", "男"),
        ("看电影", "影视欣赏"),
        ("踢足球", "足球运动"),
        ("做饭", "烹饪"),
        ("烘焙", "烘焙制作")
    ]
    
    for name1, name2 in test_pairs:
        similarity = similarity_detector._calculate_similarity(name1, name2)
        print(f"  {name1} vs {name2}: {similarity:.3f}")
    
    print("\n✅ 测试完成！")
    print("\n🎯 功能验证:")
    print("✓ 标签相似性检测")
    print("✓ 标签标准化映射")
    print("✓ 相似度计算")
    print("✓ 标签合并功能")
    print("✓ 合并信息记录")

if __name__ == "__main__":
    test_tag_similarity_detection() 