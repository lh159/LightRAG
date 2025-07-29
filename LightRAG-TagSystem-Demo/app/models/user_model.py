from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import json

@dataclass
class User:
    id: int
    username: str
    email: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    is_admin: bool
    profile_data: Dict
    settings: Dict

@dataclass
class UserSession:
    id: int
    user_id: int
    session_token: str
    created_at: datetime
    expires_at: datetime
    is_active: bool

@dataclass
class UserTag:
    id: int
    user_id: int
    dimension: str
    tag_name: str
    confidence: float
    evidence: str
    created_at: datetime
    last_updated: datetime
    is_active: bool

class UserManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, username, email, created_at, last_login, 
                           is_active, is_admin, profile_data, settings
                    FROM users WHERE id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return User(
                    id=result[0],
                    username=result[1],
                    email=result[2],
                    created_at=datetime.fromisoformat(result[3]),
                    last_login=datetime.fromisoformat(result[4]) if result[4] else None,
                    is_active=bool(result[5]),
                    is_admin=bool(result[6]),
                    profile_data=json.loads(result[7]) if result[7] else {},
                    settings=json.loads(result[8]) if result[8] else {}
                )
        except Exception as e:
            print(f"获取用户失败: {e}")
            return None
    
    def update_user_profile(self, user_id: int, profile_data: Dict) -> bool:
        """更新用户资料"""
        try:
            with self.db_manager.get_connection() as conn:
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
    
    def get_user_tags(self, user_id: int) -> List[UserTag]:
        """获取用户标签"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, user_id, dimension, tag_name, confidence,
                           evidence, created_at, last_updated, is_active
                    FROM user_tags WHERE user_id = ? AND is_active = 1
                    ORDER BY dimension, confidence DESC
                ''', (user_id,))
                
                results = cursor.fetchall()
                return [
                    UserTag(
                        id=row[0], user_id=row[1], dimension=row[2],
                        tag_name=row[3], confidence=row[4], evidence=row[5],
                        created_at=datetime.fromisoformat(row[6]),
                        last_updated=datetime.fromisoformat(row[7]),
                        is_active=bool(row[8])
                    )
                    for row in results
                ]
        except Exception as e:
            print(f"获取用户标签失败: {e}")
            return [] 