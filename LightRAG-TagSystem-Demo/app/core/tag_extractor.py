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
    category: str

class TagExtractor:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.llm_client = LLMClient()
        self.tag_categories = {
            "emotional_traits": "情感特征",
            "interest_preferences": "兴趣偏好", 
            "interaction_habits": "互动习惯",
            "value_principles": "价值观"
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
        
        请从以下4个维度提取标签（每个维度最多3个标签）：
        1. 情感特征 - 用户的情绪倾向和心理特点
        2. 兴趣偏好 - 用户感兴趣或反感的话题内容
        3. 互动习惯 - 用户的交流风格和回应偏好
        4. 价值观 - 用户的原则立场和底线禁忌
        
        输出JSON格式：
        {{
            "情感特征": [
                {{"tag": "标签名", "confidence": 0.8, "evidence": "支撑证据"}}
            ],
            "兴趣偏好": [...],
            "互动习惯": [...], 
            "价值观": [...]
        }}
        
        注意：
        - confidence范围0.1-1.0，表示该标签的确信度
        - evidence是从原文中提取的支撑该标签的具体句子
        - 如果某个维度没有明显特征，返回空数组
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
            for category_cn, tags in tag_data.items():
                # 转换中文分类名为英文key
                category_en = self._get_category_key(category_cn)
                if category_en:
                    parsed_tags[category_en] = []
                    for tag_info in tags:
                        tag = TagInfo(
                            name=tag_info.get("tag", ""),
                            confidence=tag_info.get("confidence", 0.5),
                            evidence=tag_info.get("evidence", ""),
                            category=category_en
                        )
                        parsed_tags[category_en].append(tag)
            
            return parsed_tags
            
        except Exception as e:
            print(f"解析LLM响应错误: {e}")
            return {}
    
    def _get_category_key(self, category_cn: str) -> str:
        """根据中文分类名获取英文key"""
        for key, value in self.tag_categories.items():
            if value == category_cn:
                return key
        return ""
    
    def _analyze_behavior_patterns(self, text: str) -> Dict[str, List[TagInfo]]:
        """基于规则的行为模式分析"""
        behavior_tags = {}
        
        # 文本长度分析
        if len(text) > 100:
            behavior_tags["interaction_habits"] = [
                TagInfo("偏好详细表达", 0.6, f"文本长度{len(text)}字符", "interaction_habits")
            ]
        elif len(text) < 30:
            behavior_tags["interaction_habits"] = [
                TagInfo("偏好简短交流", 0.6, f"文本长度{len(text)}字符", "interaction_habits")
            ]
        
        # 情感词检测
        positive_words = ["开心", "高兴", "快乐", "满意", "不错", "好的"]
        negative_words = ["难过", "沮丧", "失望", "糟糕", "痛苦", "烦躁"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count and positive_count > 0:
            if "emotional_traits" not in behavior_tags:
                behavior_tags["emotional_traits"] = []
            behavior_tags["emotional_traits"].append(
                TagInfo("情绪偏向积极", 0.7, f"积极词汇{positive_count}个", "emotional_traits")
            )
        elif negative_count > positive_count and negative_count > 0:
            if "emotional_traits" not in behavior_tags:
                behavior_tags["emotional_traits"] = []
            behavior_tags["emotional_traits"].append(
                TagInfo("情绪偏向消极", 0.7, f"消极词汇{negative_count}个", "emotional_traits")
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
