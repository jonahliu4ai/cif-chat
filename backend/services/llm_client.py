import openai
from config import get_llm_config


class LLMClient:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        if api_key is None or model is None:
            provider, config = get_llm_config()
            api_key = api_key or config.get("api_key", "")
            base_url = base_url or config.get("base_url")
            model = model or config.get("model", "deepseek-chat")
        
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        self.client = openai.OpenAI(**client_kwargs)
        self.async_client = openai.AsyncOpenAI(**client_kwargs)
        self.model = model
    
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
        """同步流式（保留给旧接口）"""
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

    async def chat_stream_async(self, system_prompt: str, user_prompt: str, timeout: int = 120):
        """异步流式，关闭 thinking 模式以避免超长首字延迟"""
        import time
        t0 = time.time()
        print(f"[LLM] 开始调用，prompt 长度: {len(system_prompt) + len(user_prompt)} 字")
        
        response = await self.async_client.chat.completions.create(
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
        
        t1 = time.time()
        print(f"[LLM] API 连接建立: {t1-t0:.2f}s")
        chunk_idx = 0
        async for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                if chunk_idx == 0:
                    print(f"[LLM] 首 chunk 到达: {time.time()-t0:.2f}s")
                chunk_idx += 1
                yield content
        print(f"[LLM] 完成，总 chunk: {chunk_idx}, 总耗时: {time.time()-t0:.2f}s")
