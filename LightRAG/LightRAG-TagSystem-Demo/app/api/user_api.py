from flask import Blueprint, request, jsonify, current_app
from app.auth.decorators import login_required, admin_required
from app.models.user_model import UserManager
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新用户资料"""
    try:
        data = request.json
        phone_number = request.current_user["phone_number"]
        
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        
        # 更新资料
        profile_data = data.get('profile_data', {})
        success = user_manager.update_user_profile(phone_number, profile_data)
        
        if success:
            return jsonify({
                "success": True,
                "message": "资料更新成功"
            })
        else:
            return jsonify({
                "success": False,
                "error": "资料更新失败"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"更新资料失败: {str(e)}"
        }), 500

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """获取用户资料"""
    try:
        phone_number = request.current_user["phone_number"]
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        
        user = user_manager.get_user_by_phone(phone_number)
        if not user:
            return jsonify({
                "success": False,
                "error": "用户不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "user": {
                "phone_number": user.phone_number,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "profile_data": user.profile_data
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取资料失败: {str(e)}"
        }), 500

@user_bp.route('/tags', methods=['GET'])
@login_required
def get_user_tags():
    """获取用户标签"""
    try:
        phone_number = request.current_user["phone_number"]
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        
        tags = user_manager.get_user_tags(phone_number)
        
        # 按维度分组
        tags_by_dimension = {}
        for tag in tags:
            if tag.dimension not in tags_by_dimension:
                tags_by_dimension[tag.dimension] = []
            tags_by_dimension[tag.dimension].append({
                "id": tag.id,
                "tag_name": tag.tag_name,
                "confidence": tag.confidence,
                "evidence": tag.evidence,
                "created_at": tag.created_at.isoformat(),
                "last_updated": tag.last_updated.isoformat()
            })
        
        return jsonify({
            "success": True,
            "tags": tags_by_dimension
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取标签失败: {str(e)}"
        }), 500

@user_bp.route('/data/export', methods=['GET'])
@login_required
def export_user_data():
    """导出用户数据"""
    try:
        phone_number = request.current_user["phone_number"]
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        
        # 获取用户信息
        user = user_manager.get_user_by_phone(phone_number)
        tags = user_manager.get_user_tags(phone_number)
        
        # 获取用户知识库数据
        knowledge_data = user_manager.db_manager.get_user_knowledge(phone_number)
        
        export_data = {
            "user_info": {
                "phone_number": user.phone_number,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            },
            "tags": [{
                "dimension": tag.dimension,
                "tag_name": tag.tag_name,
                "confidence": tag.confidence,
                "evidence": tag.evidence,
                "created_at": tag.created_at.isoformat()
            } for tag in tags],
            "knowledge": knowledge_data,
            "export_date": datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "data": export_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"导出数据失败: {str(e)}"
        }), 500

# 管理员专用接口
@user_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    """获取所有用户列表（管理员功能）"""
    try:
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        users = user_manager.get_all_users()
        
        users_data = []
        for user in users:
            users_data.append({
                "phone_number": user.phone_number,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "is_active": user.is_active
            })
        
        return jsonify({
            "success": True,
            "users": users_data,
            "total": len(users_data)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取用户列表失败: {str(e)}"
        }), 500

@user_bp.route('/admin/statistics', methods=['GET'])
@admin_required
def get_user_statistics():
    """获取用户统计信息（管理员功能）"""
    try:
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        stats = user_manager.get_user_statistics()
        
        return jsonify({
            "success": True,
            "statistics": stats
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取统计信息失败: {str(e)}"
        }), 500

@user_bp.route('/admin/tags/analysis', methods=['GET'])
@admin_required
def get_detailed_tag_analysis():
    """获取详细的标签分析（管理员功能）"""
    try:
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        
        # 获取分析类型参数
        analysis_type = request.args.get('type', 'comprehensive')
        
        if analysis_type == 'macro':
            # 使用新的宏观分析引擎
            from app.models.macro_analysis import MacroAnalysisEngine
            macro_engine = MacroAnalysisEngine(current_app.config['DB_MANAGER'])
            analysis = macro_engine.get_comprehensive_analysis()
        else:
            # 使用原有的详细分析
            analysis = user_manager.get_detailed_tag_analysis()
        
        return jsonify({
            "success": True,
            "analysis": analysis,
            "analysis_type": analysis_type
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取标签分析失败: {str(e)}"
        }), 500

@user_bp.route('/admin/users/<phone_number>/profile', methods=['GET'])
@admin_required
def get_user_profile_by_phone(phone_number):
    """获取指定用户的详细信息（管理员功能）"""
    try:
        user_manager = UserManager(current_app.config['DB_MANAGER'])
        
        # 获取用户基本信息
        user = user_manager.get_user_by_phone(phone_number)
        if not user:
            return jsonify({
                "success": False,
                "error": "用户不存在"
            }), 404
        
        # 获取用户标签
        tags = user_manager.get_user_tags(phone_number)
        
        # 按维度分组标签
        tags_by_dimension = {}
        for tag in tags:
            if tag.dimension not in tags_by_dimension:
                tags_by_dimension[tag.dimension] = []
            tags_by_dimension[tag.dimension].append({
                "id": tag.id,
                "tag_name": tag.tag_name,
                "confidence": tag.confidence,
                "evidence": tag.evidence,
                "created_at": tag.created_at.isoformat(),
                "last_updated": tag.last_updated.isoformat()
            })
        
        user_profile = {
            "phone_number": user.phone_number,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "is_active": user.is_active,
            "profile_data": user.profile_data,
            "tags": tags_by_dimension
        }
        
        return jsonify({
            "success": True,
            "user": user_profile
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取用户信息失败: {str(e)}"
        }), 500

@user_bp.route('/admin/analytics/detailed', methods=['GET'])
@admin_required
def get_detailed_analytics():
    """获取详细的数据分析（新版数据分析面板）"""
    try:
        db_manager = current_app.config['DB_MANAGER']
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        tag_filter = request.args.get('tag_filter', '')
        dimension_filter = request.args.get('dimension_filter', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. 用户详细列表（带标签信息）
            user_list_query = '''
                SELECT u.phone_number, u.username, u.created_at, u.last_login,
                       COUNT(DISTINCT ut.tag_name) as tag_count,
                       GROUP_CONCAT(DISTINCT ut.dimension) as dimensions,
                       AVG(ut.confidence) as avg_confidence
                FROM users u
                LEFT JOIN user_tags ut ON u.phone_number = ut.phone_number AND ut.is_active = 1
                WHERE u.is_active = 1
            '''
            
            params = []
            
            # 添加筛选条件
            if dimension_filter:
                user_list_query += ' AND ut.dimension LIKE ?'
                params.append(f'%{dimension_filter}%')
            
            if tag_filter:
                user_list_query += ' AND ut.tag_name LIKE ?'
                params.append(f'%{tag_filter}%')
            
            if date_from:
                user_list_query += ' AND u.created_at >= ?'
                params.append(date_from)
                
            if date_to:
                user_list_query += ' AND u.created_at <= ?'
                params.append(date_to + ' 23:59:59')
            
            user_list_query += '''
                GROUP BY u.phone_number, u.username, u.created_at, u.last_login
                ORDER BY u.created_at DESC
                LIMIT ? OFFSET ?
            '''
            params.extend([limit, (page - 1) * limit])
            
            cursor.execute(user_list_query, params)
            users_data = cursor.fetchall()
            
            # 获取每个用户的具体标签
            users_with_tags = []
            for user_data in users_data:
                user_id = user_data[0]
                
                # 获取用户的具体标签
                cursor.execute('''
                    SELECT dimension, tag_name, confidence, created_at, evidence
                    FROM user_tags 
                    WHERE phone_number = ? AND is_active = 1
                    ORDER BY confidence DESC, created_at DESC
                    LIMIT 10
                ''', (user_id,))
                
                user_tags = cursor.fetchall()
                
                users_with_tags.append({
                    'user_id': user_data[0],
                    'username': user_data[1] or user_data[0],
                    'created_at': user_data[2],
                    'last_login': user_data[3],
                    'tag_count': user_data[4] or 0,
                    'dimensions': user_data[5].split(',') if user_data[5] else [],
                    'avg_confidence': round(user_data[6] or 0, 2),
                    'tags': [
                        {
                            'dimension': tag[0],
                            'name': tag[1],
                            'confidence': round(tag[2], 2),
                            'created_at': tag[3],
                            'evidence': tag[4][:50] + '...' if len(tag[4]) > 50 else tag[4]
                        }
                        for tag in user_tags
                    ]
                })
            
            # 2. 标签维度分布统计
            cursor.execute('''
                SELECT dimension, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM user_tags 
                WHERE is_active = 1
                GROUP BY dimension
                ORDER BY count DESC
            ''')
            dimension_stats = [
                {
                    'dimension': row[0],
                    'count': row[1],
                    'avg_confidence': round(row[2], 2)
                }
                for row in cursor.fetchall()
            ]
            
            # 3. 热门标签TOP20
            cursor.execute('''
                SELECT tag_name, dimension, COUNT(*) as frequency, AVG(confidence) as avg_confidence
                FROM user_tags 
                WHERE is_active = 1
                GROUP BY tag_name, dimension
                ORDER BY frequency DESC, avg_confidence DESC
                LIMIT 20
            ''')
            popular_tags = [
                {
                    'name': row[0],
                    'dimension': row[1],
                    'frequency': row[2],
                    'avg_confidence': round(row[3], 2)
                }
                for row in cursor.fetchall()
            ]
            
            # 4. 用户活跃度分析
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(DISTINCT phone_number) as new_users,
                    COUNT(*) as new_tags
                FROM user_tags 
                WHERE is_active = 1 AND created_at >= date('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            ''')
            activity_trend = [
                {
                    'date': row[0],
                    'new_users': row[1],
                    'new_tags': row[2]
                }
                for row in cursor.fetchall()
            ]
            
            # 5. 用户分群分析
            cursor.execute('''
                SELECT 
                    CASE 
                        WHEN tag_count = 0 THEN '无标签用户'
                        WHEN tag_count <= 5 THEN '低活跃用户'
                        WHEN tag_count <= 15 THEN '中等活跃用户'
                        ELSE '高活跃用户'
                    END as user_segment,
                    COUNT(*) as count
                FROM (
                    SELECT u.phone_number, COUNT(ut.tag_name) as tag_count
                    FROM users u
                    LEFT JOIN user_tags ut ON u.phone_number = ut.phone_number AND ut.is_active = 1
                    WHERE u.is_active = 1
                    GROUP BY u.phone_number
                ) user_tag_counts
                GROUP BY user_segment
            ''')
            user_segments = [
                {
                    'segment': row[0],
                    'count': row[1]
                }
                for row in cursor.fetchall()
            ]
            
            # 6. 获取总数（用于分页）
            count_query = '''
                SELECT COUNT(DISTINCT u.phone_number)
                FROM users u
                LEFT JOIN user_tags ut ON u.phone_number = ut.phone_number AND ut.is_active = 1
                WHERE u.is_active = 1
            '''
            
            count_params = []
            if dimension_filter:
                count_query += ' AND ut.dimension LIKE ?'
                count_params.append(f'%{dimension_filter}%')
            
            if tag_filter:
                count_query += ' AND ut.tag_name LIKE ?'
                count_params.append(f'%{tag_filter}%')
            
            cursor.execute(count_query, count_params)
            total_users = cursor.fetchone()[0]
            
            return jsonify({
                "success": True,
                "data": {
                    "users": users_with_tags,
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total_users,
                        "total_pages": (total_users + limit - 1) // limit
                    },
                    "dimension_stats": dimension_stats,
                    "popular_tags": popular_tags,
                    "activity_trend": activity_trend,
                    "user_segments": user_segments
                }
            })
            
    except Exception as e:
        current_app.logger.error(f"获取详细分析数据失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500 