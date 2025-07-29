import sys
import os

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import uuid
import json
from datetime import datetime
from app.core.lightrag_engine import LightRAGEngine
from app.core.tag_extractor import TagExtractor  
from app.core.tag_manager import TagManager
from app.core.response_generator import ResponseGenerator
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
        return redirect(url_for('login'))
    
    return render_template('index.html', user=current_user)

@app.route('/login')
def login():
    """登录页面"""
    auth_manager = AuthManager(db_manager, app.secret_key)
    current_user = auth_manager.get_current_user()
    
    if current_user:
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """聊天接口 - 需要登录"""
    try:
        data = request.json
        user_message = data.get('message', '')
        user_id = request.current_user["user_id"]
        
        # 初始化组件
        tag_extractor = TagExtractor(str(user_id))
        tag_manager = TagManager(str(user_id))
        response_generator = ResponseGenerator(str(user_id))
        
        # 提取标签
        extracted_tags = tag_extractor.extract_tags_from_text(user_message)
        
        # 更新标签
        updated_tags = tag_manager.update_tags(extracted_tags)
        
        # 生成回应
        response_data = response_generator.generate_response(user_message)
        
        return jsonify({
            "success": True,
            "response": response_data["response"],
            "user_profile": response_data["user_profile_snapshot"],
            "extracted_tags": {k: [{"name": tag.name, "confidence": tag.confidence} for tag in v] for k, v in extracted_tags.items()}
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/profile')
@login_required
def get_profile():
    """获取用户画像 - 需要登录"""
    try:
        user_id = request.current_user["user_id"]
        tag_manager = TagManager(str(user_id))
        user_tags = tag_manager.get_user_tags()
        
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
        user_id = request.current_user["user_id"]
        
        lightrag = LightRAGEngine(str(user_id))
        result = lightrag.insert_knowledge(knowledge_text, metadata)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/chat_history')
@login_required
def get_chat_history():
    """获取历史对话记录 - 需要登录"""
    try:
        user_id = request.current_user["user_id"]
        
        # 从用户数据文件中读取历史对话
        timeline_file = f"user_data/{user_id}/tag_timeline.json"
        messages = []
        
        if os.path.exists(timeline_file):
            with open(timeline_file, 'r', encoding='utf-8') as f:
                timeline_data = json.load(f)
                
                # 从时间轴中提取对话记录
                for event in timeline_data.get('tag_events', []):
                    if event.get('event_type') == 'tag_extraction':
                        # 这里可以添加对话记录的提取逻辑
                        # 目前先返回空数组，后续可以扩展
                        pass
        
        return jsonify({
            "success": True,
            "messages": messages
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
        user_id = request.current_user["user_id"]
        
        # 清除用户数据
        import shutil
        user_data_path = f"user_data/{user_id}"
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
