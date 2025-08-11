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
    
    def get_detailed_tag_analysis(self) -> Dict:
        """获取详细的标签分析（管理员功能）"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取所有标签的详细信息
                cursor.execute('''
                    SELECT u.phone_number, u.username, u.role,
                           t.dimension, t.tag_name, t.confidence, t.evidence,
                           t.created_at, t.last_updated
                    FROM user_tags t
                    JOIN users u ON t.phone_number = u.phone_number
                    WHERE t.is_active = 1
                    ORDER BY t.dimension, t.confidence DESC
                ''')
                
                raw_tags = cursor.fetchall()
                
                if not raw_tags:
                    return {
                        'total_tags': 0,
                        'dimensions': {},
                        'user_profiles': {},
                        'tag_cloud': [],
                        'confidence_distribution': {}
                    }
                
                # 按维度分组
                dimensions = {}
                user_profiles = {}
                tag_cloud = {}
                confidence_ranges = {'高置信度(>0.8)': 0, '中置信度(0.5-0.8)': 0, '低置信度(<0.5)': 0}
                
                for phone, username, role, dimension, tag_name, confidence, evidence, created_at, updated_at in raw_tags:
                    # 维度分析
                    if dimension not in dimensions:
                        dimensions[dimension] = {
                            'name': dimension,
                            'total_tags': 0,
                            'avg_confidence': 0,
                            'tags': [],
                            'users': set()
                        }
                    
                    dimensions[dimension]['total_tags'] += 1
                    dimensions[dimension]['tags'].append({
                        'name': tag_name,
                        'confidence': confidence,
                        'user': phone,
                        'username': username or phone,
                        'evidence': evidence[:100] + '...' if len(evidence) > 100 else evidence,
                        'created_at': created_at,
                        'updated_at': updated_at
                    })
                    dimensions[dimension]['users'].add(phone)
                    
                    # 用户画像分析
                    if phone not in user_profiles:
                        user_profiles[phone] = {
                            'phone': phone,
                            'username': username or '未设置',
                            'role': role,
                            'tags_by_dimension': {},
                            'total_tags': 0,
                            'avg_confidence': 0
                        }
                    
                    if dimension not in user_profiles[phone]['tags_by_dimension']:
                        user_profiles[phone]['tags_by_dimension'][dimension] = []
                    
                    user_profiles[phone]['tags_by_dimension'][dimension].append({
                        'name': tag_name,
                        'confidence': confidence,
                        'evidence': evidence[:50] + '...' if len(evidence) > 50 else evidence
                    })
                    user_profiles[phone]['total_tags'] += 1
                    
                    # 标签云数据
                    if tag_name not in tag_cloud:
                        tag_cloud[tag_name] = 0
                    tag_cloud[tag_name] += 1
                    
                    # 置信度分布
                    if confidence > 0.8:
                        confidence_ranges['高置信度(>0.8)'] += 1
                    elif confidence >= 0.5:
                        confidence_ranges['中置信度(0.5-0.8)'] += 1
                    else:
                        confidence_ranges['低置信度(<0.5)'] += 1
                
                # 计算平均置信度
                for dim_data in dimensions.values():
                    if dim_data['total_tags'] > 0:
                        dim_data['avg_confidence'] = sum(tag['confidence'] for tag in dim_data['tags']) / dim_data['total_tags']
                        dim_data['users'] = len(dim_data['users'])
                    else:
                        dim_data['avg_confidence'] = 0
                        dim_data['users'] = 0
                
                for user_data in user_profiles.values():
                    if user_data['total_tags'] > 0:
                        total_conf = sum(
                            tag['confidence'] 
                            for dim_tags in user_data['tags_by_dimension'].values() 
                            for tag in dim_tags
                        )
                        user_data['avg_confidence'] = total_conf / user_data['total_tags']
                    else:
                        user_data['avg_confidence'] = 0
                
                # 转换标签云为列表
                tag_cloud_list = [{'name': name, 'count': count} for name, count in sorted(tag_cloud.items(), key=lambda x: x[1], reverse=True)]
                
                return {
                    'total_tags': len(raw_tags),
                    'total_users': len(user_profiles),
                    'dimensions': dimensions,
                    'user_profiles': user_profiles,
                    'tag_cloud': tag_cloud_list[:20],  # 只返回前20个最常见的标签
                    'confidence_distribution': confidence_ranges
                }
                
        except Exception as e:
            print(f"获取详细标签分析失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'total_tags': 0,
                'dimensions': {},
                'user_profiles': {},
                'tag_cloud': [],
                'confidence_distribution': {}
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