from flask import Blueprint, request, jsonify, session, current_app
from app.auth.auth_manager import AuthManager

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册（基于手机号）"""
    try:
        data = request.json
        phone_number = data.get('phone_number', '').strip()
        password = data.get('password', '')
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        
        auth_manager = AuthManager(
            current_app.config['DB_MANAGER'],
            current_app.config['SECRET_KEY']
        )
        
        result = auth_manager.register(phone_number, password, username, email)
        
        if result["success"]:
            # 设置session
            session['phone_number'] = result["phone_number"]
            session['username'] = result["username"]
            session['role'] = result["role"]
            
            return jsonify({
                "success": True,
                "message": "注册成功",
                "user": {
                    "phone_number": result["phone_number"],
                    "username": result["username"],
                    "role": result["role"],
                    "is_admin": result["is_admin"]
                },
                "token": result["jwt_token"]
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"注册失败: {str(e)}"
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录（基于手机号）"""
    try:
        data = request.json
        phone_number = data.get('phone_number', '').strip()
        password = data.get('password', '')
        
        auth_manager = AuthManager(
            current_app.config['DB_MANAGER'],
            current_app.config['SECRET_KEY']
        )
        
        result = auth_manager.login(phone_number, password)
        
        if result["success"]:
            # 设置session
            session['phone_number'] = result["phone_number"]
            session['username'] = result["username"]
            session['role'] = result["role"]
            
            return jsonify({
                "success": True,
                "message": "登录成功",
                "user": {
                    "phone_number": result["phone_number"],
                    "username": result["username"],
                    "role": result["role"],
                    "is_admin": result["is_admin"]
                },
                "token": result["jwt_token"]
            })
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"登录失败: {str(e)}"
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用户登出"""
    try:
        auth_manager = AuthManager(
            current_app.config['DB_MANAGER'],
            current_app.config['SECRET_KEY']
        )
        
        # 清除session
        session.clear()
        
        # 如果有token，也清除会话
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # 这里可以添加token黑名单逻辑
        
        return jsonify({
            "success": True,
            "message": "登出成功"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"登出失败: {str(e)}"
        }), 500

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """获取用户资料"""
    try:
        auth_manager = AuthManager(
            current_app.config['DB_MANAGER'],
            current_app.config['SECRET_KEY']
        )
        
        current_user = auth_manager.get_current_user()
        if not current_user:
            return jsonify({
                "success": False,
                "error": "需要登录"
            }), 401
        
        user = auth_manager.db_manager.get_user_by_phone(current_user["phone_number"])
        
        return jsonify({
            "success": True,
            "user": {
                "phone_number": user["phone_number"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "created_at": user["created_at"],
                "last_login": user["last_login"],
                "is_admin": user["is_admin"],
                "profile_data": user["profile_data"],
                "settings": user["settings"]
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取资料失败: {str(e)}"
        }), 500

@auth_bp.route('/quick-login', methods=['POST'])
def quick_login():
    """快速登录（仅手机号，无密码）"""
    try:
        data = request.json
        phone_number = data.get('phone_number', '').strip()
        
        auth_manager = AuthManager(
            current_app.config['DB_MANAGER'],
            current_app.config['SECRET_KEY']
        )
        
        # 验证手机号格式
        if not auth_manager._validate_phone_number(phone_number):
            return jsonify({
                "success": False,
                "error": "手机号格式不正确"
            }), 400
        
        # 检查用户是否存在，不存在则自动创建
        user = auth_manager.db_manager.get_user_by_phone(phone_number)
        if not user:
            # 自动注册用户
            create_result = auth_manager.db_manager.create_user(phone_number)
            if not create_result["success"]:
                return jsonify(create_result), 400
        
        # 登录（无密码验证）
        result = auth_manager.login(phone_number)
        
        if result["success"]:
            # 设置session
            session['phone_number'] = result["phone_number"]
            session['username'] = result["username"]
            session['role'] = result["role"]
            
            return jsonify({
                "success": True,
                "message": "登录成功",
                "user": {
                    "phone_number": result["phone_number"],
                    "username": result["username"],
                    "role": result["role"],
                    "is_admin": result["is_admin"]
                },
                "token": result["jwt_token"]
            })
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"快速登录失败: {str(e)}"
        }), 500 