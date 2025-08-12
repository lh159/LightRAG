"""
语义增强版标签提取器
专注于深度语义理解，避免简单关键词匹配的误判
"""

from typing import Dict, List, Optional
import json
import re
from .tag_extractor import TagExtractor, TagInfo
from ..utils.llm_client import LLMClient


class SemanticTagExtractor(TagExtractor):
    """语义增强版标签提取器"""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.llm_client = LLMClient()
    
    def _build_extraction_prompt(self, text: str, context: Dict = None) -> str:
        """构建语义增强版标签提取prompt"""
        context_info = ""
        if context:
            context_info = f"对话上下文: {context.get('previous_messages', '')}\n"
        
        prompt = f"""
你是一个专业的用户画像分析师，需要从用户的对话中精确提取用户自身的标签特征。

{context_info}
用户文本: "{text}"

【核心分析原则】
1. **主体识别**：严格区分"用户自身"与"用户提及的其他人"
2. **语义理解**：深度分析用户的真实意图，不要被表面词汇误导
3. **上下文推理**：结合对话情境进行综合判断
4. **证据充分性**：只有明确证据支撑的标签才能提取

【关键分析要点】

🔍 **性别分析**：
- 重点分析：用户的自我表达方式、语言习惯、关注话题
- ❌ 错误示例：用户说"大叔你好" → 不能推断用户是男性（这是对他人的称呼）
- ✅ 正确示例：用户说"我是个女孩子" → 可以推断用户是女性
- ⚠️ 注意：称呼他人的词汇（大叔、小姐姐、哥哥等）不代表用户自身特征

🔍 **年龄分析**：
- 重点分析：用户的表达成熟度、关注的话题、生活状态
- ❌ 错误示例：用户问"大叔，你多大了" → 不能推断用户年龄
- ✅ 正确示例：用户说"我还在上大学" → 可推断用户较年轻
- ⚠️ 注意：对他人年龄的询问或评价不代表用户自身年龄

🔍 **兴趣爱好分析**：
- 重点分析：用户的主动表达、情感倾向、行为描述
- ❌ 错误示例：用户问"你看过这部电影吗" → 仅表示可能对电影感兴趣，置信度应较低
- ✅ 正确示例：用户说"我最近在追这部剧" → 明确表示对影视的兴趣
- ⚠️ 注意：询问不等于喜好，需要结合语气和频率判断

🔍 **情感状态分析**：
- 重点分析：用户的情绪表达、语气特征、情感需求
- 关注：语气词、标点符号、情感色彩词汇的使用
- 结合：对话的整体氛围和用户的表达意图

【语义理解示例】

示例1：用户说"大叔，你好厉害啊"
❌ 错误分析：用户是男性（因为说了"大叔"）
✅ 正确分析：
- 性别：可能是年轻女性（年轻人对年长男性的称呼习惯）
- 年龄：相对年轻（使用"大叔"称呼暗示存在年龄差）
- 情感：赞赏、崇拜的情绪

示例2：用户说"我是一个程序员"
✅ 正确分析：
- 职业：程序员（直接自述）
- 可能的兴趣：技术、编程相关

示例3：用户说"你看过《流浪地球》吗？"
❌ 错误分析：用户喜欢科幻电影（置信度过高）
✅ 正确分析：
- 可能对科幻电影有一定兴趣（置信度0.3-0.5）
- 需要更多证据确认

【输出格式】
请严格按照以下JSON格式输出，并确保每个标签都有充分的证据支撑：

{{
    "基本人口统计学标签": {{
        "年龄": [
            {{
                "tag": "年龄段标签", 
                "confidence": 0.0-1.0, 
                "evidence": "从原文提取的具体证据",
                "reasoning": "推理过程说明"
            }}
        ],
        "性别": [...],
        "地域": [...]
    }},
    "兴趣爱好标签": {{
        "影视欣赏": [...],
        "音乐": [...],
        "运动": [...],
        "美食": [...],
        "学习": [...],
        "社交": [...],
        "其他": [...]
    }},
    "情绪与情感状态标签": {{
        "当前情绪": [...],
        "情感需求": [...]
    }}
}}

【置信度标准】
- 0.8-1.0：用户明确自述（"我是..."、"我喜欢..."）
- 0.5-0.7：间接表达但证据较强（行为描述、情感表达）
- 0.3-0.4：轻微暗示（询问、关注某话题）
- 0.1-0.2：非常微弱的暗示
- 0.0：无相关证据，不应提取

【重要提醒】
- 宁可漏提取，也不要误提取
- 对于模糊不清的情况，降低置信度或不提取
- 特别注意区分用户自身特征与用户对他人的描述
- 每个标签必须有明确的evidence和reasoning
"""
        
        return prompt
    
    def _parse_llm_response(self, response: str, original_text: str) -> Dict[str, List[TagInfo]]:
        """解析LLM返回的语义标签"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                print(f"⚠️ 语义提取器：未找到JSON格式响应")
                return {}
            
            json_str = json_match.group(0)
            tag_data = json.loads(json_str)
            
            parsed_tags = {}
            
            # 处理基本人口统计学标签
            demographics = tag_data.get("基本人口统计学标签", {})
            if demographics:
                parsed_tags["demographic_info"] = []
                for category, tags in demographics.items():
                    if isinstance(tags, list):
                        for tag_info in tags:
                            if self._validate_semantic_tag(tag_info):
                                # 映射到正确的子分类key
                                subcategory_key = self._map_demographics_subcategory(category)
                                tag = TagInfo(
                                    name=tag_info["tag"],
                                    confidence=tag_info["confidence"],
                                    evidence=tag_info["evidence"],
                                    category="demographic_info",
                                    subcategory=subcategory_key,
                                    reasoning=tag_info.get("reasoning", "")
                                )
                                parsed_tags["demographic_info"].append(tag)
                                print(f"✅ 语义标签: {tag.name} (置信度: {tag.confidence}) - {tag.reasoning}")
            
            # 处理兴趣爱好标签
            interests = tag_data.get("兴趣爱好标签", {})
            if interests:
                parsed_tags["interests_hobbies"] = []
                for category, tags in interests.items():
                    if isinstance(tags, list):
                        for tag_info in tags:
                            if self._validate_semantic_tag(tag_info):
                                # 映射到正确的子分类key
                                subcategory_key = self._map_interests_subcategory(category)
                                tag = TagInfo(
                                    name=tag_info["tag"],
                                    confidence=tag_info["confidence"],
                                    evidence=tag_info["evidence"],
                                    category="interests_hobbies",
                                    subcategory=subcategory_key,
                                    reasoning=tag_info.get("reasoning", "")
                                )
                                parsed_tags["interests_hobbies"].append(tag)
                                print(f"✅ 兴趣标签: {tag.name} (置信度: {tag.confidence}) - {tag.reasoning}")
            
            # 处理情感状态标签
            emotions = tag_data.get("情绪与情感状态标签", {})
            if emotions:
                parsed_tags["emotional_state"] = []
                for category, tags in emotions.items():
                    if isinstance(tags, list):
                        for tag_info in tags:
                            if self._validate_semantic_tag(tag_info):
                                # 映射到正确的子分类key
                                subcategory_key = self._map_emotions_subcategory(category)
                                tag = TagInfo(
                                    name=tag_info["tag"],
                                    confidence=tag_info["confidence"],
                                    evidence=tag_info["evidence"],
                                    category="emotional_state",
                                    subcategory=subcategory_key,
                                    reasoning=tag_info.get("reasoning", "")
                                )
                                parsed_tags["emotional_state"].append(tag)
                                print(f"✅ 情感标签: {tag.name} (置信度: {tag.confidence}) - {tag.reasoning}")
            
            # 确保所有主要分类都存在，即使为空
            if "demographic_info" not in parsed_tags:
                parsed_tags["demographic_info"] = []
            if "interests_hobbies" not in parsed_tags:
                parsed_tags["interests_hobbies"] = []
            if "emotional_state" not in parsed_tags:
                parsed_tags["emotional_state"] = []
                
            return parsed_tags
            
        except Exception as e:
            print(f"❌ 语义标签解析错误: {e}")
            print(f"原始响应: {response}")
            return {}
    
    def _validate_semantic_tag(self, tag_info: dict) -> bool:
        """验证语义标签的有效性"""
        if not isinstance(tag_info, dict):
            return False
        
        # 必须包含的字段
        required_fields = ["tag", "confidence", "evidence"]
        for field in required_fields:
            if field not in tag_info:
                print(f"⚠️ 标签缺少必要字段: {field}")
                return False
        
        # 置信度范围检查
        confidence = tag_info.get("confidence", 0)
        if not (0.0 <= confidence <= 1.0):
            print(f"⚠️ 置信度超出范围: {confidence}")
            return False
        
        # 证据非空检查
        evidence = tag_info.get("evidence", "").strip()
        if not evidence:
            print(f"⚠️ 标签缺少证据: {tag_info.get('tag', 'unknown')}")
            return False
        
        # 低置信度过滤
        if confidence < 0.1:
            print(f"⚠️ 置信度过低，过滤标签: {tag_info.get('tag', 'unknown')} ({confidence})")
            return False
        
        return True
    
    def extract_tags_from_text(self, text: str, context: Dict = None) -> Dict[str, List[TagInfo]]:
        """语义增强版标签提取"""
        print(f"🧠 开始语义标签提取: {text[:50]}...")
        
        try:
            # 构建语义增强prompt
            prompt = self._build_extraction_prompt(text, context)
            
            # 调用LLM进行语义分析
            response = self.llm_client.complete(
                prompt,
                max_tokens=800,  # 增加token数量以支持推理过程
                temperature=0.1  # 降低温度以提高准确性
            )
            
            # 解析语义标签
            semantic_tags = self._parse_llm_response(response, text)
            
            print(f"✅ 语义标签提取完成，共提取 {sum(len(tags) for tags in semantic_tags.values())} 个标签")
            
            return semantic_tags
            
        except Exception as e:
            print(f"❌ 语义标签提取失败: {e}")
            return {}
    
    def _map_demographics_subcategory(self, category_cn: str) -> str:
        """映射人口统计学标签的中文分类到英文key"""
        mapping = {
            "年龄": "age",
            "性别": "gender", 
            "地域": "location"
        }
        return mapping.get(category_cn, "other")
    
    def _map_interests_subcategory(self, category_cn: str) -> str:
        """映射兴趣爱好标签的中文分类到英文key"""
        mapping = {
            "影视欣赏": "film_tv_appreciation",
            "音乐": "music_appreciation",
            "运动": "ball_sports",
            "美食": "cooking",
            "学习": "knowledge_learning",
            "社交": "social_gathering",
            "烹饪/美食制作": "cooking",
            "网络流行文化": "online_culture",
            "关注人际关系": "social_interests",
            "其他": "other"
        }
        return mapping.get(category_cn, "other")
    
    def _map_emotions_subcategory(self, category_cn: str) -> str:
        """映射情感状态标签的中文分类到英文key"""
        mapping = {
            "当前情绪": "current_mood",
            "情感需求": "emotional_needs"
        }
        return mapping.get(category_cn, "current_mood")
