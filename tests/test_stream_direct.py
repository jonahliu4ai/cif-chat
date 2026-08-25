import sys
sys.path.insert(0, r'D:\src\Ziang-Nan\晶体学-ZiangNan\cif-chat\backend')

from config import get_llm_config
from services.llm_client import LLMClient
import time

provider, config = get_llm_config()
print(f"Provider: {provider}")
print(f"Model: {config.get('model')}")
print(f"Base URL: {config.get('base_url')}")

llm = LLMClient()

prompt = "用一句话描述晶体结构 CaTiO3。"

print("\n测试流式输出...")
t0 = time.time()
first_token_time = None
token_count = 0

for text in llm.chat_stream(
    system_prompt="You are a helpful assistant.",
    user_prompt=prompt,
    timeout=60,
):
    if first_token_time is None:
        first_token_time = time.time() - t0
        print(f"首字到达: {first_token_time:.2f}s")
    token_count += 1
    print(text, end="", flush=True)

total = time.time() - t0
print(f"\n\n总耗时: {total:.2f}s")
print(f"Token 数: {token_count}")
print(f"首字延迟: {first_token_time:.2f}s" if first_token_time else "无输出")
