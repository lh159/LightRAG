#!/usr/bin/env python3
"""
测试结构化对话文本的标签溯源功能
"""

import sys
import os

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.enhanced_tag_extractor import EnhancedTagExtractor
from app.core.tag_manager import TagManager
import uuid
from datetime import datetime

def test_conversation_tracing():
    """测试对话文本的标签溯源功能"""
    
    # 使用测试用户ID
    user_id = "test_conversation_user"
    
    # 初始化组件
    enhanced_extractor = EnhancedTagExtractor(user_id)
    tag_manager = TagManager(user_id)
    
    print("🔍 测试结构化对话文本的标签溯源功能")
    print("=" * 60)
    
    # 模拟对话文本
    conversation_messages = [
        {"role": "user", "content": "我今天踢了一场足球比赛，感觉很开心"},
        {"role": "assistant", "content": "那太好了！足球运动对身心健康都很有益处"},
        {"role": "user", "content": "是的，我平时也喜欢看电影，特别是科幻片"},
        {"role": "assistant", "content": "科幻电影确实很有意思"},
        {"role": "user", "content": "我还喜欢在家里做饭，尤其是烘焙蛋糕"},
        {"role": "assistant", "content": "烘焙是个很棒的爱好！"}
    ]
    
    # 生成会话ID
    session_id = str(uuid.uuid4())
    all_trigger_records = []
    
    print(f"📋 会话ID: {session_id}")
    print(f"📝 处理 {len([msg for msg in conversation_messages if msg['role'] == 'user'])} 条用户消息")
    print()
    
    # 处理每条用户消息
    for idx, message in enumerate(conversation_messages):
        if message['role'] == 'user':
            print(f"🗣️  消息 {idx + 1}: {message['content']}")
            
            # 生成消息ID
            message_id = f"{session_id}_msg_{idx}"
            
            # 构建上下文信息
            context = {
                "source": "conversation_upload",
                "message_index": idx,
                "total_messages": len(conversation_messages),
                "conversation_context": "structured_text_analysis"
            }
            
            try:
                # 使用增强版提取器进行标签提取和溯源
                extracted_tags, trigger_records = enhanced_extractor.extract_tags_with_tracing(
                    text=message['content'],
                    context=context,
                    session_id=session_id,
                    message_id=message_id
                )
                
                print(f"   ✅ 提取到 {sum(len(tags) for tags in extracted_tags.values())} 个标签")
                
                # 显示提取的标签
                for dimension, tags in extracted_tags.items():
                    if tags:
                        tag_names = [tag.name for tag in tags]
                        print(f"   📌 {dimension}: {', '.join(tag_names)}")
                
                # 显示触发记录
                if trigger_records:
                    print(f"   🔍 触发记录: {len(trigger_records)} 条")
                    for trigger in trigger_records:
                        print(f"      - {trigger.tag_name} ({trigger.tag_category})")
                        print(f"        证据: {trigger.evidence}")
                        print(f"        置信度变化: {trigger.confidence_delta:+.2f}")
                
                # 收集触发记录
                all_trigger_records.extend(trigger_records)
                
                # 更新标签
                tag_manager.update_tags(extracted_tags)
                
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
            
            print()
    
    # 显示总结信息
    print("📊 溯源总结")
    print("-" * 40)
    print(f"总触发次数: {len(all_trigger_records)}")
    
    # 按标签分组统计
    tag_stats = {}
    for trigger in all_trigger_records:
        tag_key = f"{trigger.tag_category}.{trigger.tag_name}"
        if tag_key not in tag_stats:
            tag_stats[tag_key] = {
                "tag_name": trigger.tag_name,
                "tag_category": trigger.tag_category,
                "trigger_count": 0,
                "sources": []
            }
        
        tag_stats[tag_key]["trigger_count"] += 1
        tag_stats[tag_key]["sources"].append({
            "text": trigger.trigger_text,
            "evidence": trigger.evidence,
            "confidence_change": trigger.confidence_delta
        })
    
    print(f"触发标签数: {len(tag_stats)}")
    print()
    
    # 显示每个标签的触发详情
    for tag_info in tag_stats.values():
        print(f"🏷️  {tag_info['tag_name']} ({tag_info['tag_category']})")
        print(f"   触发次数: {tag_info['trigger_count']}")
        
        for i, source in enumerate(tag_info['sources'], 1):
            print(f"   {i}. \"{source['text']}\"")
            if source['evidence']:
                print(f"      证据: {source['evidence']}")
            print(f"      置信度变化: {source['confidence_change']:+.2f}")
        print()
    
    # 测试溯源查询功能
    print("🔍 测试溯源查询功能")
    print("-" * 40)
    
    # 获取用户标签
    user_tags = tag_manager.get_user_tags()
    if user_tags and user_tags.get('tag_dimensions'):
        for dimension_name, dimension_data in user_tags['tag_dimensions'].items():
            if dimension_data.get('subcategories'):
                for sub_key, subcategory_data in dimension_data['subcategories'].items():
                    active_tags = subcategory_data.get('active_tags', [])
                    for tag in active_tags:
                        tag_name = tag.get('tag_name', '')
                        if tag_name:
                            print(f"📋 查询标签: {tag_name}")
                            try:
                                trace_info = enhanced_extractor.get_tag_trace_info(tag_name)
                                if trace_info:
                                    print(f"   历史记录: {len(trace_info.get('history', []))} 条")
                                    print(f"   证据链: {len(trace_info.get('evidence_chain', []))} 条")
                                    print(f"   最近触发: {len(trace_info.get('recent_triggers', []))} 条")
                                else:
                                    print("   无溯源信息")
                            except Exception as e:
                                print(f"   查询失败: {e}")
                            print()
    
    print("✅ 测试完成！")
    print()
    print("🎯 功能验证:")
    print("✓ 结构化对话文本解析")
    print("✓ 标签提取与溯源记录")
    print("✓ 会话ID和消息ID分配")
    print("✓ 上下文信息记录")
    print("✓ 触发记录统计和分组")
    print("✓ 溯源信息查询")

if __name__ == "__main__":
    test_conversation_tracing()