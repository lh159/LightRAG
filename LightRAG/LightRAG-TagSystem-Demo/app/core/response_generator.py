import sys
import os
from datetime import datetime
from typing import Dict, List

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.lightrag_engine import LightRAGEngine
from core.tag_manager import TagManager
from utils.llm_client import LLMClient

class ResponseGenerator:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.lightrag = LightRAGEngine(user_id)
        self.tag_manager = TagManager(user_id)
        self.llm_client = LLMClient()
        
    def generate_response(self, user_query: str, context: Dict = None) -> Dict:
        """生成个性化回应"""
        
        # 1. 获取用户标签
        user_tags = self.tag_manager.get_user_tags()
        
        # 2. 基于标签生成检索策略
        search_strategy = self._generate_search_strategy(user_tags, user_query)
        
        # 3. 使用LightRAG检索相关知识
        relevant_knowledge = self.lightrag.query_knowledge(
            user_query, 
            mode=search_strategy.get("search_mode", "hybrid")
        )
        
        # 4. 构建个性化回应prompt
        personalized_prompt = self._build_response_prompt(
            user_query, 
            relevant_knowledge, 
            user_tags, 
            search_strategy,
            context
        )
        
        # 5. 生成回应 (使用LightRAG引擎)
        response = self.lightrag.generate_response(
            personalized_prompt,
            max_tokens=500
        )
        
        # 6. 后处理和安全检查
        final_response = self._post_process_response(response, search_strategy)
        
        # 7. 提取使用的标签依据
        used_tags = self._extract_used_tags(user_tags, search_strategy, user_query)
        
        return {
            "response": final_response,
            "search_strategy": search_strategy,
            "knowledge_used": relevant_knowledge[:200] + "..." if len(relevant_knowledge) > 200 else relevant_knowledge,
            "user_profile_snapshot": self._get_profile_snapshot(user_tags),
            "used_tags": used_tags  # 新增：使用的标签依据
        }
    
    def _generate_search_strategy(self, user_tags: Dict, query: str) -> Dict:
        """基于用户标签生成检索策略"""
        strategy = {
            "search_mode": "hybrid",
            "response_tone": "warm",
            "response_style": "balanced",
            "content_filters": [],
            "boost_topics": [],
            "avoid_topics": [],
            "emotional_adaptation": "neutral"
        }
        
        dimensions = user_tags.get("tag_dimensions", {})
        
        # 基于情感特征调整
        emotional_dim = dimensions.get("emotional_traits", {})
        if emotional_dim.get("dimension_weight", 0) > 0.5:
            dominant_emotional = emotional_dim.get("dominant_tag", "")
            
            if "敏感" in dominant_emotional or "焦虑" in dominant_emotional:
                strategy["response_tone"] = "gentle"
                strategy["content_filters"].extend(["批评", "否定", "失败"])
                strategy["emotional_adaptation"] = "supportive"
            elif "乐观" in dominant_emotional or "积极" in dominant_emotional:
                strategy["response_tone"] = "upbeat"
                strategy["emotional_adaptation"] = "encouraging"
        
        return strategy
    
    def _extract_used_tags(self, user_tags: Dict, search_strategy: Dict, user_query: str) -> Dict:
        """提取生成回应时使用的标签依据"""
        used_tags = {
            "primary_tags": [],      # 主要影响标签
            "secondary_tags": [],    # 次要影响标签
            "emotional_context": [], # 情感上下文标签
            "interest_context": [],  # 兴趣上下文标签
            "demographic_context": [], # 人口统计上下文标签
            "response_adaptations": [] # 回应适应性调整
        }
        
        dimensions = user_tags.get("tag_dimensions", {})
        
        # 处理情感维度标签
        emotional_dim = dimensions.get("emotional_state", dimensions.get("emotional_traits", {}))
        if emotional_dim:
            self._extract_emotional_tags(emotional_dim, used_tags, search_strategy)
        
        # 处理兴趣维度标签
        interest_dim = dimensions.get("interests_hobbies", dimensions.get("interest_preferences", {}))
        if interest_dim:
            self._extract_interest_tags(interest_dim, used_tags, user_query)
        
        # 处理人口统计标签
        demo_dim = dimensions.get("demographic_info", {})
        if demo_dim:
            self._extract_demographic_tags(demo_dim, used_tags, user_query)
        
        # 基于搜索策略添加适应性说明
        self._add_response_adaptations(search_strategy, used_tags)
        
        return used_tags
    
    def _extract_emotional_tags(self, emotional_dim: Dict, used_tags: Dict, search_strategy: Dict):
        """提取情感相关的使用标签"""
        if emotional_dim.get('subcategories'):
            # 新的二级标签结构
            for sub_key, subcategory_data in emotional_dim['subcategories'].items():
                active_tags = subcategory_data.get("active_tags", [])
                for tag in active_tags:
                    if tag.get("current_weight", 0) > 0.3:
                        tag_info = {
                            "name": tag["tag_name"],
                            "weight": tag.get("current_weight", 0),
                            "category": "情绪与情感状态",
                            "subcategory": subcategory_data.get("subcategory_name", sub_key),
                            "influence": self._get_emotional_influence(tag["tag_name"], search_strategy)
                        }
                        if tag.get("current_weight", 0) > 0.6:
                            used_tags["primary_tags"].append(tag_info)
                        else:
                            used_tags["emotional_context"].append(tag_info)
        elif emotional_dim.get("active_tags"):
            # 兼容旧结构
            for tag in emotional_dim.get("active_tags", []):
                if tag.get("current_weight", 0) > 0.3:
                    tag_info = {
                        "name": tag["tag_name"],
                        "weight": tag.get("current_weight", 0),
                        "category": "情感特征",
                        "influence": self._get_emotional_influence(tag["tag_name"], search_strategy)
                    }
                    if tag.get("current_weight", 0) > 0.6:
                        used_tags["primary_tags"].append(tag_info)
                    else:
                        used_tags["emotional_context"].append(tag_info)
    
    def _extract_interest_tags(self, interest_dim: Dict, used_tags: Dict, user_query: str):
        """提取兴趣相关的使用标签"""
        if interest_dim.get('subcategories'):
            # 新的二级标签结构
            for sub_key, subcategory_data in interest_dim['subcategories'].items():
                active_tags = subcategory_data.get("active_tags", [])
                for tag in active_tags:
                    if tag.get("current_weight", 0) > 0.2 and self._is_relevant_to_query(tag["tag_name"], user_query):
                        tag_info = {
                            "name": tag["tag_name"],
                            "weight": tag.get("current_weight", 0),
                            "category": "兴趣爱好",
                            "subcategory": subcategory_data.get("subcategory_name", sub_key),
                            "relevance": "与用户问题相关"
                        }
                        used_tags["interest_context"].append(tag_info)
        elif interest_dim.get("active_tags"):
            # 兼容旧结构
            for tag in interest_dim.get("active_tags", []):
                if tag.get("current_weight", 0) > 0.2 and self._is_relevant_to_query(tag["tag_name"], user_query):
                    tag_info = {
                        "name": tag["tag_name"],
                        "weight": tag.get("current_weight", 0),
                        "category": "兴趣偏好",
                        "relevance": "与用户问题相关"
                    }
                    used_tags["interest_context"].append(tag_info)
    
    def _extract_demographic_tags(self, demo_dim: Dict, used_tags: Dict, user_query: str):
        """提取人口统计相关的使用标签"""
        if demo_dim.get('subcategories'):
            for sub_key, subcategory_data in demo_dim['subcategories'].items():
                active_tags = subcategory_data.get("active_tags", [])
                for tag in active_tags:
                    if tag.get("current_weight", 0) > 0.4:
                        tag_info = {
                            "name": tag["tag_name"],
                            "weight": tag.get("current_weight", 0),
                            "category": "基本人口统计学",
                            "subcategory": subcategory_data.get("subcategory_name", sub_key),
                            "usage": "影响回应风格"
                        }
                        used_tags["demographic_context"].append(tag_info)
    
    def _get_emotional_influence(self, tag_name: str, search_strategy: Dict) -> str:
        """获取情感标签的影响描述"""
        tone = search_strategy.get("response_tone", "balanced")
        adaptation = search_strategy.get("emotional_adaptation", "neutral")
        
        if "敏感" in tag_name or "焦虑" in tag_name:
            return f"调整为{tone}语调，采用{adaptation}方式回应"
        elif "乐观" in tag_name or "积极" in tag_name:
            return f"采用{tone}语调，{adaptation}用户情绪"
        else:
            return f"影响回应语调为{tone}"
    
    def _is_relevant_to_query(self, tag_name: str, user_query: str) -> bool:
        """判断标签是否与用户问题相关"""
        # 简单的关键词匹配，可以后续优化为更智能的相关性判断
        tag_keywords = tag_name.split()
        query_lower = user_query.lower()
        
        for keyword in tag_keywords:
            if keyword.lower() in query_lower:
                return True
        
        # 检查语义相关性（简化版）
        semantic_relations = {
            "美食": ["吃", "餐", "食物", "料理", "菜"],
            "运动": ["健身", "跑步", "锻炼", "体育"],
            "音乐": ["歌", "音", "乐器", "演唱"],
            "电影": ["影", "片", "电视", "观看"],
            "读书": ["书", "阅读", "文学", "小说"]
        }
        
        for concept, keywords in semantic_relations.items():
            if concept in tag_name:
                for kw in keywords:
                    if kw in query_lower:
                        return True
        
        return False
    
    def _add_response_adaptations(self, search_strategy: Dict, used_tags: Dict):
        """添加回应适应性说明"""
        adaptations = []
        
        tone = search_strategy.get("response_tone", "balanced")
        if tone != "balanced":
            adaptations.append(f"语调调整: {tone}")
        
        style = search_strategy.get("response_style", "balanced")
        if style != "balanced":
            adaptations.append(f"回应风格: {style}")
        
        emotional_adaptation = search_strategy.get("emotional_adaptation", "neutral")
        if emotional_adaptation != "neutral":
            adaptations.append(f"情感适应: {emotional_adaptation}")
        
        content_filters = search_strategy.get("content_filters", [])
        if content_filters:
            adaptations.append(f"内容过滤: 避免{', '.join(content_filters[:3])}")
        
        boost_topics = search_strategy.get("boost_topics", [])
        if boost_topics:
            adaptations.append(f"话题偏好: 倾向{', '.join(boost_topics[:3])}")
        
        used_tags["response_adaptations"] = adaptations
    
    def _build_response_prompt(self, query: str, knowledge: str, user_tags: Dict, 
                             strategy: Dict, context: Dict = None) -> str:
        """构建高度个性化的精准回应prompt"""
        
        # 提取详细的用户特征分析
        detailed_profile = self._extract_detailed_profile_analysis(user_tags)
        
        # 构建上下文信息
        context_section = self._build_context_section(context, query)
        
        # 构建策略指导
        strategy_guidance = self._build_strategy_guidance(strategy, user_tags)
        
        # 构建个性化适配指令
        personalization_instructions = self._build_personalization_instructions(user_tags, query)
        
        # 构建回应质量要求
        quality_requirements = self._build_quality_requirements(strategy, user_tags)
        
        prompt = f"""# 角色定义
你是一位专业的情感陪伴AI助手，具有深度共情能力和个性化交流技能。你的使命是为每位用户提供最贴心、最契合其个性特征的回应。

# 当前交流情境
## 用户提问
"{query}"

{context_section}

## 相关知识库信息
{knowledge if knowledge.strip() else "暂无直接相关的知识库信息，请基于常识和用户特征进行回应。"}

# 用户深度画像分析
{detailed_profile}

# 个性化策略指导
{strategy_guidance}

# 个性化适配要求
{personalization_instructions}

# 回应质量标准
{quality_requirements}

# 输出要求
请严格按照以上分析生成一个高质量的个性化回应：
1. 字数控制在200字之内
2. 必须体现对用户个性特征的深度理解
3. 语言风格要与用户的特征高度匹配
4. 内容要有温度、有深度、有针对性
5. 如果涉及专业话题，要结合用户的认知水平调整表达方式
6. 必须使用中文回复

现在请生成回应："""
        
        return prompt
    
    def _extract_profile_summary(self, user_tags: Dict) -> str:
        """提取用户画像摘要"""
        dimensions = user_tags.get("tag_dimensions", {})
        summary_parts = []
        
        for dim_key, dim_data in dimensions.items():
            if dim_data.get("overall_weight", dim_data.get("dimension_weight", 0)) > 0.3:
                dim_name = dim_data.get("dimension_name", dim_key)
                all_tags = []
                
                # 处理新的二级标签结构
                if dim_data.get('subcategories'):
                    for sub_key, subcategory_data in dim_data['subcategories'].items():
                        active_tags = subcategory_data.get("active_tags", [])
                        all_tags.extend(active_tags)
                elif dim_data.get("active_tags"):
                    # 兼容旧的一级标签结构
                    all_tags = dim_data.get("active_tags", [])
                
                if all_tags:
                    # 显示前3个最重要的标签
                    top_tags = sorted(all_tags, key=lambda x: x.get("current_weight", 0), reverse=True)[:3]
                    tag_names = [tag["tag_name"] for tag in top_tags]
                    summary_parts.append(f"- {dim_name}: {', '.join(tag_names)}")
        
        if summary_parts:
            return "\n".join(summary_parts)
        else:
            return "- 用户画像还在建立中，采用通用温和的回应方式"
    
    def _post_process_response(self, response: str, strategy: Dict) -> str:
        """后处理回应内容"""
        if not response:
            return "抱歉，我现在无法生成回应，请稍后重试。"
            
        # 根据风格调整长度
        if strategy.get("response_style") == "concise":
            # 如果要求简洁，截取前100字
            if len(response) > 100:
                response = response[:97] + "..."
        
        return response.strip()
    
    def _extract_detailed_profile_analysis(self, user_tags: Dict) -> str:
        """提取详细的用户画像分析"""
        dimensions = user_tags.get("tag_dimensions", {})
        analysis_parts = []
        
        # 分析各个维度
        for dim_key, dim_data in dimensions.items():
            if dim_data.get("overall_weight", dim_data.get("dimension_weight", 0)) > 0.1:
                dim_name = dim_data.get("dimension_name", dim_key)
                analysis_parts.append(f"\n## {dim_name}")
                
                # 处理二级标签结构
                if dim_data.get('subcategories'):
                    for sub_key, subcategory_data in dim_data['subcategories'].items():
                        active_tags = subcategory_data.get("active_tags", [])
                        if active_tags:
                            sub_name = subcategory_data.get("subcategory_name", sub_key)
                            analysis_parts.append(f"### {sub_name}")
                            
                            # 按权重排序，显示详细信息
                            sorted_tags = sorted(active_tags, key=lambda x: x.get("current_weight", 0), reverse=True)[:3]
                            for tag in sorted_tags:
                                tag_name = tag.get("tag_name", "")
                                confidence = tag.get("avg_confidence", 0)
                                weight = tag.get("current_weight", 0)
                                evidence = tag.get("evidence", "")[:100]
                                
                                analysis_parts.append(f"- **{tag_name}** (置信度: {confidence:.2f}, 权重: {weight:.2f})")
                                if evidence:
                                    analysis_parts.append(f"  依据: {evidence}...")
                elif dim_data.get("active_tags"):
                    # 兼容旧结构
                    sorted_tags = sorted(dim_data.get("active_tags", []), 
                                       key=lambda x: x.get("current_weight", 0), reverse=True)[:3]
                    for tag in sorted_tags:
                        tag_name = tag.get("tag_name", "")
                        confidence = tag.get("avg_confidence", 0)
                        weight = tag.get("current_weight", 0)
                        analysis_parts.append(f"- **{tag_name}** (置信度: {confidence:.2f}, 权重: {weight:.2f})")
        
        if not analysis_parts:
            return "用户画像数据较少，建议采用通用友好的交流方式，通过对话逐步了解用户特征。"
        
        return "\n".join(analysis_parts)
    
    def _build_context_section(self, context: Dict, query: str) -> str:
        """构建上下文信息段落"""
        if not context:
            return ""
        
        context_parts = []
        
        # 对话历史
        if context.get("conversation_history"):
            recent_messages = context["conversation_history"][-3:]
            context_parts.append("## 近期对话上下文")
            for i, msg in enumerate(recent_messages, 1):
                context_parts.append(f"{i}. {msg}")
        
        # 当前会话信息
        if context.get("session_info"):
            session_info = context["session_info"]
            context_parts.append("## 会话信息")
            if session_info.get("duration"):
                context_parts.append(f"- 对话时长: {session_info['duration']}")
            if session_info.get("message_count"):
                context_parts.append(f"- 消息数量: {session_info['message_count']}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _build_strategy_guidance(self, strategy: Dict, user_tags: Dict) -> str:
        """构建策略指导"""
        guidance_parts = []
        
        # 语气风格指导
        tone = strategy.get('response_tone', 'warm')
        tone_guidance = {
            'warm': '采用温暖亲切的语气，让用户感受到关怀和理解',
            'gentle': '使用轻柔温和的表达，避免任何可能造成压力的词汇',
            'upbeat': '保持积极乐观的语调，传递正能量和鼓励',
            'professional': '采用专业但友好的语气，体现专业性的同时保持亲和力',
            'casual': '使用轻松随意的语气，营造轻松愉快的对话氛围'
        }
        guidance_parts.append(f"**语气风格**: {tone_guidance.get(tone, '采用温和友好的语气')}")
        
        # 回应风格指导
        style = strategy.get('response_style', 'balanced')
        style_guidance = {
            'balanced': '保持内容的平衡性，既有深度又易于理解',
            'concise': '回应简洁明了，直击要点，避免冗长',
            'detailed': '提供详细深入的回应，充分展开话题',
            'supportive': '重点提供支持和鼓励，强化用户的信心'
        }
        guidance_parts.append(f"**回应风格**: {style_guidance.get(style, '采用平衡的回应风格')}")
        
        # 情感适配指导
        emotional = strategy.get('emotional_adaptation', 'neutral')
        emotional_guidance = {
            'neutral': '保持情感中性，根据用户情绪进行自然回应',
            'supportive': '提供情感支持，给予用户鼓励和安慰',
            'encouraging': '积极鼓励用户，激发其正面情绪',
            'empathetic': '深度共情，充分理解并回应用户的情感需求'
        }
        guidance_parts.append(f"**情感适配**: {emotional_guidance.get(emotional, '保持情感适度')}")
        
        # 内容过滤指导
        if strategy.get('content_filters'):
            filters = strategy['content_filters'][:3]
            guidance_parts.append(f"**内容注意**: 避免提及 {', '.join(filters)} 等可能引起用户不适的话题")
        
        # 话题偏好指导
        if strategy.get('boost_topics'):
            topics = strategy['boost_topics'][:3]
            guidance_parts.append(f"**话题偏好**: 可适当引入 {', '.join(topics)} 等用户感兴趣的话题")
        
        return "\n".join(guidance_parts)
    
    def _build_personalization_instructions(self, user_tags: Dict, query: str) -> str:
        """构建个性化适配指令"""
        instructions = []
        dimensions = user_tags.get("tag_dimensions", {})
        
        # 基于兴趣爱好的适配
        interests = dimensions.get("interests_hobbies", {})
        if interests.get("overall_weight", 0) > 0.3:
            instructions.append("**兴趣适配**: 结合用户的兴趣爱好，使用相关的比喻、例子或话题引导")
            
            # 分析具体兴趣类型
            if interests.get('subcategories'):
                active_interests = []
                for sub_key, sub_data in interests['subcategories'].items():
                    if sub_data.get('active_tags'):
                        sub_name = sub_data.get('subcategory_name', sub_key)
                        active_interests.append(sub_name)
                
                if active_interests:
                    instructions.append(f"  - 用户活跃兴趣领域: {', '.join(active_interests[:3])}")
        
        # 基于情感状态的适配
        emotional = dimensions.get("emotional_state", {})
        if emotional.get("overall_weight", 0) > 0.3:
            instructions.append("**情感适配**: 根据用户当前的情感状态调整回应的情感色彩和支持程度")
            
            # 分析具体情感状态
            if emotional.get('subcategories'):
                current_mood = emotional.get('subcategories', {}).get('current_mood', {})
                if current_mood.get('active_tags'):
                    mood_tags = [tag.get('tag_name', '') for tag in current_mood['active_tags'][:2]]
                    instructions.append(f"  - 当前情绪倾向: {', '.join(mood_tags)}")
        
        # 基于人口统计的适配
        demo = dimensions.get("demographic_info", {})
        if demo.get("overall_weight", 0) > 0.3:
            instructions.append("**表达适配**: 根据用户的年龄、背景等特征调整表达方式和用词选择")
        
        # 查询类型适配
        query_lower = query.lower()
        if any(word in query_lower for word in ['怎么', '如何', '怎样']):
            instructions.append("**回应类型**: 用户寻求方法指导，提供具体可行的建议和步骤")
        elif any(word in query_lower for word in ['为什么', '原因', '为何']):
            instructions.append("**回应类型**: 用户寻求原因解释，提供深入的分析和解释")
        elif any(word in query_lower for word in ['感觉', '心情', '情绪']):
            instructions.append("**回应类型**: 用户表达情感，重点提供情感支持和共情")
        
        return "\n".join(instructions) if instructions else "**基础适配**: 采用温和友好的通用交流方式"
    
    def _build_quality_requirements(self, strategy: Dict, user_tags: Dict) -> str:
        """构建回应质量要求"""
        requirements = [
            "**准确性**: 确保信息准确，避免误导用户",
            "**相关性**: 回应内容必须与用户问题高度相关",
            "**个性化**: 体现对用户个人特征的理解和尊重",
            "**情感温度**: 传递温暖和关怀，让用户感受到被理解",
            "**实用性**: 如果涉及建议，确保建议具体可行"
        ]
        
        # 根据用户特征添加特殊要求
        dimensions = user_tags.get("tag_dimensions", {})
        
        # 如果用户有敏感情绪标签
        emotional = dimensions.get("emotional_state", {})
        if emotional.get('subcategories'):
            for sub_data in emotional['subcategories'].values():
                for tag in sub_data.get('active_tags', []):
                    if any(word in tag.get('tag_name', '') for word in ['敏感', '焦虑', '紧张']):
                        requirements.append("**特别注意**: 用词谨慎，避免可能引起情绪波动的表达")
                        break
        
        # 如果用户有学习相关兴趣
        interests = dimensions.get("interests_hobbies", {})
        if interests.get('subcategories', {}).get('knowledge_learning', {}).get('active_tags'):
            requirements.append("**知识性**: 适当提供有价值的知识点，满足用户的学习需求")
        
        return "\n".join(requirements)
    
    def _get_profile_snapshot(self, user_tags: Dict) -> Dict:
        """获取用户画像快照 - 增强版，包含冲突处理信息"""
        metrics = user_tags.get("computed_metrics", {})
        dimensions = user_tags.get("tag_dimensions", {})
        
        snapshot = {
            "emotional_health_index": metrics.get("emotional_health_index", 0.5),
            "profile_maturity": metrics.get("overall_profile_maturity", 0.0),
            "active_dimensions": [],
            "global_conflict_summary": self._get_global_conflict_summary(user_tags)
        }
        
        for dim_key, dim_data in dimensions.items():
            if dim_data.get("overall_weight", dim_data.get("dimension_weight", 0)) > 0.1:
                all_tags = []
                
                # 处理新的二级标签结构
                if dim_data.get('subcategories'):
                    for sub_key, subcategory_data in dim_data['subcategories'].items():
                        active_tags = subcategory_data.get("active_tags", [])
                        all_tags.extend(active_tags)
                elif dim_data.get("active_tags"):
                    # 兼容旧的一级标签结构
                    all_tags = dim_data.get("active_tags", [])
                
                # 获取该维度的前8个最重要标签（增加数量）
                sorted_tags = sorted(all_tags, key=lambda x: x.get("current_weight", 0), reverse=True)[:8]
                
                # 🆕 分类标签：当前标签、历史标签、上下文标签
                current_tags = []
                historical_tags = []
                contextual_tags = []
                
                for tag in sorted_tags:
                    tag_info = {
                        "name": tag["tag_name"],
                        "weight": tag.get("current_weight", 0),
                        "confidence": tag.get("avg_confidence", 0),
                        "evidence_count": tag.get("evidence_count", 0),
                        "first_detected": tag.get("first_detected", ""),
                        "last_reinforced": tag.get("last_reinforced", ""),
                        "evidence": tag.get("evidence", "")[:100] + "..." if len(tag.get("evidence", "")) > 100 else tag.get("evidence", ""),
                        "is_historical": tag.get("is_historical", False),
                        "is_contextual": tag.get("is_contextual", False),
                        "conflict_resolved": tag.get("conflict_resolved", False)
                    }
                    
                    if tag.get("is_historical", False):
                        historical_tags.append(tag_info)
                    elif tag.get("is_contextual", False):
                        contextual_tags.append(tag_info)
                    else:
                        current_tags.append(tag_info)
                
                # 🆕 获取最近的冲突历史
                recent_conflicts = dim_data.get("conflict_history", [])[-3:]
                
                # 🆕 计算标签变化趋势
                tag_trend = self._calculate_tag_trend(all_tags)
                
                snapshot["active_dimensions"].append({
                    "dimension": dim_data.get("dimension_name", dim_key),
                    "dimension_key": dim_key,
                    "dominant_tag": dim_data.get("dominant_tag"),
                    "dimension_weight": dim_data.get("overall_weight", dim_data.get("dimension_weight", 0)),
                    "stability_score": dim_data.get("overall_stability", dim_data.get("stability_score", 0)),
                    
                    # 🆕 增强的标签分类
                    "current_tags": current_tags,
                    "historical_tags": historical_tags,
                    "contextual_tags": contextual_tags,
                    
                    # 🆕 冲突和变化信息
                    "recent_conflicts": recent_conflicts,
                    "tag_trend": tag_trend,
                    "total_tags": len(all_tags),
                    "conflict_count": len(dim_data.get("conflict_history", [])),
                    
                    # 兼容性：保留原有的tags字段
                    "tags": current_tags + contextual_tags
                })
        
        return snapshot
    
    def _get_global_conflict_summary(self, user_tags: Dict) -> Dict:
        """获取全局冲突摘要"""
        all_conflicts = []
        
        # 收集所有维度的冲突
        for dim_data in user_tags.get("tag_dimensions", {}).values():
            all_conflicts.extend(dim_data.get("conflict_history", []))
        
        # 按时间排序，获取最近的冲突
        all_conflicts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        recent_conflicts = all_conflicts[:5]
        
        # 统计冲突类型
        conflict_types = {}
        for conflict in all_conflicts:
            conflict_type = conflict.get("conflict_type", "unknown")
            conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
        
        return {
            "total_conflicts": len(all_conflicts),
            "recent_conflicts": recent_conflicts,
            "conflict_type_stats": conflict_types,
            "last_conflict_time": recent_conflicts[0].get("timestamp", "") if recent_conflicts else ""
        }
    
    def _calculate_tag_trend(self, active_tags: List[Dict]) -> Dict:
        """计算标签变化趋势"""
        if not active_tags:
            return {"trend": "stable", "description": "暂无数据"}
        
        # 计算最近强化的标签数量
        now = datetime.now()
        recent_reinforced = 0
        
        for tag in active_tags:
            try:
                last_reinforced = datetime.fromisoformat(tag.get("last_reinforced", ""))
                days_since = (now - last_reinforced).days
                if days_since <= 7:  # 一周内强化的标签
                    recent_reinforced += 1
            except:
                continue
        
        total_tags = len(active_tags)
        recent_ratio = recent_reinforced / total_tags if total_tags > 0 else 0
        
        if recent_ratio > 0.5:
            return {"trend": "active", "description": f"近期活跃，{recent_reinforced}/{total_tags}个标签被强化"}
        elif recent_ratio > 0.2:
            return {"trend": "moderate", "description": f"适度变化，{recent_reinforced}/{total_tags}个标签被强化"}
        else:
            return {"trend": "stable", "description": f"相对稳定，{recent_reinforced}/{total_tags}个标签被强化"}
