"""
diagnose_stream.py - 诊断流式输出的瓶颈
用法：cd backend && python diagnose_stream.py
"""
import time
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def diagnose_stream():
    """直接测试 DeepSeek API 的流式延迟，绕过后端"""
    from openai import AsyncOpenAI

    provider = os.getenv("LLM_PROVIDER", "deepseek")

    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        base_url = "https://api.deepseek.com"
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    elif provider == "deepseek-siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY", "")
        base_url = "https://api.siliconflow.cn/v1"
        model = os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V4-Flash")
    else:
        print(f"不支持的 provider: {provider}")
        return

    print(f"=" * 60)
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"API Key 前8位: {api_key[:8]}...")
    print(f"=" * 60)

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    # 模拟实际的长 prompt（从 prompt_templates.py 复制的）
    long_system = "你是一位资深晶体学家和无机化学家。请根据以下晶体结构数据进行全面的学术分析，用中文撰写。"
    long_user_prefix = """## 分析要求

1. **总体判断**
   - 化合物组成与化学式
   - 推断各元素的氧化态

2. **晶体学与对称性分析**（重点）
   - 空间群的对称元素
   - 点群与空间群的关系

3. **金属核心与配位几何**
   - 各金属中心的配位数
   - 配位多面体几何构型
   - 关键键角数据

4. **键长与化学键分析**
   - 金属-配体键长合理性
   - 金属-金属距离分析

5. **配体作用与拓扑**
   - 配体的桥连/螯合模式
   - 整体拓扑描述

6. **晶体堆积与弱相互作用**
   - 分子间作用力类型
   - 堆积方向性

7. **一句话总结**

Structure Data:
"""
    # 模拟一个典型的 CIF 导出文本
    structure_data = """Ca1 Ti1 O3
Space group: Pm-3m (No. 221)
Lattice: a=3.905 b=3.905 c=3.905 alpha=90 beta=90 gamma=90
Volume: 59.52 A^3
Sites:
  Ca (0.000, 0.000, 0.000) Wyckoff 1a
  Ti (0.500, 0.500, 0.500) Wyckoff 1b
  O  (0.500, 0.500, 0.000) Wyckoff 3c
Bond lengths:
  Ti-O: 1.953 A (x6)
Angles:
  O-Ti-O: 90.0, 180.0 deg"""

    long_user = long_user_prefix + structure_data

    # ========== 测试 1：长 Prompt 流式 ==========
    print("\n[测试 1/3] 长 Prompt 流式调用...")
    print(f"System prompt: {len(long_system)} 字")
    print(f"User prompt: {len(long_user)} 字")

    t0 = time.time()
    chunks = []
    first_chunk_time = None
    total_content = ""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": long_system},
                {"role": "user", "content": long_user},
            ],
            temperature=0.3,
            stream=True,
            timeout=120,
        )
        async for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                now = time.time()
                if first_chunk_time is None:
                    first_chunk_time = now - t0
                    print(f"  ✅ 首 chunk 到达: {first_chunk_time:.2f}s")
                chunks.append((now - t0, content))
                total_content += content
    except Exception as e:
        print(f"  ❌ 错误: {type(e).__name__}: {e}")
        return

    total_time = time.time() - t0
    print(f"  ✅ 完成: {total_time:.2f}s")
    print(f"  总 chunk 数: {len(chunks)}")
    print(f"  总输出字数: {len(total_content)}")
    print(f"  输出速率: {len(total_content)/max(total_time-first_chunk_time, 0.1):.1f} 字/秒")

    # 分析 chunk 分布
    if len(chunks) >= 3:
        print(f"\n  前5个 chunk 的到达时间：")
        for i, (t, text) in enumerate(chunks[:5]):
            print(f"    chunk {i+1}: t={t:.2f}s, text='{text[:30].replace(chr(10), '\\n')}'")

    # ========== 测试 2：短 Prompt 流式（对照组）==========
    print(f"\n[测试 2/3] 短 Prompt 流式调用（对照组）...")
    short_system = "你是一个助手。"
    short_user = "Ti 的配位数是多少？"

    t0 = time.time()
    short_first = None
    short_content = ""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": short_system},
                {"role": "user", "content": short_user},
            ],
            temperature=0.3,
            stream=True,
            timeout=30,
        )
        async for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                if short_first is None:
                    short_first = time.time() - t0
                short_content += content
    except Exception as e:
        print(f"  ❌ 错误: {type(e).__name__}: {e}")
        return

    short_total = time.time() - t0
    print(f"  ✅ 首 chunk: {short_first:.2f}s, 总耗时: {short_total:.2f}s")

    # ========== 测试 3：长 Prompt 非流式 ==========
    print(f"\n[测试 3/3] 长 Prompt 非流式（对照组）...")
    t0 = time.time()
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": long_system},
                {"role": "user", "content": long_user},
            ],
            temperature=0.3,
            timeout=120,
        )
        nonstream_time = time.time() - t0
        print(f"  ✅ 完成: {nonstream_time:.2f}s")
        print(f"  输出字数: {len(resp.choices[0].message.content)}")
    except Exception as e:
        print(f"  ❌ 错误: {type(e).__name__}: {e}")

    # ========== 总结 ==========
    print(f"\n{'=' * 60}")
    print("诊断总结：")
    print(f"  长 prompt 首 chunk 延迟: {first_chunk_time:.1f}s")
    print(f"  短 prompt 首 chunk 延迟: {short_first:.1f}s")
    print(f"  长/短延迟比: {first_chunk_time/max(short_first, 0.1):.1f}x")
    if first_chunk_time and short_first:
        if first_chunk_time > 10:
            print(f"\n  ⚠️  结论：TTFT 过长（>{first_chunk_time:.0f}s），这是 API 端的问题。")
            print(f"      建议：缩短 prompt 或换更快的模型。")
        else:
            print(f"\n  ✅ TTFT 正常，问题可能出在传输层缓冲。")


if __name__ == "__main__":
    asyncio.run(diagnose_stream())
