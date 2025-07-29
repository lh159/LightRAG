import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
import secrets

class DatabaseManager:
    def __init__(self, db_path: str = "database/users.db"):
        self.db_path = db_path
        self.ensure_database_directory()
        self.init_database()
    
    def ensure_database_directory(self):
        """确保数据库目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    is_admin BOOLEAN DEFAULT 0,
                    profile_data TEXT,
                    settings TEXT
                )
            ''')
            
            # 会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 用户标签表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    dimension VARCHAR(50) NOT NULL,
                    tag_name VARCHAR(100) NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    evidence TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 用户知识库表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
    
    def create_user(self, username: str, password: str, email: str = None) -> Dict:
        """创建新用户"""
        try:
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, salt)
                    VALUES (?, ?, ?, ?)
                ''', (username, email, password_hash, salt))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "username": username
                }
        except sqlite3.IntegrityError:
            return {
                "success": False,
                "error": "用户名或邮箱已存在"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"创建用户失败: {str(e)}"
            }
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """用户认证"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, username, password_hash, salt, is_active
                    FROM users WHERE username = ?
                ''', (username,))
                
                result = cursor.fetchone()
                if not result:
                    return {"success": False, "error": "用户不存在"}
                
                user_id, username, stored_hash, salt, is_active = result
                
                if not is_active:
                    return {"success": False, "error": "账户已被禁用"}
                
                # 验证密码
                input_hash = self._hash_password(password, salt)
                if input_hash != stored_hash:
                    return {"success": False, "error": "密码错误"}
                
                # 更新最后登录时间
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (user_id,))
                conn.commit()
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "username": username
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"认证失败: {str(e)}"
            }
    
    def create_session(self, user_id: int, expires_hours: int = 24) -> str:
        """创建用户会话"""
        session_token = secrets.token_hex(32)
        expires_at = datetime.now().timestamp() + (expires_hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (user_id, session_token, expires_at)
                VALUES (?, ?, datetime(?, 'unixepoch'))
            ''', (user_id, session_token, expires_at))
            conn.commit()
        
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[int]:
        """验证会话并返回用户ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id FROM sessions 
                    WHERE session_token = ? 
                    AND expires_at > CURRENT_TIMESTAMP
                    AND is_active = 1
                ''', (session_token,))
                
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception:
            return None
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, username, email, created_at, last_login, 
                           is_active, is_admin, profile_data, settings
                    FROM users WHERE id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return {
                    "id": result[0],
                    "username": result[1],
                    "email": result[2],
                    "created_at": result[3],
                    "last_login": result[4],
                    "is_active": bool(result[5]),
                    "is_admin": bool(result[6]),
                    "profile_data": json.loads(result[7]) if result[7] else {},
                    "settings": json.loads(result[8]) if result[8] else {}
                }
        except Exception as e:
            print(f"获取用户失败: {e}")
            return None
    
    def update_user_profile(self, user_id: int, profile_data: Dict) -> bool:
        """更新用户资料"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET profile_data = ?
                    WHERE id = ?
                ''', (json.dumps(profile_data), user_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"更新用户资料失败: {e}")
            return False
    
    def get_user_knowledge(self, user_id: int) -> List[Dict]:
        """获取用户知识库数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT content, metadata, created_at, last_accessed, access_count
                    FROM user_knowledge WHERE user_id = ?
                    ORDER BY last_accessed DESC
                ''', (user_id,))
                
                results = cursor.fetchall()
                return [
                    {
                        "content": row[0],
                        "metadata": json.loads(row[1]) if row[1] else {},
                        "created_at": row[2],
                        "last_accessed": row[3],
                        "access_count": row[4]
                    }
                    for row in results
                ]
        except Exception as e:
            print(f"获取用户知识库失败: {e}")
            return []
    
    def backup_database(self) -> bool:
        """备份数据库"""
        try:
            import shutil
            from datetime import datetime
            
            backup_dir = "database/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{backup_dir}/users_backup_{timestamp}.db"
            
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"数据库备份失败: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sessions SET is_active = 0
                    WHERE expires_at < CURRENT_TIMESTAMP
                ''')
                affected_rows = cursor.rowcount
                conn.commit()
                return affected_rows
        except Exception as e:
            print(f"清理过期会话失败: {e}")
            return 0
    
    def _hash_password(self, password: str, salt: str) -> str:
        """密码哈希"""
        return hashlib.sha256((password + salt).encode()).hexdigest() 