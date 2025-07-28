import sys
import os

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, session
import uuid
import json
from datetime import datetime
from app.core.lightrag_engine import LightRAGEngine
from app.core.tag_extractor import TagExtractor  
from app.core.tag_manager import TagManager
from app.core.response_generator import ResponseGenerator

app = Flask(__name__)
app.secret_key = 'lightrag_demo_secret_key'

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天接口"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        # 获取或创建用户ID
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        
        user_id = session['user_id']
        
        # 初始化组件
        tag_extractor = TagExtractor(user_id)
        tag_manager = TagManager(user_id)
        response_generator = ResponseGenerator(user_id)
        
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
def get_profile():
    """获取用户画像"""
    try:
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "用户未初始化"})
        
        user_id = session['user_id']
        tag_manager = TagManager(user_id)
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
def add_knowledge():
    """添加知识"""
    try:
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "用户未初始化"})
        
        data = request.json
        knowledge_text = data.get('text', '')
        metadata = data.get('metadata', {})
        
        user_id = session['user_id']
        lightrag = LightRAGEngine(user_id)
        
        result = lightrag.insert_knowledge(knowledge_text, metadata)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/reset_user', methods=['POST'])
def reset_user():
    """重置用户（新建用户会话）"""
    session.pop('user_id', None)
    return jsonify({"success": True, "message": "用户会话已重置"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
