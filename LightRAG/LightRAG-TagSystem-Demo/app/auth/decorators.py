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
        if not current_user.get("is_admin", False):
            return jsonify({
                "success": False,
                "error": "需要管理员权限"
            }), 403
        
        request.current_user = current_user
        return f(*args, **kwargs)
    
    return decorated_function

def phone_required(f):
    """手机号验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求中获取手机号参数
        phone_number = request.json.get('phone_number') if request.json else request.args.get('phone_number')
        
        if not phone_number:
            return jsonify({
                "success": False,
                "error": "缺少手机号参数"
            }), 400
        
        # 验证手机号格式
        import re
        pattern = r'^1[3-9]\d{9}$'
        if not re.match(pattern, phone_number):
            return jsonify({
                "success": False,
                "error": "手机号格式不正确"
            }), 400
        
        # 将手机号添加到请求上下文
        request.phone_number = phone_number
        return f(*args, **kwargs)
    
    return decorated_function 