import streamlit as st
import openai


class LLMClient:
    """支持 Streamlit Cloud secrets 的 LLM 客户端"""
    
    def __init__(self):
        # 优先从 st.secrets 读取（Streamlit Cloud）
        # 回退到环境变量（本地开发）
        self.api_key = self._get_secret("DEEPSEEK_API_KEY") or self._get_secret("api_key", "")
        self.base_url = self._get_secret("DEEPSEEK_BASE_URL") or self._get_secret("base_url", "https://api.deepseek.com")
        self.model = self._get_secret("DEEPSEEK_MODEL") or self._get_secret("model", "deepseek-v4-flash")
        
        if not self.api_key:
            raise ValueError("API Key not configured. Please set DEEPSEEK_API_KEY in Streamlit secrets.")
        
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        self.client = openai.OpenAI(**client_kwargs)
    
    def _get_secret(self, key: str, default=None):
        """安全读取 secrets，兼容多级配置"""
        try:
            # 支持 [llm] 分组配置
            if "llm" in st.secrets and key in st.secrets["llm"]:
                return st.secrets["llm"][key]
            # 支持顶级配置
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass
        # 回退到环境变量
        import os
        return os.getenv(key, default)
    
    def chat(self, system_prompt: str, user_prompt: str, timeout: int = 120) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            timeout=timeout,
            extra_body={"thinking": {"type": "disabled"}},
        )
        return response.choices[0].message.content
    
    def chat_stream(self, system_prompt: str, user_prompt: str, timeout: int = 120):
        """同步流式，逐字 yield"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            timeout=timeout,
            stream=True,
            extra_body={"thinking": {"type": "disabled"}},
        )
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content
