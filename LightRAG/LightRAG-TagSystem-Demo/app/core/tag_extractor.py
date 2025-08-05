import json
import re
import sys
import os
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.llm_client import LLMClient
from core.tag_similarity_detector import TagSimilarityDetector

@dataclass
class TagInfo:
    name: str
    confidence: float
    evidence: str
    category: str  # 一级标签类别
    subcategory: str  # 二级标签类别

class TagExtractor:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.llm_client = LLMClient()
        self.similarity_detector = TagSimilarityDetector()
        self.tag_categories = {
            "demographic_info": {
                "name": "基本人口统计学标签",
                "subcategories": {
                    "age": "年龄",
                    "gender": "性别", 
                    "location": "地域"
                }
            },
            "interests_hobbies": {
                "name": "兴趣爱好标签",
                "subcategories": {
                    "art_creation": "文艺创作类",
                    "handcraft_diy": "手工DIY类",
                    "music_appreciation": "音乐欣赏类",
                    "music_performance": "音乐演奏类",
                    "film_tv_appreciation": "影视欣赏类",
                    "ball_sports": "球类运动类",
                    "sports_watching": "运动比赛欣赏类",
                    "extreme_sports": "极限运动类",
                    "health_fitness": "养生锻炼身体类",
                    "pet_keeping": "饲养宠物类",
                    "home_cooking": "家常菜烹饪类",
                    "baking": "烘焙类",
                    "food_exploration": "美食探店类",
                    "offline_socializing": "线下聚会社交类",
                    "home_design": "家装设计类",
                    "knowledge_learning": "知识学习类",
                    "collecting_appreciation": "收藏鉴赏类",
                    "life_experience": "体验生活类"
                }
            },
            "emotional_state": {
                "name": "情绪与情感状态标签",
                "subcategories": {
                    "current_mood": "当前情绪状态",
                    "emotional_needs": "情感需求"
                }
            }
        }
        
    def extract_tags_from_text(self, text: str, context: Dict = None) -> Dict[str, List[TagInfo]]:
        """从文本中提取标签"""
        
        # 构建提取prompt
        extraction_prompt = self._build_extraction_prompt(text, context)
        
        # 调用LLM提取
        try:
            llm_response = self.llm_client.complete(
                extraction_prompt, 
                max_tokens=300,
                temperature=0.3
            )
            
            # 解析LLM响应
            extracted_tags = self._parse_llm_response(llm_response, text)
            
            # 添加行为模式分析
            behavior_tags = self._analyze_behavior_patterns(text)
            
            # 融合结果
            final_tags = self._merge_tag_results(extracted_tags, behavior_tags)
            
            # 🆕 应用标签标准化和相似性合并
            standardized_tags = self._apply_tag_standardization(final_tags)
            
            return standardized_tags
            
        except Exception as e:
            print(f"标签提取错误: {e}")
            return {}
    
    def _build_extraction_prompt(self, text: str, context: Dict = None) -> str:
        """构建标签提取的prompt - 增强版"""
        context_info = ""
        if context:
            context_info = f"对话上下文: {context.get('previous_messages', '')}\n"
        
        prompt = f"""
        你是一个专业的用户画像分析师，请深入分析以下用户文本并精确提取标签。

        {context_info}
        用户文本: "{text}"

        【重要提示】请仔细分析用户的表达方式、用词习惯、话题偏好，进行语义理解和意图识别。

        请从以下3个维度提取标签，每个维度下有详细的二级分类：

        ====== 1. 基本人口统计学标签 ======
        - 年龄：通过语言风格、话题偏好、生活经历推断年龄段
        - 性别：通过表达方式、关注话题、用词习惯推断性别特征  
        - 地域：通过方言、生活习惯、文化偏好推断地域特征

        ====== 2. 兴趣爱好标签（重点分析） ======
        请仔细分析用户对以下兴趣爱好的表达：

        【文艺创作类】关键词：绘画、写作、摄影、设计、创作、艺术、画画、写文章、拍照、PS、剪辑
        示例："我喜欢画画"、"我经常写文章"、"我爱好摄影"

        【手工DIY类】关键词：手工、DIY、编织、木工、制作、手工艺、针织、刺绣、模型
        示例："我喜欢做手工"、"我会编织"、"我做了个模型"

        【音乐欣赏类】关键词：听音乐、听歌、音乐、歌曲、歌手、演唱会、音乐节、播放器、耳机
        示例："我喜欢听音乐"、"我经常听歌"、"我去过演唱会"

        【音乐演奏类】关键词：弹琴、吉他、钢琴、唱歌、演奏、乐器、乐队、音乐创作
        示例："我会弹吉他"、"我学过钢琴"、"我喜欢唱歌"

        【影视欣赏类】关键词：电影、电视剧、看剧、追剧、院线、影院、电影院、网剧、综艺、纪录片
        示例："我喜欢看电影"、"我经常追剧"、"我去电影院"、"你看最近的院线电影了吗"

        【球类运动类】关键词：足球、篮球、网球、乒乓球、羽毛球、排球、踢球、打球、运动
        示例："我喜欢踢足球"、"我会打篮球"、"我经常打乒乓球"

        【运动比赛欣赏类】关键词：看比赛、体育、赛事、直播、解说、球迷、支持、球队
        示例："我喜欢看足球比赛"、"我是球迷"、"我经常看体育直播"

        【极限运动类】关键词：攀岩、滑雪、跳伞、蹦极、冲浪、滑板、极限运动
        示例："我喜欢攀岩"、"我去滑雪"、"我想尝试跳伞"

        【养生锻炼身体类】关键词：健身、瑜伽、跑步、锻炼、运动、养生、保健、健康
        示例："我经常健身"、"我练瑜伽"、"我跑步"

        【饲养宠物类】关键词：养宠物、猫、狗、宠物、动物、铲屎官、遛狗
        示例："我养了一只猫"、"我喜欢狗"、"我经常遛狗"

        【家常菜烹饪类】关键词：做饭、烹饪、做菜、下厨、菜谱、家常菜、炒菜
        示例："我喜欢做饭"、"我会做菜"、"我经常下厨"

        【烘焙类】关键词：烘焙、蛋糕、面包、甜点、烤箱、制作、甜品
        示例："我喜欢烘焙"、"我会做蛋糕"、"我经常做甜点"

        【美食探店类】关键词：探店、美食、餐厅、吃、美食推荐、品鉴、美食博主
        示例："我喜欢探店"、"我经常找美食"、"我是美食博主"

        【线下聚会社交类】关键词：聚会、聚餐、社交、朋友、约饭、KTV、酒吧
        示例："我喜欢聚会"、"我经常和朋友聚餐"、"我喜欢社交"

        【家装设计类】关键词：装修、家装、设计、家具、装饰、布置、家居
        示例："我喜欢家装设计"、"我装修过房子"、"我关注家居"

        【知识学习类】关键词：学习、读书、知识、技能、课程、培训、进修、考证
        示例："我喜欢学习"、"我经常读书"、"我在学新技能"

        【收藏鉴赏类】关键词：收藏、古董、艺术品、鉴赏、收集、藏品
        示例："我喜欢收藏"、"我懂古董"、"我收藏艺术品"

        【体验生活类】关键词：旅行、旅游、体验、探索、新事物、生活体验
        示例："我喜欢旅行"、"我经常体验新事物"、"我探索生活"

        ====== 3. 情绪与情感状态标签 ======
        - 当前情绪状态：高兴、兴奋、满意、平静、焦虑、沮丧、愤怒等
        - 情感需求：倾诉、陪伴、鼓励、支持、理解、安慰等

        【分析要求】
        1. 仔细理解用户的表达意图，不要只看表面词汇
        2. 对于兴趣爱好，要识别用户的真实兴趣倾向
        3. 注意间接表达，如"你有没有看最近的院线电影"暗示对电影的关注
        4. 结合上下文和语气判断情感状态
        5. 置信度要基于证据的充分程度

        输出JSON格式：
        {{
            "基本人口统计学标签": {{
                "年龄": [{{"tag": "标签名", "confidence": 0.8, "evidence": "支撑证据"}}],
                "性别": [...],
                "地域": [...]
            }},
            "兴趣爱好标签": {{
                "文艺创作类": [...],
                "手工DIY类": [...],
                "音乐欣赏类": [...],
                "音乐演奏类": [...],
                "影视欣赏类": [...],
                "球类运动类": [...],
                "运动比赛欣赏类": [...],
                "极限运动类": [...],
                "养生锻炼身体类": [...],
                "饲养宠物类": [...],
                "家常菜烹饪类": [...],
                "烘焙类": [...],
                "美食探店类": [...],
                "线下聚会社交类": [...],
                "家装设计类": [...],
                "知识学习类": [...],
                "收藏鉴赏类": [...],
                "体验生活类": [...]
            }},
            "情绪与情感状态标签": {{
                "当前情绪状态": [...],
                "情感需求": [...]
            }}
        }}

        【输出要求】
        - confidence范围0.1-1.0，基于证据充分程度
        - evidence必须是从原文提取的具体句子或短语
        - 如果某个二级标签没有明显特征，返回空数组
        - 每个二级标签最多提取3个标签
        - 优先提取最相关、最明显的标签
        """
        
        return prompt
    
    def _parse_llm_response(self, response: str, original_text: str) -> Dict[str, List[TagInfo]]:
        """解析LLM返回的标签 - 增强版"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                print(f"⚠️ 未找到JSON格式响应，原始响应: {response[:200]}...")
                return {}
            
            json_str = json_match.group(0)
            
            # 🔧 优先使用手动解析，避免JSON格式问题
            print("🔧 优先使用手动解析JSON...")
            tag_data = self._parse_incomplete_json(json_str)
            
            if not tag_data:
                print("⚠️ 手动解析失败，尝试标准JSON解析...")
                try:
                    tag_data = json.loads(json_str)
                    print("✅ 标准JSON解析成功")
                except json.JSONDecodeError as e:
                    print(f"❌ 所有解析方法都失败: {e}")
                    print(f"原始响应: {response}")
                    return {}
            else:
                print("✅ 手动解析JSON成功")
            
            parsed_tags = {}
            # 处理新的二级标签结构
            for category_cn, subcategories in tag_data.items():
                # 转换中文分类名为英文key
                category_en = self._get_category_key(category_cn)
                if category_en and isinstance(subcategories, dict):
                    parsed_tags[category_en] = []
                    
                    # 遍历二级标签
                    for subcategory_cn, tags in subcategories.items():
                        # 转换中文二级分类名为英文key
                        subcategory_en = self._get_subcategory_key(category_en, subcategory_cn)
                        if subcategory_en and isinstance(tags, list):
                            for tag_info in tags:
                                tag_name = tag_info.get("tag", "")
                                confidence = tag_info.get("confidence", 0.5)
                                evidence = tag_info.get("evidence", "")
                                
                                # 验证标签有效性
                                if tag_name and confidence > 0.1:
                                    tag = TagInfo(
                                        name=tag_name,
                                        confidence=confidence,
                                        evidence=evidence,
                                        category=category_en,
                                        subcategory=subcategory_en
                                    )
                                    parsed_tags[category_en].append(tag)
                                    
                                    # 调试信息
                                    print(f"✅ 解析标签: {tag_name} -> {category_en}.{subcategory_en} (置信度: {confidence})")
                        else:
                            print(f"⚠️ 子分类映射失败: {subcategory_cn} -> {subcategory_en}")
                else:
                    print(f"⚠️ 分类映射失败: {category_cn} -> {category_en}")
            
            return parsed_tags
            
        except Exception as e:
            print(f"❌ 解析LLM响应错误: {e}")
            print(f"原始响应: {response}")
            return {}
    
    def _get_category_key(self, category_cn: str) -> str:
        """根据中文分类名获取英文key"""
        for key, value in self.tag_categories.items():
            if value.get("name") == category_cn:
                return key
        return ""
    
    def _get_subcategory_key(self, category_en: str, subcategory_cn: str) -> str:
        """根据中文二级分类名获取英文key - 增强版"""
        if category_en in self.tag_categories:
            subcategories = self.tag_categories[category_en].get("subcategories", {})
            
            # 精确匹配
            for key, value in subcategories.items():
                if value == subcategory_cn:
                    return key
            
            # 模糊匹配 - 处理可能的变体
            for key, value in subcategories.items():
                if subcategory_cn in value or value in subcategory_cn:
                    print(f"🔍 模糊匹配: '{subcategory_cn}' -> '{value}' ({key})")
                    return key
            
            # 特殊映射 - 处理常见的错误映射
            special_mappings = {
                "影视欣赏类": "film_tv_appreciation",
                "电影欣赏类": "film_tv_appreciation", 
                "电视剧欣赏类": "film_tv_appreciation",
                "看剧类": "film_tv_appreciation",
                "追剧类": "film_tv_appreciation",
                "院线电影类": "film_tv_appreciation",
                "球类运动类": "ball_sports",
                "足球类": "ball_sports",
                "篮球类": "ball_sports",
                "运动类": "ball_sports",
                "音乐欣赏类": "music_appreciation",
                "听音乐类": "music_appreciation",
                "音乐演奏类": "music_performance",
                "演奏类": "music_performance",
                "唱歌类": "music_performance",
                "知识学习类": "knowledge_learning",
                "学习类": "knowledge_learning",
                "读书类": "knowledge_learning",
                "美食探店类": "food_exploration",
                "美食类": "food_exploration",
                "探店类": "food_exploration",
                "线下聚会社交类": "offline_socializing",
                "社交类": "offline_socializing",
                "聚会类": "offline_socializing"
            }
            
            if subcategory_cn in special_mappings:
                print(f"🔍 特殊映射: '{subcategory_cn}' -> '{special_mappings[subcategory_cn]}'")
                return special_mappings[subcategory_cn]
        
        print(f"❌ 无法映射子分类: '{subcategory_cn}' (分类: {category_en})")
        return ""
    
    def _fix_incomplete_json(self, json_str: str) -> str:
        """修复不完整的JSON字符串"""
        try:
            # 移除可能的markdown代码块标记
            json_str = json_str.replace('```json', '').replace('```', '').strip()
            
            # 查找最后一个有效的完整结构
            # 1. 如果包含 "情感需求": 但不完整，尝试补全
            if '"情感需求":' in json_str and not json_str.rstrip().endswith('}'):
                # 找到情感需求的位置
                emotional_needs_pos = json_str.rfind('"情感需求":')
                if emotional_needs_pos != -1:
                    # 截取到情感需求之前的完整部分，并移除末尾的逗号
                    before_emotional = json_str[:emotional_needs_pos].rstrip(', \n\r\t')
                    # 补全JSON结构
                    json_str = before_emotional + '\n    }\n}'
                    print(f"🔧 修复JSON: 截断在情感需求之前")
            
            # 2. 处理其他不完整的情况
            elif '"情感需求"' in json_str and not json_str.rstrip().endswith('}'):
                # 如果只是 "情感需求" 没有冒号
                emotional_needs_pos = json_str.rfind('"情感需求"')
                if emotional_needs_pos != -1:
                    before_emotional = json_str[:emotional_needs_pos].rstrip(', \n\r\t')
                    json_str = before_emotional + '\n    }\n}'
                    print(f"🔧 修复JSON: 截断在情感需求标签之前")
            
            # 3. 确保所有大括号都正确闭合
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            if open_braces > close_braces:
                # 添加缺失的闭合括号
                missing_braces = open_braces - close_braces
                json_str += '}' * missing_braces
                print(f"🔧 修复JSON: 添加了 {missing_braces} 个闭合括号")
            
            # 4. 移除末尾多余的逗号
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # 5. 处理末尾的冒号问题
            json_str = re.sub(r':\s*$', '', json_str.rstrip())
            if not json_str.endswith('}'):
                json_str += '}'
            
            print(f"🔧 修复后的JSON长度: {len(json_str)} 字符")
            return json_str
            
        except Exception as e:
            print(f"⚠️ JSON修复过程中出错: {e}")
            return json_str
    
    def _parse_incomplete_json(self, json_str: str) -> Dict:
        """手动解析不完整的JSON，提取有效的标签数据 - 增强版"""
        try:
            # 移除markdown标记和多余空白
            json_str = json_str.replace('```json', '').replace('```', '').strip()
            
            # 使用正则表达式提取各个标签分类
            result = {}
            
            # 🔧 更鲁棒的提取基本人口统计学标签
            demo_patterns = [
                r'"基本人口统计学标签":\s*\{([^}]*)\}',  # 完整匹配
                r'"基本人口统计学标签":\s*\{(.*?)(?="兴趣爱好标签"|"情绪与情感状态标签"|$)'  # 截断匹配
            ]
            
            for pattern in demo_patterns:
                demo_match = re.search(pattern, json_str, re.DOTALL)
                if demo_match:
                    demo_content = demo_match.group(1).rstrip(', \n\r\t}')
                    parsed_demo = self._parse_category_content(demo_content)
                    if parsed_demo:
                        result["基本人口统计学标签"] = parsed_demo
                        print("✅ 提取基本人口统计学标签")
                        break
            
            # 🔧 更鲁棒的提取兴趣爱好标签
            interest_patterns = [
                r'"兴趣爱好标签":\s*\{(.*?)\}(?=\s*,\s*"情绪与情感状态标签")',  # 完整匹配
                r'"兴趣爱好标签":\s*\{(.*?)(?=\s*"情绪与情感状态标签"|$)',  # 截断匹配
                r'"兴趣爱好标签":\s*\{([^}]*(?:\}[^}]*)*)'  # 复杂嵌套匹配
            ]
            
            for pattern in interest_patterns:
                interest_match = re.search(pattern, json_str, re.DOTALL)
                if interest_match:
                    interest_content = interest_match.group(1).rstrip(', \n\r\t}')
                    parsed_interest = self._parse_hobby_content(interest_content)
                    if parsed_interest:
                        result["兴趣爱好标签"] = parsed_interest
                        print("✅ 提取兴趣爱好标签")
                        break
            
            # 🔧 更鲁棒的提取情绪与情感状态标签
            emotion_patterns = [
                r'"情绪与情感状态标签":\s*\{([^}]*)\}',  # 完整匹配
                r'"情绪与情感状态标签":\s*\{(.*?)(?=\s*$)',  # 截断匹配
                r'"情绪与情感状态标签":\s*\{([^}]*)'  # 不完整匹配
            ]
            
            for pattern in emotion_patterns:
                emotion_match = re.search(pattern, json_str, re.DOTALL)
                if emotion_match:
                    emotion_content = emotion_match.group(1).rstrip(', \n\r\t}')
                    parsed_emotion = self._parse_category_content(emotion_content)
                    if parsed_emotion:
                        result["情绪与情感状态标签"] = parsed_emotion
                        print("✅ 提取情绪与情感状态标签")
                        break
            
            print(f"🎯 手动解析结果: 成功提取 {len(result)} 个分类")
            return result
            
        except Exception as e:
            print(f"⚠️ 手动解析JSON出错: {e}")
            return {}
    
    def _parse_category_content(self, content: str) -> Dict:
        """解析分类内容"""
        result = {}
        
        # 使用正则表达式提取各个子分类
        subcategory_pattern = r'"([^"]+)":\s*\[(.*?)\]'
        matches = re.findall(subcategory_pattern, content, re.DOTALL)
        
        for subcategory_name, tags_content in matches:
            tags = []
            if tags_content.strip():
                # 提取标签信息
                tag_pattern = r'\{\s*"tag":\s*"([^"]+)"\s*,\s*"confidence":\s*([0-9.]+)\s*,\s*"evidence":\s*"([^"]+)"\s*\}'
                tag_matches = re.findall(tag_pattern, tags_content)
                for tag_name, confidence, evidence in tag_matches:
                    tags.append({
                        "tag": tag_name,
                        "confidence": float(confidence),
                        "evidence": evidence
                    })
            result[subcategory_name] = tags
        
        return result
    
    def _parse_hobby_content(self, content: str) -> Dict:
        """特殊处理兴趣爱好标签内容 - 增强版"""
        result = {}
        
        # 定义所有可能的子分类
        subcategories = [
            "文艺创作类", "手工DIY类", "音乐欣赏类", "音乐演奏类", "影视欣赏类",
            "球类运动类", "运动比赛欣赏类", "极限运动类", "养生锻炼身体类", "饲养宠物类",
            "家常菜烹饪类", "烘焙类", "美食探店类", "线下聚会社交类", "家装设计类",
            "知识学习类", "收藏鉴赏类", "体验生活类"
        ]
        
        for subcategory in subcategories:
            # 🔧 使用多种模式匹配，提高成功率
            patterns = [
                f'"{subcategory}":\\s*\\[(.*?)\\]',  # 标准模式
                f'"{subcategory}":\\s*\\[(.*?)(?=\\s*,\\s*"|\\s*\\}}|$)',  # 截断模式
                f'"{subcategory}":\\s*\\[([^\\]]*)'  # 不完整模式
            ]
            
            tags = []
            matched = False
            
            for pattern in patterns:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    tags_content = match.group(1).rstrip(', \n\r\t]')
                    
                    if tags_content.strip():
                        # 🔧 更鲁棒的标签提取
                        tag_patterns = [
                            r'\{\s*"tag":\s*"([^"]+)"\s*,\s*"confidence":\s*([0-9.]+)\s*,\s*"evidence":\s*"([^"]+)"\s*\}',  # 完整格式
                            r'\{\s*"tag":\s*"([^"]+)"\s*,\s*"confidence":\s*([0-9.]+)\s*,\s*"evidence":\s*"([^"]*)"?\s*(?:\}|$)',  # 不完整格式
                            r'\{\s*"tag":\s*"([^"]+)"\s*,\s*"confidence":\s*([0-9.]+)'  # 最简格式
                        ]
                        
                        for tag_pattern in tag_patterns:
                            tag_matches = re.findall(tag_pattern, tags_content)
                            if tag_matches:
                                for match_tuple in tag_matches:
                                    if len(match_tuple) >= 2:
                                        tag_name = match_tuple[0]
                                        confidence = match_tuple[1]
                                        evidence = match_tuple[2] if len(match_tuple) > 2 else ""
                                        
                                        tags.append({
                                            "tag": tag_name,
                                            "confidence": float(confidence),
                                            "evidence": evidence
                                        })
                                        print(f"🎯 提取到兴趣标签: {tag_name} -> {subcategory} (置信度: {confidence})")
                                matched = True
                                break
                    
                    if matched or not tags_content.strip():
                        matched = True
                        break
            
            result[subcategory] = tags
        
        # 统计提取结果
        total_tags = sum(len(tags) for tags in result.values())
        print(f"📊 兴趣爱好标签提取完成: {total_tags} 个标签分布在 {len([k for k, v in result.items() if v])} 个子分类中")
        
        return result
    
    def _analyze_behavior_patterns(self, text: str) -> Dict[str, List[TagInfo]]:
        """基于规则的行为模式分析"""
        behavior_tags = {}
        
        # 文本长度分析 - 映射到情感需求
        if len(text) > 100:
            behavior_tags["emotional_state"] = [
                TagInfo("偏好详细表达", 0.6, f"文本长度{len(text)}字符", "emotional_state", "emotional_needs")
            ]
        elif len(text) < 30:
            behavior_tags["emotional_state"] = [
                TagInfo("偏好简短交流", 0.6, f"文本长度{len(text)}字符", "emotional_state", "emotional_needs")
            ]
        
        # 情感词检测
        positive_words = ["开心", "高兴", "快乐", "满意", "不错", "好的"]
        negative_words = ["难过", "沮丧", "失望", "糟糕", "痛苦", "烦躁"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count and positive_count > 0:
            if "emotional_state" not in behavior_tags:
                behavior_tags["emotional_state"] = []
            behavior_tags["emotional_state"].append(
                TagInfo("情绪偏向积极", 0.7, f"积极词汇{positive_count}个", "emotional_state", "current_mood")
            )
        elif negative_count > positive_count and negative_count > 0:
            if "emotional_state" not in behavior_tags:
                behavior_tags["emotional_state"] = []
            behavior_tags["emotional_state"].append(
                TagInfo("情绪偏向消极", 0.7, f"消极词汇{negative_count}个", "emotional_state", "current_mood")
            )
        
        return behavior_tags
    
    def _merge_tag_results(self, llm_tags: Dict, behavior_tags: Dict) -> Dict[str, List[TagInfo]]:
        """融合LLM提取和行为分析的结果"""
        merged = llm_tags.copy()
        
        for category, tags in behavior_tags.items():
            if category not in merged:
                merged[category] = []
            
            # 避免重复标签
            existing_names = [tag.name for tag in merged[category]]
            for tag in tags:
                if tag.name not in existing_names:
                    merged[category].append(tag)
        
        return merged
    
    def _apply_tag_standardization(self, tags: Dict[str, List[TagInfo]]) -> Dict[str, List[TagInfo]]:
        """应用标签标准化和相似性合并"""
        standardized_tags = {}
        
        for category, tag_list in tags.items():
            if not tag_list:
                continue
            
            # 对每个类别的标签进行标准化
            standardized_list = []
            
            for tag in tag_list:
                # 获取类别特定的规则
                category_rules = self.similarity_detector.category_similarity_rules.get(category, {})
                
                # 标准化标签名称
                standardized_name = self.similarity_detector._standardize_tag_name(tag.name, category_rules)
                
                # 如果标签名称发生了变化，创建新的TagInfo对象
                if standardized_name != tag.name:
                    standardized_tag = TagInfo(
                        name=standardized_name,
                        confidence=tag.confidence,
                        evidence=f"标准化自: {tag.name} | {tag.evidence}",
                        category=tag.category,
                        subcategory=tag.subcategory
                    )
                    print(f"🔧 标签标准化: {tag.name} -> {standardized_name}")
                else:
                    standardized_tag = tag
                
                # 检查是否已有相同的标准化标签
                existing_tag = None
                for existing in standardized_list:
                    if existing.name == standardized_tag.name and existing.subcategory == standardized_tag.subcategory:
                        existing_tag = existing
                        break
                
                if existing_tag:
                    # 合并置信度（取更高的值）
                    if standardized_tag.confidence > existing_tag.confidence:
                        existing_tag.confidence = standardized_tag.confidence
                        existing_tag.evidence = f"{existing_tag.evidence}; {standardized_tag.evidence}"
                    print(f"🔄 合并相似标签: {standardized_tag.name} (置信度: {existing_tag.confidence:.2f})")
                else:
                    standardized_list.append(standardized_tag)
            
            if standardized_list:
                standardized_tags[category] = standardized_list
        
        return standardized_tags
