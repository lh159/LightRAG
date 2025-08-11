import jwt
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict
from flask import request, session

class AuthManager:
    def __init__(self, db_manager, secret_key: str):
        self.db_manager = db_manager
        self.secret_key = secret_key
    
    def login(self, phone_number: str, password: str = None) -> Dict:
        """用户登录（基于手机号）"""
        # 验证手机号格式
        if not self._validate_phone_number(phone_number):
            return {"success": False, "error": "手机号格式不正确"}
        
        # 验证用户凭据
        auth_result = self.db_manager.authenticate_user(phone_number, password)
        
        if not auth_result["success"]:
            return auth_result
        
        phone_number = auth_result["phone_number"]
        username = auth_result["username"]
        role = auth_result["role"]
        
        # 创建会话
        session_token = self.db_manager.create_session(phone_number)
        
        # 生成JWT令牌
        jwt_token = self._generate_jwt_token(phone_number, username, role)
        
        return {
            "success": True,
            "phone_number": phone_number,
            "username": username,
            "role": role,
            "is_admin": role == 'admin',
            "session_token": session_token,
            "jwt_token": jwt_token
        }
    
    def register(self, phone_number: str, password: str = None, username: str = None, email: str = None) -> Dict:
        """用户注册（基于手机号）"""
        # 验证输入
        validation_result = self._validate_registration_input(phone_number, password, username, email)
        if not validation_result["success"]:
            return validation_result
        
        # 创建用户
        create_result = self.db_manager.create_user(phone_number, password, username, email)
        
        if create_result["success"]:
            # 自动登录
            return self.login(phone_number, password)
        else:
            return create_result
    
    def logout(self, session_token: str) -> bool:
        """用户登出"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sessions SET is_active = 0
                    WHERE session_token = ?
                ''', (session_token,))
                conn.commit()
                return True
        except Exception:
            return False
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            phone_number = payload.get("phone_number")
            username = payload.get("username")
            role = payload.get("role")
            exp = payload.get("exp")
            
            if not phone_number or not exp:
                return None
            
            # 检查令牌是否过期
            if datetime.utcnow().timestamp() > exp:
                return None
            
            return {
                "phone_number": phone_number,
                "username": username,
                "role": role,
                "is_admin": role == 'admin'
            }
        except jwt.InvalidTokenError:
            return None
    
    def get_current_user(self) -> Optional[Dict]:
        """获取当前用户"""
        # 从请求头获取令牌
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            return self.validate_token(token)
        
        # 从session获取
        if "phone_number" in session:
            phone_number = session["phone_number"]
            # 验证session中的用户是否仍然存在且有效
            user = self.db_manager.get_user_by_phone(phone_number)
            if user and user.get("is_active", True):
                return {
                    "phone_number": user["phone_number"],
                    "username": user["username"],
                    "role": user["role"],
                    "is_admin": user["role"] == "admin"
                }
            else:
                # 用户不存在或已被禁用，清除session
                session.clear()
        
        return None
    
    def require_admin(self) -> bool:
        """检查当前用户是否为管理员"""
        current_user = self.get_current_user()
        return current_user and current_user.get("is_admin", False)
    
    def _generate_jwt_token(self, phone_number: str, username: str, role: str) -> str:
        """生成JWT令牌"""
        payload = {
            "phone_number": phone_number,
            "username": username,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def _validate_phone_number(self, phone: str) -> bool:
        """验证手机号格式"""
        # 中国大陆手机号验证
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, phone) is not None
    
    def _validate_registration_input(self, phone_number: str, password: str = None, username: str = None, email: str = None) -> Dict:
        """验证注册输入"""
        if not self._validate_phone_number(phone_number):
            return {"success": False, "error": "手机号格式不正确"}
        
        if password and len(password) < 6:
            return {"success": False, "error": "密码至少需要6个字符"}
        
        if username and len(username) < 2:
            return {"success": False, "error": "用户名至少需要2个字符"}
        
        if email and "@" not in email:
            return {"success": False, "error": "邮箱格式不正确"}
        
        return {"success": True} 