"""
标签相似性检测器
用于识别和合并语义相似但表述不同的标签
"""

import re
import difflib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SimilarTagGroup:
    """相似标签组"""
    primary_tag: str  # 主要标签（标准表述）
    similar_tags: List[str]  # 相似标签列表
    similarity_score: float  # 相似度分数
    merge_reason: str  # 合并原因


class TagSimilarityDetector:
    """标签相似性检测器"""
    
    def __init__(self):
        # 预定义的标签标准化映射
        self.tag_standardization_map = {
            # 年龄相关 - 移除"或"字眼，使用更明确的标签
            "青少年或年轻成年": "青少年",
            "青少年或年轻成人": "青少年",
            "年轻成年": "年轻成人",
            "青年": "年轻成人",
            "中年": "中年人",
            "老年": "老年人",
            
            # 性别相关
            "男性": "男",
            "女性": "女",
            "男生": "男",
            "女生": "女",
            
            # 兴趣爱好相关
            "看电影": "影视欣赏",
            "看剧": "影视欣赏",
            "追剧": "影视欣赏",
            "踢足球": "足球运动",
            "打篮球": "篮球运动",
            "打网球": "网球运动",
            "听音乐": "音乐欣赏",
            "弹钢琴": "钢琴演奏",
            "弹吉他": "吉他演奏",
            "做饭": "烹饪",
            "做菜": "烹饪",
            "烘焙": "烘焙制作",
            "做蛋糕": "烘焙制作",
            "养宠物": "宠物饲养",
            "养猫": "宠物饲养",
            "养狗": "宠物饲养",
            "社交": "社交活动",
            "聚会": "社交活动",
            "学习": "知识学习",
            "读书": "知识学习",
            "看书": "知识学习",
            "运动": "体育锻炼",
            "健身": "体育锻炼",
            "锻炼": "体育锻炼",
            "收藏": "收藏鉴赏",
            "收集": "收藏鉴赏",
        }
        
        # 标签类别特定的相似性规则
        self.category_similarity_rules = {
            "demographic_info": {
                "age": {
                    "keywords": ["青少年", "年轻", "成年", "成人", "中年", "老年"],
                    "patterns": [
                        (r"青少年.*年轻.*", "青少年"),  # 移除"或"字眼
                        (r"年轻.*成年", "年轻成人"),
                        (r"年轻.*成人", "年轻成人"),
                    ]
                },
                "gender": {
                    "keywords": ["男", "女", "性"],
                    "patterns": [
                        (r"男性?", "男"),
                        (r"女性?", "女"),
                    ]
                }
            },
            "interests_hobbies": {
                "keywords": ["喜欢", "爱好", "兴趣", "爱", "擅长"],
                "patterns": [
                    (r"喜欢.*电影", "影视欣赏"),
                    (r"喜欢.*剧", "影视欣赏"),
                    (r"喜欢.*足球", "足球运动"),
                    (r"喜欢.*篮球", "篮球运动"),
                    (r"喜欢.*音乐", "音乐欣赏"),
                    (r"喜欢.*做饭", "烹饪"),
                    (r"喜欢.*烘焙", "烘焙制作"),
                    (r"喜欢.*宠物", "宠物饲养"),
                    (r"喜欢.*社交", "社交活动"),
                    (r"喜欢.*学习", "知识学习"),
                    (r"喜欢.*运动", "体育锻炼"),
                ]
            }
        }
    
    def detect_similar_tags(self, existing_tags: List[Dict], new_tags: List) -> List[SimilarTagGroup]:
        """检测相似标签组"""
        similar_groups = []
        
        # 将现有标签转换为统一格式以便处理
        existing_tag_infos = []
        for tag in existing_tags:
            # 创建一个简单的对象来模拟TagInfo
            tag_obj = type('TagInfo', (), {
                'name': tag["tag_name"],
                'confidence': tag.get("avg_confidence", 0.5),
                'evidence': tag.get("evidence", ""),
                'category': tag.get("category", ""),
                'subcategory': tag.get("subcategory", "")
            })()
            existing_tag_infos.append(tag_obj)
        
        # 合并所有标签
        all_tags = existing_tag_infos + new_tags
        
        # 按类别分组处理
        tags_by_category = self._group_tags_by_category(all_tags)
        
        for category, category_tags in tags_by_category.items():
            # 检测每个类别内的相似标签
            category_groups = self._detect_category_similarity(category, category_tags)
            similar_groups.extend(category_groups)
        
        return similar_groups
    
    def _group_tags_by_category(self, tags: List) -> Dict[str, List]:
        """按类别分组标签"""
        grouped = {}
        for tag in tags:
            category = tag.category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(tag)
        return grouped
    
    def _detect_category_similarity(self, category: str, tags: List) -> List[SimilarTagGroup]:
        """检测特定类别内的相似标签"""
        similar_groups = []
        
        # 获取类别特定的相似性规则
        category_rules = self.category_similarity_rules.get(category, {})
        
        # 标准化标签名称
        standardized_tags = []
        for tag in tags:
            standardized_name = self._standardize_tag_name(tag.name, category_rules)
            standardized_tags.append((tag, standardized_name))
        
        # 按标准化名称分组
        groups = {}
        for tag, std_name in standardized_tags:
            if std_name not in groups:
                groups[std_name] = []
            groups[std_name].append(tag)
        
        # 创建相似标签组
        for std_name, tag_list in groups.items():
            if len(tag_list) > 1:  # 有多个相似标签
                # 选择置信度最高的作为主要标签
                primary_tag = max(tag_list, key=lambda t: t.confidence)
                
                similar_names = [tag.name for tag in tag_list if tag.name != primary_tag.name]
                
                if similar_names:  # 有需要合并的标签
                    group = SimilarTagGroup(
                        primary_tag=primary_tag.name,
                        similar_tags=similar_names,
                        similarity_score=0.9,  # 标准化后的标签相似度很高
                        merge_reason=f"标准化合并: {', '.join(similar_names)} -> {primary_tag.name}"
                    )
                    similar_groups.append(group)
        
        # 使用模糊匹配检测其他相似标签
        fuzzy_groups = self._detect_fuzzy_similarity(tags)
        similar_groups.extend(fuzzy_groups)
        
        return similar_groups
    
    def _standardize_tag_name(self, tag_name: str, category_rules: Dict) -> str:
        """标准化标签名称"""
        # 首先检查预定义映射
        if tag_name in self.tag_standardization_map:
            return self.tag_standardization_map[tag_name]
        
        # 应用类别特定的模式匹配
        patterns = category_rules.get("patterns", [])
        for pattern, replacement in patterns:
            if re.search(pattern, tag_name):
                return replacement
        
        # 如果没有匹配的规则，返回原名称
        return tag_name
    
    def _detect_fuzzy_similarity(self, tags: List) -> List[SimilarTagGroup]:
        """使用模糊匹配检测相似标签"""
        similar_groups = []
        
        # 计算所有标签对之间的相似度
        for i, tag1 in enumerate(tags):
            for j, tag2 in enumerate(tags[i+1:], i+1):
                similarity = self._calculate_similarity(tag1.name, tag2.name)
                
                if similarity >= 0.8:  # 相似度阈值
                    # 选择置信度更高的作为主要标签
                    if tag1.confidence >= tag2.confidence:
                        primary_tag = tag1
                        similar_tag = tag2
                    else:
                        primary_tag = tag2
                        similar_tag = tag1
                    
                    group = SimilarTagGroup(
                        primary_tag=primary_tag.name,
                        similar_tags=[similar_tag.name],
                        similarity_score=similarity,
                        merge_reason=f"模糊匹配相似度: {similarity:.2f}"
                    )
                    similar_groups.append(group)
        
        return similar_groups
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """计算两个标签名称的相似度"""
        # 使用difflib计算序列相似度
        sequence_similarity = difflib.SequenceMatcher(None, name1, name2).ratio()
        
        # 计算词汇重叠度
        words1 = set(name1.replace("或", "").replace("与", "").split())
        words2 = set(name2.replace("或", "").replace("与", "").split())
        
        if not words1 or not words2:
            word_overlap = 0.0
        else:
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            word_overlap = len(intersection) / len(union)
        
        # 综合相似度（序列相似度和词汇重叠度的加权平均）
        combined_similarity = 0.6 * sequence_similarity + 0.4 * word_overlap
        
        return combined_similarity
    
    def merge_similar_tags(self, existing_tags: List[Dict], new_tags: List) -> Tuple[List[Dict], List]:
        """合并相似标签"""
        # 检测相似标签组
        similar_groups = self.detect_similar_tags(existing_tags, new_tags)
        
        if not similar_groups:
            return existing_tags, new_tags
        
        # 创建标签名称到标准化名称的映射
        name_mapping = {}
        for group in similar_groups:
            for similar_name in group.similar_tags:
                name_mapping[similar_name] = group.primary_tag
        
        # 更新现有标签
        updated_existing_tags = []
        for tag in existing_tags:
            if tag["tag_name"] in name_mapping:
                # 更新标签名称
                tag["tag_name"] = name_mapping[tag["tag_name"]]
                tag["merge_info"] = {
                    "original_name": tag["tag_name"],
                    "merged_to": name_mapping[tag["tag_name"]],
                    "merge_reason": "相似标签合并"
                }
            updated_existing_tags.append(tag)
        
        # 更新新标签
        updated_new_tags = []
        for tag in new_tags:
            if tag.name in name_mapping:
                # 更新标签名称
                tag.name = name_mapping[tag.name]
                # 可以在这里添加合并信息
            updated_new_tags.append(tag)
        
        return updated_existing_tags, updated_new_tags
    
    def get_merge_suggestions(self, existing_tags: List[Dict], new_tags: List) -> List[Dict]:
        """获取合并建议"""
        similar_groups = self.detect_similar_tags(existing_tags, new_tags)
        
        suggestions = []
        for group in similar_groups:
            suggestion = {
                "primary_tag": group.primary_tag,
                "similar_tags": group.similar_tags,
                "similarity_score": group.similarity_score,
                "merge_reason": group.merge_reason,
                "action": "merge"
            }
            suggestions.append(suggestion)
        
        return suggestions 