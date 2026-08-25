"""
test_v4_flash.py - 直接测试 deepseek-v4-flash 的流式速度
用法：cd backend && python test_v4_flash.py
"""
import asyncio
import time
from openai import AsyncOpenAI
from config import get_llm_config


async def test():
    provider, config = get_llm_config()
    print(f"Provider: {provider}")
    print(f"Model: {config.get('model')}")
    print(f"Base URL: {config.get('base_url')}")
    print("-" * 50)

    client = AsyncOpenAI(
        api_key=config.get("api_key"),
        base_url=config.get("base_url"),
    )

    # 模拟后端的实际 prompt（简短版）
    system = "You are a helpful crystallography assistant."
    user = """Analyze this crystal structure:
Ca1 Ti1 O3, Space group: Pm-3m, Lattice: a=3.905 Å
Sites: Ca(0,0,0), Ti(0.5,0.5,0.5), O(0.5,0.5,0)
Bonds: Ti-O: 1.953 Å (x6)"""

    print("\n[测试] 使用当前配置的模型流式调用...")
    t0 = time.time()
    first = None
    content = ""

    try:
        resp = await client.chat.completions.create(
            model=config.get("model"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            stream=True,
            timeout=120,
        )
        async for chunk in resp:
            delta = chunk.choices[0].delta.content
            if delta:
                if first is None:
                    first = time.time() - t0
                    print(f"\n[首字延迟: {first:.2f}s]")
                print(delta, end="", flush=True)
                content += delta
        print(f"\n\n[完成] 总耗时: {time.time()-t0:.2f}s, 字数: {len(content)}")
    except Exception as e:
        print(f"\n[错误] {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test())
