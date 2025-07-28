import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.tag_extractor import TagInfo

class TagManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.user_data_path = f"user_data/{user_id}"
        self.tags_file = f"{self.user_data_path}/user_tags.json"
        self.timeline_file = f"{self.user_data_path}/tag_timeline.json"
        
        # 确保文件存在
        self._ensure_tag_files()
        
    def _ensure_tag_files(self):
        """确保标签文件存在"""
        os.makedirs(self.user_data_path, exist_ok=True)
        if not os.path.exists(self.tags_file):
            self._create_empty_tags_file()
        if not os.path.exists(self.timeline_file):
            self._create_empty_timeline_file()
    
    def _create_empty_tags_file(self):
        """创建空的标签文件"""
        empty_tags = {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "tag_dimensions": {
                "emotional_traits": {
                    "dimension_name": "情感特征维度",
                    "active_tags": [],
                    "dominant_tag": None,
                    "dimension_weight": 0.0,
                    "stability_score": 0.0
                },
                "interest_preferences": {
                    "dimension_name": "兴趣偏好维度", 
                    "active_tags": [],
                    "dominant_tag": None,
                    "dimension_weight": 0.0,
                    "stability_score": 0.0
                },
                "interaction_habits": {
                    "dimension_name": "互动习惯维度",
                    "active_tags": [],
                    "dominant_tag": None,
                    "dimension_weight": 0.0,
                    "stability_score": 0.0
                },
                "value_principles": {
                    "dimension_name": "价值观维度",
                    "active_tags": [],
                    "dominant_tag": None,
                    "dimension_weight": 0.0,
                    "stability_score": 0.0
                }
            },
            "computed_metrics": {
                "emotional_health_index": 0.5,
                "interest_concentration": 0.0,
                "interaction_dependency": 0.0,
                "overall_profile_maturity": 0.0
            }
        }
        
        with open(self.tags_file, 'w', encoding='utf-8') as f:
            json.dump(empty_tags, f, ensure_ascii=False, indent=2)
    
    def _create_empty_timeline_file(self):
        """创建空的时间轴文件"""
        empty_timeline = {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "tag_events": []
        }
        
        with open(self.timeline_file, 'w', encoding='utf-8') as f:
            json.dump(empty_timeline, f, ensure_ascii=False, indent=2)
    
    def update_tags(self, extracted_tags: Dict[str, List[TagInfo]]) -> Dict:
        """更新用户标签"""
        # 加载当前标签
        current_tags = self._load_current_tags()
        
        # 更新各维度标签
        for dimension, new_tags in extracted_tags.items():
            if dimension in current_tags["tag_dimensions"]:
                self._update_dimension_tags(
                    current_tags["tag_dimensions"][dimension], 
                    new_tags
                )
        
        # 重新计算权重和指标
        self._recalculate_weights_and_metrics(current_tags)
        
        # 更新时间戳
        current_tags["last_updated"] = datetime.now().isoformat()
        
        # 保存到文件
        self._save_tags(current_tags)
        
        # 记录到时间轴
        self._record_tag_timeline(extracted_tags)
        
        return current_tags
    
    def _load_current_tags(self) -> Dict:
        """加载当前标签"""
        with open(self.tags_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _update_dimension_tags(self, dimension_data: Dict, new_tags: List[TagInfo]):
        """更新单个维度的标签"""
        active_tags = dimension_data["active_tags"]
        
        for new_tag in new_tags:
            # 查找是否已存在相同标签
            existing_tag = None
            for tag in active_tags:
                if tag["tag_name"] == new_tag.name:
                    existing_tag = tag
                    break
            
            if existing_tag:
                # 强化已有标签
                existing_tag["evidence_count"] += 1
                existing_tag["last_reinforced"] = datetime.now().isoformat()
                existing_tag["total_confidence"] += new_tag.confidence
                existing_tag["avg_confidence"] = existing_tag["total_confidence"] / existing_tag["evidence_count"]
            else:
                # 添加新标签
                new_tag_data = {
                    "tag_name": new_tag.name,
                    "first_detected": datetime.now().isoformat(),
                    "last_reinforced": datetime.now().isoformat(),
                    "evidence_count": 1,
                    "total_confidence": new_tag.confidence,
                    "avg_confidence": new_tag.confidence,
                    "decay_rate": 0.1
                }
                active_tags.append(new_tag_data)
        
        # 应用时间衰减
        self._apply_time_decay(active_tags)
        
        # 限制标签数量（保留权重最高的20个）
        if len(active_tags) > 20:
            active_tags.sort(key=lambda x: x["avg_confidence"], reverse=True)
            dimension_data["active_tags"] = active_tags[:20]
    
    def _apply_time_decay(self, active_tags: List[Dict]):
        """应用时间衰减"""
        now = datetime.now()
        
        for tag in active_tags:
            last_reinforced = datetime.fromisoformat(tag["last_reinforced"])
            days_since_reinforced = (now - last_reinforced).days
            
            # 计算衰减因子
            decay_factor = max(0.1, 1.0 - (days_since_reinforced * tag["decay_rate"] / 30))
            tag["current_weight"] = tag["avg_confidence"] * decay_factor
    
    def _recalculate_weights_and_metrics(self, tags_data: Dict):
        """重新计算权重和指标"""
        dimensions = tags_data["tag_dimensions"]
        
        for dimension_key, dimension_data in dimensions.items():
            active_tags = dimension_data["active_tags"]
            
            if active_tags:
                # 找到主导标签（权重最高）
                dominant_tag = max(active_tags, key=lambda x: x.get("current_weight", 0))
                dimension_data["dominant_tag"] = dominant_tag["tag_name"]
                
                # 计算维度权重
                dimension_data["dimension_weight"] = dominant_tag.get("current_weight", 0)
                
                # 计算稳定性评分（基于标签数量和平均置信度）
                avg_confidence = sum(tag.get("avg_confidence", 0) for tag in active_tags) / len(active_tags)
                tag_count_factor = min(1.0, len(active_tags) / 10.0)
                dimension_data["stability_score"] = avg_confidence * tag_count_factor
            else:
                dimension_data["dominant_tag"] = None
                dimension_data["dimension_weight"] = 0.0
                dimension_data["stability_score"] = 0.0
        
        # 计算综合指标
        self._compute_overall_metrics(tags_data)
    
    def _compute_overall_metrics(self, tags_data: Dict):
        """计算综合指标"""
        dimensions = tags_data["tag_dimensions"]
        metrics = tags_data["computed_metrics"]
        
        # 情感健康指数 (基于情感特征维度)
        emotional_dim = dimensions.get("emotional_traits", {})
        emotional_tags = emotional_dim.get("active_tags", [])
        
        positive_weight = 0
        negative_weight = 0
        for tag in emotional_tags:
            tag_name = tag["tag_name"]
            weight = tag.get("current_weight", 0)
            
            if any(word in tag_name for word in ["乐观", "积极", "开朗", "自信"]):
                positive_weight += weight
            elif any(word in tag_name for word in ["焦虑", "消极", "悲观", "敏感"]):
                negative_weight += weight
        
        total_emotional_weight = positive_weight + negative_weight
        if total_emotional_weight > 0:
            metrics["emotional_health_index"] = (positive_weight - negative_weight * 0.5) / total_emotional_weight
        else:
            metrics["emotional_health_index"] = 0.5
        
        # 整体画像成熟度
        total_dimensions = len(dimensions)
        active_dimensions = sum(1 for dim in dimensions.values() if dim["dimension_weight"] > 0.1)
        avg_stability = sum(dim["stability_score"] for dim in dimensions.values()) / total_dimensions if total_dimensions > 0 else 0
        
        metrics["overall_profile_maturity"] = (active_dimensions / total_dimensions) * avg_stability if total_dimensions > 0 else 0
    
    def _save_tags(self, tags_data: Dict):
        """保存标签数据"""
        with open(self.tags_file, 'w', encoding='utf-8') as f:
            json.dump(tags_data, f, ensure_ascii=False, indent=2)
    
    def _record_tag_timeline(self, extracted_tags: Dict[str, List[TagInfo]]):
        """记录标签时间轴"""
        try:
            timeline_data = self._load_timeline()
            
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "tag_extraction",
                "extracted_tags": {}
            }
            
            for dimension, tags in extracted_tags.items():
                event["extracted_tags"][dimension] = [
                    {
                        "tag_name": tag.name,
                        "confidence": tag.confidence,
                        "evidence": tag.evidence
                    }
                    for tag in tags
                ]
            
            timeline_data["tag_events"].append(event)
            
            # 限制时间轴长度（保留最近100个事件）
            if len(timeline_data["tag_events"]) > 100:
                timeline_data["tag_events"] = timeline_data["tag_events"][-100:]
            
            with open(self.timeline_file, 'w', encoding='utf-8') as f:
                json.dump(timeline_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"记录时间轴错误: {e}")
    
    def _load_timeline(self) -> Dict:
        """加载时间轴数据"""
        with open(self.timeline_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_user_tags(self) -> Dict:
        """获取用户标签"""
        return self._load_current_tags()
    
    def get_dimension_weight(self, dimension: str) -> float:
        """获取维度权重"""
        tags_data = self._load_current_tags()
        return tags_data["tag_dimensions"].get(dimension, {}).get("dimension_weight", 0.0)
