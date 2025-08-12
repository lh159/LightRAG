import json
import os
import sys
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.tag_extractor import TagInfo, TagExtractor
from core.tag_similarity_detector import TagSimilarityDetector

# 内嵌冲突处理器类
@dataclass
class ConflictResolution:
    """冲突解决方案"""
    action: str
    resolved_tags: List[TagInfo]
    conflict_type: str
    explanation: str
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class TagConflictResolver:
    """标签冲突解决器 - 内嵌版本"""
    
    def __init__(self):
        self.contradictory_pairs = {
            "情感特征": [("乐观", "悲观"), ("积极", "消极"), ("开朗", "内向"), ("自信", "自卑")],
            "兴趣偏好": [("喜欢运动", "反感运动"), ("爱好读书", "讨厌阅读")],
            "互动习惯": [("偏好详细表达", "偏好简短交流"), ("主动交流", "被动回应")],
            "价值观": [("追求自由", "重视稳定"), ("个人主义", "集体主义")]
        }
        
        self.intensity_groups = {
            "情感特征": [["轻微焦虑", "中度焦虑", "重度焦虑"], ["略显内向", "比较内向", "极度内向"]],
            "兴趣偏好": [["一般喜欢", "比较喜欢", "非常喜欢", "狂热爱好"]]
        }
    
    def resolve_conflicts(self, dimension: str, existing_tags: List[Dict], new_tags: List[TagInfo]) -> List[ConflictResolution]:
        """解决标签冲突 - 性能优化版"""
        # 🚀 性能优化：快速返回空结果
        if not existing_tags or not new_tags:
            return []
        
        resolutions = []
        
        # 🚀 性能优化：预处理现有标签名称集合，避免重复查找
        existing_names = {tag["tag_name"] for tag in existing_tags}
        
        for new_tag in new_tags:
            # 🚀 性能优化：如果标签已存在，跳过冲突检测
            if new_tag.name in existing_names:
                continue
                
            # 检查直接矛盾（简化版）
            contradiction = self._check_contradictory_fast(dimension, existing_tags, new_tag)
            if contradiction:
                resolutions.append(contradiction)
                continue
            
            # 🚀 性能优化：只在必要时检查时间性变化  
            max_tags_for_temporal = getattr(self, 'max_tags_for_temporal_check', 10)
            if len(existing_tags) < max_tags_for_temporal:
                temporal = self._check_temporal_change(existing_tags, new_tag)
                if temporal:
                    resolutions.append(temporal)
                    continue
        
        return resolutions
    
    def _check_contradictory_fast(self, dimension: str, existing_tags: List[Dict], new_tag: TagInfo) -> Optional[ConflictResolution]:
        """快速矛盾检测 - 性能优化版"""
        # 🚀 性能优化：只检查核心矛盾对
        core_contradictions = {
            "情感特征": [("乐观", "悲观"), ("积极", "消极"), ("开朗", "内向")],
            "兴趣偏好": [("喜欢", "反感"), ("爱好", "讨厌")],
            "互动习惯": [("主动", "被动"), ("详细", "简短")],
            "价值观": [("自由", "稳定"), ("个人", "集体")]
        }
        
        dimension_key = "情感特征" if "情感" in dimension else "兴趣偏好" if "兴趣" in dimension else "互动习惯" if "互动" in dimension else "价值观" if "价值" in dimension else dimension
        pairs = core_contradictions.get(dimension_key, [])
        
        new_name = new_tag.name.lower()
        
        for existing_tag in existing_tags:
            existing_name = existing_tag["tag_name"].lower()
            
            # 🚀 性能优化：简化匹配逻辑
            for pair in pairs:
                word1, word2 = pair[0].lower(), pair[1].lower()
                if (word1 in existing_name and word2 in new_name) or (word2 in existing_name and word1 in new_name):
                    if new_tag.confidence > existing_tag.get("avg_confidence", 0) + 0.15:
                        return ConflictResolution(
                            action='replace',
                            resolved_tags=[new_tag],
                            conflict_type='contradictory',
                            explanation=f'矛盾替换: "{existing_tag["tag_name"]}" → "{new_tag.name}"'
                        )
        return None
    
    def _check_contradictory(self, dimension: str, existing_tags: List[Dict], new_tag: TagInfo) -> Optional[ConflictResolution]:
        """检查矛盾标签"""
        # 🔧 修复维度名称匹配问题
        dimension_key = "情感特征" if "情感" in dimension else "兴趣偏好" if "兴趣" in dimension else "互动习惯" if "互动" in dimension else "价值观" if "价值" in dimension else dimension
        pairs = self.contradictory_pairs.get(dimension_key, [])
        
        for existing_tag in existing_tags:
            existing_name = existing_tag["tag_name"]
            new_name = new_tag.name
            
            for pair in pairs:
                # 🔧 改为包含匹配，不要求精确匹配
                existing_match = any(word in existing_name for word in pair[0].split()) or any(word in existing_name for word in pair[1].split())
                new_match = any(word in new_name for word in pair[0].split()) or any(word in new_name for word in pair[1].split())
                
                # 检查是否为矛盾对：existing在pair[0]，new在pair[1] 或 反之
                is_contradictory = False
                if existing_match and new_match:
                    for word0 in pair[0].split():
                        for word1 in pair[1].split():
                            if (word0 in existing_name and word1 in new_name) or (word1 in existing_name and word0 in new_name):
                                is_contradictory = True
                                break
                        if is_contradictory:
                            break
                
                if is_contradictory:
                    # 🔧 降低置信度阈值要求
                    if new_tag.confidence > existing_tag.get("avg_confidence", 0) + 0.1:
                        return ConflictResolution(
                            action='replace',
                            resolved_tags=[new_tag],
                            conflict_type='contradictory',
                            explanation=f'矛盾标签替换: "{existing_name}" → "{new_name}" (置信度: {existing_tag.get("avg_confidence", 0):.2f} → {new_tag.confidence:.2f})'
                        )
                    else:
                        return ConflictResolution(
                            action='keep_existing',
                            resolved_tags=[],
                            conflict_type='contradictory',
                            explanation=f'检测到矛盾但保留原标签: "{existing_name}" vs "{new_name}" (置信度差异不足)'
                        )
        return None
    
    def _check_temporal_change(self, existing_tags: List[Dict], new_tag: TagInfo) -> Optional[ConflictResolution]:
        """检查时间性变化"""
        for existing_tag in existing_tags:
            last_reinforced = datetime.fromisoformat(existing_tag["last_reinforced"])
            days_since = (datetime.now() - last_reinforced).days
            
            if days_since > 7 and self._is_opposite(existing_tag["tag_name"], new_tag.name):
                old_tag = TagInfo(f"{existing_tag['tag_name']}(历史)", existing_tag.get("avg_confidence", 0), "历史标签", new_tag.category, new_tag.subcategory)
                new_temporal = TagInfo(f"{new_tag.name}(当前)", new_tag.confidence, new_tag.evidence, new_tag.category, new_tag.subcategory)
                
                return ConflictResolution(
                    action='create_temporal',
                    resolved_tags=[old_tag, new_temporal],
                    conflict_type='temporal_change',
                    explanation=f'时间性变化: "{existing_tag["tag_name"]}" → "{new_tag.name}"'
                )
        return None
    
    def _is_opposite(self, name1: str, name2: str) -> bool:
        """简单的对立判断"""
        opposites = [("喜欢", "反感"), ("积极", "消极"), ("主动", "被动")]
        for pair in opposites:
            if (name1 in pair[0] and name2 in pair[1]) or (name1 in pair[1] and name2 in pair[0]):
                return True
        return False
    
    def apply_resolutions(self, existing_tags: List[Dict], resolutions: List[ConflictResolution]) -> Tuple[List[Dict], List[Dict]]:
        """应用冲突解决方案"""
        updated_tags = existing_tags.copy()
        conflict_records = []
        
        for resolution in resolutions:
            record = {
                "timestamp": resolution.timestamp,
                "conflict_type": resolution.conflict_type,
                "action": resolution.action,
                "explanation": resolution.explanation
            }
            
            if resolution.action == 'replace':
                for i, tag in enumerate(updated_tags):
                    for resolved_tag in resolution.resolved_tags:
                        if self._should_replace(tag, resolved_tag):
                            updated_tags[i] = self._tag_to_dict(resolved_tag)
                            break
            
            elif resolution.action == 'create_temporal':
                for resolved_tag in resolution.resolved_tags:
                    if "历史" in resolved_tag.name:
                        for tag in updated_tags:
                            if tag["tag_name"] == resolved_tag.name.replace("(历史)", ""):
                                tag["tag_name"] = resolved_tag.name
                                tag["is_historical"] = True
                    else:
                        updated_tags.append(self._tag_to_dict(resolved_tag))
            
            conflict_records.append(record)
        
        return updated_tags, conflict_records
    
    def _should_replace(self, existing_tag: Dict, new_tag: TagInfo) -> bool:
        """判断是否应该替换"""
        return existing_tag["tag_name"] in new_tag.name or new_tag.name in existing_tag["tag_name"]
    
    def _tag_to_dict(self, tag_info: TagInfo) -> Dict:
        """TagInfo转字典"""
        return {
            "tag_name": tag_info.name,
            "first_detected": datetime.now().isoformat(),
            "last_reinforced": datetime.now().isoformat(),
            "evidence_count": 1,
            "total_confidence": tag_info.confidence,
            "avg_confidence": tag_info.confidence,
            "decay_rate": 0.1,
            "current_weight": tag_info.confidence,
            "evidence": tag_info.evidence,
            "category": tag_info.category,
            "subcategory": tag_info.subcategory,
            "is_historical": "(历史)" in tag_info.name,
            "is_contextual": "[" in tag_info.name,
            "conflict_resolved": True
        }

class TagManager:
    def __init__(self, user_id: str, db_manager=None):
        self.user_id = user_id
        self.user_data_path = f"user_data/{user_id}"
        self.tags_file = f"{self.user_data_path}/user_tags.json"
        self.timeline_file = f"{self.user_data_path}/tag_timeline.json"
        
        # 🆕 数据库管理器（用于同步标签数据）
        self.db_manager = db_manager
        if not self.db_manager:
            # 如果没有传入，尝试导入并创建
            try:
                from utils.database import DatabaseManager
                self.db_manager = DatabaseManager()
            except ImportError:
                self.db_manager = None
        
        # 🚀 加载性能配置
        self.performance_config = self._load_performance_config()
        
        # 🆕 初始化冲突处理器（传递性能配置）
        self.conflict_resolver = TagConflictResolver()
        self.conflict_resolver.max_tags_for_temporal_check = self.performance_config.get('max_tags_for_temporal_check', 10)
        
        # 🆕 初始化相似性检测器
        self.similarity_detector = TagSimilarityDetector()
        
        # 确保文件存在
        self._ensure_tag_files()
    
    def _load_performance_config(self) -> Dict:
        """加载性能配置"""
        try:
            with open("config.yaml", 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('tag_system', {}).get('performance', {
                    'enable_debug_logs': False,
                    'enable_conflict_detection': True,
                    'conflict_detection_mode': 'fast',
                    'max_tags_for_temporal_check': 10,
                    'cache_conflict_results': True
                })
        except Exception as e:
            print(f"警告: 无法加载性能配置，使用默认设置: {e}")
            return {
                'enable_debug_logs': True,  # 🔧 临时启用调试模式
                'enable_conflict_detection': True,
                'conflict_detection_mode': 'fast',
                'max_tags_for_temporal_check': 10,
                'cache_conflict_results': True
            }
        
    def _ensure_tag_files(self):
        """确保标签文件存在"""
        os.makedirs(self.user_data_path, exist_ok=True)
        if not os.path.exists(self.tags_file):
            self._create_empty_tags_file()
        if not os.path.exists(self.timeline_file):
            self._create_empty_timeline_file()
    
    def _create_empty_tags_file(self):
        """创建空的标签文件"""
        empty_tags = {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "tag_dimensions": {
                "demographic_info": {
                    "dimension_name": "基本人口统计学标签",
                    "subcategories": {
                        "age": {
                            "subcategory_name": "年龄",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "gender": {
                            "subcategory_name": "性别",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "location": {
                            "subcategory_name": "地域",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        }
                    },
                    "overall_weight": 0.0,
                    "overall_stability": 0.0
                },
                "interests_hobbies": {
                    "dimension_name": "兴趣爱好标签",
                    "subcategories": {
                        "art_creation": {
                            "subcategory_name": "文艺创作类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "handcraft_diy": {
                            "subcategory_name": "手工DIY类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "music_appreciation": {
                            "subcategory_name": "音乐欣赏类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "music_performance": {
                            "subcategory_name": "音乐演奏类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "film_tv_appreciation": {
                            "subcategory_name": "影视欣赏类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "ball_sports": {
                            "subcategory_name": "球类运动类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "sports_watching": {
                            "subcategory_name": "运动比赛欣赏类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "extreme_sports": {
                            "subcategory_name": "极限运动类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "health_fitness": {
                            "subcategory_name": "养生锻炼身体类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "pet_keeping": {
                            "subcategory_name": "饲养宠物类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "home_cooking": {
                            "subcategory_name": "家常菜烹饪类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "baking": {
                            "subcategory_name": "烘焙类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "food_exploration": {
                            "subcategory_name": "美食探店类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "offline_socializing": {
                            "subcategory_name": "线下聚会社交类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "home_design": {
                            "subcategory_name": "家装设计类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "knowledge_learning": {
                            "subcategory_name": "知识学习类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "collecting_appreciation": {
                            "subcategory_name": "收藏鉴赏类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "life_experience": {
                            "subcategory_name": "体验生活类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "cooking": {
                            "subcategory_name": "烹饪美食类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "social_gathering": {
                            "subcategory_name": "社交聚会类",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "other": {
                            "subcategory_name": "其他兴趣爱好",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        }
                    },
                    "overall_weight": 0.0,
                    "overall_stability": 0.0
                },
                "emotional_state": {
                    "dimension_name": "情绪与情感状态标签",
                    "subcategories": {
                        "current_mood": {
                            "subcategory_name": "当前情绪状态",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        },
                        "emotional_needs": {
                            "subcategory_name": "情感需求",
                            "active_tags": [],
                            "dominant_tag": None,
                            "dimension_weight": 0.0,
                            "stability_score": 0.0,
                            "conflict_history": []
                        }
                    },
                    "overall_weight": 0.0,
                    "overall_stability": 0.0
                }
            },
            "computed_metrics": {
                "emotional_health_index": 0.5,
                "interest_concentration": 0.0,
                "interaction_dependency": 0.0,
                "overall_profile_maturity": 0.0
            },
            "global_conflict_log": []
        }
        
        with open(self.tags_file, 'w', encoding='utf-8') as f:
            json.dump(empty_tags, f, ensure_ascii=False, indent=2)
    
    def _create_empty_timeline_file(self):
        """创建空的时间轴文件"""
        empty_timeline = {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "tag_events": []
        }
        
        with open(self.timeline_file, 'w', encoding='utf-8') as f:
            json.dump(empty_timeline, f, ensure_ascii=False, indent=2)
    
    def update_tags(self, extracted_tags: Dict[str, List[TagInfo]]) -> Dict:
        """更新用户标签"""
        # 加载当前标签
        current_tags = self._load_current_tags()
        
        # 更新各维度标签
        for dimension, new_tags in extracted_tags.items():
            if dimension in current_tags["tag_dimensions"]:
                self._update_dimension_tags(
                    current_tags["tag_dimensions"][dimension], 
                    new_tags
                )
        
        # 重新计算权重和指标
        self._recalculate_weights_and_metrics(current_tags)
        
        # 更新时间戳
        current_tags["last_updated"] = datetime.now().isoformat()
        
        # 保存到文件
        self._save_tags(current_tags)
        
        # 🆕 同步到数据库
        self._sync_tags_to_database(current_tags)
        
        # 记录到时间轴
        self._record_tag_timeline(extracted_tags)
        
        return current_tags
    
    def _sync_tags_to_database(self, current_tags: Dict):
        """同步标签数据到数据库"""
        if not self.db_manager:
            return
        
        try:
            import sqlite3
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 先清除该用户的所有标签（标记为非活跃）
                cursor.execute('''
                    UPDATE user_tags SET is_active = 0 
                    WHERE phone_number = ?
                ''', (self.user_id,))
                
                tag_count = 0
                
                # 处理嵌套的标签数据结构
                for dimension_key, dimension_data in current_tags.get("tag_dimensions", {}).items():
                    if not isinstance(dimension_data, dict):
                        continue
                        
                    dimension_name = dimension_data.get("dimension_name", dimension_key)
                    
                    # 处理子分类
                    for subcategory_key, subcategory_data in dimension_data.get("subcategories", {}).items():
                        if not isinstance(subcategory_data, dict):
                            continue
                            
                        # 处理活跃标签
                        for tag_data in subcategory_data.get("active_tags", []):
                            if not isinstance(tag_data, dict):
                                continue
                                
                            cursor.execute('''
                                INSERT OR REPLACE INTO user_tags 
                                (phone_number, dimension, tag_name, confidence, evidence, 
                                 created_at, last_updated, is_active)
                                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                            ''', (
                                self.user_id,
                                dimension_name,
                                tag_data.get("tag_name", "未知标签"),
                                tag_data.get("avg_confidence", 0.5),
                                json.dumps(tag_data.get("evidence", ""), ensure_ascii=False),
                                tag_data.get("first_detected", datetime.now().isoformat()),
                                tag_data.get("last_reinforced", datetime.now().isoformat())
                            ))
                            tag_count += 1
                
                conn.commit()
                print(f"✅ 成功同步标签数据到数据库: 用户 {self.user_id} ({tag_count} 个标签)")
                
        except Exception as e:
            print(f"❌ 同步标签数据到数据库失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _load_current_tags(self) -> Dict:
        """加载当前标签"""
        with open(self.tags_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _update_dimension_tags(self, dimension_data: Dict, new_tags: List[TagInfo]):
        """更新单个维度的标签 - 支持二级标签结构"""
        dimension_name = dimension_data.get("dimension_name", "")
        debug_mode = self.performance_config.get('enable_debug_logs', False)
        enable_conflict_detection = self.performance_config.get('enable_conflict_detection', True)
        
        if debug_mode:
            print(f"🔍 [调试] 更新维度标签 - 维度: {dimension_name}, 新标签: {[tag.name for tag in new_tags]}")
        
        # 检查是否为新的二级标签结构
        if "subcategories" in dimension_data:
            # 新的二级标签结构
            for new_tag in new_tags:
                subcategory_key = new_tag.subcategory
                
                # 🔧 修复：添加调试日志和自动创建缺失的子分类
                if debug_mode:
                    print(f"🔍 [调试] 处理标签: {new_tag.name}, 子分类: {subcategory_key}")
                    print(f"🔍 [调试] 可用子分类: {list(dimension_data['subcategories'].keys())}")
                
                if subcategory_key in dimension_data["subcategories"]:
                    subcategory_data = dimension_data["subcategories"][subcategory_key]
                    active_tags = subcategory_data["active_tags"]
                else:
                    # 🆕 如果子分类不存在，自动创建（防止标签丢失）
                    if debug_mode:
                        print(f"⚠️ [调试] 子分类 '{subcategory_key}' 不存在，自动创建")
                    
                    # 尝试获取子分类的中文名称
                    extractor = TagExtractor(self.user_id)
                    subcategory_name = "未知子分类"
                    
                    # 从标签提取器的定义中查找对应的中文名
                    for dim_key, dim_config in extractor.tag_categories.items():
                        if dim_key == new_tag.category:
                            subcategories = dim_config.get("subcategories", {})
                            subcategory_name = subcategories.get(subcategory_key, f"未知子分类-{subcategory_key}")
                            break
                    
                    # 创建新的子分类结构
                    dimension_data["subcategories"][subcategory_key] = {
                        "subcategory_name": subcategory_name,
                        "active_tags": [],
                        "dominant_tag": None,
                        "dimension_weight": 0.0,
                        "stability_score": 0.0,
                        "conflict_history": []
                    }
                    subcategory_data = dimension_data["subcategories"][subcategory_key]
                    active_tags = subcategory_data["active_tags"]
                    
                    if debug_mode:
                        print(f"✅ [调试] 已创建子分类: {subcategory_key} ({subcategory_name})")
                
                # 🔧 修复：将冲突检测和标签更新逻辑移到 if/else 外面
                # 对每个二级标签进行冲突检测
                if enable_conflict_detection and len(active_tags) > 0:
                    resolutions = self.conflict_resolver.resolve_conflicts(
                        f"{dimension_name}-{subcategory_key}", active_tags, [new_tag]
                    )
                    
                    if resolutions:
                        updated_tags, conflict_records = self.conflict_resolver.apply_resolutions(
                            active_tags, resolutions
                        )
                        subcategory_data["active_tags"] = updated_tags
                        
                        # 记录冲突历史
                        if "conflict_history" not in subcategory_data:
                            subcategory_data["conflict_history"] = []
                        subcategory_data["conflict_history"].extend(conflict_records)
                
                # 更新或添加标签到对应的二级分类
                self._update_subcategory_tag(subcategory_data, new_tag)
        else:
            # 兼容旧的一级标签结构
            active_tags = dimension_data.get("active_tags", [])
            
            # 冲突检测和处理
            if enable_conflict_detection and len(active_tags) > 0 and len(new_tags) > 0:
                resolutions = self.conflict_resolver.resolve_conflicts(
                    dimension_name, active_tags, new_tags
                )
                
                if resolutions:
                    updated_tags, conflict_records = self.conflict_resolver.apply_resolutions(
                        active_tags, resolutions
                    )
                    dimension_data["active_tags"] = updated_tags
                    
                    # 记录冲突历史
                    if "conflict_history" not in dimension_data:
                        dimension_data["conflict_history"] = []
                    dimension_data["conflict_history"].extend(conflict_records)
        
        if debug_mode:
            print(f"🎯 [调试] 标签更新完成 - 维度: {dimension_name}")
    
    def _update_subcategory_tag(self, subcategory_data: Dict, new_tag: TagInfo):
        """更新二级分类中的标签"""
        active_tags = subcategory_data["active_tags"]
        
        # 🆕 相似性检测和合并
        if active_tags:
            # 检测相似标签
            similar_groups = self.similarity_detector.detect_similar_tags(active_tags, [new_tag])
            
            if similar_groups:
                # 找到需要合并的标签组
                for group in similar_groups:
                    if new_tag.name in group.similar_tags or new_tag.name == group.primary_tag:
                        # 检查是否已存在主要标签
                        existing_primary_tag = None
                        existing_similar_tag = None
                        
                        for tag in active_tags:
                            if tag["tag_name"] == group.primary_tag:
                                existing_primary_tag = tag
                            elif tag["tag_name"] in group.similar_tags:
                                existing_similar_tag = tag
                        
                        if existing_primary_tag:
                            # 强化主要标签
                            existing_primary_tag["evidence_count"] += 1
                            existing_primary_tag["last_reinforced"] = datetime.now().isoformat()
                            existing_primary_tag["total_confidence"] += new_tag.confidence
                            existing_primary_tag["avg_confidence"] = existing_primary_tag["total_confidence"] / existing_primary_tag["evidence_count"]
                            
                            # 更新证据信息
                            if "evidence" not in existing_primary_tag:
                                existing_primary_tag["evidence"] = new_tag.evidence
                            else:
                                existing_primary_tag["evidence"] = f"{existing_primary_tag['evidence']}; {new_tag.evidence}"[:200] + "..."
                            
                            # 记录合并信息
                            existing_primary_tag["merge_info"] = {
                                "merged_from": new_tag.name,
                                "merge_reason": group.merge_reason,
                                "similarity_score": group.similarity_score,
                                "merge_time": datetime.now().isoformat()
                            }
                            
                            # 如果存在相似标签，将其移除（避免重复）
                            if existing_similar_tag:
                                active_tags.remove(existing_similar_tag)
                            
                            # 应用时间衰减
                            self._apply_time_decay(active_tags)
                            
                            # 限制标签数量（保留权重最高的10个）
                            if len(active_tags) > 10:
                                active_tags.sort(key=lambda x: x.get("current_weight", x.get("avg_confidence", 0)), reverse=True)
                                subcategory_data["active_tags"] = active_tags[:10]
                            
                            return  # 已合并，不需要进一步处理
        
        # 查找是否已存在完全相同的标签
        existing_tag = None
        for tag in active_tags:
            if tag["tag_name"] == new_tag.name:
                existing_tag = tag
                break
        
        if existing_tag:
            # 强化已有标签
            existing_tag["evidence_count"] += 1
            existing_tag["last_reinforced"] = datetime.now().isoformat()
            existing_tag["total_confidence"] += new_tag.confidence
            existing_tag["avg_confidence"] = existing_tag["total_confidence"] / existing_tag["evidence_count"]
            
            # 更新证据信息
            if "evidence" not in existing_tag:
                existing_tag["evidence"] = new_tag.evidence
            else:
                existing_tag["evidence"] = f"{existing_tag['evidence']}; {new_tag.evidence}"[:200] + "..."
            
            # 更新分类信息
            existing_tag["category"] = new_tag.category
            existing_tag["subcategory"] = new_tag.subcategory
        else:
            # 添加新标签
            new_tag_data = {
                "tag_name": new_tag.name,
                "first_detected": datetime.now().isoformat(),
                "last_reinforced": datetime.now().isoformat(),
                "evidence_count": 1,
                "total_confidence": new_tag.confidence,
                "avg_confidence": new_tag.confidence,
                "decay_rate": 0.1,
                "evidence": new_tag.evidence,
                "category": new_tag.category,
                "subcategory": new_tag.subcategory,
                "is_historical": False,
                "is_contextual": "[" in new_tag.name,
                "conflict_resolved": False
            }
            active_tags.append(new_tag_data)
        
        # 应用时间衰减
        self._apply_time_decay(active_tags)
        
        # 限制标签数量（保留权重最高的10个）
        if len(active_tags) > 10:
            active_tags.sort(key=lambda x: x.get("current_weight", x.get("avg_confidence", 0)), reverse=True)
            subcategory_data["active_tags"] = active_tags[:10]

    
    def _apply_time_decay(self, active_tags: List[Dict]):
        """应用时间衰减"""
        now = datetime.now()
        
        for tag in active_tags:
            last_reinforced = datetime.fromisoformat(tag["last_reinforced"])
            days_since_reinforced = (now - last_reinforced).days
            
            # 计算衰减因子
            decay_factor = max(0.1, 1.0 - (days_since_reinforced * tag["decay_rate"] / 30))
            tag["current_weight"] = tag["avg_confidence"] * decay_factor
    
    def _recalculate_weights_and_metrics(self, tags_data: Dict):
        """重新计算权重和指标 - 支持新的二级标签结构"""
        dimensions = tags_data["tag_dimensions"]
        
        for dimension_key, dimension_data in dimensions.items():
            all_tags = []
            
            # 处理新的二级标签结构
            if dimension_data.get('subcategories'):
                for sub_key, subcategory_data in dimension_data['subcategories'].items():
                    active_tags = subcategory_data.get("active_tags", [])
                    all_tags.extend(active_tags)
                    
                    # 计算每个二级分类的指标
                    if active_tags:
                        dominant_tag = max(active_tags, key=lambda x: x.get("current_weight", 0))
                        subcategory_data["dominant_tag"] = dominant_tag["tag_name"]
                        subcategory_data["dimension_weight"] = dominant_tag.get("current_weight", 0)
                        
                        avg_confidence = sum(tag.get("avg_confidence", 0) for tag in active_tags) / len(active_tags)
                        tag_count_factor = min(1.0, len(active_tags) / 10.0)
                        subcategory_data["stability_score"] = avg_confidence * tag_count_factor
                    else:
                        subcategory_data["dominant_tag"] = None
                        subcategory_data["dimension_weight"] = 0.0
                        subcategory_data["stability_score"] = 0.0
                
                # 计算整个维度的综合指标
                if all_tags:
                    dominant_tag = max(all_tags, key=lambda x: x.get("current_weight", 0))
                    dimension_data["dominant_tag"] = dominant_tag["tag_name"]
                    dimension_data["overall_weight"] = sum(tag.get("current_weight", 0) for tag in all_tags) / len(all_tags)
                    
                    avg_confidence = sum(tag.get("avg_confidence", 0) for tag in all_tags) / len(all_tags)
                    tag_count_factor = min(1.0, len(all_tags) / 10.0)
                    dimension_data["overall_stability"] = avg_confidence * tag_count_factor
                else:
                    dimension_data["dominant_tag"] = None
                    dimension_data["overall_weight"] = 0.0
                    dimension_data["overall_stability"] = 0.0
                    
            elif dimension_data.get("active_tags"):
                # 兼容旧的一级标签结构
                active_tags = dimension_data["active_tags"]
                
                if active_tags:
                    # 找到主导标签（权重最高）
                    dominant_tag = max(active_tags, key=lambda x: x.get("current_weight", 0))
                    dimension_data["dominant_tag"] = dominant_tag["tag_name"]
                    
                    # 计算维度权重
                    dimension_data["dimension_weight"] = dominant_tag.get("current_weight", 0)
                    
                    # 计算稳定性评分（基于标签数量和平均置信度）
                    avg_confidence = sum(tag.get("avg_confidence", 0) for tag in active_tags) / len(active_tags)
                    tag_count_factor = min(1.0, len(active_tags) / 10.0)
                    dimension_data["stability_score"] = avg_confidence * tag_count_factor
                else:
                    dimension_data["dominant_tag"] = None
                    dimension_data["dimension_weight"] = 0.0
                    dimension_data["stability_score"] = 0.0
        
        # 计算综合指标
        self._compute_overall_metrics(tags_data)
    
    def _compute_overall_metrics(self, tags_data: Dict):
        """计算综合指标 - 支持新的二级标签结构"""
        dimensions = tags_data["tag_dimensions"]
        metrics = tags_data["computed_metrics"]
        
        # 情感健康指数 (基于情绪与情感状态标签)
        emotional_dim = dimensions.get("emotional_state", dimensions.get("emotional_traits", {}))
        emotional_tags = []
        
        # 处理新的二级标签结构
        if emotional_dim.get('subcategories'):
            for sub_key, subcategory_data in emotional_dim['subcategories'].items():
                active_tags = subcategory_data.get("active_tags", [])
                emotional_tags.extend(active_tags)
        elif emotional_dim.get("active_tags"):
            # 兼容旧的一级标签结构
            emotional_tags = emotional_dim.get("active_tags", [])
        
        positive_weight = 0
        negative_weight = 0
        for tag in emotional_tags:
            tag_name = tag["tag_name"]
            weight = tag.get("current_weight", 0)
            
            if any(word in tag_name for word in ["乐观", "积极", "开朗", "自信", "快乐", "满足", "兴奋"]):
                positive_weight += weight
            elif any(word in tag_name for word in ["焦虑", "消极", "悲观", "敏感", "沮丧", "愤怒", "恐惧"]):
                negative_weight += weight
        
        total_emotional_weight = positive_weight + negative_weight
        if total_emotional_weight > 0:
            metrics["emotional_health_index"] = (positive_weight - negative_weight * 0.5) / total_emotional_weight
        else:
            metrics["emotional_health_index"] = 0.5
        
        # 整体画像成熟度 - 适应新的结构
        total_dimensions = len(dimensions)
        active_dimensions = 0
        total_stability = 0
        
        for dim_data in dimensions.values():
            # 检查新的二级标签结构
            if dim_data.get('subcategories'):
                if dim_data.get("overall_weight", 0) > 0.1:
                    active_dimensions += 1
                total_stability += dim_data.get("overall_stability", 0)
            elif dim_data.get("dimension_weight", 0) > 0.1:
                # 兼容旧结构
                active_dimensions += 1
                total_stability += dim_data.get("stability_score", 0)
        
        avg_stability = total_stability / total_dimensions if total_dimensions > 0 else 0
        
        metrics["overall_profile_maturity"] = (active_dimensions / total_dimensions) * avg_stability if total_dimensions > 0 else 0
    
    def _save_tags(self, tags_data: Dict):
        """保存标签数据"""
        with open(self.tags_file, 'w', encoding='utf-8') as f:
            json.dump(tags_data, f, ensure_ascii=False, indent=2)
    
    def _record_tag_timeline(self, extracted_tags: Dict[str, List[TagInfo]]):
        """记录标签时间轴"""
        try:
            timeline_data = self._load_timeline()
            
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "tag_extraction",
                "extracted_tags": {}
            }
            
            for dimension, tags in extracted_tags.items():
                event["extracted_tags"][dimension] = [
                    {
                        "tag_name": tag.name,
                        "confidence": tag.confidence,
                        "evidence": tag.evidence
                    }
                    for tag in tags
                ]
            
            timeline_data["tag_events"].append(event)
            
            # 限制时间轴长度（保留最近100个事件）
            if len(timeline_data["tag_events"]) > 100:
                timeline_data["tag_events"] = timeline_data["tag_events"][-100:]
            
            with open(self.timeline_file, 'w', encoding='utf-8') as f:
                json.dump(timeline_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"记录时间轴错误: {e}")
    
    def _load_timeline(self) -> Dict:
        """加载时间轴数据"""
        with open(self.timeline_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_user_tags(self) -> Dict:
        """获取用户标签"""
        return self._load_current_tags()
    
    def get_dimension_weight(self, dimension: str) -> float:
        """获取维度权重"""
        tags_data = self._load_current_tags()
        return tags_data["tag_dimensions"].get(dimension, {}).get("dimension_weight", 0.0)
