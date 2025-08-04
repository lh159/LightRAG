import os
import openai
import yaml
from typing import Optional

class LLMClient:
    def __init__(self, api_key: Optional[str] = None, model: str = None, base_url: str = None):
        # 从配置文件加载设置
        self.config = self._load_config()
        
        self.api_key = api_key or self.config.get('llm', {}).get('api_key') or os.getenv("OPENAI_API_KEY")
        self.model = model or self.config.get('llm', {}).get('model', "deepseek-chat")
        self.base_url = base_url or self.config.get('llm', {}).get('base_url')
        
        if not self.api_key:
            raise ValueError("API key is required")
        
        # 配置OpenAI客户端以使用DeepSeek API
        if self.base_url:
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = openai.OpenAI(api_key=self.api_key)
    
    def _load_config(self):
        """加载配置文件"""
        try:
            with open('config.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"警告: 无法加载配置文件: {e}")
            return {}

    def complete(self, prompt: str, max_tokens: int = 300, temperature: float = 0.3) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM调用错误: {e}")
            return ""
