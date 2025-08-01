"""
标签触发检测器
基于大模型标签提取结果检测标签的触发和变化
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime

from .tag_extractor import TagInfo
from .tag_tracer import TagTriggerRecord


class TagTriggerDetector:
    """标签触发检测器 - 基于大模型输出进行触发检测"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.confidence_threshold = 0.05  # 置信度变化阈值
        self.new_tag_threshold = 0.3  # 新标签的最低置信度阈值
    
    def detect_triggers(self, 
                       text: str, 
                       old_tags: Dict[str, List[TagInfo]], 
                       new_tags: Dict[str, List[TagInfo]],
                       session_id: str = None,
                       message_id: str = None) -> List[TagTriggerRecord]:
        """
        检测标签触发情况 - 基于大模型的标签提取结果
        
        Args:
            text: 输入文本
            old_tags: 处理前的标签状态
            new_tags: 处理后的标签状态（大模型输出）
            session_id: 会话ID
            message_id: 消息ID
            
        Returns:
            触发记录列表
        """
        triggers = []
        
        # 检测新增标签
        new_tag_triggers = self._detect_new_tags(text, old_tags, new_tags, session_id, message_id)
        triggers.extend(new_tag_triggers)
        
        # 检测置信度变化
        confidence_change_triggers = self._detect_confidence_changes(
            text, old_tags, new_tags, session_id, message_id
        )
        triggers.extend(confidence_change_triggers)
        
        return triggers
    
    def _detect_new_tags(self, 
                        text: str, 
                        old_tags: Dict[str, List[TagInfo]], 
                        new_tags: Dict[str, List[TagInfo]],
                        session_id: str,
                        message_id: str) -> List[TagTriggerRecord]:
        """检测新增标签 - 基于大模型识别的新标签"""
        triggers = []
        
        for category, tag_list in new_tags.items():
            old_tag_names = {tag.name for tag in old_tags.get(category, [])}
            
            for tag in tag_list:
                if tag.name not in old_tag_names and tag.confidence >= self.new_tag_threshold:
                    # 这是一个新标签，且置信度达到阈值
                    evidence = self._extract_evidence(text, tag.name, category, tag)
                    trigger = self._create_trigger_record(
                        tag_name=tag.name,
                        tag_category=category,
                        trigger_text=text,
                        confidence_before=0.0,
                        confidence_after=tag.confidence,
                        evidence=evidence,
                        session_id=session_id,
                        message_id=message_id,
                        action_type="create"
                    )
                    triggers.append(trigger)
        
        return triggers
    
    def _detect_confidence_changes(self, 
                                  text: str, 
                                  old_tags: Dict[str, List[TagInfo]], 
                                  new_tags: Dict[str, List[TagInfo]],
                                  session_id: str,
                                  message_id: str) -> List[TagTriggerRecord]:
        """检测置信度变化 - 基于大模型输出的置信度差异"""
        triggers = []
        
        for category, new_tag_list in new_tags.items():
            old_tag_dict = {tag.name: tag for tag in old_tags.get(category, [])}
            
            for new_tag in new_tag_list:
                old_tag = old_tag_dict.get(new_tag.name)
                
                if old_tag and abs(new_tag.confidence - old_tag.confidence) > self.confidence_threshold:
                    # 置信度发生了显著变化
                    confidence_delta = new_tag.confidence - old_tag.confidence
                    action_type = "strengthen" if confidence_delta > 0 else "weaken"
                    
                    evidence = self._extract_evidence(text, new_tag.name, category, new_tag)
                    trigger = self._create_trigger_record(
                        tag_name=new_tag.name,
                        tag_category=category,
                        trigger_text=text,
                        confidence_before=old_tag.confidence,
                        confidence_after=new_tag.confidence,
                        evidence=evidence,
                        session_id=session_id,
                        message_id=message_id,
                        action_type=action_type
                    )
                    triggers.append(trigger)
        
        return triggers
    
    def _extract_evidence(self, text: str, tag_name: str, category: str, tag_info: TagInfo = None) -> str:
        """从文本中提取支持标签的证据"""
        # 优先使用TagInfo中的evidence字段（大模型提取的证据）
        if tag_info and hasattr(tag_info, 'evidence') and tag_info.evidence:
            return tag_info.evidence
        
        # 如果没有大模型提供的证据，使用整个文本作为证据
        # 但限制长度以避免存储过长的文本
        if len(text) > 150:
            return text[:150] + "..."
        else:
            return text
    
    def _create_trigger_record(self, 
                              tag_name: str,
                              tag_category: str,
                              trigger_text: str,
                              confidence_before: float,
                              confidence_after: float,
                              evidence: str,
                              session_id: str,
                              message_id: str,
                              action_type: str) -> TagTriggerRecord:
        """创建触发记录"""
        from .tag_tracer import TagTriggerRecord
        import uuid
        
        return TagTriggerRecord(
            trigger_id=str(uuid.uuid4()),
            tag_name=tag_name,
            tag_category=tag_category,
            trigger_text=trigger_text,
            trigger_time=datetime.now(),
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            confidence_delta=confidence_after - confidence_before,
            evidence=evidence,
            context={
                "text_length": len(trigger_text),
                "confidence_change_magnitude": abs(confidence_after - confidence_before),
                "is_new_tag": confidence_before == 0.0,
                "llm_based_detection": True  # 标记这是基于大模型的检测
            },
            session_id=session_id or "default",
            message_id=message_id or str(uuid.uuid4()),
            action_type=action_type
        )
    
    def analyze_tag_changes(self, old_tags: Dict[str, List[TagInfo]], new_tags: Dict[str, List[TagInfo]]) -> Dict:
        """分析标签变化的详细信息"""
        analysis = {
            "new_tags": [],
            "strengthened_tags": [],
            "weakened_tags": [],
            "unchanged_tags": [],
            "removed_tags": []
        }
        
        # 获取所有旧标签的映射
        old_tag_map = {}
        for category, tag_list in old_tags.items():
            for tag in tag_list:
                old_tag_map[f"{category}:{tag.name}"] = tag
        
        # 获取所有新标签的映射
        new_tag_map = {}
        for category, tag_list in new_tags.items():
            for tag in tag_list:
                new_tag_map[f"{category}:{tag.name}"] = tag
        
        # 分析变化
        for tag_key, new_tag in new_tag_map.items():
            category, tag_name = tag_key.split(":", 1)
            
            if tag_key not in old_tag_map:
                # 新标签
                analysis["new_tags"].append({
                    "name": tag_name,
                    "category": category,
                    "confidence": new_tag.confidence,
                    "evidence": new_tag.evidence if hasattr(new_tag, 'evidence') else ""
                })
            else:
                # 现有标签
                old_tag = old_tag_map[tag_key]
                confidence_delta = new_tag.confidence - old_tag.confidence
                
                if abs(confidence_delta) > self.confidence_threshold:
                    if confidence_delta > 0:
                        analysis["strengthened_tags"].append({
                            "name": tag_name,
                            "category": category,
                            "old_confidence": old_tag.confidence,
                            "new_confidence": new_tag.confidence,
                            "change": confidence_delta
                        })
                    else:
                        analysis["weakened_tags"].append({
                            "name": tag_name,
                            "category": category,
                            "old_confidence": old_tag.confidence,
                            "new_confidence": new_tag.confidence,
                            "change": confidence_delta
                        })
                else:
                    analysis["unchanged_tags"].append({
                        "name": tag_name,
                        "category": category,
                        "confidence": new_tag.confidence
                    })
        
        # 检查被移除的标签
        for tag_key, old_tag in old_tag_map.items():
            if tag_key not in new_tag_map:
                category, tag_name = tag_key.split(":", 1)
                analysis["removed_tags"].append({
                    "name": tag_name,
                    "category": category,
                    "confidence": old_tag.confidence
                })
        
        return analysis
    
    def get_trigger_summary(self, triggers: List[TagTriggerRecord]) -> Dict:
        """获取触发记录的统计摘要"""
        if not triggers:
            return {
                "total_triggers": 0,
                "new_tags": 0,
                "strengthened_tags": 0,
                "weakened_tags": 0,
                "categories_affected": 0,
                "avg_confidence_change": 0.0
            }
        
        summary = {
            "total_triggers": len(triggers),
            "new_tags": len([t for t in triggers if t.action_type == "create"]),
            "strengthened_tags": len([t for t in triggers if t.action_type == "strengthen"]),
            "weakened_tags": len([t for t in triggers if t.action_type == "weaken"]),
            "categories_affected": len(set(t.tag_category for t in triggers)),
            "avg_confidence_change": sum(abs(t.confidence_delta) for t in triggers) / len(triggers)
        }
        
        return summary
    
    def get_trigger_explanation(self, trigger_record: TagTriggerRecord) -> str:
        """获取触发记录的解释 - 基于大模型输出"""
        explanations = {
            "create": f"大模型识别出新标签 '{trigger_record.tag_name}'，置信度: {trigger_record.confidence_after:.1%}",
            "strengthen": f"大模型判断标签 '{trigger_record.tag_name}' 得到加强，置信度从 {trigger_record.confidence_before:.1%} 提升到 {trigger_record.confidence_after:.1%}",
            "weaken": f"大模型判断标签 '{trigger_record.tag_name}' 有所减弱，置信度从 {trigger_record.confidence_before:.1%} 降低到 {trigger_record.confidence_after:.1%}"
        }
        
        base_explanation = explanations.get(trigger_record.action_type, "标签发生变化")
        
        # 添加证据信息
        if trigger_record.evidence:
            evidence_text = trigger_record.evidence[:50] + "..." if len(trigger_record.evidence) > 50 else trigger_record.evidence
            base_explanation += f"\n支持证据: {evidence_text}"
        
        return base_explanation
    
    def validate_tag_consistency(self, old_tags: Dict[str, List[TagInfo]], new_tags: Dict[str, List[TagInfo]]) -> Dict:
        """验证标签变化的一致性"""
        validation_result = {
            "is_consistent": True,
            "warnings": [],
            "errors": []
        }
        
        # 检查是否有置信度异常变化
        for category, new_tag_list in new_tags.items():
            old_tag_dict = {tag.name: tag for tag in old_tags.get(category, [])}
            
            for new_tag in new_tag_list:
                old_tag = old_tag_dict.get(new_tag.name)
                
                if old_tag:
                    confidence_delta = abs(new_tag.confidence - old_tag.confidence)
                    
                    # 检查是否有异常大的置信度变化
                    if confidence_delta > 0.5:
                        validation_result["warnings"].append(
                            f"标签 '{new_tag.name}' 的置信度变化过大: {confidence_delta:.2f}"
                        )
                    
                    # 检查置信度是否在合理范围内
                    if new_tag.confidence < 0 or new_tag.confidence > 1:
                        validation_result["errors"].append(
                            f"标签 '{new_tag.name}' 的置信度超出范围: {new_tag.confidence}"
                        )
                        validation_result["is_consistent"] = False
        
        return validation_result