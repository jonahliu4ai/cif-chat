import sys
sys.path.insert(0, r'D:\src\Ziang-Nan\晶体学-ZiangNan\cif-chat\backend')

import os
from dotenv import load_dotenv

# 加载 .env
load_dotenv(dotenv_path=r'D:\src\Ziang-Nan\晶体学-ZiangNan\cif-chat\backend\.env')

print(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
print(f"DEEPSEEK_API_KEY set: {bool(os.getenv('DEEPSEEK_API_KEY'))}")
print(f"SILICONFLOW_API_KEY set: {bool(os.getenv('SILICONFLOW_API_KEY'))}")
print(f"OPENAI_API_KEY set: {bool(os.getenv('OPENAI_API_KEY'))}")

from services.cif_parser import CIFParser
from services.llm_client import LLMClient
from services.prompt_templates import STRUCTURE_DESCRIPTION

p = CIFParser(r'D:\src\Ziang-Nan\晶体学-ZiangNan\cif-chat\tests\CaTiO3.cif')
structure_data = p.export_for_llm()
print(f"\n结构数据长度: {len(structure_data)} 字符")

try:
    llm = LLMClient()
    print(f"LLM 初始化成功: model={llm.model}")
    print("正在调用 LLM...")
    analysis = llm.chat(
        system_prompt="You are a helpful crystallography assistant.",
        user_prompt=STRUCTURE_DESCRIPTION.format(structure_data=structure_data),
    )
    print(f"LLM 返回成功，长度: {len(analysis)} 字符")
    print(f"前 200 字: {analysis[:200]}")
except Exception as e:
    print(f"LLM 调用失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
