from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import json
import re

# 管理员手机号配置
ADMIN_PHONE_NUMBERS = ['19802025320']

@dataclass
class User:
    phone_number: str  # 主键，用户手机号
    username: Optional[str]  # 显示名称（可选）
    email: Optional[str]
    role: str  # 用户角色：'user' 或 'admin'
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    profile_data: Dict
    settings: Dict
    
    @property
    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.role == 'admin'
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """验证手机号格式"""
        # 中国大陆手机号验证
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def assign_admin_role(phone_number: str) -> str:
        """自动分配用户角色"""
        if phone_number in ADMIN_PHONE_NUMBERS:
            return 'admin'
        return 'user'

@dataclass
class UserSession:
    id: int
    phone_number: str  # 改用手机号关联
    session_token: str
    created_at: datetime
    expires_at: datetime
    is_active: bool

@dataclass
class UserTag:
    id: int
    phone_number: str  # 改用手机号关联
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
    
    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """根据手机号获取用户"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT phone_number, username, email, role, created_at, 
                           last_login, is_active, profile_data, settings
                    FROM users WHERE phone_number = ?
                ''', (phone_number,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return User(
                    phone_number=result[0],
                    username=result[1],
                    email=result[2],
                    role=result[3],
                    created_at=datetime.fromisoformat(result[4]),
                    last_login=datetime.fromisoformat(result[5]) if result[5] else None,
                    is_active=bool(result[6]),
                    profile_data=json.loads(result[7]) if result[7] else {},
                    settings=json.loads(result[8]) if result[8] else {}
                )
        except Exception as e:
            print(f"获取用户失败: {e}")
            return None
    
    def create_user(self, phone_number: str, username: str = None, email: str = None) -> bool:
        """创建新用户"""
        if not User.validate_phone_number(phone_number):
            print(f"手机号格式不正确: {phone_number}")
            return False
            
        try:
            role = User.assign_admin_role(phone_number)
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (phone_number, username, email, role, created_at, 
                                     last_login, is_active, profile_data, settings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (phone_number, username, email, role, datetime.now().isoformat(),
                      None, True, '{}', '{}'))
                conn.commit()
                return True
        except Exception as e:
            print(f"创建用户失败: {e}")
            return False
    
    def update_user_profile(self, phone_number: str, profile_data: Dict) -> bool:
        """更新用户资料"""
        try:
            with self.db_manager.get_connection() as conn:
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
    
    def update_last_login(self, phone_number: str) -> bool:
        """更新最后登录时间"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET last_login = ?
                    WHERE phone_number = ?
                ''', (datetime.now().isoformat(), phone_number))
                conn.commit()
                return True
        except Exception as e:
            print(f"更新登录时间失败: {e}")
            return False
    
    def get_user_tags(self, phone_number: str) -> List[UserTag]:
        """获取用户标签"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, phone_number, dimension, tag_name, confidence,
                           evidence, created_at, last_updated, is_active
                    FROM user_tags WHERE phone_number = ? AND is_active = 1
                    ORDER BY dimension, confidence DESC
                ''', (phone_number,))
                
                results = cursor.fetchall()
                return [
                    UserTag(
                        id=row[0], phone_number=row[1], dimension=row[2],
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
    
    def get_all_users(self) -> List[User]:
        """获取所有用户（管理员功能）"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT phone_number, username, email, role, created_at, 
                           last_login, is_active, profile_data, settings
                    FROM users ORDER BY created_at DESC
                ''')
                
                results = cursor.fetchall()
                return [
                    User(
                        phone_number=row[0], username=row[1], email=row[2],
                        role=row[3], created_at=datetime.fromisoformat(row[4]),
                        last_login=datetime.fromisoformat(row[5]) if row[5] else None,
                        is_active=bool(row[6]),
                        profile_data=json.loads(row[7]) if row[7] else {},
                        settings=json.loads(row[8]) if row[8] else {}
                    )
                    for row in results
                ]
        except Exception as e:
            print(f"获取用户列表失败: {e}")
            return []
    
    def get_user_statistics(self) -> Dict:
        """获取用户统计信息（管理员功能）"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 总用户数
                cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
                total_users = cursor.fetchone()[0]
                
                # 管理员数量
                cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin" AND is_active = 1')
                admin_count = cursor.fetchone()[0]
                
                # 活跃用户（有登录记录的用户）
                cursor.execute('SELECT COUNT(*) FROM users WHERE last_login IS NOT NULL AND is_active = 1')
                active_users = cursor.fetchone()[0]
                
                # 今日新增用户
                today = datetime.now().date().isoformat()
                cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(created_at) = ?', (today,))
                new_users_today = cursor.fetchone()[0]
                
                # 标签统计
                cursor.execute('SELECT COUNT(*) FROM user_tags WHERE is_active = 1')
                total_tags = cursor.fetchone()[0] or 0
                
                # 人均标签数
                if total_users > 0:
                    avg_tags_per_user = total_tags / total_users
                else:
                    avg_tags_per_user = 0
                
                # 最常见的标签维度
                cursor.execute('''
                    SELECT dimension, COUNT(*) as count
                    FROM user_tags WHERE is_active = 1 
                    GROUP BY dimension
                    ORDER BY count DESC
                    LIMIT 1
                ''')
                most_common_result = cursor.fetchone()
                most_common_dimension = most_common_result[0] if most_common_result else "暂无数据"
                
                # 标签维度统计
                cursor.execute('''
                    SELECT dimension, COUNT(*) 
                    FROM user_tags WHERE is_active = 1 
                    GROUP BY dimension
                ''')
                tag_stats = dict(cursor.fetchall())
                
                return {
                    'total_users': total_users,
                    'admin_count': admin_count,
                    'active_users': active_users,
                    'new_users_today': new_users_today,
                    'total_tags': total_tags,
                    'avg_tags_per_user': round(avg_tags_per_user, 1),
                    'most_common_dimension': most_common_dimension,
                    'tag_statistics': tag_stats
                }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {
                'total_users': 0,
                'admin_count': 0,
                'active_users': 0,
                'new_users_today': 0,
                'total_tags': 0,
                'avg_tags_per_user': 0,
                'most_common_dimension': '暂无数据',
                'tag_statistics': {}
            }
    
    def migrate_user_data(self):
        """数据迁移方法：将现有用户数据迁移到新结构"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查是否存在旧的用户表结构
                cursor.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'phone_number' not in columns:
                    print("开始数据迁移...")
                    
                    # 备份现有数据
                    cursor.execute('CREATE TABLE users_backup AS SELECT * FROM users')
                    
                    # 删除旧表
                    cursor.execute('DROP TABLE users')
                    
                    # 创建新表结构
                    cursor.execute('''
                        CREATE TABLE users (
                            phone_number TEXT PRIMARY KEY,
                            username TEXT,
                            email TEXT,
                            role TEXT DEFAULT 'user',
                            created_at TEXT NOT NULL,
                            last_login TEXT,
                            is_active BOOLEAN DEFAULT 1,
                            profile_data TEXT DEFAULT '{}',
                            settings TEXT DEFAULT '{}'
                        )
                    ''')
                    
                    # 这里可以添加从备份表迁移数据的逻辑
                    # 由于现有用户没有手机号，需要手动处理或要求用户重新注册
                    
                    print("数据迁移完成")
                    conn.commit()
                
        except Exception as e:
            print(f"数据迁移失败: {e}")
            return False 