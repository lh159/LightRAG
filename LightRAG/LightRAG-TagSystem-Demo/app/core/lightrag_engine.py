import os
import json
import yaml
import openai
from typing import Dict, List, Optional
from lightrag.core import Generator, LocalDB

class LightRAGEngine:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.user_data_path = f"user_data/{user_id}"
        self.ensure_user_directory()
        
        # 从配置文件加载设置
        self.config = self._load_config()
        
        # 直接使用OpenAI客户端连接DeepSeek
        self.openai_client = self._create_openai_client()
        
        # 初始化本地数据库
        self.local_db = LocalDB()
        
    def _load_config(self):
        """加载配置文件"""
        try:
            with open('config.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"警告: 无法加载配置文件: {e}")
            return {}
    
    def _create_openai_client(self):
        """创建OpenAI客户端连接DeepSeek"""
        api_key = self.config.get('llm', {}).get('api_key')
        base_url = self.config.get('llm', {}).get('base_url')
        
        if not api_key:
            raise ValueError("API key is required")
        
        # 创建OpenAI客户端，配置为使用DeepSeek
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        return client
        
    def ensure_user_directory(self):
        """确保用户目录存在"""
        os.makedirs(self.user_data_path, exist_ok=True)
        os.makedirs(f"{self.user_data_path}/documents", exist_ok=True)
        os.makedirs(f"{self.user_data_path}/knowledge_graph", exist_ok=True)
        
    def insert_knowledge(self, text: str, metadata: Dict = None):
        """插入知识到用户知识库"""
        try:
            # 创建文档记录
            doc_data = {
                "content": text,
                "metadata": metadata or {},
                "user_id": self.user_id,
                "timestamp": json.dumps({"created": "now"}, default=str)
            }
            
            # 确保文档目录存在
            docs_dir = f"{self.user_data_path}/documents"
            os.makedirs(docs_dir, exist_ok=True)
            
            # 保存到本地文件
            existing_files = [f for f in os.listdir(docs_dir) if f.endswith('.json')]
            doc_file = f"{docs_dir}/doc_{len(existing_files)}.json"
            
            with open(doc_file, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, ensure_ascii=False, indent=2)
                
            return {"status": "success", "message": "知识插入成功"}
        except Exception as e:
            return {"status": "error", "message": f"插入失败: {str(e)}"}
    
    def query_knowledge(self, query: str, mode: str = "hybrid") -> str:
        """查询知识库"""
        try:
            # 简单的知识检索（基于关键词匹配）
            documents_dir = f"{self.user_data_path}/documents"
            if not os.path.exists(documents_dir):
                return "知识库为空，请先添加一些知识。"
            
            relevant_docs = []
            doc_files = [f for f in os.listdir(documents_dir) if f.endswith('.json')]
            
            for doc_file in doc_files[:5]:  # 限制检索数量
                doc_path = os.path.join(documents_dir, doc_file)
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        content = doc_data.get('content', '')
                        
                        # 简单的关键词匹配
                        query_words = query.lower().split()
                        content_lower = content.lower()
                        
                        if any(word in content_lower for word in query_words):
                            relevant_docs.append(content[:200] + "..." if len(content) > 200 else content)
                except Exception as e:
                    continue
            
            if relevant_docs:
                return f"找到相关知识:\\n" + "\\n\\n".join(relevant_docs)
            else:
                return "未找到相关知识，但我会基于一般知识来回答您的问题。"
                
        except Exception as e:
            return f"查询错误: {str(e)}"
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """使用DeepSeek API生成回应"""
        try:
            model = self.config.get('llm', {}).get('model', 'deepseek-chat')
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"生成回应失败: {e}")
            return "抱歉，我现在无法生成回应，请检查网络连接或API配置。"
    
    def get_knowledge_graph(self):
        """获取知识图谱结构"""
        try:
            documents_dir = f"{self.user_data_path}/documents"
            if os.path.exists(documents_dir):
                doc_count = len([f for f in os.listdir(documents_dir) if f.endswith('.json')])
                return {"status": "success", "document_count": doc_count}
            else:
                return {"status": "success", "document_count": 0}
        except Exception as e:
            return {"status": "error", "message": str(e)}
