import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.tag_extractor import TagInfo

# 内嵌冲突处理器类
@dataclass
class ConflictResolution:
    """冲突解决方案"""
    action: str
    resolved_tags: List[TagInfo]
    conflict_type: str
    explanation: str
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class TagConflictResolver:
    """标签冲突解决器 - 内嵌版本"""
    
    def __init__(self):
        self.contradictory_pairs = {
            "情感特征": [("乐观", "悲观"), ("积极", "消极"), ("开朗", "内向"), ("自信", "自卑")],
            "兴趣偏好": [("喜欢运动", "反感运动"), ("爱好读书", "讨厌阅读")],
            "互动习惯": [("偏好详细表达", "偏好简短交流"), ("主动交流", "被动回应")],
            "价值观": [("追求自由", "重视稳定"), ("个人主义", "集体主义")]
        }
        
        self.intensity_groups = {
            "情感特征": [["轻微焦虑", "中度焦虑", "重度焦虑"], ["略显内向", "比较内向", "极度内向"]],
            "兴趣偏好": [["一般喜欢", "比较喜欢", "非常喜欢", "狂热爱好"]]
        }
    
    def resolve_conflicts(self, dimension: str, existing_tags: List[Dict], new_tags: List[TagInfo]) -> List[ConflictResolution]:
        """解决标签冲突"""
        resolutions = []
        for new_tag in new_tags:
            # 检查直接矛盾
            contradiction = self._check_contradictory(dimension, existing_tags, new_tag)
            if contradiction:
                resolutions.append(contradiction)
                continue
            
            # 检查时间性变化
            temporal = self._check_temporal_change(existing_tags, new_tag)
            if temporal:
                resolutions.append(temporal)
                continue
        
        return resolutions
    
    def _check_contradictory(self, dimension: str, existing_tags: List[Dict], new_tag: TagInfo) -> Optional[ConflictResolution]:
        """检查矛盾标签"""
        # 🔧 修复维度名称匹配问题
        dimension_key = "情感特征" if "情感" in dimension else "兴趣偏好" if "兴趣" in dimension else "互动习惯" if "互动" in dimension else "价值观" if "价值" in dimension else dimension
        pairs = self.contradictory_pairs.get(dimension_key, [])
        
        for existing_tag in existing_tags:
            existing_name = existing_tag["tag_name"]
            new_name = new_tag.name
            
            for pair in pairs:
                # 🔧 改为包含匹配，不要求精确匹配
                existing_match = any(word in existing_name for word in pair[0].split()) or any(word in existing_name for word in pair[1].split())
                new_match = any(word in new_name for word in pair[0].split()) or any(word in new_name for word in pair[1].split())
                
                # 检查是否为矛盾对：existing在pair[0]，new在pair[1] 或 反之
                is_contradictory = False
                if existing_match and new_match:
                    for word0 in pair[0].split():
                        for word1 in pair[1].split():
                            if (word0 in existing_name and word1 in new_name) or (word1 in existing_name and word0 in new_name):
                                is_contradictory = True
                                break
                        if is_contradictory:
                            break
                
                if is_contradictory:
                    # 🔧 降低置信度阈值要求
                    if new_tag.confidence > existing_tag.get("avg_confidence", 0) + 0.1:
                        return ConflictResolution(
                            action='replace',
                            resolved_tags=[new_tag],
                            conflict_type='contradictory',
                            explanation=f'矛盾标签替换: "{existing_name}" → "{new_name}" (置信度: {existing_tag.get("avg_confidence", 0):.2f} → {new_tag.confidence:.2f})'
                        )
                    else:
                        return ConflictResolution(
                            action='keep_existing',
                            resolved_tags=[],
                            conflict_type='contradictory',
                            explanation=f'检测到矛盾但保留原标签: "{existing_name}" vs "{new_name}" (置信度差异不足)'
                        )
        return None
    
    def _check_temporal_change(self, existing_tags: List[Dict], new_tag: TagInfo) -> Optional[ConflictResolution]:
        """检查时间性变化"""
        for existing_tag in existing_tags:
            last_reinforced = datetime.fromisoformat(existing_tag["last_reinforced"])
            days_since = (datetime.now() - last_reinforced).days
            
            if days_since > 7 and self._is_opposite(existing_tag["tag_name"], new_tag.name):
                old_tag = TagInfo(f"{existing_tag['tag_name']}(历史)", existing_tag.get("avg_confidence", 0), "历史标签", new_tag.category)
                new_temporal = TagInfo(f"{new_tag.name}(当前)", new_tag.confidence, new_tag.evidence, new_tag.category)
                
                return ConflictResolution(
                    action='create_temporal',
                    resolved_tags=[old_tag, new_temporal],
                    conflict_type='temporal_change',
                    explanation=f'时间性变化: "{existing_tag["tag_name"]}" → "{new_tag.name}"'
                )
        return None
    
    def _is_opposite(self, name1: str, name2: str) -> bool:
        """简单的对立判断"""
        opposites = [("喜欢", "反感"), ("积极", "消极"), ("主动", "被动")]
        for pair in opposites:
            if (name1 in pair[0] and name2 in pair[1]) or (name1 in pair[1] and name2 in pair[0]):
                return True
        return False
    
    def apply_resolutions(self, existing_tags: List[Dict], resolutions: List[ConflictResolution]) -> Tuple[List[Dict], List[Dict]]:
        """应用冲突解决方案"""
        updated_tags = existing_tags.copy()
        conflict_records = []
        
        for resolution in resolutions:
            record = {
                "timestamp": resolution.timestamp,
                "conflict_type": resolution.conflict_type,
                "action": resolution.action,
                "explanation": resolution.explanation
            }
            
            if resolution.action == 'replace':
                for i, tag in enumerate(updated_tags):
                    for resolved_tag in resolution.resolved_tags:
                        if self._should_replace(tag, resolved_tag):
                            updated_tags[i] = self._tag_to_dict(resolved_tag)
                            break
            
            elif resolution.action == 'create_temporal':
                for resolved_tag in resolution.resolved_tags:
                    if "历史" in resolved_tag.name:
                        for tag in updated_tags:
                            if tag["tag_name"] == resolved_tag.name.replace("(历史)", ""):
                                tag["tag_name"] = resolved_tag.name
                                tag["is_historical"] = True
                    else:
                        updated_tags.append(self._tag_to_dict(resolved_tag))
            
            conflict_records.append(record)
        
        return updated_tags, conflict_records
    
    def _should_replace(self, existing_tag: Dict, new_tag: TagInfo) -> bool:
        """判断是否应该替换"""
        return existing_tag["tag_name"] in new_tag.name or new_tag.name in existing_tag["tag_name"]
    
    def _tag_to_dict(self, tag_info: TagInfo) -> Dict:
        """TagInfo转字典"""
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

class TagManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.user_data_path = f"user_data/{user_id}"
        self.tags_file = f"{self.user_data_path}/user_tags.json"
        self.timeline_file = f"{self.user_data_path}/tag_timeline.json"
        
        # 🆕 初始化冲突处理器
        self.conflict_resolver = TagConflictResolver()
        
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
                    "stability_score": 0.0,
                    "conflict_history": []
                },
                "interest_preferences": {
                    "dimension_name": "兴趣偏好维度", 
                    "active_tags": [],
                    "dominant_tag": None,
                    "dimension_weight": 0.0,
                    "stability_score": 0.0,
                    "conflict_history": []
                },
                "interaction_habits": {
                    "dimension_name": "互动习惯维度",
                    "active_tags": [],
                    "dominant_tag": None,
                    "dimension_weight": 0.0,
                    "stability_score": 0.0,
                    "conflict_history": []
                },
                "value_principles": {
                    "dimension_name": "价值观维度",
                    "active_tags": [],
                    "dominant_tag": None,
                    "dimension_weight": 0.0,
                    "stability_score": 0.0,
                    "conflict_history": []
                }
            },
            "computed_metrics": {
                "emotional_health_index": 0.5,
                "interest_concentration": 0.0,
                "interaction_dependency": 0.0,
                "overall_profile_maturity": 0.0
            },
            "global_conflict_log": []
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
        """更新单个维度的标签 - 集成冲突处理"""
        active_tags = dimension_data["active_tags"]
        dimension_name = dimension_data.get("dimension_name", "")
        
        # 🆕 第一步：冲突检测和处理
        print(f"🔍 [调试] 检测冲突 - 维度: {dimension_name}, 现有标签: {len(active_tags)}, 新标签: {[tag.name for tag in new_tags]}")
        resolutions = self.conflict_resolver.resolve_conflicts(
            dimension_name, active_tags, new_tags
        )
        print(f"🎯 [调试] 冲突检测结果: {len(resolutions)} 个冲突")
        
        # 🆕 第二步：应用冲突解决方案
        if resolutions:
            updated_tags, conflict_records = self.conflict_resolver.apply_resolutions(
                active_tags, resolutions
            )
            dimension_data["active_tags"] = updated_tags
            
            # 记录冲突历史
            if "conflict_history" not in dimension_data:
                dimension_data["conflict_history"] = []
            dimension_data["conflict_history"].extend(conflict_records)
            
            # 限制冲突历史长度（保留最近50个）
            if len(dimension_data["conflict_history"]) > 50:
                dimension_data["conflict_history"] = dimension_data["conflict_history"][-50:]
            
            # 打印冲突处理日志
            for resolution in resolutions:
                print(f"[冲突处理] {dimension_name}: {resolution.explanation}")
        
        # 🆕 第三步：处理未发生冲突的新标签
        processed_tag_names = set()
        if resolutions:
            for resolution in resolutions:
                for tag in resolution.resolved_tags:
                    processed_tag_names.add(tag.name.split("(")[0].split("[")[0])
        
        for new_tag in new_tags:
            base_name = new_tag.name.split("(")[0].split("[")[0]
            if base_name in processed_tag_names:
                continue  # 已被冲突处理器处理，跳过
            
            # 查找是否已存在相同标签
            existing_tag = None
            for tag in dimension_data["active_tags"]:
                if tag["tag_name"] == new_tag.name:
                    existing_tag = tag
                    break
            
            if existing_tag:
                # 强化已有标签
                existing_tag["evidence_count"] += 1
                existing_tag["last_reinforced"] = datetime.now().isoformat()
                existing_tag["total_confidence"] += new_tag.confidence
                existing_tag["avg_confidence"] = existing_tag["total_confidence"] / existing_tag["evidence_count"]
                
                # 🆕 更新证据信息
                if "evidence" not in existing_tag:
                    existing_tag["evidence"] = new_tag.evidence
                else:
                    existing_tag["evidence"] = f"{existing_tag['evidence']}; {new_tag.evidence}"[:200] + "..."
            else:
                # 添加新标签
                new_tag_data = {
                    "tag_name": new_tag.name,
                    "first_detected": datetime.now().isoformat(),
                    "last_reinforced": datetime.now().isoformat(),
                    "evidence_count": 1,
                    "total_confidence": new_tag.confidence,
                    "avg_confidence": new_tag.confidence,
                    "decay_rate": 0.1,
                    "evidence": new_tag.evidence,
                    "is_historical": False,
                    "is_contextual": "[" in new_tag.name,
                    "conflict_resolved": False
                }
                dimension_data["active_tags"].append(new_tag_data)
        
        # 应用时间衰减
        self._apply_time_decay(dimension_data["active_tags"])
        
        # 限制标签数量（保留权重最高的20个）
        if len(dimension_data["active_tags"]) > 20:
            dimension_data["active_tags"].sort(key=lambda x: x.get("current_weight", x.get("avg_confidence", 0)), reverse=True)
            dimension_data["active_tags"] = dimension_data["active_tags"][:20]
    
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
