"""
quick_test_api.py - 快速测试 LLM API 连通性和流式效果
用法：cd backend && python quick_test_api.py
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from openai import AsyncOpenAI
from config import get_llm_config


async def test():
    provider, config = get_llm_config()
    print(f"Provider: {provider}")
    print(f"Model: {config.get('model')}")
    print(f"Base URL: {config.get('base_url')}")
    print(f"API Key set: {bool(config.get('api_key'))}")
    print("-" * 50)

    client = AsyncOpenAI(
        api_key=config.get("api_key"),
        base_url=config.get("base_url"),
    )

    print("\n[测试] 短问题流式输出（观察是否逐字出现）：")
    t0 = __import__('time').time()
    first = None
    content = ""

    try:
        resp = await client.chat.completions.create(
            model=config.get("model"),
            messages=[
                {"role": "user", "content": "请用一句话介绍钙钛矿结构。"},
            ],
            stream=True,
            timeout=30,
        )
        async for chunk in resp:
            delta = chunk.choices[0].delta.content
            if delta:
                if first is None:
                    first = __import__('time').time() - t0
                    print(f"\n[首字延迟: {first:.2f}s]\n")
                print(delta, end="", flush=True)
                content += delta
        print(f"\n\n[完成] 总耗时: {__import__('time').time() - t0:.2f}s, 字数: {len(content)}")
    except Exception as e:
        print(f"\n[错误] {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test())
