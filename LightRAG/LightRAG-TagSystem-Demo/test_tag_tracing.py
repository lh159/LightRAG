#!/usr/bin/env python3
"""
标签溯源功能测试脚本
"""

import sys
import os
sys.path.append('.')

from app.core.enhanced_tag_extractor import EnhancedTagExtractor
from app.core.tag_tracer import TagTracer
from app.core.tag_trigger_detector import TagTriggerDetector
from app.core.tag_manager import TagManager
import json

def test_tag_tracing():
    """测试标签溯源功能"""
    print("🧪 开始测试标签溯源功能...")
    
    # 使用测试用户ID
    user_id = "test_user_001"
    
    # 初始化组件
    enhanced_extractor = EnhancedTagExtractor(user_id)
    tag_tracer = TagTracer(user_id)
    tag_manager = TagManager(user_id)
    
    # 测试对话序列
    test_conversations = [
        "你好！今天心情特别好，刚刚听了一首很棒的音乐。",
        "我特别喜欢跑步，每天早上都会去公园跑步锻炼身体。",
        "工作上遇到了一些困难，感觉有点沮丧，但我相信努力就能解决。",
        "最近在学习新的编程技术，虽然有挑战但很有趣！",
        "和朋友们聊天总是很开心，我比较喜欢和大家分享有趣的事情。"
    ]
    
    print("\n📝 处理测试对话...")
    session_id = "test_session_001"
    
    # 逐条处理对话
    for i, text in enumerate(test_conversations, 1):
        print(f"\n--- 处理第 {i} 条对话 ---")
        print(f"内容: {text}")
        
        # 提取标签并记录溯源
        new_tags, triggers = enhanced_extractor.extract_tags_with_tracing(
            text=text,
            context={"test": True, "conversation_index": i},
            session_id=session_id,
            message_id=f"msg_{i:03d}"
        )
        
        # 更新标签管理器
        tag_manager.update_tags(new_tags)
        
        # 显示触发信息
        if triggers:
            print(f"🏷️  触发了 {len(triggers)} 个标签变化:")
            for trigger in triggers:
                print(f"  • {trigger.tag_name} ({trigger.tag_category}): {trigger.action_type}")
                print(f"    置信度: {trigger.confidence_before:.2f} → {trigger.confidence_after:.2f}")
                print(f"    证据: {trigger.evidence[:50]}...")
        else:
            print("🔍 未检测到标签触发")
    
    print("\n📊 测试溯源查询功能...")
    
    # 获取所有标签
    all_tags = tag_manager.get_user_tags()
    
    if not all_tags:
        print("❌ 没有生成任何标签，测试失败")
        return
    
    # 测试每个标签的溯源信息
    for category, tag_list in all_tags.items():
        print(f"\n--- {category} 类别标签 ---")
        
        for tag in tag_list:
            print(f"\n🔍 标签: {tag.name} (置信度: {tag.confidence:.2f})")
            
            # 获取溯源信息
            trace_info = enhanced_extractor.get_tag_trace_info(tag.name)
            
            # 显示统计信息
            stats = trace_info.get('statistics', {})
            print(f"  📈 统计信息:")
            print(f"    创建时间: {stats.get('creation_time', 'N/A')}")
            print(f"    总触发次数: {stats.get('total_triggers', 0)}")
            print(f"    正向触发: {stats.get('positive_triggers', 0)}")
            print(f"    负向触发: {stats.get('negative_triggers', 0)}")
            print(f"    证据数量: {stats.get('evidence_count', 0)}")
            
            # 显示证据链
            evidence_chain = trace_info.get('evidence_chain', [])
            if evidence_chain:
                print(f"  📝 主要证据:")
                for evidence in evidence_chain[:3]:  # 显示前3条
                    print(f"    • 权重: {evidence['weight']:.2f} | {evidence['text'][:40]}...")
            
            # 显示历史记录
            history = trace_info.get('history', [])
            if history:
                print(f"  📚 最近变化:")
                for entry in history[:3]:  # 显示最近3条
                    print(f"    • {entry['action']} | 置信度: {entry['confidence']:.2f}")
    
    print("\n🎯 测试会话总结功能...")
    
    # 获取会话总结
    session_summary = enhanced_extractor.get_conversation_tag_summary(session_id)
    
    print(f"📋 会话 {session_id} 总结:")
    print(f"  新增标签: {session_summary['summary']['total_new_tags']}")
    print(f"  标签更新: {session_summary['summary']['total_updates']}")
    print(f"  总触发次数: {session_summary['summary']['total_triggers']}")
    print(f"  影响类别: {session_summary['summary']['categories_affected']}")
    
    # 显示标签变化详情
    if session_summary['tag_changes']:
        print(f"\n🏷️  标签变化详情:")
        for tag_change in session_summary['tag_changes'][:5]:  # 显示前5个
            print(f"  • {tag_change['tag_name']} ({tag_change['category']})")
            print(f"    总置信度变化: {tag_change['total_confidence_change']:+.2f}")
            print(f"    触发次数: {len(tag_change['triggers'])}")
    
    print("\n📄 测试报告导出功能...")
    
    # 导出第一个标签的报告
    if all_tags:
        first_category = list(all_tags.keys())[0]
        first_tag = all_tags[first_category][0]
        
        try:
            # 导出Markdown报告
            markdown_report = enhanced_extractor.export_tag_trace_report(
                first_tag.name, 
                format='markdown'
            )
            
            # 保存到文件
            report_filename = f"test_report_{first_tag.name}.md"
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(markdown_report)
            
            print(f"✅ 成功导出报告: {report_filename}")
            print(f"   报告长度: {len(markdown_report)} 字符")
            
        except Exception as e:
            print(f"❌ 导出报告失败: {e}")
    
    print("\n🎉 标签溯源功能测试完成！")
    
    # 清理测试数据（可选）
    cleanup = input("\n🧹 是否清理测试数据？(y/n): ")
    if cleanup.lower() == 'y':
        import shutil
        test_data_path = f"user_data/{user_id}"
        if os.path.exists(test_data_path):
            shutil.rmtree(test_data_path)
            print("✅ 测试数据已清理")


def test_trigger_detection():
    """测试标签触发检测功能"""
    print("\n🔍 测试标签触发检测功能...")
    
    user_id = "test_trigger_user"
    detector = TagTriggerDetector(user_id)
    enhanced_extractor = EnhancedTagExtractor(user_id)
    
    # 测试文本
    test_texts = [
        "我今天特别开心，听了很多音乐",
        "工作压力很大，感觉很焦虑", 
        "喜欢跑步和健身，保持身体健康",
        "努力学习新技术，追求进步"
    ]
    
    # 模拟标签变化检测
    old_tags = {}  # 初始没有标签
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 处理文本 {i}: {text}")
        
        # 使用大模型提取标签
        new_tags, triggers = enhanced_extractor.extract_tags_with_tracing(
            text=text,
            session_id="test_detection_session",
            message_id=f"test_msg_{i}"
        )
        
        # 分析标签变化
        if old_tags:
            analysis = detector.analyze_tag_changes(old_tags, new_tags)
            print(f"  📊 变化分析:")
            print(f"    新增标签: {len(analysis['new_tags'])}")
            print(f"    强化标签: {len(analysis['strengthened_tags'])}")
            print(f"    弱化标签: {len(analysis['weakened_tags'])}")
        
        # 获取触发摘要
        if triggers:
            summary = detector.get_trigger_summary(triggers)
            print(f"  🎯 触发摘要:")
            print(f"    总触发数: {summary['total_triggers']}")
            print(f"    新建标签: {summary['new_tags']}")
            print(f"    强化标签: {summary['strengthened_tags']}")
            print(f"    影响类别: {summary['categories_affected']}")
        
        # 更新旧标签状态
        old_tags = new_tags


if __name__ == "__main__":
    print("🚀 标签溯源功能测试程序")
    print("=" * 50)
    
    try:
        # 测试基本溯源功能
        test_tag_tracing()
        
        # 测试触发检测功能
        test_trigger_detection()
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✨ 测试程序结束")