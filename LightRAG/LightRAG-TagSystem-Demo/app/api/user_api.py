from flask import Blueprint, request, jsonify, current_app
from app.auth.decorators import login_required, admin_required
from app.models.user_model import UserManager
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新用户资料"""
    try:
        data = request.json
        phone_number = request.current_user["phone_number"]
        
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        
        # 更新资料
        profile_data = data.get('profile_data', {})
        success = user_manager.update_user_profile(phone_number, profile_data)
        
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

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """获取用户资料"""
    try:
        phone_number = request.current_user["phone_number"]
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        
        user = user_manager.get_user_by_phone(phone_number)
        if not user:
            return jsonify({
                "success": False,
                "error": "用户不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "user": {
                "phone_number": user.phone_number,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "profile_data": user.profile_data
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取资料失败: {str(e)}"
        }), 500

@user_bp.route('/tags', methods=['GET'])
@login_required
def get_user_tags():
    """获取用户标签"""
    try:
        phone_number = request.current_user["phone_number"]
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        
        tags = user_manager.get_user_tags(phone_number)
        
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
        phone_number = request.current_user["phone_number"]
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        
        # 获取用户信息
        user = user_manager.get_user_by_phone(phone_number)
        tags = user_manager.get_user_tags(phone_number)
        
        # 获取用户知识库数据
        knowledge_data = user_manager.db_manager.get_user_knowledge(phone_number)
        
        export_data = {
            "user_info": {
                "phone_number": user.phone_number,
                "username": user.username,
                "email": user.email,
                "role": user.role,
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

# 管理员专用接口
@user_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    """获取所有用户列表（管理员功能）"""
    try:
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        users = user_manager.get_all_users()
        
        users_data = []
        for user in users:
            users_data.append({
                "phone_number": user.phone_number,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "is_active": user.is_active
            })
        
        return jsonify({
            "success": True,
            "users": users_data,
            "total": len(users_data)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取用户列表失败: {str(e)}"
        }), 500

@user_bp.route('/admin/statistics', methods=['GET'])
@admin_required
def get_user_statistics():
    """获取用户统计信息（管理员功能）"""
    try:
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        stats = user_manager.get_user_statistics()
        
        return jsonify({
            "success": True,
            "statistics": stats
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取统计信息失败: {str(e)}"
        }), 500

@user_bp.route('/admin/users/<phone_number>/profile', methods=['GET'])
@admin_required
def get_user_profile_by_phone(phone_number):
    """获取指定用户的详细信息（管理员功能）"""
    try:
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        
        # 获取用户基本信息
        user = user_manager.get_user_by_phone(phone_number)
        if not user:
            return jsonify({
                "success": False,
                "error": "用户不存在"
            }), 404
        
        # 获取用户标签
        tags = user_manager.get_user_tags(phone_number)
        
        # 按维度分组标签
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
        
        user_profile = {
            "phone_number": user.phone_number,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "is_active": user.is_active,
            "profile_data": user.profile_data,
            "tags": tags_by_dimension
        }
        
        return jsonify({
            "success": True,
            "user": user_profile
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取用户信息失败: {str(e)}"
        }), 500 