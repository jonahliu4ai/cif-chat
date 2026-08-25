"""
test_backend_stream.py - 直接测试后端流式端点，绕过 Streamlit
用法：cd backend && python test_backend_stream.py
"""
import time
import requests

API_URL = "http://localhost:8000"

# 模拟一个典型的 structure_text
structure_text = """Ca1 Ti1 O3
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

print("=" * 60)
print("测试后端 /api/analyze/stream 流式端点")
print("=" * 60)

t0 = time.time()
resp = requests.post(
    f"{API_URL}/api/analyze/stream",
    json={"structure_text": structure_text},
    stream=True,
)

first = None
chunk_count = 0
char_count = 0
last_flush = t0

# 关键：不用 iter_content，直接用 raw.stream 读取原始字节
# 这样可以排除 requests 库的缓冲干扰
for chunk in resp.raw.stream(1, decode_content=False):
    if chunk:
        now = time.time()
        if first is None:
            first = now - t0
            print(f"\n✅ 首字节到达: {first:.2f}s")
        chunk_count += 1
        # 尝试解码看看是不是完整字符
        try:
            text = chunk.decode('utf-8')
            char_count += len(text)
            if chunk_count <= 10:
                print(f"  chunk {chunk_count}: t={now-t0:.3f}s char='{text}'")
            elif chunk_count == 11:
                print("  ... (后续省略)")
        except UnicodeDecodeError:
            # 中文字符被拆分了，这是正常的（UTF-8 中文 3 字节）
            if chunk_count <= 10:
                print(f"  chunk {chunk_count}: t={now-t0:.3f}s bytes={chunk.hex()} (不完整 UTF-8)")

elapsed = time.time() - t0
print(f"\n{'=' * 60}")
print(f"总 chunk 数: {chunk_count}")
print(f"总字符数: {char_count}")
print(f"总耗时: {elapsed:.2f}s")
print(f"首字节延迟: {first:.2f}s" if first else "无数据")

if first and chunk_count > 0:
    if chunk_count > 100:
        print(f"\n✅ 后端流式正常：chunk 数量多（{chunk_count}），说明是逐字节/逐小块传输")
    else:
        print(f"\n⚠️ 后端流式异常：chunk 数量少（{chunk_count}），可能存在缓冲")
