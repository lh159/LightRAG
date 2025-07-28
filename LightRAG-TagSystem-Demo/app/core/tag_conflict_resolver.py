# LightRAG-TagSystem-Demo/app/core/tag_conflict_resolver.py

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.tag_extractor import TagInfo

@dataclass
class ConflictResolution:
    """冲突解决方案"""
    action: str  # 'replace', 'merge', 'create_temporal', 'add_context', 'keep_existing'
    resolved_tags: List[TagInfo]
    conflict_type: str
    explanation: str
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class TagConflictResolver:
    """标签冲突解决器"""
    
    def __init__(self):
        # 🎯 1. 直接矛盾 - 相反标签同时出现
        self.contradictory_pairs = {
            "emotional_traits": [
                ("乐观", "悲观"), ("积极", "消极"), ("开朗", "内向"),
                ("自信", "自卑"), ("冷静", "急躁"), ("温和", "暴躁"),
                ("理性", "感性"), ("外向", "内向")
            ],
            "interest_preferences": [
                ("喜欢运动", "反感运动"), ("爱好读书", "讨厌阅读"),
                ("热爱音乐", "不喜欢音乐"), ("喜欢社交", "偏好独处")
            ],
            "interaction_habits": [
                ("偏好详细表达", "偏好简短交流"), ("主动交流", "被动回应"),
                ("直接沟通", "委婉表达"), ("正式语气", "随意语气")
            ],
            "value_principles": [
                ("追求自由", "重视稳定"), ("个人主义", "集体主义"),
                ("冒险精神", "谨慎保守"), ("创新思维", "传统观念")
            ]
        }
        
        # 🎯 3. 程度差异 - 同类标签强度不同
        self.intensity_groups = {
            "emotional_traits": [
                ["轻微焦虑", "中度焦虑", "重度焦虑"],
                ["略显内向", "比较内向", "极度内向"],
                ["有点乐观", "很乐观", "极度乐观"],
                ["轻微敏感", "比较敏感", "高度敏感"]
            ],
            "interest_preferences": [
                ["一般喜欢", "比较喜欢", "非常喜欢", "狂热爱好"],
                ["偶尔关注", "经常关注", "深度关注"]
            ]
        }
        
        # 时间性变化的常见模式
        self.temporal_patterns = [
            ("喜欢", "反感"), ("热爱", "厌倦"), ("积极", "消极"),
            ("主动", "被动"), ("外向", "内向")
        ]
        
    def resolve_conflicts(self, dimension: str, existing_tags: List[Dict], 
                         new_tags: List[TagInfo]) -> List[ConflictResolution]:
        """解决标签冲突主入口"""
        resolutions = []
        
        for new_tag in new_tags:
            # 1️⃣ 直接矛盾处理
            contradictory_resolution = self._resolve_contradictory_tags(
                dimension, existing_tags, new_tag
            )
            if contradictory_resolution:
                resolutions.append(contradictory_resolution)
                continue
            
            # 2️⃣ 时间性变化处理  
            temporal_resolution = self._resolve_temporal_changes(
                dimension, existing_tags, new_tag
            )
            if temporal_resolution:
                resolutions.append(temporal_resolution)
                continue
            
            # 3️⃣ 程度差异处理
            intensity_resolution = self._resolve_intensity_differences(
                dimension, existing_tags, new_tag
            )
            if intensity_resolution:
                resolutions.append(intensity_resolution)
                continue
            
            # 4️⃣ 上下文依赖处理
            context_resolution = self._resolve_context_dependency(
                dimension, existing_tags, new_tag
            )
            if context_resolution:
                resolutions.append(context_resolution)
        
        return resolutions
    
    def _resolve_contradictory_tags(self, dimension: str, existing_tags: List[Dict], 
                                   new_tag: TagInfo) -> Optional[ConflictResolution]:
        """处理直接矛盾的标签"""
        if dimension not in self.contradictory_pairs:
            return None
        
        pairs = self.contradictory_pairs[dimension]
        
        for existing_tag in existing_tags:
            existing_name = existing_tag["tag_name"]
            new_name = new_tag.name
            
            # 检查是否为矛盾对
            for pair in pairs:
                if self._is_contradictory_pair(existing_name, new_name, pair):
                    existing_confidence = existing_tag.get("avg_confidence", 0)
                    new_confidence = new_tag.confidence
                    
                    if new_confidence > existing_confidence + 0.2:
                        # 新标签置信度明显更高，替换
                        resolved_tag = TagInfo(
                            name=new_tag.name,
                            confidence=new_confidence,
                            evidence=new_tag.evidence + f" [替换原标签:{existing_name}]",
                            category=new_tag.category
                        )
                        
                        return ConflictResolution(
                            action='replace',
                            resolved_tags=[resolved_tag],
                            conflict_type='contradictory',
                            explanation=f'新标签"{new_name}"置信度({new_confidence:.2f})高于矛盾标签"{existing_name}"({existing_confidence:.2f})，执行替换'
                        )
                    else:
                        # 保留原有标签
                        return ConflictResolution(
                            action='keep_existing',
                            resolved_tags=[],
                            conflict_type='contradictory',
                            explanation=f'保留原有标签"{existing_name}"，新标签"{new_name}"置信度不足'
                        )
        
        return None
    
    def _resolve_temporal_changes(self, dimension: str, existing_tags: List[Dict], 
                                 new_tag: TagInfo) -> Optional[ConflictResolution]:
        """处理时间性变化"""
        for existing_tag in existing_tags:
            existing_name = existing_tag["tag_name"]
            new_name = new_tag.name
            
            # 检查是否为时间性变化
            if self._is_temporal_variant(existing_name, new_name):
                last_reinforced = datetime.fromisoformat(existing_tag["last_reinforced"])
                days_since = (datetime.now() - last_reinforced).days
                
                if days_since > 7:  # 一周以上的变化认为是时间性变化
                    # 创建时间段标签
                    old_temporal_tag = TagInfo(
                        name=f"{existing_name}(历史)",
                        confidence=existing_tag.get("avg_confidence", 0),
                        evidence=f"历史标签，活跃期至{days_since}天前",
                        category=new_tag.category
                    )
                    
                    new_temporal_tag = TagInfo(
                        name=f"{new_name}(当前)",
                        confidence=new_tag.confidence,
                        evidence=new_tag.evidence + " [时间段标签]",
                        category=new_tag.category
                    )
                    
                    return ConflictResolution(
                        action='create_temporal',
                        resolved_tags=[old_temporal_tag, new_temporal_tag],
                        conflict_type='temporal_change',
                        explanation=f'检测到从"{existing_name}"到"{new_name}"的时间性变化({days_since}天间隔)，创建时间段标签'
                    )
        
        return None
    
    def _resolve_intensity_differences(self, dimension: str, existing_tags: List[Dict], 
                                     new_tag: TagInfo) -> Optional[ConflictResolution]:
        """处理程度差异"""
        if dimension not in self.intensity_groups:
            return None
        
        groups = self.intensity_groups[dimension]
        
        for existing_tag in existing_tags:
            existing_name = existing_tag["tag_name"]
            new_name = new_tag.name
            
            # 检查是否在同一程度组内
            for group in groups:
                if existing_name in group and new_name in group:
                    existing_weight = existing_tag.get("current_weight", existing_tag.get("avg_confidence", 0))
                    new_weight = new_tag.confidence
                    
                    # 权重融合：70%旧 + 30%新
                    merged_weight = 0.7 * existing_weight + 0.3 * new_weight
                    merged_confidence = (existing_tag.get("avg_confidence", 0) + new_tag.confidence) / 2
                    
                    # 选择程度更高的标签名称
                    intensity_levels = {tag: i for i, tag in enumerate(group)}
                    final_name = new_name if intensity_levels.get(new_name, 0) > intensity_levels.get(existing_name, 0) else existing_name
                    
                    merged_tag = TagInfo(
                        name=final_name,
                        confidence=merged_confidence,
                        evidence=f"程度融合: [{existing_name}→{new_name}] " + new_tag.evidence,
                        category=new_tag.category
                    )
                    
                    return ConflictResolution(
                        action='merge',
                        resolved_tags=[merged_tag],
                        conflict_type='intensity_difference',
                        explanation=f'同类标签程度融合: "{existing_name}"({existing_weight:.2f}) + "{new_name}"({new_weight:.2f}) → "{final_name}"({merged_weight:.2f})'
                    )
        
        return None
    
    def _resolve_context_dependency(self, dimension: str, existing_tags: List[Dict], 
                                   new_tag: TagInfo) -> Optional[ConflictResolution]:
        """处理上下文依赖"""
        context_indicators = ["工作", "学习", "家庭", "社交", "娱乐", "运动", "旅行"]
        
        for indicator in context_indicators:
            if indicator in new_tag.evidence.lower():
                contextualized_tag = TagInfo(
                    name=f"{new_tag.name}[{indicator}]",
                    confidence=new_tag.confidence,
                    evidence=new_tag.evidence + f" [上下文:{indicator}]",
                    category=new_tag.category
                )
                
                return ConflictResolution(
                    action='add_context',
                    resolved_tags=[contextualized_tag],
                    conflict_type='context_dependent',
                    explanation=f'为标签"{new_tag.name}"添加"{indicator}"上下文限定'
                )
        
        return None
    
    def _is_contradictory_pair(self, name1: str, name2: str, pair: Tuple[str, str]) -> bool:
        """判断是否为矛盾对"""
        return (name1 in pair[0] and name2 in pair[1]) or (name1 in pair[1] and name2 in pair[0])
    
    def _is_temporal_variant(self, name1: str, name2: str) -> bool:
        """判断是否为时间性变体"""
        for pattern in self.temporal_patterns:
            if self._is_contradictory_pair(name1, name2, pattern):
                return True
        return False
    
    def apply_resolutions(self, existing_tags: List[Dict], 
                         resolutions: List[ConflictResolution]) -> Tuple[List[Dict], List[Dict]]:
        """应用冲突解决方案，返回(更新后的标签, 冲突记录)"""
        updated_tags = existing_tags.copy()
        conflict_records = []
        
        for resolution in resolutions:
            conflict_record = {
                "timestamp": resolution.timestamp,
                "conflict_type": resolution.conflict_type,
                "action": resolution.action,
                "explanation": resolution.explanation,
                "resolved_tags": [tag.name for tag in resolution.resolved_tags]
            }
            
            if resolution.action == 'replace':
                # 替换矛盾标签
                for i, tag in enumerate(updated_tags):
                    for resolved_tag in resolution.resolved_tags:
                        if self._should_replace(tag, resolved_tag):
                            updated_tags[i] = self._tag_info_to_dict(resolved_tag)
                            conflict_record["replaced_tag"] = tag["tag_name"]
                            break
            
            elif resolution.action == 'merge':
                # 移除旧标签，添加融合标签
                for resolved_tag in resolution.resolved_tags:
                    # 移除相关的旧标签
                    updated_tags = [tag for tag in updated_tags 
                                  if not self._is_similar_tag(tag["tag_name"], resolved_tag.name)]
                    # 添加融合后的标签
                    updated_tags.append(self._tag_info_to_dict(resolved_tag))
            
            elif resolution.action == 'create_temporal':
                # 修改原标签为历史标签，添加当前标签
                for resolved_tag in resolution.resolved_tags:
                    if "历史" in resolved_tag.name:
                        # 更新原有标签为历史标签
                        for tag in updated_tags:
                            if self._is_base_tag(tag["tag_name"], resolved_tag.name):
                                tag["tag_name"] = resolved_tag.name
                                tag["is_historical"] = True
                                break
                    else:
                        # 添加当前标签
                        updated_tags.append(self._tag_info_to_dict(resolved_tag))
            
            elif resolution.action == 'add_context':
                # 添加上下文标签
                for resolved_tag in resolution.resolved_tags:
                    updated_tags.append(self._tag_info_to_dict(resolved_tag))
            
            conflict_records.append(conflict_record)
        
        return updated_tags, conflict_records
    
    def _should_replace(self, existing_tag: Dict, new_tag: TagInfo) -> bool:
        """判断是否应该替换标签"""
        existing_base = existing_tag["tag_name"].split("(")[0].split("[")[0]
        new_base = new_tag.name.split("(")[0].split("[")[0]
        return existing_base == new_base or new_base in existing_tag["tag_name"]
    
    def _is_similar_tag(self, tag1: str, tag2: str) -> bool:
        """判断是否为相似标签"""
        base1 = tag1.split("(")[0].split("[")[0]
        base2 = tag2.split("(")[0].split("[")[0]
        return base1 in base2 or base2 in base1
    
    def _is_base_tag(self, tag_name: str, historical_tag_name: str) -> bool:
        """判断是否为基础标签"""
        base_name = historical_tag_name.replace("(历史)", "").strip()
        return tag_name == base_name
    
    def _tag_info_to_dict(self, tag_info: TagInfo) -> Dict:
        """将TagInfo转换为字典格式"""
        return {
            "tag_name": tag_info.name,
            "first_detected": datetime.now().isoformat(),
            "last_reinforced": datetime.now().isoformat(),
            "evidence_count": 1,
            "total_confidence": tag_info.confidence,
            "avg_confidence": tag_info.confidence,
            "decay_rate": 0.1,
            "current_weight": tag_info.confidence,
            "evidence": tag_info.evidence,
            "is_historical": "(历史)" in tag_info.name,
            "is_contextual": "[" in tag_info.name,
            "conflict_resolved": True
        }