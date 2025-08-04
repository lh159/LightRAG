import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from flask import request, session

class AuthManager:
    def __init__(self, db_manager, secret_key: str):
        self.db_manager = db_manager
        self.secret_key = secret_key
    
    def login(self, username: str, password: str) -> Dict:
        """用户登录"""
        # 验证用户凭据
        auth_result = self.db_manager.authenticate_user(username, password)
        
        if not auth_result["success"]:
            return auth_result
        
        user_id = auth_result["user_id"]
        
        # 创建会话
        session_token = self.db_manager.create_session(user_id)
        
        # 生成JWT令牌
        jwt_token = self._generate_jwt_token(user_id, username)
        
        return {
            "success": True,
            "user_id": user_id,
            "username": username,
            "session_token": session_token,
            "jwt_token": jwt_token
        }
    
    def register(self, username: str, password: str, email: str = None) -> Dict:
        """用户注册"""
        # 验证输入
        validation_result = self._validate_registration_input(username, password, email)
        if not validation_result["success"]:
            return validation_result
        
        # 创建用户
        create_result = self.db_manager.create_user(username, password, email)
        
        if create_result["success"]:
            # 自动登录
            return self.login(username, password)
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
            user_id = payload.get("user_id")
            username = payload.get("username")
            exp = payload.get("exp")
            
            if not user_id or not username or not exp:
                return None
            
            # 检查令牌是否过期
            if datetime.utcnow().timestamp() > exp:
                return None
            
            return {
                "user_id": user_id,
                "username": username
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
        if "user_id" in session:
            user_id = session["user_id"]
            user = self.db_manager.get_user_by_id(user_id)
            if user:
                return {
                    "user_id": user["id"],
                    "username": user["username"]
                }
        
        return None
    
    def _generate_jwt_token(self, user_id: int, username: str) -> str:
        """生成JWT令牌"""
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def _validate_registration_input(self, username: str, password: str, email: str = None) -> Dict:
        """验证注册输入"""
        if not username or len(username) < 3:
            return {"success": False, "error": "用户名至少需要3个字符"}
        
        if not password or len(password) < 6:
            return {"success": False, "error": "密码至少需要6个字符"}
        
        if email and "@" not in email:
            return {"success": False, "error": "邮箱格式不正确"}
        
        return {"success": True} 