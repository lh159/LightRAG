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
        """构建个性化回应prompt"""
        
        # 提取关键用户特征
        profile_summary = self._extract_profile_summary(user_tags)
        
        prompt = f"""你是一个温暖的情感陪伴助手，请基于以下信息生成个性化回应。

用户问题: "{query}"

相关知识:
{knowledge}

用户特征:
{profile_summary}

回应要求:
- 语气风格: {strategy.get('response_tone', 'warm')}
- 回应风格: {strategy.get('response_style', 'balanced')}  
- 情感适配: {strategy.get('emotional_adaptation', 'neutral')}

请生成一个200字以内的个性化回应，要体现出对用户特征的理解和关怀。使用中文回复。"""
        
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
