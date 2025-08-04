#!/usr/bin/env python3
"""
对比自动JSON解析和手动解析的效果
"""

import sys
import os
import json
import re

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.tag_extractor import TagExtractor

def test_json_parsing_comparison():
    """对比自动JSON解析和手动解析的效果"""
    print("🚀 开始对比JSON解析方法...")
    
    # 模拟一个典型的不完整JSON响应（来自LLM）
    incomplete_json = '''```json
{
    "基本人口统计学标签": {
        "年龄": [
            {"tag": "青年", "confidence": 0.7, "evidence": "喜欢看电影是年轻人常见的娱乐方式"}
        ],
        "性别": [
            {"tag": "中性", "confidence": 0.5, "evidence": "表达方式中性，无明显性别倾向"}
        ],
        "地域": []
    },
    "兴趣爱好标签": {
        "文艺创作类": [],
        "手工DIY类": [],
        "音乐欣赏类": [],
        "音乐演奏类": [],
        "影视欣赏类": [
            {"tag": "电影爱好者", "confidence": 0.9, "evidence": "我喜欢看电影"}
        ],
        "球类运动类": [],
        "运动比赛欣赏类": [],
        "极限运动类": [],
        "养生锻炼身体类": [],
        "饲养宠物类": [],
        "家常菜烹饪类": [],
        "烘焙类": [],
        "美食探店类": [],
        "线下聚会社交类": [],
        "家装设计类": [],
        "知识学习类": [],
        "收藏鉴赏类": [],
        "体验生活类": []
    },
    "情绪与情感状态标签": {
        "当前情绪状态": [
            {"tag": "平静", "confidence": 0.7, "evidence": "陈述语气，无明显情绪波动"}
        ],
        "情感需求":'''
    
    print("=" * 80)
    print("📄 测试用的不完整JSON:")
    print("=" * 80)
    print(incomplete_json)
    print("=" * 80)
    
    # 创建TagExtractor实例
    extractor = TagExtractor("test_comparison")
    
    # 提取JSON部分
    json_match = re.search(r'\{.*\}', incomplete_json, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        
        print("\n🔍 测试1: 标准JSON解析")
        print("-" * 50)
        try:
            standard_result = json.loads(json_str)
            print("✅ 标准JSON解析成功")
            print(f"📊 提取到 {len(standard_result)} 个分类")
        except json.JSONDecodeError as e:
            print(f"❌ 标准JSON解析失败: {e}")
            print(f"   错误位置: 第{e.lineno}行，第{e.colno}列")
            standard_result = None
        
        print("\n🔧 测试2: 手动JSON解析")
        print("-" * 50)
        manual_result = extractor._parse_incomplete_json(json_str)
        
        if manual_result:
            print("✅ 手动JSON解析成功")
            print(f"📊 提取到 {len(manual_result)} 个分类")
            
            # 详细分析提取结果
            for category, subcategories in manual_result.items():
                print(f"\n📋 {category}:")
                if isinstance(subcategories, dict):
                    for sub_name, tags in subcategories.items():
                        if tags:  # 只显示有标签的子分类
                            print(f"   📂 {sub_name}: {len(tags)} 个标签")
                            for tag in tags:
                                print(f"      ✅ {tag.get('tag', '')} (置信度: {tag.get('confidence', 0)})")
        else:
            print("❌ 手动JSON解析失败")
        
        print("\n📊 解析结果对比:")
        print("-" * 50)
        print(f"标准JSON解析: {'成功' if standard_result else '失败'}")
        print(f"手动JSON解析: {'成功' if manual_result else '失败'}")
        
        if manual_result and not standard_result:
            print("🎯 结论: 手动解析在处理不完整JSON方面更加鲁棒！")
            
            # 统计提取的标签数量
            total_tags = 0
            for category, subcategories in manual_result.items():
                if isinstance(subcategories, dict):
                    for sub_name, tags in subcategories.items():
                        total_tags += len(tags)
            
            print(f"📈 手动解析共提取到 {total_tags} 个有效标签")
        
        print("\n🔍 测试3: 为什么自动解析会失败？")
        print("-" * 50)
        
        # 找到问题所在
        lines = json_str.split('\n')
        for i, line in enumerate(lines, 1):
            if '"情感需求":' in line and not line.strip().endswith('}'):
                print(f"❌ 第{i}行发现问题: {line.strip()}")
                print("   原因: '情感需求'后面缺少值和闭合括号")
                break
        
        print("\n💡 手动解析的优势:")
        print("   1. 容错性强：能处理不完整的JSON结构")
        print("   2. 智能截断：自动识别并处理截断的内容")
        print("   3. 多模式匹配：使用多种正则表达式模式")
        print("   4. 渐进式解析：逐个分类提取，部分失败不影响整体")
        print("   5. 详细日志：提供清晰的解析过程反馈")

if __name__ == "__main__":
    test_json_parsing_comparison()