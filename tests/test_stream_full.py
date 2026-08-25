import sys
sys.path.insert(0, r'D:\src\Ziang-Nan\晶体学-ZiangNan\cif-chat\backend')

from services.cif_parser import CIFParser
from services.llm_client import LLMClient
from services.prompt_templates import STRUCTURE_DESCRIPTION
import time

p = CIFParser(r'D:\src\Ziang-Nan\晶体学-ZiangNan\cif-chat\tests\CaTiO3.cif')
structure_text = p.export_for_llm()
prompt = STRUCTURE_DESCRIPTION.format(structure_data=structure_text)

print(f"Prompt length: {len(prompt)} chars")
print(f"Prompt preview:\n{prompt[:500]}...\n")

llm = LLMClient()

print("测试流式输出（完整分析 prompt）...")
t0 = time.time()
first_token_time = None
token_count = 0
buffer = ""

for text in llm.chat_stream(
    system_prompt="You are a helpful crystallography assistant.",
    user_prompt=prompt,
    timeout=120,
):
    if first_token_time is None:
        first_token_time = time.time() - t0
        print(f"首字到达: {first_token_time:.2f}s")
    token_count += 1
    buffer += text
    # 每 10 个 token 打印一次进度
    if token_count % 10 == 0:
        print(f"  [{token_count} tokens, {time.time()-t0:.1f}s]", end="\r")

total = time.time() - t0
print(f"\n总耗时: {total:.2f}s")
print(f"Token 数: {token_count}")
print(f"首字延迟: {first_token_time:.2f}s")
print(f"\n回复前 200 字:\n{buffer[:200]}...")
