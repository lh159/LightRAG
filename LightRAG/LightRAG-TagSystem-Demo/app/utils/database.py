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
            
            # 检查是否需要数据迁移
            self._check_and_migrate_schema(cursor)
            
            # 用户表（新结构：以手机号为主键）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    phone_number VARCHAR(11) PRIMARY KEY,
                    username VARCHAR(50),
                    email VARCHAR(100),
                    password_hash VARCHAR(255),
                    salt VARCHAR(255),
                    role VARCHAR(20) DEFAULT 'user',
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    profile_data TEXT DEFAULT '{}',
                    settings TEXT DEFAULT '{}'
                )
            ''')
            
            # 会话表（关联手机号）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number VARCHAR(11) NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (phone_number) REFERENCES users (phone_number)
                )
            ''')
            
            # 用户标签表（关联手机号）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number VARCHAR(11) NOT NULL,
                    dimension VARCHAR(50) NOT NULL,
                    tag_name VARCHAR(100) NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    evidence TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (phone_number) REFERENCES users (phone_number)
                )
            ''')
            
            # 用户知识库表（关联手机号）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number VARCHAR(11) NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    FOREIGN KEY (phone_number) REFERENCES users (phone_number)
                )
            ''')
            
            conn.commit()
    
    def create_user(self, phone_number: str, password: str = None, username: str = None, email: str = None) -> Dict:
        """创建新用户"""
        try:
            # 验证手机号格式
            if not self._validate_phone_number(phone_number):
                return {
                    "success": False,
                    "error": "手机号格式不正确"
                }
            
            # 自动分配角色
            role = self._assign_admin_role(phone_number)
            
            # 如果提供了密码，则创建密码哈希
            password_hash = None
            salt = None
            if password:
                salt = secrets.token_hex(16)
                password_hash = self._hash_password(password, salt)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (phone_number, username, email, password_hash, salt, role, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (phone_number, username, email, password_hash, salt, role, datetime.now().isoformat()))
                
                conn.commit()
                
                return {
                    "success": True,
                    "phone_number": phone_number,
                    "username": username,
                    "role": role
                }
        except sqlite3.IntegrityError:
            return {
                "success": False,
                "error": "手机号已存在"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"创建用户失败: {str(e)}"
            }
    
    def authenticate_user(self, phone_number: str, password: str = None) -> Dict:
        """用户认证"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT phone_number, username, password_hash, salt, is_active, role
                    FROM users WHERE phone_number = ?
                ''', (phone_number,))
                
                result = cursor.fetchone()
                if not result:
                    return {"success": False, "error": "用户不存在"}
                
                phone_number, username, stored_hash, salt, is_active, role = result
                
                if not is_active:
                    return {"success": False, "error": "账户已被禁用"}
                
                # 如果设置了密码，则验证密码
                if stored_hash and password:
                    input_hash = self._hash_password(password, salt)
                    if input_hash != stored_hash:
                        return {"success": False, "error": "密码错误"}
                elif stored_hash and not password:
                    return {"success": False, "error": "需要密码"}
                
                # 更新最后登录时间
                cursor.execute('''
                    UPDATE users SET last_login = ?
                    WHERE phone_number = ?
                ''', (datetime.now().isoformat(), phone_number))
                conn.commit()
                
                return {
                    "success": True,
                    "phone_number": phone_number,
                    "username": username,
                    "role": role
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"认证失败: {str(e)}"
            }
    
    def create_session(self, phone_number: str, expires_hours: int = 24) -> str:
        """创建用户会话"""
        session_token = secrets.token_hex(32)
        expires_at = datetime.now().timestamp() + (expires_hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (phone_number, session_token, expires_at)
                VALUES (?, ?, datetime(?, 'unixepoch'))
            ''', (phone_number, session_token, expires_at))
            conn.commit()
        
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[str]:
        """验证会话并返回手机号"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT phone_number FROM sessions 
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
    
    def get_user_by_phone(self, phone_number: str) -> Optional[Dict]:
        """根据手机号获取用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT phone_number, username, email, role, created_at, last_login, 
                           is_active, profile_data, settings
                    FROM users WHERE phone_number = ?
                ''', (phone_number,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return {
                    "phone_number": result[0],
                    "username": result[1],
                    "email": result[2],
                    "role": result[3],
                    "created_at": result[4],
                    "last_login": result[5],
                    "is_active": bool(result[6]),
                    "is_admin": result[3] == 'admin',
                    "profile_data": json.loads(result[7]) if result[7] else {},
                    "settings": json.loads(result[8]) if result[8] else {}
                }
        except Exception as e:
            print(f"获取用户失败: {e}")
            return None
    
    def update_user_profile(self, phone_number: str, profile_data: Dict) -> bool:
        """更新用户资料"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET profile_data = ?
                    WHERE phone_number = ?
                ''', (json.dumps(profile_data), phone_number))
                conn.commit()
                return True
        except Exception as e:
            print(f"更新用户资料失败: {e}")
            return False
    
    def get_user_knowledge(self, phone_number: str) -> List[Dict]:
        """获取用户知识库数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT content, metadata, created_at, last_accessed, access_count
                    FROM user_knowledge WHERE phone_number = ?
                    ORDER BY last_accessed DESC
                ''', (phone_number,))
                
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
    
    def get_all_users(self) -> List[Dict]:
        """获取所有用户（管理员功能）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT phone_number, username, email, role, created_at, last_login, 
                           is_active, profile_data, settings
                    FROM users ORDER BY created_at DESC
                ''')
                
                results = cursor.fetchall()
                return [
                    {
                        "phone_number": row[0],
                        "username": row[1],
                        "email": row[2],
                        "role": row[3],
                        "created_at": row[4],
                        "last_login": row[5],
                        "is_active": bool(row[6]),
                        "is_admin": row[3] == 'admin',
                        "profile_data": json.loads(row[7]) if row[7] else {},
                        "settings": json.loads(row[8]) if row[8] else {}
                    }
                    for row in results
                ]
        except Exception as e:
            print(f"获取用户列表失败: {e}")
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
    
    def _validate_phone_number(self, phone: str) -> bool:
        """验证手机号格式"""
        import re
        # 中国大陆手机号验证
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, phone) is not None
    
    def _assign_admin_role(self, phone_number: str) -> str:
        """自动分配用户角色"""
        # 管理员手机号配置
        ADMIN_PHONE_NUMBERS = ['19802025320']
        if phone_number in ADMIN_PHONE_NUMBERS:
            return 'admin'
        return 'user'
    
    def _check_and_migrate_schema(self, cursor):
        """检查并迁移数据库结构"""
        try:
            # 检查是否存在旧的用户表结构
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if columns and 'phone_number' not in columns:
                print("检测到旧的用户表结构，开始数据迁移...")
                
                # 备份现有数据
                cursor.execute('CREATE TABLE IF NOT EXISTS users_backup AS SELECT * FROM users')
                
                # 删除旧表
                cursor.execute('DROP TABLE IF EXISTS users')
                
                # 删除相关的外键表
                cursor.execute('DROP TABLE IF EXISTS sessions')
                cursor.execute('DROP TABLE IF EXISTS user_tags')
                cursor.execute('DROP TABLE IF EXISTS user_knowledge')
                
                print("旧表结构已清理，将创建新的表结构")
                
        except Exception as e:
            print(f"数据迁移检查失败: {e}")
    
    def get_user_statistics(self) -> Dict:
        """获取用户统计信息（管理员功能）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 总用户数
                cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
                total_users = cursor.fetchone()[0]
                
                # 管理员数量
                cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin" AND is_active = 1')
                admin_count = cursor.fetchone()[0]
                
                # 今日活跃用户
                today = datetime.now().date().isoformat()
                cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(last_login) = ?', (today,))
                daily_active = cursor.fetchone()[0] if cursor.fetchone() else 0
                
                # 标签统计
                cursor.execute('''
                    SELECT dimension, COUNT(*) 
                    FROM user_tags WHERE is_active = 1 
                    GROUP BY dimension
                ''')
                tag_stats = dict(cursor.fetchall())
                
                return {
                    'total_users': total_users,
                    'admin_count': admin_count,
                    'daily_active': daily_active,
                    'tag_statistics': tag_stats
                }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {
                'total_users': 0,
                'admin_count': 0,
                'daily_active': 0,
                'tag_statistics': {}
            } 