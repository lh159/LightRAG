"""
标签溯源追踪器
负责追踪标签的触发、变化和历史记录
"""

import json
import uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import os

from .tag_extractor import TagInfo


@dataclass
class TagTriggerRecord:
    """标签触发记录"""
    trigger_id: str
    tag_name: str
    tag_category: str
    trigger_text: str
    trigger_time: datetime
    confidence_before: float
    confidence_after: float
    confidence_delta: float
    evidence: str
    context: Dict[str, Any]
    session_id: str
    message_id: str
    action_type: str  # 'create', 'strengthen', 'weaken'
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        data = asdict(self)
        data['trigger_time'] = self.trigger_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TagTriggerRecord':
        """从字典创建对象"""
        data['trigger_time'] = datetime.fromisoformat(data['trigger_time'])
        return cls(**data)


@dataclass
class TagHistoryEntry:
    """标签历史记录条目"""
    entry_id: str
    timestamp: datetime
    action: str  # 'create', 'update', 'strengthen', 'weaken'
    confidence: float
    evidence: str
    source_text: str
    context: Dict[str, Any]
    confidence_delta: float = 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TagHistoryEntry':
        """从字典创建对象"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class TagEvidence:
    """标签证据"""
    evidence_id: str
    text: str
    weight: float
    confidence_contribution: float
    timestamp: datetime
    session_id: str
    context: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TagEvidence':
        """从字典创建对象"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class TagTracer:
    """标签溯源追踪器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.user_data_path = f"user_data/{user_id}"
        self.traces_path = f"{self.user_data_path}/tag_traces"
        self.history_path = f"{self.user_data_path}/tag_history"
        self.evidence_path = f"{self.user_data_path}/tag_evidence"
        
        # 确保目录存在
        os.makedirs(self.traces_path, exist_ok=True)
        os.makedirs(self.history_path, exist_ok=True)
        os.makedirs(self.evidence_path, exist_ok=True)
    
    def track_tag_trigger(self, 
                         tag_name: str,
                         tag_category: str,
                         trigger_text: str, 
                         confidence_before: float,
                         confidence_after: float,
                         evidence: str,
                         context: Dict = None,
                         session_id: str = None,
                         message_id: str = None) -> TagTriggerRecord:
        """追踪标签触发"""
        
        trigger_id = str(uuid.uuid4())
        confidence_delta = confidence_after - confidence_before
        
        # 确定动作类型
        if confidence_before == 0:
            action_type = "create"
        elif confidence_delta > 0:
            action_type = "strengthen"
        else:
            action_type = "weaken"
        
        # 创建触发记录
        trigger_record = TagTriggerRecord(
            trigger_id=trigger_id,
            tag_name=tag_name,
            tag_category=tag_category,
            trigger_text=trigger_text,
            trigger_time=datetime.now(),
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            confidence_delta=confidence_delta,
            evidence=evidence,
            context=context or {},
            session_id=session_id or "default",
            message_id=message_id or str(uuid.uuid4()),
            action_type=action_type
        )
        
        # 保存触发记录
        self._save_trigger_record(trigger_record)
        
        # 添加到历史记录
        self._add_history_entry(
            tag_name=tag_name,
            action=action_type,
            confidence=confidence_after,
            evidence=evidence,
            source_text=trigger_text,
            context=context or {},
            confidence_delta=confidence_delta
        )
        
        # 添加证据
        self._add_evidence(
            tag_name=tag_name,
            text=trigger_text,
            weight=abs(confidence_delta),
            confidence_contribution=confidence_delta,
            session_id=session_id or "default",
            context=context or {}
        )
        
        return trigger_record
    
    def get_tag_history(self, tag_name: str) -> List[TagHistoryEntry]:
        """获取标签历史"""
        history_file = f"{self.history_path}/{tag_name}.json"
        
        if not os.path.exists(history_file):
            return []
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [TagHistoryEntry.from_dict(entry) for entry in data]
        except Exception as e:
            print(f"读取标签历史失败: {e}")
            return []
    
    def get_trigger_records(self, tag_name: str = None) -> List[TagTriggerRecord]:
        """获取触发记录"""
        records = []
        
        if tag_name:
            # 获取特定标签的触发记录
            trigger_file = f"{self.traces_path}/{tag_name}_triggers.json"
            if os.path.exists(trigger_file):
                try:
                    with open(trigger_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        records = [TagTriggerRecord.from_dict(record) for record in data]
                except Exception as e:
                    print(f"读取触发记录失败: {e}")
        else:
            # 获取所有触发记录
            for filename in os.listdir(self.traces_path):
                if filename.endswith('_triggers.json'):
                    filepath = os.path.join(self.traces_path, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            records.extend([TagTriggerRecord.from_dict(record) for record in data])
                    except Exception as e:
                        print(f"读取触发记录失败: {e}")
        
        # 按时间排序
        records.sort(key=lambda x: x.trigger_time, reverse=True)
        return records
    
    def get_evidence_chain(self, tag_name: str) -> List[TagEvidence]:
        """获取标签的证据链"""
        evidence_file = f"{self.evidence_path}/{tag_name}_evidence.json"
        
        if not os.path.exists(evidence_file):
            return []
        
        try:
            with open(evidence_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                evidence_list = [TagEvidence.from_dict(evidence) for evidence in data]
                # 按权重排序
                evidence_list.sort(key=lambda x: x.weight, reverse=True)
                return evidence_list
        except Exception as e:
            print(f"读取证据链失败: {e}")
            return []
    
    def get_confidence_timeline(self, tag_name: str) -> List[Dict]:
        """获取置信度时间线"""
        history = self.get_tag_history(tag_name)
        timeline = []
        
        for entry in history:
            timeline.append({
                'timestamp': entry.timestamp.isoformat(),
                'confidence': entry.confidence,
                'action': entry.action,
                'confidence_delta': entry.confidence_delta,
                'evidence': entry.evidence[:100] + '...' if len(entry.evidence) > 100 else entry.evidence
            })
        
        return timeline
    
    def analyze_text_triggers(self, text: str, session_id: str = None) -> Dict[str, List[str]]:
        """分析文本可能触发的标签（预测功能）"""
        # 这里可以实现简单的关键词匹配或使用ML模型预测
        # 暂时返回空字典，可以后续扩展
        return {}
    
    def get_tag_statistics(self, tag_name: str) -> Dict:
        """获取标签统计信息"""
        history = self.get_tag_history(tag_name)
        evidence = self.get_evidence_chain(tag_name)
        triggers = self.get_trigger_records(tag_name)
        
        if not history:
            return {}
        
        # 计算统计信息
        current_confidence = history[0].confidence if history else 0
        creation_time = history[-1].timestamp if history else None
        total_triggers = len(triggers)
        positive_triggers = len([t for t in triggers if t.confidence_delta > 0])
        negative_triggers = len([t for t in triggers if t.confidence_delta < 0])
        
        # 计算平均置信度变化
        avg_positive_delta = sum(t.confidence_delta for t in triggers if t.confidence_delta > 0) / max(positive_triggers, 1)
        avg_negative_delta = sum(t.confidence_delta for t in triggers if t.confidence_delta < 0) / max(negative_triggers, 1)
        
        return {
            'tag_name': tag_name,
            'current_confidence': current_confidence,
            'creation_time': creation_time.isoformat() if creation_time else None,
            'total_triggers': total_triggers,
            'positive_triggers': positive_triggers,
            'negative_triggers': negative_triggers,
            'evidence_count': len(evidence),
            'avg_positive_delta': avg_positive_delta,
            'avg_negative_delta': avg_negative_delta,
            'total_evidence_weight': sum(e.weight for e in evidence)
        }
    
    def _save_trigger_record(self, record: TagTriggerRecord):
        """保存触发记录"""
        trigger_file = f"{self.traces_path}/{record.tag_name}_triggers.json"
        
        # 读取现有记录
        existing_records = []
        if os.path.exists(trigger_file):
            try:
                with open(trigger_file, 'r', encoding='utf-8') as f:
                    existing_records = json.load(f)
            except Exception as e:
                print(f"读取现有触发记录失败: {e}")
        
        # 添加新记录
        existing_records.append(record.to_dict())
        
        # 保持最近的100条记录
        if len(existing_records) > 100:
            existing_records = existing_records[-100:]
        
        # 保存
        try:
            with open(trigger_file, 'w', encoding='utf-8') as f:
                json.dump(existing_records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存触发记录失败: {e}")
    
    def _add_history_entry(self, 
                          tag_name: str,
                          action: str,
                          confidence: float,
                          evidence: str,
                          source_text: str,
                          context: Dict,
                          confidence_delta: float = 0.0):
        """添加历史记录条目"""
        entry = TagHistoryEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            action=action,
            confidence=confidence,
            evidence=evidence,
            source_text=source_text,
            context=context,
            confidence_delta=confidence_delta
        )
        
        history_file = f"{self.history_path}/{tag_name}.json"
        
        # 读取现有历史
        existing_history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    existing_history = json.load(f)
            except Exception as e:
                print(f"读取现有历史失败: {e}")
        
        # 添加新条目（插入到开头，保持时间倒序）
        existing_history.insert(0, entry.to_dict())
        
        # 保持最近的50条记录
        if len(existing_history) > 50:
            existing_history = existing_history[:50]
        
        # 保存
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(existing_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def _add_evidence(self, 
                     tag_name: str,
                     text: str,
                     weight: float,
                     confidence_contribution: float,
                     session_id: str,
                     context: Dict):
        """添加证据"""
        evidence = TagEvidence(
            evidence_id=str(uuid.uuid4()),
            text=text,
            weight=weight,
            confidence_contribution=confidence_contribution,
            timestamp=datetime.now(),
            session_id=session_id,
            context=context
        )
        
        evidence_file = f"{self.evidence_path}/{tag_name}_evidence.json"
        
        # 读取现有证据
        existing_evidence = []
        if os.path.exists(evidence_file):
            try:
                with open(evidence_file, 'r', encoding='utf-8') as f:
                    existing_evidence = json.load(f)
            except Exception as e:
                print(f"读取现有证据失败: {e}")
        
        # 添加新证据
        existing_evidence.append(evidence.to_dict())
        
        # 保持最近的30条证据
        if len(existing_evidence) > 30:
            # 按权重排序，保留权重最高的
            existing_evidence.sort(key=lambda x: x['weight'], reverse=True)
            existing_evidence = existing_evidence[:30]
        
        # 保存
        try:
            with open(evidence_file, 'w', encoding='utf-8') as f:
                json.dump(existing_evidence, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存证据失败: {e}")