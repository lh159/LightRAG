from flask import Blueprint, request, jsonify, session, current_app
from app.auth.auth_manager import AuthManager

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        auth_manager = AuthManager(
            current_app.config['DB_MANAGER'],
            current_app.config['SECRET_KEY']
        )
        
        result = auth_manager.register(username, password, email)
        
        if result["success"]:
            # 设置session
            session['user_id'] = result["user_id"]
            session['username'] = result["username"]
            
            return jsonify({
                "success": True,
                "message": "注册成功",
                "user": {
                    "id": result["user_id"],
                    "username": result["username"]
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
    """用户登录"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        auth_manager = AuthManager(
            current_app.config['DB_MANAGER'],
            current_app.config['SECRET_KEY']
        )
        
        result = auth_manager.login(username, password)
        
        if result["success"]:
            # 设置session
            session['user_id'] = result["user_id"]
            session['username'] = result["username"]
            
            return jsonify({
                "success": True,
                "message": "登录成功",
                "user": {
                    "id": result["user_id"],
                    "username": result["username"]
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
        
        user = auth_manager.db_manager.get_user_by_id(current_user["user_id"])
        
        return jsonify({
            "success": True,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
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