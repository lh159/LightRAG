from flask import Blueprint, request, jsonify
from app.auth.decorators import login_required
from app.models.user_model import UserManager
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新用户资料"""
    try:
        data = request.json
        user_id = request.current_user["user_id"]
        
        user_manager = UserManager(request.app.config['DB_MANAGER'])
        
        # 更新资料
        profile_data = data.get('profile_data', {})
        success = user_manager.update_user_profile(user_id, profile_data)
        
        if success:
            return jsonify({
                "success": True,
                "message": "资料更新成功"
            })
        else:
            return jsonify({
                "success": False,
                "error": "资料更新失败"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"更新资料失败: {str(e)}"
        }), 500

@user_bp.route('/tags', methods=['GET'])
@login_required
def get_user_tags():
    """获取用户标签"""
    try:
        user_id = request.current_user["user_id"]
        user_manager = UserManager(request.app.config['DB_MANAGER'])
        
        tags = user_manager.get_user_tags(user_id)
        
        # 按维度分组
        tags_by_dimension = {}
        for tag in tags:
            if tag.dimension not in tags_by_dimension:
                tags_by_dimension[tag.dimension] = []
            tags_by_dimension[tag.dimension].append({
                "id": tag.id,
                "tag_name": tag.tag_name,
                "confidence": tag.confidence,
                "evidence": tag.evidence,
                "created_at": tag.created_at.isoformat(),
                "last_updated": tag.last_updated.isoformat()
            })
        
        return jsonify({
            "success": True,
            "tags": tags_by_dimension
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取标签失败: {str(e)}"
        }), 500

@user_bp.route('/data/export', methods=['GET'])
@login_required
def export_user_data():
    """导出用户数据"""
    try:
        user_id = request.current_user["user_id"]
        user_manager = UserManager(request.app.config['DB_MANAGER'])
        
        # 获取用户信息
        user = user_manager.get_user_by_id(user_id)
        tags = user_manager.get_user_tags(user_id)
        
        # 获取用户知识库数据
        knowledge_data = user_manager.db_manager.get_user_knowledge(user_id)
        
        export_data = {
            "user_info": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            },
            "tags": [{
                "dimension": tag.dimension,
                "tag_name": tag.tag_name,
                "confidence": tag.confidence,
                "evidence": tag.evidence,
                "created_at": tag.created_at.isoformat()
            } for tag in tags],
            "knowledge": knowledge_data,
            "export_date": datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "data": export_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"导出数据失败: {str(e)}"
        }), 500 