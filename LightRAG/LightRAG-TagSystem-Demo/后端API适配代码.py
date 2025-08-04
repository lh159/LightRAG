"""
后端API适配新标签结构的代码修改示例
这些代码需要替换到 web/app.py 中的相应位置
"""

from flask import Flask, request, jsonify, session, redirect, url_for
from core.tag_manager import TagManager
from core.enhanced_tag_extractor import EnhancedTagExtractor
from core.response_generator import ResponseGenerator
import time
import uuid

# ==================== 更新 /api/profile 接口 ====================

@app.route('/api/profile')
@login_required
def get_profile():
    """获取用户画像 - 适配新的二级标签结构"""
    try:
        user_id = request.current_user["user_id"]
        tag_manager = TagManager(str(user_id))
        user_tags = tag_manager.get_user_tags()
        
        # 确保返回新的二级标签结构
        dimensions = user_tags.get('tag_dimensions', {})
        
        # 新的默认维度结构
        default_dimensions = {
            "demographic_info": {
                "dimension_name": "基本人口统计学标签",
                "subcategories": {
                    "age": {
                        "subcategory_name": "年龄",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "gender": {
                        "subcategory_name": "性别",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "location": {
                        "subcategory_name": "地域",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    }
                },
                "overall_weight": 0.0,
                "overall_stability": 0.0
            },
            "interests_hobbies": {
                "dimension_name": "兴趣爱好标签",
                "subcategories": {
                    "entertainment": {
                        "subcategory_name": "娱乐爱好",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "sports": {
                        "subcategory_name": "运动爱好",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "learning_career": {
                        "subcategory_name": "学习与职业相关爱好",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    }
                },
                "overall_weight": 0.0,
                "overall_stability": 0.0
            },
            "emotional_state": {
                "dimension_name": "情绪与情感状态标签",
                "subcategories": {
                    "current_mood": {
                        "subcategory_name": "当前情绪状态",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "emotional_needs": {
                        "subcategory_name": "情感需求",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    }
                },
                "overall_weight": 0.0,
                "overall_stability": 0.0
            }
        }
        
        # 合并默认结构和实际数据
        for key, default_dim in default_dimensions.items():
            if key not in dimensions:
                dimensions[key] = default_dim
            else:
                # 确保维度名称存在
                if 'dimension_name' not in dimensions[key]:
                    dimensions[key]['dimension_name'] = default_dim['dimension_name']
                
                # 确保二级分类结构完整
                if 'subcategories' not in dimensions[key]:
                    dimensions[key]['subcategories'] = default_dim['subcategories']
                else:
                    # 检查每个二级分类
                    for sub_key, sub_default in default_dim['subcategories'].items():
                        if sub_key not in dimensions[key]['subcategories']:
                            dimensions[key]['subcategories'][sub_key] = sub_default
                        else:
                            # 确保二级分类的必要字段存在
                            sub_data = dimensions[key]['subcategories'][sub_key]
                            for field, default_value in sub_default.items():
                                if field not in sub_data:
                                    sub_data[field] = default_value
                
                # 确保顶级字段存在
                if 'overall_weight' not in dimensions[key]:
                    dimensions[key]['overall_weight'] = 0.0
                if 'overall_stability' not in dimensions[key]:
                    dimensions[key]['overall_stability'] = 0.0
        
        user_tags['tag_dimensions'] = dimensions
        
        # 确保综合指标存在
        if 'computed_metrics' not in user_tags:
            user_tags['computed_metrics'] = {}
        
        computed_metrics = user_tags['computed_metrics']
        default_metrics = {
            'emotional_health_index': 0.5,
            'interest_concentration': 0.0,
            'interaction_dependency': 0.0,
            'overall_profile_maturity': 0.0
        }
        
        for metric, default_value in default_metrics.items():
            if metric not in computed_metrics:
                computed_metrics[metric] = default_value
        
        # 为向后兼容性添加顶级指标
        user_tags['emotional_health_index'] = computed_metrics['emotional_health_index']
        user_tags['profile_maturity'] = computed_metrics['overall_profile_maturity']
        
        return jsonify({
            "success": True,
            "user_tags": user_tags
        })
        
    except Exception as e:
        print(f"获取用户画像错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== 更新 /api/chat 接口 ====================

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """聊天接口 - 适配新的二级标签结构"""
    try:
        data = request.json
        user_message = data.get('message', '')
        user_id = request.current_user["user_id"]
        
        # 初始化组件
        enhanced_extractor = EnhancedTagExtractor(str(user_id))
        tag_manager = TagManager(str(user_id))
        response_generator = ResponseGenerator(str(user_id))
        
        # 提取标签并记录溯源信息
        extracted_tags, triggers = enhanced_extractor.extract_tags_with_tracing(
            text=user_message,
            context={"source": "chat"},
            session_id=f"chat_{user_id}_{int(time.time())}",
            message_id=str(uuid.uuid4())
        )
        
        # 更新标签
        updated_tags = tag_manager.update_tags(extracted_tags)
        
        # 生成回应
        response_data = response_generator.generate_response(user_message)
        
        # 获取标准化的用户画像数据
        user_profile = _get_standardized_user_profile_v2(str(user_id))
        
        # 格式化提取的标签信息（适配新结构）
        formatted_extracted_tags = {}
        for category, tags in extracted_tags.items():
            formatted_extracted_tags[category] = []
            for tag in tags:
                formatted_extracted_tags[category].append({
                    "name": tag.name,
                    "confidence": tag.confidence,
                    "category": tag.category,
                    "subcategory": tag.subcategory,
                    "evidence": tag.evidence
                })
        
        return jsonify({
            "success": True,
            "response": response_data["response"],
            "user_profile": user_profile,
            "extracted_tags": formatted_extracted_tags,
            "triggers": len(triggers) if triggers else 0
        })
        
    except Exception as e:
        print(f"聊天处理错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== 新的标准化用户画像函数 ====================

def _get_standardized_user_profile_v2(user_id: str):
    """获取标准化的用户画像数据 - 适配新的二级标签结构"""
    try:
        tag_manager = TagManager(user_id)
        user_tags = tag_manager.get_user_tags()
        
        dimensions = user_tags.get('tag_dimensions', {})
        
        # 构建标准化的数据结构
        standardized_profile = {
            'tag_dimensions': dimensions,
            'computed_metrics': user_tags.get('computed_metrics', {}),
            'active_dimensions': []  # 保持向后兼容
        }
        
        # 为向后兼容，构建 active_dimensions 格式
        for key, dimension in dimensions.items():
            all_tags = []
            
            # 从二级分类中收集所有标签
            if 'subcategories' in dimension:
                for sub_key, sub_data in dimension['subcategories'].items():
                    if 'active_tags' in sub_data and sub_data['active_tags']:
                        for tag in sub_data['active_tags']:
                            all_tags.append({
                                'name': tag.get('tag_name', ''),
                                'confidence': tag.get('avg_confidence', tag.get('confidence', 0)),
                                'weight': tag.get('current_weight', tag.get('weight', 0)),
                                'category': tag.get('category', key),
                                'subcategory': tag.get('subcategory', sub_key)
                            })
            
            # 添加维度信息
            standardized_profile['active_dimensions'].append({
                'name': dimension.get('dimension_name', key),
                'dimension': key,
                'tags': all_tags
            })
        
        return standardized_profile
        
    except Exception as e:
        print(f"获取标准化用户画像错误: {e}")
        return {
            'tag_dimensions': {},
            'computed_metrics': {},
            'active_dimensions': []
        }

# ==================== 新增标签统计接口 ====================

@app.route('/api/tag_statistics')
@login_required
def get_tag_statistics():
    """获取标签统计信息 - 适配新的二级标签结构"""
    try:
        user_id = request.current_user["user_id"]
        tag_manager = TagManager(str(user_id))
        user_tags = tag_manager.get_user_tags()
        
        dimensions = user_tags.get('tag_dimensions', {})
        
        # 统计信息
        total_tags = 0
        total_categories = len(dimensions)
        tag_statistics = {}
        
        # 按新结构统计标签
        for dim_key, dimension in dimensions.items():
            tag_statistics[dim_key] = {}
            
            if 'subcategories' in dimension:
                for sub_key, sub_data in dimension['subcategories'].items():
                    if 'active_tags' in sub_data and sub_data['active_tags']:
                        tag_statistics[dim_key][sub_key] = []
                        
                        for tag in sub_data['active_tags']:
                            total_tags += 1
                            tag_statistics[dim_key][sub_key].append({
                                'tag_name': tag.get('tag_name', ''),
                                'current_confidence': tag.get('avg_confidence', 0),
                                'total_triggers': tag.get('evidence_count', 0),
                                'last_reinforced': tag.get('last_reinforced', ''),
                                'category': dim_key,
                                'subcategory': sub_key
                            })
        
        # 获取最近触发记录（如果有溯源系统）
        recent_triggers = []
        try:
            from core.tag_tracer import TagTracer
            tracer = TagTracer(user_id)
            recent_triggers = tracer.get_recent_triggers(limit=10)
        except Exception as e:
            print(f"获取最近触发记录失败: {e}")
        
        return jsonify({
            "success": True,
            "total_tags": total_tags,
            "total_categories": total_categories,
            "tag_statistics": tag_statistics,
            "recent_triggers": recent_triggers
        })
        
    except Exception as e:
        print(f"获取标签统计错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== 标签搜索接口 ====================

@app.route('/api/search_tags')
@login_required
def search_tags():
    """搜索标签 - 支持按分类搜索"""
    try:
        user_id = request.current_user["user_id"]
        query = request.args.get('q', '').lower()
        category = request.args.get('category', '')
        subcategory = request.args.get('subcategory', '')
        
        tag_manager = TagManager(str(user_id))
        user_tags = tag_manager.get_user_tags()
        
        dimensions = user_tags.get('tag_dimensions', {})
        results = []
        
        for dim_key, dimension in dimensions.items():
            # 如果指定了分类，只搜索该分类
            if category and dim_key != category:
                continue
                
            if 'subcategories' in dimension:
                for sub_key, sub_data in dimension['subcategories'].items():
                    # 如果指定了二级分类，只搜索该二级分类
                    if subcategory and sub_key != subcategory:
                        continue
                        
                    if 'active_tags' in sub_data and sub_data['active_tags']:
                        for tag in sub_data['active_tags']:
                            tag_name = tag.get('tag_name', '').lower()
                            
                            # 搜索匹配
                            if not query or query in tag_name:
                                results.append({
                                    'name': tag.get('tag_name', ''),
                                    'confidence': tag.get('avg_confidence', 0),
                                    'category': dim_key,
                                    'subcategory': sub_key,
                                    'category_name': dimension.get('dimension_name', dim_key),
                                    'subcategory_name': sub_data.get('subcategory_name', sub_key),
                                    'evidence_count': tag.get('evidence_count', 0),
                                    'last_reinforced': tag.get('last_reinforced', '')
                                })
        
        # 按置信度排序
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        return jsonify({
            "success": True,
            "results": results,
            "total": len(results)
        })
        
    except Exception as e:
        print(f"搜索标签错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== 标签详情接口 ====================

@app.route('/api/tag_detail/<tag_name>')
@login_required
def get_tag_detail(tag_name):
    """获取标签详细信息"""
    try:
        user_id = request.current_user["user_id"]
        
        # 从标签管理器获取标签信息
        tag_manager = TagManager(str(user_id))
        user_tags = tag_manager.get_user_tags()
        
        # 查找标签
        tag_info = None
        dimensions = user_tags.get('tag_dimensions', {})
        
        for dim_key, dimension in dimensions.items():
            if 'subcategories' in dimension:
                for sub_key, sub_data in dimension['subcategories'].items():
                    if 'active_tags' in sub_data and sub_data['active_tags']:
                        for tag in sub_data['active_tags']:
                            if tag.get('tag_name') == tag_name:
                                tag_info = {
                                    'name': tag.get('tag_name', ''),
                                    'confidence': tag.get('avg_confidence', 0),
                                    'category': dim_key,
                                    'subcategory': sub_key,
                                    'category_name': dimension.get('dimension_name', dim_key),
                                    'subcategory_name': sub_data.get('subcategory_name', sub_key),
                                    'evidence_count': tag.get('evidence_count', 0),
                                    'total_confidence': tag.get('total_confidence', 0),
                                    'first_detected': tag.get('first_detected', ''),
                                    'last_reinforced': tag.get('last_reinforced', ''),
                                    'evidence': tag.get('evidence', ''),
                                    'conflict_resolved': tag.get('conflict_resolved', False)
                                }
                                break
                    if tag_info:
                        break
            if tag_info:
                break
        
        if not tag_info:
            return jsonify({
                "success": False,
                "error": "标签未找到"
            }), 404
        
        # 获取溯源信息（如果有）
        trace_info = []
        try:
            from core.tag_tracer import TagTracer
            tracer = TagTracer(user_id)
            trace_info = tracer.get_tag_trace(tag_name)
        except Exception as e:
            print(f"获取标签溯源信息失败: {e}")
        
        return jsonify({
            "success": True,
            "tag_info": tag_info,
            "trace_info": trace_info
        })
        
    except Exception as e:
        print(f"获取标签详情错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500