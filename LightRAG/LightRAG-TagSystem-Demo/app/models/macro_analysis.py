#!/usr/bin/env python3
"""
宏观用户画像分析模块
专门为管理员提供深度的用户群体洞察分析
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import math
from collections import defaultdict, Counter
from dataclasses import dataclass
import statistics

@dataclass
class InterestCluster:
    """兴趣聚类"""
    name: str
    tags: List[str]
    user_count: int
    avg_confidence: float
    growth_trend: str  # 'rising', 'stable', 'declining'
    dominance_score: float  # 在用户群体中的主导程度

@dataclass
class DemographicInsight:
    """人口统计学洞察"""
    category: str
    distribution: Dict[str, int]
    dominant_segment: str
    diversity_index: float  # 多样性指数
    correlation_with_interests: Dict[str, float]

@dataclass
class EmotionalPattern:
    """情感模式"""
    pattern_name: str
    emotion_sequence: List[str]
    frequency: int
    avg_duration: float
    trigger_contexts: List[str]

class MacroAnalysisEngine:
    """宏观分析引擎"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_comprehensive_analysis(self) -> Dict:
        """获取综合宏观分析"""
        try:
            # 获取基础数据
            raw_data = self._get_raw_tag_data()
            if not raw_data:
                return self._empty_analysis()
            
            # 三大维度分析
            interest_analysis = self._analyze_interests(raw_data)
            demographic_analysis = self._analyze_demographics(raw_data)
            emotional_analysis = self._analyze_emotions(raw_data)
            
            # 跨维度关联分析
            cross_dimension_insights = self._analyze_cross_dimensions(raw_data)
            
            # 用户群体细分
            user_segments = self._segment_users(raw_data)
            
            # 趋势分析
            trend_analysis = self._analyze_trends(raw_data)
            
            return {
                'analysis_timestamp': datetime.now().isoformat(),
                'total_users': len(set(tag['phone'] for tag in raw_data)),
                'total_tags': len(raw_data),
                'analysis_period': self._get_analysis_period(),
                
                # 三大维度深度分析
                'interest_analysis': interest_analysis,
                'demographic_analysis': demographic_analysis,
                'emotional_analysis': emotional_analysis,
                
                # 综合洞察
                'cross_dimension_insights': cross_dimension_insights,
                'user_segments': user_segments,
                'trend_analysis': trend_analysis,
                
                # 业务建议
                'business_recommendations': self._generate_recommendations(
                    interest_analysis, demographic_analysis, emotional_analysis
                )
            }
            
        except Exception as e:
            print(f"宏观分析失败: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_analysis()
    
    def _get_raw_tag_data(self) -> List[Dict]:
        """获取原始标签数据"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.phone_number, u.username, u.role, u.created_at,
                       t.dimension, t.tag_name, t.confidence, t.evidence,
                       t.created_at as tag_created, t.last_updated
                FROM user_tags t
                JOIN users u ON t.phone_number = u.phone_number
                WHERE t.is_active = 1
                ORDER BY t.created_at DESC
            ''')
            
            rows = cursor.fetchall()
            return [
                {
                    'phone': row[0],
                    'username': row[1] or row[0],
                    'role': row[2],
                    'user_created': row[3],
                    'dimension': row[4],
                    'tag_name': row[5],
                    'confidence': row[6],
                    'evidence': row[7],
                    'tag_created': row[8],
                    'last_updated': row[9]
                }
                for row in rows
            ]
    
    def _analyze_interests(self, raw_data: List[Dict]) -> Dict:
        """兴趣爱好深度分析（重点）"""
        interest_tags = [tag for tag in raw_data if tag['dimension'] == '兴趣爱好标签']
        
        if not interest_tags:
            return {'clusters': [], 'insights': [], 'recommendations': []}
        
        # 1. 兴趣聚类分析
        clusters = self._cluster_interests(interest_tags)
        
        # 2. 兴趣多样性分析
        diversity_metrics = self._calculate_interest_diversity(interest_tags)
        
        # 3. 兴趣强度分析
        intensity_analysis = self._analyze_interest_intensity(interest_tags)
        
        # 4. 兴趣演化趋势
        evolution_trends = self._analyze_interest_evolution(interest_tags)
        
        # 5. 兴趣相关性分析
        correlation_matrix = self._analyze_interest_correlations(interest_tags)
        
        # 6. 潜在兴趣挖掘
        potential_interests = self._discover_potential_interests(interest_tags)
        
        # 7. 兴趣群体画像
        interest_personas = self._create_interest_personas(interest_tags)
        
        return {
            'summary': {
                'total_interest_tags': len(interest_tags),
                'unique_interests': len(set(tag['tag_name'] for tag in interest_tags)),
                'avg_interests_per_user': len(interest_tags) / len(set(tag['phone'] for tag in interest_tags)),
                'dominant_interest_category': self._get_dominant_interest_category(interest_tags)
            },
            'clusters': clusters,
            'diversity_metrics': diversity_metrics,
            'intensity_analysis': intensity_analysis,
            'evolution_trends': evolution_trends,
            'correlation_matrix': correlation_matrix,
            'potential_interests': potential_interests,
            'interest_personas': interest_personas,
            'insights': self._generate_interest_insights(interest_tags, clusters),
            'recommendations': self._generate_interest_recommendations(clusters, intensity_analysis)
        }
    
    def _analyze_demographics(self, raw_data: List[Dict]) -> Dict:
        """基本人口统计学标签分析"""
        demo_tags = [tag for tag in raw_data if tag['dimension'] == '基本人口统计学标签']
        
        if not demo_tags:
            return {'distribution': {}, 'insights': [], 'recommendations': []}
        
        # 1. 年龄分布分析
        age_analysis = self._analyze_age_distribution(demo_tags)
        
        # 2. 性别分布分析
        gender_analysis = self._analyze_gender_distribution(demo_tags)
        
        # 3. 地域分布分析
        location_analysis = self._analyze_location_distribution(demo_tags)
        
        # 4. 人口统计学多样性指数
        diversity_index = self._calculate_demographic_diversity(demo_tags)
        
        # 5. 人口统计学与兴趣的关联
        demo_interest_correlation = self._analyze_demo_interest_correlation(raw_data)
        
        return {
            'summary': {
                'total_users_with_demographics': len(set(tag['phone'] for tag in demo_tags)),
                'demographic_completeness': self._calculate_demographic_completeness(demo_tags),
                'diversity_index': diversity_index
            },
            'age_analysis': age_analysis,
            'gender_analysis': gender_analysis,
            'location_analysis': location_analysis,
            'demo_interest_correlation': demo_interest_correlation,
            'insights': self._generate_demographic_insights(demo_tags, age_analysis, gender_analysis),
            'recommendations': self._generate_demographic_recommendations(demo_tags)
        }
    
    def _analyze_emotions(self, raw_data: List[Dict]) -> Dict:
        """情绪与情感状态标签分析"""
        emotion_tags = [tag for tag in raw_data if tag['dimension'] == '情绪与情感状态标签']
        
        if not emotion_tags:
            return {'patterns': [], 'insights': [], 'recommendations': []}
        
        # 1. 情绪分布分析
        emotion_distribution = self._analyze_emotion_distribution(emotion_tags)
        
        # 2. 情绪模式识别
        emotion_patterns = self._identify_emotion_patterns(emotion_tags)
        
        # 3. 情绪稳定性分析
        stability_analysis = self._analyze_emotion_stability(emotion_tags)
        
        # 4. 情绪触发因子分析
        trigger_analysis = self._analyze_emotion_triggers(emotion_tags)
        
        # 5. 情绪健康指数
        health_index = self._calculate_emotional_health_index(emotion_tags)
        
        return {
            'summary': {
                'total_emotion_records': len(emotion_tags),
                'users_with_emotions': len(set(tag['phone'] for tag in emotion_tags)),
                'emotional_health_score': health_index,
                'most_common_emotion': self._get_most_common_emotion(emotion_tags)
            },
            'distribution': emotion_distribution,
            'patterns': emotion_patterns,
            'stability_analysis': stability_analysis,
            'trigger_analysis': trigger_analysis,
            'insights': self._generate_emotional_insights(emotion_tags, emotion_patterns),
            'recommendations': self._generate_emotional_recommendations(emotion_tags, health_index)
        }
    
    def _cluster_interests(self, interest_tags: List[Dict]) -> List[Dict]:
        """兴趣聚类分析"""
        # 按标签名称分组
        tag_groups = defaultdict(list)
        for tag in interest_tags:
            tag_groups[tag['tag_name']].append(tag)
        
        clusters = []
        for tag_name, tags in tag_groups.items():
            if len(tags) >= 2:  # 至少2个用户有此兴趣才形成聚类
                cluster = {
                    'name': tag_name,
                    'user_count': len(set(tag['phone'] for tag in tags)),
                    'avg_confidence': statistics.mean(tag['confidence'] for tag in tags),
                    'total_mentions': len(tags),
                    'evidence_keywords': self._extract_evidence_keywords(tags),
                    'user_diversity': self._calculate_cluster_diversity(tags)
                }
                clusters.append(cluster)
        
        # 按用户数量排序
        return sorted(clusters, key=lambda x: x['user_count'], reverse=True)
    
    def _calculate_interest_diversity(self, interest_tags: List[Dict]) -> Dict:
        """计算兴趣多样性"""
        users = defaultdict(set)
        for tag in interest_tags:
            users[tag['phone']].add(tag['tag_name'])
        
        if not users:
            return {'shannon_diversity': 0, 'avg_interests_per_user': 0}
        
        # Shannon多样性指数
        all_interests = [interest for user_interests in users.values() for interest in user_interests]
        interest_counts = Counter(all_interests)
        total = len(all_interests)
        
        shannon_diversity = -sum((count/total) * math.log2(count/total) for count in interest_counts.values())
        
        return {
            'shannon_diversity': round(shannon_diversity, 3),
            'avg_interests_per_user': round(statistics.mean(len(interests) for interests in users.values()), 2),
            'max_interests_per_user': max(len(interests) for interests in users.values()),
            'users_with_single_interest': sum(1 for interests in users.values() if len(interests) == 1)
        }
    
    def _analyze_interest_intensity(self, interest_tags: List[Dict]) -> Dict:
        """分析兴趣强度"""
        # 按置信度分组
        high_intensity = [tag for tag in interest_tags if tag['confidence'] > 0.8]
        medium_intensity = [tag for tag in interest_tags if 0.5 <= tag['confidence'] <= 0.8]
        low_intensity = [tag for tag in interest_tags if tag['confidence'] < 0.5]
        
        return {
            'intensity_distribution': {
                'high_intensity': len(high_intensity),
                'medium_intensity': len(medium_intensity),
                'low_intensity': len(low_intensity)
            },
            'avg_confidence': round(statistics.mean(tag['confidence'] for tag in interest_tags), 3),
            'confidence_std': round(statistics.stdev(tag['confidence'] for tag in interest_tags) if len(interest_tags) > 1 else 0, 3),
            'high_confidence_interests': list(set(tag['tag_name'] for tag in high_intensity))[:10]
        }
    
    def _generate_interest_insights(self, interest_tags: List[Dict], clusters: List[Dict]) -> List[str]:
        """生成兴趣洞察"""
        insights = []
        
        if not interest_tags:
            return ["用户兴趣数据不足，建议增加用户互动以收集更多兴趣信息"]
        
        # 用户兴趣集中度分析
        unique_users = len(set(tag['phone'] for tag in interest_tags))
        unique_interests = len(set(tag['tag_name'] for tag in interest_tags))
        
        if unique_interests / unique_users > 2:
            insights.append("🎯 用户兴趣多样化程度较高，适合推荐多元化内容")
        else:
            insights.append("🎯 用户兴趣相对集中，可以深耕垂直领域内容")
        
        # 热门兴趣分析
        if clusters:
            top_cluster = clusters[0]
            insights.append(f"🔥 最受欢迎的兴趣是'{top_cluster['name']}'，有{top_cluster['user_count']}个用户")
        
        # 兴趣质量分析
        avg_confidence = statistics.mean(tag['confidence'] for tag in interest_tags)
        if avg_confidence > 0.7:
            insights.append("✅ 整体兴趣标签质量较高，用户表达明确")
        else:
            insights.append("⚠️ 部分兴趣标签置信度较低，可能需要更多互动确认")
        
        return insights
    
    def _generate_interest_recommendations(self, clusters: List[Dict], intensity_analysis: Dict) -> List[str]:
        """生成兴趣相关建议"""
        recommendations = []
        
        if clusters:
            top_clusters = clusters[:3]
            recommendations.append(
                f"📈 重点关注热门兴趣：{', '.join(c['name'] for c in top_clusters)}，可以针对性地提供相关内容"
            )
        
        high_intensity_ratio = intensity_analysis['intensity_distribution']['high_intensity'] / sum(intensity_analysis['intensity_distribution'].values())
        if high_intensity_ratio < 0.3:
            recommendations.append("🎯 建议通过更深入的对话来提升用户兴趣标签的置信度")
        
        return recommendations
    
    def _analyze_cross_dimensions(self, raw_data: List[Dict]) -> Dict:
        """跨维度关联分析"""
        # 分析不同维度标签之间的关联性
        users_data = defaultdict(lambda: {'demographic': [], 'interests': [], 'emotions': []})
        
        for tag in raw_data:
            phone = tag['phone']
            if tag['dimension'] == '基本人口统计学标签':
                users_data[phone]['demographic'].append(tag)
            elif tag['dimension'] == '兴趣爱好标签':
                users_data[phone]['interests'].append(tag)
            elif tag['dimension'] == '情绪与情感状态标签':
                users_data[phone]['emotions'].append(tag)
        
        # 分析关联模式
        correlations = []
        for phone, data in users_data.items():
            if data['demographic'] and data['interests']:
                # 分析人口统计学与兴趣的关联
                for demo_tag in data['demographic']:
                    for interest_tag in data['interests']:
                        correlations.append({
                            'demographic': demo_tag['tag_name'],
                            'interest': interest_tag['tag_name'],
                            'user': phone
                        })
        
        # 统计关联频次
        correlation_counts = Counter((c['demographic'], c['interest']) for c in correlations)
        
        return {
            'total_correlations': len(correlations),
            'top_correlations': [
                {'demographic': demo, 'interest': interest, 'frequency': freq}
                for (demo, interest), freq in correlation_counts.most_common(10)
            ],
            'users_with_complete_profile': len([
                phone for phone, data in users_data.items()
                if data['demographic'] and data['interests'] and data['emotions']
            ])
        }
    
    def _segment_users(self, raw_data: List[Dict]) -> List[Dict]:
        """用户群体细分"""
        users_data = defaultdict(lambda: {'tags': [], 'dimensions': set()})
        
        for tag in raw_data:
            phone = tag['phone']
            users_data[phone]['tags'].append(tag)
            users_data[phone]['dimensions'].add(tag['dimension'])
        
        segments = []
        
        # 活跃度细分
        for phone, data in users_data.items():
            tag_count = len(data['tags'])
            if tag_count >= 10:
                segment = 'high_activity'
            elif tag_count >= 5:
                segment = 'medium_activity'
            else:
                segment = 'low_activity'
            
            segments.append({
                'user': phone,
                'segment': segment,
                'tag_count': tag_count,
                'dimension_count': len(data['dimensions'])
            })
        
        # 统计各细分群体
        segment_stats = Counter(s['segment'] for s in segments)
        
        return {
            'segments': [
                {'name': segment, 'count': count, 'percentage': round(count/len(segments)*100, 1)}
                for segment, count in segment_stats.items()
            ],
            'total_users': len(segments)
        }
    
    def _analyze_trends(self, raw_data: List[Dict]) -> Dict:
        """趋势分析"""
        if not raw_data:
            return {'daily_trends': [], 'growth_rate': 0}
        
        # 按日期分组标签创建数据
        daily_counts = defaultdict(int)
        for tag in raw_data:
            try:
                date = datetime.fromisoformat(tag['tag_created']).date()
                daily_counts[date.isoformat()] += 1
            except:
                continue
        
        # 计算增长趋势
        dates = sorted(daily_counts.keys())
        if len(dates) >= 2:
            recent_avg = statistics.mean(daily_counts[d] for d in dates[-7:]) if len(dates) >= 7 else daily_counts[dates[-1]]
            early_avg = statistics.mean(daily_counts[d] for d in dates[:7]) if len(dates) >= 7 else daily_counts[dates[0]]
            growth_rate = ((recent_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0
        else:
            growth_rate = 0
        
        return {
            'daily_trends': [{'date': date, 'count': count} for date, count in sorted(daily_counts.items())],
            'growth_rate': round(growth_rate, 2),
            'peak_day': max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else None
        }
    
    def _generate_recommendations(self, interest_analysis: Dict, demographic_analysis: Dict, emotional_analysis: Dict) -> List[str]:
        """生成业务建议"""
        recommendations = []
        
        # 基于兴趣分析的建议
        if interest_analysis.get('clusters'):
            top_interest = interest_analysis['clusters'][0]['name']
            recommendations.append(f"🎯 重点发展{top_interest}相关功能和内容，这是用户最感兴趣的领域")
        
        # 基于情绪分析的建议
        emotional_health = emotional_analysis.get('summary', {}).get('emotional_health_score', 0.5)
        if emotional_health < 0.6:
            recommendations.append("💚 建议加强情感关怀功能，提升用户情绪健康水平")
        
        # 基于用户完整度的建议
        if demographic_analysis.get('summary', {}).get('demographic_completeness', 0) < 0.7:
            recommendations.append("📝 建议引导用户完善个人信息，以提供更精准的个性化服务")
        
        return recommendations
    
    def _empty_analysis(self) -> Dict:
        """返回空分析结果"""
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_users': 0,
            'total_tags': 0,
            'interest_analysis': {'clusters': [], 'insights': ['暂无足够数据进行兴趣分析'], 'recommendations': []},
            'demographic_analysis': {'distribution': {}, 'insights': ['暂无足够数据进行人口统计学分析'], 'recommendations': []},
            'emotional_analysis': {'patterns': [], 'insights': ['暂无足够数据进行情绪分析'], 'recommendations': []},
            'cross_dimension_insights': {'total_correlations': 0, 'top_correlations': []},
            'user_segments': {'segments': [], 'total_users': 0},
            'trend_analysis': {'daily_trends': [], 'growth_rate': 0},
            'business_recommendations': ['建议增加用户互动以收集更多标签数据']
        }
    
    # 辅助方法
    def _get_analysis_period(self) -> str:
        """获取分析周期"""
        return f"最近30天 ({(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')} 至 {datetime.now().strftime('%Y-%m-%d')})"
    
    def _extract_evidence_keywords(self, tags: List[Dict]) -> List[str]:
        """提取证据关键词"""
        all_evidence = ' '.join(tag['evidence'] for tag in tags)
        # 这里可以使用更复杂的关键词提取算法
        words = all_evidence.split()
        return list(set(words))[:5]
    
    def _calculate_cluster_diversity(self, tags: List[Dict]) -> float:
        """计算聚类多样性"""
        users = set(tag['phone'] for tag in tags)
        return len(users) / len(tags) if tags else 0
    
    def _get_dominant_interest_category(self, interest_tags: List[Dict]) -> str:
        """获取主导兴趣类别"""
        if not interest_tags:
            return "暂无数据"
        
        tag_counts = Counter(tag['tag_name'] for tag in interest_tags)
        return tag_counts.most_common(1)[0][0] if tag_counts else "暂无数据"
    
    def _analyze_age_distribution(self, demo_tags: List[Dict]) -> Dict:
        """分析年龄分布"""
        age_tags = [tag for tag in demo_tags if '岁' in tag['tag_name'] or '年' in tag['tag_name']]
        age_counts = Counter(tag['tag_name'] for tag in age_tags)
        
        return {
            'distribution': dict(age_counts),
            'total_with_age': len(age_tags),
            'most_common_age_group': age_counts.most_common(1)[0][0] if age_counts else None
        }
    
    def _analyze_gender_distribution(self, demo_tags: List[Dict]) -> Dict:
        """分析性别分布"""
        gender_tags = [tag for tag in demo_tags if tag['tag_name'] in ['男性', '女性', '男', '女']]
        gender_counts = Counter(tag['tag_name'] for tag in gender_tags)
        
        return {
            'distribution': dict(gender_counts),
            'total_with_gender': len(gender_tags),
            'gender_ratio': self._calculate_gender_ratio(gender_counts)
        }
    
    def _calculate_gender_ratio(self, gender_counts: Counter) -> str:
        """计算性别比例"""
        male_count = gender_counts.get('男性', 0) + gender_counts.get('男', 0)
        female_count = gender_counts.get('女性', 0) + gender_counts.get('女', 0)
        
        if male_count + female_count == 0:
            return "无数据"
        
        ratio = male_count / (male_count + female_count)
        return f"男性{ratio:.1%}，女性{1-ratio:.1%}"
    
    def _analyze_location_distribution(self, demo_tags: List[Dict]) -> Dict:
        """分析地域分布"""
        # 这里可以根据实际的地域标签格式进行调整
        location_tags = [tag for tag in demo_tags if any(keyword in tag['tag_name'] for keyword in ['市', '省', '区', '县'])]
        location_counts = Counter(tag['tag_name'] for tag in location_tags)
        
        return {
            'distribution': dict(location_counts.most_common(10)),
            'total_with_location': len(location_tags),
            'geographic_diversity': len(location_counts)
        }
    
    def _calculate_demographic_diversity(self, demo_tags: List[Dict]) -> float:
        """计算人口统计学多样性指数"""
        if not demo_tags:
            return 0
        
        tag_counts = Counter(tag['tag_name'] for tag in demo_tags)
        total = len(demo_tags)
        
        # Shannon多样性指数
        diversity = -sum((count/total) * math.log2(count/total) for count in tag_counts.values())
        return round(diversity, 3)
    
    def _calculate_demographic_completeness(self, demo_tags: List[Dict]) -> float:
        """计算人口统计学完整度"""
        users_with_demo = set(tag['phone'] for tag in demo_tags)
        # 这里需要获取总用户数，暂时用demo_tags的用户数
        total_users = len(users_with_demo) if users_with_demo else 1
        return len(users_with_demo) / total_users
    
    def _analyze_demo_interest_correlation(self, raw_data: List[Dict]) -> Dict:
        """分析人口统计学与兴趣的关联"""
        # 这里实现人口统计学标签与兴趣标签的关联分析
        correlations = {}
        # 简化实现，可以扩展为更复杂的关联分析
        return {'correlations': correlations}
    
    def _generate_demographic_insights(self, demo_tags: List[Dict], age_analysis: Dict, gender_analysis: Dict) -> List[str]:
        """生成人口统计学洞察"""
        insights = []
        
        if age_analysis.get('most_common_age_group'):
            insights.append(f"👥 用户群体以{age_analysis['most_common_age_group']}为主")
        
        if gender_analysis.get('gender_ratio') and gender_analysis['gender_ratio'] != "无数据":
            insights.append(f"👫 用户性别分布：{gender_analysis['gender_ratio']}")
        
        return insights
    
    def _generate_demographic_recommendations(self, demo_tags: List[Dict]) -> List[str]:
        """生成人口统计学建议"""
        recommendations = []
        
        if len(demo_tags) < 10:
            recommendations.append("📊 建议收集更多用户基本信息，以便进行精准的用户画像分析")
        
        return recommendations
    
    def _analyze_emotion_distribution(self, emotion_tags: List[Dict]) -> Dict:
        """分析情绪分布"""
        emotion_counts = Counter(tag['tag_name'] for tag in emotion_tags)
        
        return {
            'distribution': dict(emotion_counts.most_common(10)),
            'total_emotion_records': len(emotion_tags),
            'unique_emotions': len(emotion_counts)
        }
    
    def _identify_emotion_patterns(self, emotion_tags: List[Dict]) -> List[Dict]:
        """识别情绪模式"""
        # 按用户分组情绪标签
        user_emotions = defaultdict(list)
        for tag in emotion_tags:
            user_emotions[tag['phone']].append({
                'tag_name': tag['tag_name'],
                'timestamp': tag['tag_created'],
                'confidence': tag['confidence']
            })
        
        patterns = []
        for phone, emotions in user_emotions.items():
            if len(emotions) >= 3:  # 至少3个情绪记录才分析模式
                # 排序并分析序列
                emotions.sort(key=lambda x: x['timestamp'])
                emotion_sequence = [e['tag_name'] for e in emotions]
                
                patterns.append({
                    'user': phone,
                    'sequence': emotion_sequence[-5:],  # 最近5个情绪
                    'pattern_type': self._classify_emotion_pattern(emotion_sequence),
                    'stability_score': self._calculate_emotion_stability(emotions)
                })
        
        return patterns
    
    def _classify_emotion_pattern(self, emotions: List[str]) -> str:
        """分类情绪模式"""
        if len(set(emotions)) == 1:
            return "稳定型"
        elif len(emotions) >= 3 and emotions[-1] != emotions[-2] != emotions[-3]:
            return "波动型"
        else:
            return "混合型"
    
    def _calculate_emotion_stability(self, emotions: List[Dict]) -> float:
        """计算情绪稳定性"""
        if len(emotions) <= 1:
            return 1.0
        
        # 基于情绪变化频率计算稳定性
        changes = sum(1 for i in range(1, len(emotions)) if emotions[i]['tag_name'] != emotions[i-1]['tag_name'])
        stability = 1 - (changes / (len(emotions) - 1))
        return round(stability, 3)
    
    def _analyze_emotion_stability(self, emotion_tags: List[Dict]) -> Dict:
        """分析情绪稳定性"""
        user_emotions = defaultdict(list)
        for tag in emotion_tags:
            user_emotions[tag['phone']].append(tag)
        
        stability_scores = []
        for emotions in user_emotions.values():
            if len(emotions) > 1:
                emotions.sort(key=lambda x: x['tag_created'])
                stability = self._calculate_emotion_stability(emotions)
                stability_scores.append(stability)
        
        if stability_scores:
            avg_stability = statistics.mean(stability_scores)
            return {
                'average_stability': round(avg_stability, 3),
                'stable_users': len([s for s in stability_scores if s > 0.7]),
                'unstable_users': len([s for s in stability_scores if s < 0.3])
            }
        else:
            return {'average_stability': 0, 'stable_users': 0, 'unstable_users': 0}
    
    def _analyze_emotion_triggers(self, emotion_tags: List[Dict]) -> Dict:
        """分析情绪触发因子"""
        # 基于evidence分析情绪触发的上下文
        trigger_keywords = defaultdict(int)
        
        for tag in emotion_tags:
            evidence = tag['evidence'].lower()
            # 提取关键词（简化实现）
            words = evidence.split()
            for word in words[:5]:  # 只取前5个词
                if len(word) > 1:
                    trigger_keywords[word] += 1
        
        return {
            'top_triggers': dict(Counter(trigger_keywords).most_common(10)),
            'total_triggers': len(trigger_keywords)
        }
    
    def _calculate_emotional_health_index(self, emotion_tags: List[Dict]) -> float:
        """计算情绪健康指数"""
        if not emotion_tags:
            return 0.5
        
        # 基于积极/消极情绪比例计算
        positive_emotions = ['高兴', '开心', '快乐', '兴奋', '满足', '愉快']
        negative_emotions = ['生气', '愤怒', '悲伤', '沮丧', '焦虑', '紧张']
        
        positive_count = sum(1 for tag in emotion_tags if any(pos in tag['tag_name'] for pos in positive_emotions))
        negative_count = sum(1 for tag in emotion_tags if any(neg in tag['tag_name'] for neg in negative_emotions))
        
        total_emotional_tags = positive_count + negative_count
        if total_emotional_tags == 0:
            return 0.5
        
        health_index = (positive_count + 0.5 * (len(emotion_tags) - total_emotional_tags)) / len(emotion_tags)
        return round(health_index, 3)
    
    def _get_most_common_emotion(self, emotion_tags: List[Dict]) -> str:
        """获取最常见情绪"""
        if not emotion_tags:
            return "无数据"
        
        emotion_counts = Counter(tag['tag_name'] for tag in emotion_tags)
        return emotion_counts.most_common(1)[0][0]
    
    def _generate_emotional_insights(self, emotion_tags: List[Dict], patterns: List[Dict]) -> List[str]:
        """生成情绪洞察"""
        insights = []
        
        if not emotion_tags:
            return ["情绪数据不足，建议增加情感交互"]
        
        # 分析情绪多样性
        unique_emotions = len(set(tag['tag_name'] for tag in emotion_tags))
        if unique_emotions > 5:
            insights.append("😊 用户情绪表达丰富，情感体验多样化")
        else:
            insights.append("😐 用户情绪表达相对单一，可以引导更多情感交流")
        
        # 分析情绪稳定性
        if patterns:
            stable_users = len([p for p in patterns if p['stability_score'] > 0.7])
            if stable_users > len(patterns) * 0.6:
                insights.append("✅ 大部分用户情绪相对稳定")
            else:
                insights.append("⚠️ 部分用户情绪波动较大，需要关注情感健康")
        
        return insights
    
    def _generate_emotional_recommendations(self, emotion_tags: List[Dict], health_index: float) -> List[str]:
        """生成情绪相关建议"""
        recommendations = []
        
        if health_index < 0.4:
            recommendations.append("💚 建议加强正向情绪引导，提升用户情绪健康水平")
        elif health_index > 0.8:
            recommendations.append("🎉 用户整体情绪健康状况良好，继续保持积极互动")
        
        return recommendations
    
    def _analyze_interest_evolution(self, interest_tags: List[Dict]) -> Dict:
        """分析兴趣演化趋势"""
        # 按时间分组分析兴趣变化
        return {'trend': 'stable', 'emerging_interests': [], 'declining_interests': []}
    
    def _analyze_interest_correlations(self, interest_tags: List[Dict]) -> Dict:
        """分析兴趣相关性"""
        # 分析哪些兴趣经常同时出现
        return {'correlations': []}
    
    def _discover_potential_interests(self, interest_tags: List[Dict]) -> List[str]:
        """挖掘潜在兴趣"""
        # 基于现有兴趣推断可能的潜在兴趣
        return []
    
    def _create_interest_personas(self, interest_tags: List[Dict]) -> List[Dict]:
        """创建兴趣人群画像"""
        # 基于兴趣聚类创建典型用户画像
        return []
