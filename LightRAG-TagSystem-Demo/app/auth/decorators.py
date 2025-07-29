from functools import wraps
from flask import request, jsonify, session, current_app
from app.auth.auth_manager import AuthManager

def login_required(f):
    """登录必需装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_manager = AuthManager(current_app.config['DB_MANAGER'], 
                                 current_app.config['SECRET_KEY'])
        
        current_user = auth_manager.get_current_user()
        if not current_user:
            return jsonify({
                "success": False,
                "error": "需要登录"
            }), 401
        
        # 将用户信息添加到请求上下文
        request.current_user = current_user
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_manager = AuthManager(current_app.config['DB_MANAGER'], 
                                 current_app.config['SECRET_KEY'])
        
        current_user = auth_manager.get_current_user()
        if not current_user:
            return jsonify({
                "success": False,
                "error": "需要登录"
            }), 401
        
        # 检查管理员权限
        user = auth_manager.db_manager.get_user_by_id(current_user["user_id"])
        if not user or not user["is_admin"]:
            return jsonify({
                "success": False,
                "error": "需要管理员权限"
            }), 403
        
        request.current_user = current_user
        return f(*args, **kwargs)
    
    return decorated_function 