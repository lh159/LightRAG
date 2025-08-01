"""
增强版标签提取器
集成溯源功能的标签提取器
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid

from .tag_extractor import TagExtractor, TagInfo
from .tag_tracer import TagTracer
from .tag_trigger_detector import TagTriggerDetector
from .tag_manager import TagManager


class EnhancedTagExtractor:
    """增强版标签提取器，支持溯源功能"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.base_extractor = TagExtractor(user_id)
        self.tag_tracer = TagTracer(user_id)
        self.trigger_detector = TagTriggerDetector(user_id)
        self.tag_manager = TagManager(user_id)
    
    def extract_tags_with_tracing(self, 
                                 text: str, 
                                 context: Dict = None,
                                 session_id: str = None,
                                 message_id: str = None) -> Tuple[Dict[str, List[TagInfo]], List]:
        """
        提取标签并记录溯源信息
        
        Args:
            text: 输入文本
            context: 上下文信息
            session_id: 会话ID
            message_id: 消息ID
            
        Returns:
            (新标签, 触发记录列表)
        """
        # 获取当前标签状态
        old_tags_raw = self.tag_manager.get_user_tags()
        
        # 转换为触发检测器期望的格式
        old_tags = self._convert_tags_format(old_tags_raw)
        
        # 提取新标签
        new_tags = self.base_extractor.extract_tags_from_text(text, context)
        
        # 检测触发情况
        triggers = self.trigger_detector.detect_triggers(
            text=text,
            old_tags=old_tags,
            new_tags=new_tags,
            session_id=session_id or str(uuid.uuid4()),
            message_id=message_id or str(uuid.uuid4())
        )
        
        # 记录溯源信息
        for trigger in triggers:
            self.tag_tracer.track_tag_trigger(
                tag_name=trigger.tag_name,
                tag_category=trigger.tag_category,
                trigger_text=text,
                confidence_before=trigger.confidence_before,
                confidence_after=trigger.confidence_after,
                evidence=trigger.evidence,
                context=context or {},
                session_id=session_id,
                message_id=message_id
            )
        
        return new_tags, triggers
    
    def _convert_tags_format(self, tags_data) -> Dict[str, List]:
        """将TagManager的完整格式转换为简单的Dict[str, List[TagInfo]]格式"""
        from .tag_extractor import TagInfo
        
        if not tags_data:
            return {}
        
        converted = {}
        
        # 检查是否是TagManager的完整格式
        if isinstance(tags_data, dict) and "tag_dimensions" in tags_data:
            for dimension, dimension_data in tags_data["tag_dimensions"].items():
                active_tags = dimension_data.get("active_tags", [])
                converted[dimension] = []
                
                for tag in active_tags:
                    if isinstance(tag, dict):
                        # 转换字典格式为TagInfo对象
                        tag_info = TagInfo(
                            name=tag.get('name', ''),
                            confidence=tag.get('confidence', 0.0),
                            evidence=tag.get('evidence', ''),
                            category=dimension
                        )
                        converted[dimension].append(tag_info)
                    elif hasattr(tag, 'name'):
                        # 已经是TagInfo对象
                        converted[dimension].append(tag)
        else:
            # 已经是简单格式，直接返回
            converted = tags_data
        
        return converted
    
    def get_tag_trace_info(self, tag_name: str) -> Dict:
        """获取标签的完整溯源信息"""
        # 获取标签历史
        history = self.tag_tracer.get_tag_history(tag_name)
        
        # 获取证据链
        evidence_chain = self.tag_tracer.get_evidence_chain(tag_name)
        
        # 获取置信度时间线
        confidence_timeline = self.tag_tracer.get_confidence_timeline(tag_name)
        
        # 获取统计信息
        statistics = self.tag_tracer.get_tag_statistics(tag_name)
        
        # 获取最近的触发记录
        recent_triggers = self.tag_tracer.get_trigger_records(tag_name)[:10]  # 最近10条
        
        return {
            'tag_name': tag_name,
            'history': [entry.to_dict() for entry in history],
            'evidence_chain': [evidence.to_dict() for evidence in evidence_chain],
            'confidence_timeline': confidence_timeline,
            'statistics': statistics,
            'recent_triggers': [trigger.to_dict() for trigger in recent_triggers]
        }
    
    def analyze_text_impact(self, text: str) -> Dict:
        """分析文本对标签的潜在影响 - 基于大模型的简化版本"""
        # 获取当前标签状态
        current_tags_raw = self.tag_manager.get_user_tags()
        current_tags = self._convert_tags_format(current_tags_raw)
        
        # 使用大模型快速提取可能的标签（不更新状态）
        try:
            potential_new_tags = self.base_extractor.extract_tags_from_text(text, {"preview_mode": True})
        except Exception as e:
            print(f"预测标签时出错: {e}")
            potential_new_tags = {}
        
        # 分析对现有标签的影响
        impact_analysis = {}
        
        for category, tag_list in current_tags.items():
            if not tag_list:
                continue
                
            category_impacts = []
            new_category_tags = potential_new_tags.get(category, [])
            
            for tag in tag_list:
                # 检查是否在新提取的标签中
                matching_new_tag = None
                for new_tag in new_category_tags:
                    if hasattr(new_tag, 'name') and new_tag.name == tag.name:
                        matching_new_tag = new_tag
                        break
                
                if matching_new_tag:
                    # 计算可能的影响
                    predicted_confidence = matching_new_tag.confidence
                    impact = predicted_confidence - tag.confidence
                    
                    if abs(impact) > 0.05:  # 只显示有显著影响的
                        category_impacts.append({
                            'tag_name': tag.name,
                            'current_confidence': tag.confidence,
                            'predicted_confidence': predicted_confidence,
                            'predicted_impact': impact
                        })
            
            if category_impacts:
                impact_analysis[category] = category_impacts
        
        # 检查潜在的新标签
        potential_new_only = {}
        for category, new_tags in potential_new_tags.items():
            existing_names = {tag.name for tag in current_tags.get(category, [])}
            new_only = []
            
            for new_tag in new_tags:
                if hasattr(new_tag, 'name') and new_tag.name not in existing_names:
                    if new_tag.confidence >= 0.3:  # 只显示置信度较高的新标签
                        new_only.append({
                            'name': new_tag.name,
                            'predicted_confidence': new_tag.confidence,
                            'evidence': getattr(new_tag, 'evidence', '')
                        })
            
            if new_only:
                potential_new_only[category] = new_only
        
        return {
            'potential_new_tags': potential_new_only,
            'existing_tag_impacts': impact_analysis,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def get_conversation_tag_summary(self, session_id: str) -> Dict:
        """获取会话的标签变化总结"""
        # 获取该会话的所有触发记录
        all_triggers = self.tag_tracer.get_trigger_records()
        session_triggers = [t for t in all_triggers if t.session_id == session_id]
        
        # 按标签分组
        tag_changes = {}
        for trigger in session_triggers:
            if trigger.tag_name not in tag_changes:
                tag_changes[trigger.tag_name] = {
                    'tag_name': trigger.tag_name,
                    'category': trigger.tag_category,
                    'triggers': [],
                    'total_confidence_change': 0,
                    'creation_time': None,
                    'last_update_time': None
                }
            
            tag_info = tag_changes[trigger.tag_name]
            tag_info['triggers'].append(trigger.to_dict())
            tag_info['total_confidence_change'] += trigger.confidence_delta
            
            if trigger.action_type == 'create':
                tag_info['creation_time'] = trigger.trigger_time.isoformat()
            
            if not tag_info['last_update_time'] or trigger.trigger_time > datetime.fromisoformat(tag_info['last_update_time']):
                tag_info['last_update_time'] = trigger.trigger_time.isoformat()
        
        # 计算统计信息
        total_new_tags = len([t for t in tag_changes.values() if t['creation_time']])
        total_updates = len(session_triggers) - total_new_tags
        
        return {
            'session_id': session_id,
            'tag_changes': list(tag_changes.values()),
            'summary': {
                'total_new_tags': total_new_tags,
                'total_updates': total_updates,
                'total_triggers': len(session_triggers),
                'categories_affected': len(set(t.tag_category for t in session_triggers))
            }
        }
    
    def export_tag_trace_report(self, tag_name: str, format: str = 'json') -> str:
        """导出标签溯源报告"""
        trace_info = self.get_tag_trace_info(tag_name)
        
        if format == 'json':
            import json
            return json.dumps(trace_info, ensure_ascii=False, indent=2)
        
        elif format == 'markdown':
            return self._generate_markdown_report(trace_info)
        
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _generate_markdown_report(self, trace_info: Dict) -> str:
        """生成Markdown格式的溯源报告"""
        tag_name = trace_info['tag_name']
        statistics = trace_info['statistics']
        
        report = f"""# 标签溯源报告：{tag_name}

## 基本信息
- **当前置信度**: {statistics.get('current_confidence', 0):.1%}
- **创建时间**: {statistics.get('creation_time', 'N/A')}
- **总触发次数**: {statistics.get('total_triggers', 0)}
- **正向触发**: {statistics.get('positive_triggers', 0)}
- **负向触发**: {statistics.get('negative_triggers', 0)}
- **证据数量**: {statistics.get('evidence_count', 0)}

## 置信度变化趋势
"""
        
        # 添加置信度时间线
        timeline = trace_info['confidence_timeline']
        if timeline:
            report += "\n| 时间 | 置信度 | 变化 | 动作 |\n|------|--------|------|------|\n"
            for entry in timeline[:10]:  # 显示最近10条
                report += f"| {entry['timestamp'][:19]} | {entry['confidence']:.1%} | {entry['confidence_delta']:+.1%} | {entry['action']} |\n"
        
        # 添加主要证据
        evidence_chain = trace_info['evidence_chain']
        if evidence_chain:
            report += "\n## 主要支持证据\n\n"
            for i, evidence in enumerate(evidence_chain[:5], 1):  # 显示前5条
                report += f"### 证据 {i}\n"
                report += f"- **权重**: {evidence['weight']:.2f}\n"
                report += f"- **贡献度**: {evidence['confidence_contribution']:+.1%}\n"
                report += f"- **时间**: {evidence['timestamp'][:19]}\n"
                report += f"- **内容**: {evidence['text']}\n\n"
        
        return report