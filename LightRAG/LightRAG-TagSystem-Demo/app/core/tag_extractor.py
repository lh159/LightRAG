import json
import re
import sys
import os
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.llm_client import LLMClient

@dataclass
class TagInfo:
    name: str
    confidence: float
    evidence: str
    category: str  # 一级标签类别
    subcategory: str  # 二级标签类别

class TagExtractor:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.llm_client = LLMClient()
        self.tag_categories = {
            "demographic_info": {
                "name": "基本人口统计学标签",
                "subcategories": {
                    "age": "年龄",
                    "gender": "性别", 
                    "location": "地域"
                }
            },
            "interests_hobbies": {
                "name": "兴趣爱好标签",
                "subcategories": {
                    "entertainment": "娱乐爱好",
                    "sports": "运动爱好",
                    "learning_career": "学习与职业相关爱好"
                }
            },
            "emotional_state": {
                "name": "情绪与情感状态标签",
                "subcategories": {
                    "current_mood": "当前情绪状态",
                    "emotional_needs": "情感需求"
                }
            }
        }
        
    def extract_tags_from_text(self, text: str, context: Dict = None) -> Dict[str, List[TagInfo]]:
        """从文本中提取标签"""
        
        # 构建提取prompt
        extraction_prompt = self._build_extraction_prompt(text, context)
        
        # 调用LLM提取
        try:
            llm_response = self.llm_client.complete(
                extraction_prompt, 
                max_tokens=300,
                temperature=0.3
            )
            
            # 解析LLM响应
            extracted_tags = self._parse_llm_response(llm_response, text)
            
            # 添加行为模式分析
            behavior_tags = self._analyze_behavior_patterns(text)
            
            # 融合结果
            final_tags = self._merge_tag_results(extracted_tags, behavior_tags)
            
            return final_tags
            
        except Exception as e:
            print(f"标签提取错误: {e}")
            return {}
    
    def _build_extraction_prompt(self, text: str, context: Dict = None) -> str:
        """构建标签提取的prompt"""
        context_info = ""
        if context:
            context_info = f"对话上下文: {context.get('previous_messages', '')}\n"
        
        prompt = f"""
        你是一个专业的心理分析师，请分析以下用户文本并提取标签。
        
        {context_info}
        用户文本: "{text}"
        
        请从以下3个一级标签维度提取标签，每个一级标签下有对应的二级标签：
        
        1. 基本人口统计学标签
           - 年龄：年龄段特征（如青少年、中年、老年等）
           - 性别：性别相关的语言风格和话题偏好
           - 地域：地区文化、方言、生活习惯特征
        
        2. 兴趣爱好标签
           - 娱乐爱好：电影、音乐、游戏、阅读等娱乐相关
           - 运动爱好：体育运动、健身、户外活动等
           - 学习与职业相关爱好：专业技能、行业知识、学习兴趣等
        
        3. 情绪与情感状态标签
           - 当前情绪状态：高兴、悲伤、愤怒、焦虑等情绪
           - 情感需求：倾诉需求、鼓励支持、陪伴等情感诉求
        
        输出JSON格式：
        {{
            "基本人口统计学标签": {{
                "年龄": [{{"tag": "标签名", "confidence": 0.8, "evidence": "支撑证据"}}],
                "性别": [...],
                "地域": [...]
            }},
            "兴趣爱好标签": {{
                "娱乐爱好": [...],
                "运动爱好": [...],
                "学习与职业相关爱好": [...]
            }},
            "情绪与情感状态标签": {{
                "当前情绪状态": [...],
                "情感需求": [...]
            }}
        }}
        
        注意：
        - confidence范围0.1-1.0，表示该标签的确信度
        - evidence是从原文中提取的支撑该标签的具体句子
        - 如果某个二级标签没有明显特征，返回空数组
        - 每个二级标签最多提取3个标签
        """
        
        return prompt
    
    def _parse_llm_response(self, response: str, original_text: str) -> Dict[str, List[TagInfo]]:
        """解析LLM返回的标签"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return {}
            
            json_str = json_match.group(0)
            tag_data = json.loads(json_str)
            
            parsed_tags = {}
            # 处理新的二级标签结构
            for category_cn, subcategories in tag_data.items():
                # 转换中文分类名为英文key
                category_en = self._get_category_key(category_cn)
                if category_en and isinstance(subcategories, dict):
                    parsed_tags[category_en] = []
                    
                    # 遍历二级标签
                    for subcategory_cn, tags in subcategories.items():
                        # 转换中文二级分类名为英文key
                        subcategory_en = self._get_subcategory_key(category_en, subcategory_cn)
                        if subcategory_en and isinstance(tags, list):
                            for tag_info in tags:
                                tag = TagInfo(
                                    name=tag_info.get("tag", ""),
                                    confidence=tag_info.get("confidence", 0.5),
                                    evidence=tag_info.get("evidence", ""),
                                    category=category_en,
                                    subcategory=subcategory_en
                                )
                                parsed_tags[category_en].append(tag)
            
            return parsed_tags
            
        except Exception as e:
            print(f"解析LLM响应错误: {e}")
            return {}
    
    def _get_category_key(self, category_cn: str) -> str:
        """根据中文分类名获取英文key"""
        for key, value in self.tag_categories.items():
            if value.get("name") == category_cn:
                return key
        return ""
    
    def _get_subcategory_key(self, category_en: str, subcategory_cn: str) -> str:
        """根据中文二级分类名获取英文key"""
        if category_en in self.tag_categories:
            subcategories = self.tag_categories[category_en].get("subcategories", {})
            for key, value in subcategories.items():
                if value == subcategory_cn:
                    return key
        return ""
    
    def _analyze_behavior_patterns(self, text: str) -> Dict[str, List[TagInfo]]:
        """基于规则的行为模式分析"""
        behavior_tags = {}
        
        # 文本长度分析 - 映射到情感需求
        if len(text) > 100:
            behavior_tags["emotional_state"] = [
                TagInfo("偏好详细表达", 0.6, f"文本长度{len(text)}字符", "emotional_state", "emotional_needs")
            ]
        elif len(text) < 30:
            behavior_tags["emotional_state"] = [
                TagInfo("偏好简短交流", 0.6, f"文本长度{len(text)}字符", "emotional_state", "emotional_needs")
            ]
        
        # 情感词检测
        positive_words = ["开心", "高兴", "快乐", "满意", "不错", "好的"]
        negative_words = ["难过", "沮丧", "失望", "糟糕", "痛苦", "烦躁"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count and positive_count > 0:
            if "emotional_state" not in behavior_tags:
                behavior_tags["emotional_state"] = []
            behavior_tags["emotional_state"].append(
                TagInfo("情绪偏向积极", 0.7, f"积极词汇{positive_count}个", "emotional_state", "current_mood")
            )
        elif negative_count > positive_count and negative_count > 0:
            if "emotional_state" not in behavior_tags:
                behavior_tags["emotional_state"] = []
            behavior_tags["emotional_state"].append(
                TagInfo("情绪偏向消极", 0.7, f"消极词汇{negative_count}个", "emotional_state", "current_mood")
            )
        
        return behavior_tags
    
    def _merge_tag_results(self, llm_tags: Dict, behavior_tags: Dict) -> Dict[str, List[TagInfo]]:
        """融合LLM提取和行为分析的结果"""
        merged = llm_tags.copy()
        
        for category, tags in behavior_tags.items():
            if category not in merged:
                merged[category] = []
            
            # 避免重复标签
            existing_names = [tag.name for tag in merged[category]]
            for tag in tags:
                if tag.name not in existing_names:
                    merged[category].append(tag)
        
        return merged
