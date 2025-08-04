#!/usr/bin/env python3
"""
测试增强版个性化Prompt
"""

import sys
import os
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.response_generator import ResponseGenerator
from app.core.tag_manager import TagManager

def test_enhanced_prompt():
    """测试增强版个性化Prompt"""
    print("🚀 测试增强版个性化Prompt...")
    
    user_id = "test_enhanced_prompt"
    
    try:
        # 创建模拟用户数据
        mock_user_tags = {
            "tag_dimensions": {
                "interests_hobbies": {
                    "dimension_name": "兴趣爱好标签",
                    "overall_weight": 0.8,
                    "subcategories": {
                        "film_tv_appreciation": {
                            "subcategory_name": "影视欣赏类",
                            "active_tags": [
                                {
                                    "tag_name": "电影爱好者",
                                    "avg_confidence": 0.9,
                                    "current_weight": 0.85,
                                    "evidence": "我喜欢看电影，你有没有看最近的院线电影",
                                    "first_detected": "2024-01-15",
                                    "last_reinforced": "2024-01-15"
                                }
                            ]
                        },
                        "knowledge_learning": {
                            "subcategory_name": "知识学习类",
                            "active_tags": [
                                {
                                    "tag_name": "技术学习者",
                                    "avg_confidence": 0.7,
                                    "current_weight": 0.6,
                                    "evidence": "想了解AI技术相关内容",
                                    "first_detected": "2024-01-15",
                                    "last_reinforced": "2024-01-15"
                                }
                            ]
                        }
                    }
                },
                "emotional_state": {
                    "dimension_name": "情绪与情感状态标签",
                    "overall_weight": 0.6,
                    "subcategories": {
                        "current_mood": {
                            "subcategory_name": "当前情绪状态",
                            "active_tags": [
                                {
                                    "tag_name": "好奇",
                                    "avg_confidence": 0.8,
                                    "current_weight": 0.7,
                                    "evidence": "对新技术表现出浓厚兴趣",
                                    "first_detected": "2024-01-15",
                                    "last_reinforced": "2024-01-15"
                                }
                            ]
                        }
                    }
                },
                "demographic_info": {
                    "dimension_name": "基本人口统计学标签",
                    "overall_weight": 0.5,
                    "subcategories": {
                        "age": {
                            "subcategory_name": "年龄",
                            "active_tags": [
                                {
                                    "tag_name": "青年",
                                    "avg_confidence": 0.7,
                                    "current_weight": 0.6,
                                    "evidence": "语言表达和兴趣偏好显示为青年群体特征",
                                    "first_detected": "2024-01-15",
                                    "last_reinforced": "2024-01-15"
                                }
                            ]
                        }
                    }
                }
            },
            "computed_metrics": {
                "emotional_health_index": 0.75,
                "overall_profile_maturity": 0.65
            }
        }
        
        # 创建ResponseGenerator实例
        response_generator = ResponseGenerator(user_id)
        
        # 测试查询
        test_query = "请推荐一些好看的科幻电影"
        
        # 模拟知识库内容
        mock_knowledge = """
        科幻电影推荐：
        1. 《星际穿越》- 诺兰执导的硬科幻大作
        2. 《银翼杀手2049》- 视觉效果惊艳的赛博朋克电影
        3. 《降临》- 探讨语言与时间的深度科幻片
        """
        
        # 模拟策略
        mock_strategy = {
            "response_tone": "warm",
            "response_style": "detailed",
            "emotional_adaptation": "encouraging",
            "boost_topics": ["电影", "科技", "学习"]
        }
        
        # 模拟上下文
        mock_context = {
            "conversation_history": [
                "用户: 我最近对科幻题材很感兴趣",
                "助手: 科幻是一个很有趣的领域！",
                "用户: 你觉得哪些科幻电影值得看？"
            ],
            "session_info": {
                "duration": "15分钟",
                "message_count": 8
            }
        }
        
        # 生成增强版prompt
        enhanced_prompt = response_generator._build_response_prompt(
            query=test_query,
            knowledge=mock_knowledge,
            user_tags=mock_user_tags,
            strategy=mock_strategy,
            context=mock_context
        )
        
        print("=" * 80)
        print("🎯 增强版个性化Prompt:")
        print("=" * 80)
        print(enhanced_prompt)
        print("=" * 80)
        
        # 计算prompt长度和结构
        lines = enhanced_prompt.split('\n')
        sections = [line for line in lines if line.startswith('#')]
        
        print(f"\n📊 Prompt统计信息:")
        print(f"- 总长度: {len(enhanced_prompt)} 字符")
        print(f"- 总行数: {len(lines)} 行")
        print(f"- 主要章节: {len(sections)} 个")
        print(f"- 章节列表: {', '.join([s.strip('# ') for s in sections])}")
        
        return enhanced_prompt
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_enhanced_prompt()