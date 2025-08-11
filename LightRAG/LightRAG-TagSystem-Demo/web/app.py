import sys
import os

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import uuid
import json
import time
from datetime import datetime
from app.core.lightrag_engine import LightRAGEngine
from app.core.tag_extractor import TagExtractor
from app.core.tag_manager import TagManager
from app.core.response_generator import ResponseGenerator
from app.core.enhanced_tag_extractor import EnhancedTagExtractor
from app.core.tag_tracer import TagTracer
from app.core.tag_trigger_detector import TagTriggerDetector
from app.utils.database import DatabaseManager
from app.auth.auth_manager import AuthManager
from app.auth.decorators import login_required

# 导入API蓝图
from app.api.auth_api import auth_bp
from app.api.user_api import user_bp

app = Flask(__name__)
app.secret_key = 'lightrag_demo_secret_key'

# 初始化数据库
db_manager = DatabaseManager()
app.config['DB_MANAGER'] = db_manager

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/user')

@app.route('/')
def index():
    """主页 - 检查登录状态"""
    auth_manager = AuthManager(db_manager, app.secret_key)
    current_user = auth_manager.get_current_user()
    
    if not current_user:
        # 清除可能存在的无效session
        session.clear()
        return redirect(url_for('login'))
    
    # 管理员也可以访问普通用户界面，不强制重定向
    return render_template('index.html', user=current_user)

@app.route('/login')
def login():
    """登录页面"""
    auth_manager = AuthManager(db_manager, app.secret_key)
    current_user = auth_manager.get_current_user()
    
    if current_user:
        # 根据用户角色重定向
        if current_user.get('is_admin', False):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    """管理员看板页面"""
    auth_manager = AuthManager(db_manager, app.secret_key)
    current_user = auth_manager.get_current_user()
    
    if not current_user:
        return redirect(url_for('login'))
    
    if not current_user.get('is_admin', False):
        return redirect(url_for('index'))  # 非管理员重定向到普通页面
    
    return render_template('admin_dashboard.html', user=current_user)

@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    
    # 如果是AJAX请求，返回JSON响应
    if request.headers.get('Content-Type') == 'application/json' or \
       'application/json' in request.headers.get('Accept', ''):
        return jsonify({"success": True, "message": "退出登录成功"})
    
    # 普通请求重定向到登录页面
    return redirect(url_for('login'))

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """聊天接口 - 需要登录"""
    try:
        data = request.json
        user_message = data.get('message', '')
        phone_number = request.current_user["phone_number"]
        
        # 初始化组件
        enhanced_extractor = EnhancedTagExtractor(str(phone_number))
        tag_manager = TagManager(str(phone_number), db_manager)
        response_generator = ResponseGenerator(str(phone_number))
        
        # 提取标签并记录溯源信息
        extracted_tags, triggers = enhanced_extractor.extract_tags_with_tracing(
            text=user_message,
            context={"source": "chat"},
            session_id=f"chat_{phone_number}_{int(time.time())}",
            message_id=str(uuid.uuid4())
        )
        
        # 更新标签
        updated_tags = tag_manager.update_tags(extracted_tags)
        
        # 生成回应
        response_data = response_generator.generate_response(user_message)
        
        # 🔧 修复：获取标准化的用户画像数据（与/api/profile接口保持一致）
        user_profile = _get_standardized_user_profile(str(phone_number))
        
        return jsonify({
            "success": True,
            "response": response_data["response"],
            "user_profile": user_profile,
            "extracted_tags": {k: [{"name": tag.name, "confidence": tag.confidence} for tag in v] for k, v in extracted_tags.items()},
            "used_tags": response_data.get("used_tags", {})  # 新增：返回标签依据信息
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def _get_standardized_user_profile(phone_number: str):
    """获取标准化的用户画像数据，与/api/profile接口保持一致"""
    try:
        tag_manager = TagManager(phone_number, db_manager)
        user_tags = tag_manager.get_user_tags()
        
        dimensions = user_tags.get('tag_dimensions', {})
        active_dimensions = []
        
        # 处理新的二级标签结构
        for key, dimension in dimensions.items():
            tags = []
            
            # 处理新的二级标签结构
            if dimension.get('subcategories'):
                # 遍历所有二级分类
                for sub_key, subcategory_data in dimension['subcategories'].items():
                    if subcategory_data.get('active_tags') and len(subcategory_data['active_tags']) > 0:
                        for tag in subcategory_data['active_tags']:
                            tags.append({
                                'name': tag.get('tag_name', ''),
                                'confidence': tag.get('avg_confidence', tag.get('confidence', 0)),
                                'weight': tag.get('current_weight', tag.get('weight', 0)),
                                'category': tag.get('category', key),
                                'subcategory': tag.get('subcategory', sub_key),
                                'subcategory_name': subcategory_data.get('subcategory_name', sub_key)
                            })
            elif dimension.get('active_tags') and len(dimension['active_tags']) > 0:
                # 兼容旧的一级标签结构
                for tag in dimension['active_tags']:
                    tags.append({
                        'name': tag.get('tag_name', ''),
                        'confidence': tag.get('avg_confidence', tag.get('confidence', 0)),
                        'weight': tag.get('current_weight', tag.get('weight', 0))
                    })
            elif dimension.get('tags') and len(dimension['tags']) > 0:
                # 兼容更旧的tags对象格式
                for tag_name, tag_info in dimension['tags'].items():
                    tags.append({
                        'name': tag_name,
                        'confidence': tag_info.get('confidence', 0),
                        'weight': tag_info.get('weight', 0)
                    })
            
            # 总是添加维度，即使没有标签
            active_dimensions.append({
                'name': dimension.get('dimension_name', dimension.get('name', key)),
                'dimension': key,
                'tags': tags,
                'subcategories': dimension.get('subcategories')
            })
        
        return {
            'tag_dimensions': dimensions,  # 🔧 修复：直接返回tag_dimensions结构
            'active_dimensions': active_dimensions,  # 保留向后兼容
            'emotional_health_index': user_tags.get('emotional_health_index',
                                                   user_tags.get('computed_metrics', {}).get('emotional_health_index', 0.5)),
            'profile_maturity': user_tags.get('profile_maturity',
                                            user_tags.get('computed_metrics', {}).get('overall_profile_maturity', 0.0))
        }
        
    except Exception as e:
        print(f"获取标准化用户画像时出错: {e}")
        return {
            'active_dimensions': [],
            'emotional_health_index': 0.5,
            'profile_maturity': 0.0
        }

@app.route('/api/profile')
@login_required
def get_profile():
    """获取用户画像 - 需要登录"""
    try:
        phone_number = request.current_user["phone_number"]
        tag_manager = TagManager(str(phone_number))
        user_tags = tag_manager.get_user_tags()
        
        # 确保所有维度都存在，即使没有标签 - 新的二级标签结构
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
                    "art_creation": {
                        "subcategory_name": "文艺创作类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "handcraft_diy": {
                        "subcategory_name": "手工DIY类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "music_appreciation": {
                        "subcategory_name": "音乐欣赏类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "music_performance": {
                        "subcategory_name": "音乐演奏类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "film_tv_appreciation": {
                        "subcategory_name": "影视欣赏类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "ball_sports": {
                        "subcategory_name": "球类运动类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "sports_watching": {
                        "subcategory_name": "运动比赛欣赏类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "extreme_sports": {
                        "subcategory_name": "极限运动类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "health_fitness": {
                        "subcategory_name": "养生锻炼身体类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "pet_keeping": {
                        "subcategory_name": "饲养宠物类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "home_cooking": {
                        "subcategory_name": "家常菜烹饪类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "baking": {
                        "subcategory_name": "烘焙类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "food_exploration": {
                        "subcategory_name": "美食探店类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "offline_socializing": {
                        "subcategory_name": "线下聚会社交类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "home_design": {
                        "subcategory_name": "家装设计类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "knowledge_learning": {
                        "subcategory_name": "知识学习类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "collecting_appreciation": {
                        "subcategory_name": "收藏鉴赏类",
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    },
                    "life_experience": {
                        "subcategory_name": "体验生活类",
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
        
        # 合并默认维度和用户实际数据
        dimensions = user_tags.get('tag_dimensions', {})
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
        if 'emotional_health_index' not in computed_metrics:
            computed_metrics['emotional_health_index'] = 0.5
        if 'overall_profile_maturity' not in computed_metrics:
            computed_metrics['overall_profile_maturity'] = 0.0
            
        # 为向后兼容性添加顶级指标
        user_tags['emotional_health_index'] = computed_metrics['emotional_health_index']
        user_tags['profile_maturity'] = computed_metrics['overall_profile_maturity']
        
        return jsonify({
            "success": True,
            "user_tags": user_tags
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/add_knowledge', methods=['POST'])
@login_required
def add_knowledge():
    """添加知识 - 需要登录"""
    try:
        data = request.json
        knowledge_text = data.get('text', '')
        metadata = data.get('metadata', {})
        phone_number = request.current_user["phone_number"]
        
        lightrag = LightRAGEngine(str(phone_number))
        result = lightrag.insert_knowledge(knowledge_text, metadata)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/process_conversation', methods=['POST'])
@login_required
def process_conversation():
    """处理结构化对话文本并提取标签 - 需要登录"""
    try:
        data = request.json
        conversation_text = data.get('conversation_text', '')
        extract_tags = data.get('extract_tags', True)
        phone_number = request.current_user["phone_number"]
        
        if not conversation_text.strip():
            return jsonify({
                "success": False,
                "error": "对话文本不能为空"
            }), 400
        
        # 解析对话文本
        conversation_messages = parse_conversation_text(conversation_text)
        
        if not conversation_messages:
            return jsonify({
                "success": False,
                "error": "无法解析对话文本，请检查格式"
            }), 400
        
        # 初始化组件 - 使用增强版标签提取器支持溯源
        from app.core.enhanced_tag_extractor import EnhancedTagExtractor
        enhanced_extractor = EnhancedTagExtractor(str(phone_number))
        tag_manager = TagManager(str(phone_number))
        response_generator = ResponseGenerator(str(phone_number))
        lightrag = LightRAGEngine(str(phone_number))
        
        all_extracted_tags = {}
        all_trigger_records = []
        knowledge_added = False
        
        # 生成会话ID用于溯源
        session_id = str(uuid.uuid4())
        
        # 处理每条用户消息
        for idx, message in enumerate(conversation_messages):
            if message['role'] == 'user':
                try:
                    # 生成消息ID
                    message_id = f"{session_id}_msg_{idx}"
                    
                    # 提取标签并记录溯源信息
                    if extract_tags:
                        # 构建上下文信息
                        context = {
                            "source": "conversation_upload",
                            "message_index": idx,
                            "total_messages": len(conversation_messages),
                            "conversation_context": "structured_text_analysis"
                        }
                        
                        # 使用增强版提取器进行标签提取和溯源
                        extracted_tags, trigger_records = enhanced_extractor.extract_tags_with_tracing(
                            text=message['content'],
                            context=context,
                            session_id=session_id,
                            message_id=message_id
                        )
                        
                        # 合并标签结果
                        for dimension, tags in extracted_tags.items():
                            if dimension not in all_extracted_tags:
                                all_extracted_tags[dimension] = []
                            all_extracted_tags[dimension].extend([tag.name for tag in tags])
                        
                        # 收集触发记录
                        all_trigger_records.extend(trigger_records)
                        
                        # 更新标签
                        tag_manager.update_tags(extracted_tags)
                    
                    # 添加到知识库
                    lightrag.insert_knowledge(
                        f"用户消息: {message['content']}", 
                        {"source": "conversation_upload", "timestamp": datetime.now().isoformat(), "message_id": message_id}
                    )
                    knowledge_added = True
                    
                except Exception as e:
                    print(f"处理消息时出错: {e}")
                    continue
        
        # 获取更新后的用户画像
        user_profile = None
        if extract_tags:
            try:
                profile_data = tag_manager.get_user_tags()
                dimensions = profile_data.get('tag_dimensions', {})
                active_dimensions = []
                
                for key, dimension in dimensions.items():
                    tags = []
                    
                    # 处理新的二级标签结构
                    if dimension.get('subcategories'):
                        # 遍历所有二级分类
                        for sub_key, subcategory_data in dimension['subcategories'].items():
                            if subcategory_data.get('active_tags') and len(subcategory_data['active_tags']) > 0:
                                for tag in subcategory_data['active_tags']:
                                    tags.append({
                                        'name': tag.get('tag_name', ''),
                                        'confidence': tag.get('avg_confidence', tag.get('confidence', 0)),
                                        'weight': tag.get('current_weight', tag.get('weight', 0)),
                                        'category': tag.get('category', key),
                                        'subcategory': tag.get('subcategory', sub_key)
                                    })
                    elif dimension.get('active_tags') and len(dimension['active_tags']) > 0:
                        # 兼容旧的一级标签结构
                        for tag in dimension['active_tags']:
                            tags.append({
                                'name': tag.get('tag_name', ''),
                                'confidence': tag.get('avg_confidence', tag.get('confidence', 0)),
                                'weight': tag.get('current_weight', tag.get('weight', 0))
                            })
                    elif dimension.get('tags') and len(dimension['tags']) > 0:
                        # 兼容更旧的tags对象格式
                        for tag_name, tag_info in dimension['tags'].items():
                            tags.append({
                                'name': tag_name,
                                'confidence': tag_info.get('confidence', 0),
                                'weight': tag_info.get('weight', 0)
                            })
                    
                    if tags:  # 只有有标签时才添加到active_dimensions
                        active_dimensions.append({
                            'name': dimension.get('dimension_name', dimension.get('name', key)),
                            'tags': tags,
                            'subcategories': dimension.get('subcategories')
                        })
                
                user_profile = {
                    'active_dimensions': active_dimensions,
                    'emotional_health_index': profile_data.get('emotional_health_index', 0.5),
                    'profile_maturity': profile_data.get('profile_maturity', 0.0)
                }
            except Exception as e:
                print(f"获取用户画像时出错: {e}")
        
        # 去重标签
        for dimension in all_extracted_tags:
            all_extracted_tags[dimension] = list(set(all_extracted_tags[dimension]))
        
        # 准备溯源信息
        tracing_info = {
            "session_id": session_id,
            "total_triggers": len(all_trigger_records),
            "trigger_summary": {}
        }
        
        # 按标签分组触发记录
        for trigger in all_trigger_records:
            tag_key = f"{trigger.tag_category}.{trigger.tag_name}"
            if tag_key not in tracing_info["trigger_summary"]:
                tracing_info["trigger_summary"][tag_key] = {
                    "tag_name": trigger.tag_name,
                    "tag_category": trigger.tag_category,
                    "trigger_count": 0,
                    "sources": []
                }
            
            tracing_info["trigger_summary"][tag_key]["trigger_count"] += 1
            tracing_info["trigger_summary"][tag_key]["sources"].append({
                "text": trigger.trigger_text,
                "evidence": trigger.evidence,
                "confidence_change": trigger.confidence_delta,
                "message_id": trigger.message_id
            })
        
        return jsonify({
            "success": True,
            "extracted_tags": all_extracted_tags,
            "user_profile": user_profile,
            "knowledge_added": knowledge_added,
            "processed_messages": len(conversation_messages),
            "tracing_info": tracing_info
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def parse_conversation_text(text):
    """解析不同格式的对话文本"""
    messages = []
    
    # 尝试解析为JSON格式
    try:
        json_data = json.loads(text.strip())
        if isinstance(json_data, list):
            for item in json_data:
                if isinstance(item, dict) and 'role' in item and 'content' in item:
                    role = item['role'].lower()
                    if role in ['user', 'assistant', 'human', 'ai']:
                        messages.append({
                            'role': 'user' if role in ['user', 'human'] else 'assistant',
                            'content': item['content'].strip()
                        })
            if messages:
                return messages
    except:
        pass
    
    # 尝试解析文本格式
    lines = text.strip().split('\n')
    current_role = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检查角色标识
        role = None
        content = line
        
        # 文本格式: "用户:" 或 "角色:" (支持中英文冒号)
        if (line.startswith('用户:') or line.startswith('用户：') or 
            line.startswith('User:') or line.startswith('human:') or line.startswith('Human:')):
            role = 'user'
            # 支持中英文冒号分割
            if '：' in line:
                content = line.split('：', 1)[1].strip()
            else:
                content = line.split(':', 1)[1].strip()
        elif (line.startswith('角色:') or line.startswith('角色：') or 
              line.startswith('助手:') or line.startswith('助手：') or 
              line.startswith('Assistant:') or line.startswith('AI:') or line.startswith('ai:')):
            role = 'assistant'
            # 支持中英文冒号分割
            if '：' in line:
                content = line.split('：', 1)[1].strip()
            else:
                content = line.split(':', 1)[1].strip()
        
        # Markdown格式: "## 用户" 或 "## 角色"
        elif line.startswith('## 用户') or line.startswith('## User') or line.startswith('## Human'):
            role = 'user'
            content = ''
        elif line.startswith('## 角色') or line.startswith('## 助手') or line.startswith('## Assistant') or line.startswith('## AI'):
            role = 'assistant'
            content = ''
        
        # 如果识别到新角色
        if role:
            # 保存之前的内容
            if current_role and current_content:
                messages.append({
                    'role': current_role,
                    'content': '\n'.join(current_content).strip()
                })
            
            # 开始新的角色内容
            current_role = role
            current_content = [content] if content else []
        else:
            # 继续当前角色的内容
            if current_role:
                current_content.append(line)
    
    # 保存最后一个角色的内容
    if current_role and current_content:
        messages.append({
            'role': current_role,
            'content': '\n'.join(current_content).strip()
        })
    
    return messages

@app.route('/api/chat_history')
@login_required
def get_chat_history():
    """获取历史对话记录 - 需要登录"""
    try:
        phone_number = request.current_user["phone_number"]
        
        # 从用户数据文件中读取历史对话
        timeline_file = f"user_data/{phone_number}/tag_timeline.json"
        chat_history = []
        
        if os.path.exists(timeline_file):
            with open(timeline_file, 'r', encoding='utf-8') as f:
                timeline_data = json.load(f)
                
                # 从时间轴中提取对话记录
                for event in timeline_data.get('tag_events', []):
                    if event.get('event_type') == 'tag_extraction' and event.get('context'):
                        context = event['context']
                        if 'user_input' in context:
                            chat_history.append({
                                'role': 'user',
                                'content': context['user_input'],
                                'timestamp': event.get('timestamp')
                            })
        
        return jsonify({
            "success": True,
            "chat_history": chat_history
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/reset_user', methods=['POST'])
@login_required
def reset_user():
    """重置用户数据 - 需要登录"""
    try:
        phone_number = request.current_user["phone_number"]
        
        # 清除用户数据
        import shutil
        user_data_path = f"user_data/{phone_number}"
        if os.path.exists(user_data_path):
            shutil.rmtree(user_data_path)
        
        return jsonify({
            "success": True,
            "message": "用户数据已重置"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============= 标签溯源功能API =============

@app.route('/api/analyze_message_triggers', methods=['POST'])
@login_required
def analyze_message_triggers():
    """分析单条消息的标签触发情况"""
    try:
        data = request.json
        message_text = data.get('message_text', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        message_id = data.get('message_id', str(uuid.uuid4()))
        phone_number = request.current_user["phone_number"]
        
        if not message_text.strip():
            return jsonify({
                "success": False,
                "error": "消息文本不能为空"
            }), 400
        
        # 使用增强版标签提取器
        enhanced_extractor = EnhancedTagExtractor(str(phone_number))
        
        # 提取标签并获取触发信息
        new_tags, triggers = enhanced_extractor.extract_tags_with_tracing(
            text=message_text,
            context={"source": "single_message"},
            session_id=session_id,
            message_id=message_id
        )
        
        # 更新标签管理器
        tag_manager = TagManager(str(phone_number))
        tag_manager.update_tags(new_tags)
        
        # 分析文本影响
        impact_analysis = enhanced_extractor.analyze_text_impact(message_text)
        
        return jsonify({
            "success": True,
            "triggers": [trigger.to_dict() for trigger in triggers],
            "new_tags": serialize_tags(new_tags),
            "impact_analysis": impact_analysis,
            "session_id": session_id,
            "message_id": message_id
        })
        
    except Exception as e:
        print(f"分析消息触发错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/tag_trace/<tag_name>', methods=['GET'])
@login_required
def get_tag_trace(tag_name):
    """获取标签的完整溯源信息"""
    try:
        phone_number = request.current_user["phone_number"]
        enhanced_extractor = EnhancedTagExtractor(str(phone_number))
        
        # 获取标签溯源信息
        trace_info = enhanced_extractor.get_tag_trace_info(tag_name)
        
        return jsonify({
            "success": True,
            "trace_info": trace_info
        })
        
    except Exception as e:
        print(f"获取标签溯源信息错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/session_tag_summary/<session_id>', methods=['GET'])
@login_required
def get_session_tag_summary(session_id):
    """获取会话的标签变化总结"""
    try:
        phone_number = request.current_user["phone_number"]
        enhanced_extractor = EnhancedTagExtractor(str(phone_number))
        
        # 获取会话标签总结
        summary = enhanced_extractor.get_conversation_tag_summary(session_id)
        
        return jsonify({
            "success": True,
            "summary": summary
        })
        
    except Exception as e:
        print(f"获取会话标签总结错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/tag_statistics', methods=['GET'])
@login_required
def get_tag_statistics():
    """获取用户的标签统计信息"""
    try:
        phone_number = request.current_user["phone_number"]
        tag_tracer = TagTracer(str(phone_number))
        tag_manager = TagManager(str(phone_number))
        
        # 获取所有标签
        all_tags_raw = tag_manager.get_user_tags()
        
        # 转换为简单格式 - 支持新的二级标签结构
        all_tags = {}
        if isinstance(all_tags_raw, dict) and "tag_dimensions" in all_tags_raw:
            for dimension, dimension_data in all_tags_raw["tag_dimensions"].items():
                all_tags[dimension] = []
                
                # 处理新的二级标签结构
                if dimension_data.get('subcategories'):
                    for sub_key, subcategory_data in dimension_data['subcategories'].items():
                        active_tags = subcategory_data.get("active_tags", [])
                        all_tags[dimension].extend(active_tags)
                elif dimension_data.get("active_tags"):
                    # 兼容旧的一级标签结构
                    active_tags = dimension_data.get("active_tags", [])
                    all_tags[dimension] = active_tags
        else:
            all_tags = all_tags_raw
        
        # 获取每个标签的统计信息
        tag_stats = {}
        for category, tag_list in all_tags.items():
            if not isinstance(tag_list, list):
                continue
                
            category_stats = []
            for tag in tag_list:
                # 获取标签名称
                tag_name = tag.get('name') if isinstance(tag, dict) else (tag.name if hasattr(tag, 'name') else str(tag))
                
                if tag_name:
                    stats = tag_tracer.get_tag_statistics(tag_name)
                    if stats:
                        category_stats.append(stats)
            
            if category_stats:
                tag_stats[category] = category_stats
        
        # 获取最近的触发记录
        recent_triggers = tag_tracer.get_trigger_records()[:20]  # 最近20条
        
        return jsonify({
            "success": True,
            "tag_statistics": tag_stats,
            "recent_triggers": [trigger.to_dict() for trigger in recent_triggers],
            "total_tags": sum(len(tags) for tags in all_tags.values()),
            "total_categories": len(all_tags)
        })
        
    except Exception as e:
        print(f"获取标签统计信息错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/export_tag_report/<tag_name>', methods=['GET'])
@login_required
def export_tag_report(tag_name):
    """导出标签溯源报告"""
    try:
        phone_number = request.current_user["phone_number"]
        format_type = request.args.get('format', 'json')
        
        enhanced_extractor = EnhancedTagExtractor(str(phone_number))
        
        # 导出报告
        report = enhanced_extractor.export_tag_trace_report(tag_name, format_type)
        
        if format_type == 'markdown':
            return report, 200, {'Content-Type': 'text/markdown; charset=utf-8'}
        else:
            return jsonify({
                "success": True,
                "report": report,
                "format": format_type
            })
        
    except Exception as e:
        print(f"导出标签报告错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/predict_tag_impact', methods=['POST'])
@login_required
def predict_tag_impact():
    """预测文本对标签的影响"""
    try:
        data = request.json
        text = data.get('text', '')
        phone_number = request.current_user["phone_number"]
        
        if not text.strip():
            return jsonify({
                "success": False,
                "error": "文本不能为空"
            }), 400
        
        enhanced_extractor = EnhancedTagExtractor(str(phone_number))
        
        # 分析文本影响
        impact_analysis = enhanced_extractor.analyze_text_impact(text)
        
        return jsonify({
            "success": True,
            "impact_analysis": impact_analysis
        })
        
    except Exception as e:
        print(f"预测标签影响错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# 辅助函数
def serialize_tags(tags_dict):
    """序列化标签字典 - 支持多种数据格式"""
    if not tags_dict:
        return {}
    
    serialized = {}
    
    # 检查是否是TagManager返回的完整格式
    if isinstance(tags_dict, dict) and "tag_dimensions" in tags_dict:
        # 处理TagManager的完整格式 - 支持新的二级标签结构
        for dimension, dimension_data in tags_dict["tag_dimensions"].items():
            serialized[dimension] = []
            
            # 处理新的二级标签结构
            if dimension_data.get('subcategories'):
                for sub_key, subcategory_data in dimension_data['subcategories'].items():
                    active_tags = subcategory_data.get("active_tags", [])
                    for tag in active_tags:
                        if isinstance(tag, dict):
                            # 如果是字典格式
                            serialized[dimension].append({
                                'name': tag.get('tag_name', tag.get('name', '')),
                                'confidence': tag.get('avg_confidence', tag.get('confidence', 0.0)),
                                'evidence': tag.get('evidence', ''),
                                'category': tag.get('category', dimension),
                                'subcategory': tag.get('subcategory', sub_key)
                            })
                        elif hasattr(tag, 'name'):
                            # 如果是TagInfo对象
                            serialized[dimension].append({
                                'name': tag.name,
                                'confidence': tag.confidence,
                                'evidence': tag.evidence,
                                'category': getattr(tag, 'category', dimension),
                                'subcategory': getattr(tag, 'subcategory', sub_key)
                            })
            elif dimension_data.get("active_tags"):
                # 兼容旧的一级标签结构
                active_tags = dimension_data.get("active_tags", [])
                for tag in active_tags:
                    if isinstance(tag, dict):
                        # 如果是字典格式
                        serialized[dimension].append({
                            'name': tag.get('tag_name', tag.get('name', '')),
                            'confidence': tag.get('avg_confidence', tag.get('confidence', 0.0)),
                            'evidence': tag.get('evidence', ''),
                            'category': tag.get('category', dimension)
                        })
                    elif hasattr(tag, 'name'):
                        # 如果是TagInfo对象
                        serialized[dimension].append({
                            'name': tag.name,
                            'confidence': tag.confidence,
                            'evidence': getattr(tag, 'evidence', ''),
                            'category': getattr(tag, 'category', dimension)
                        })
                    else:
                        # 如果是字符串或其他格式，跳过或使用默认值
                        print(f"警告：未知的标签格式: {type(tag)} - {tag}")
                        continue
    else:
        # 处理简单的Dict[str, List[TagInfo]]格式
        for category, tag_list in tags_dict.items():
            if not isinstance(tag_list, list):
                continue
                
            serialized[category] = []
            for tag in tag_list:
                if isinstance(tag, dict):
                    # 如果是字典格式
                    serialized[category].append({
                        'name': tag.get('name', ''),
                        'confidence': tag.get('confidence', 0.0),
                        'evidence': tag.get('evidence', ''),
                        'category': category
                    })
                elif hasattr(tag, 'name'):
                    # 如果是TagInfo对象
                    serialized[category].append({
                        'name': tag.name,
                        'confidence': tag.confidence,
                        'evidence': getattr(tag, 'evidence', ''),
                        'category': getattr(tag, 'category', category)
                    })
                else:
                    # 如果是字符串，创建基本格式
                    if isinstance(tag, str):
                        serialized[category].append({
                            'name': tag,
                            'confidence': 0.0,
                            'evidence': '',
                            'category': category
                        })
                    else:
                        print(f"警告：未知的标签格式: {type(tag)} - {tag}")
                        continue
    
    return serialized


if __name__ == '__main__':
    app.run(debug=True, port=8080)
