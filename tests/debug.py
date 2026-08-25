import sys
sys.path.insert(0, r'D:\src\Ziang-Nan\晶体学-ZiangNan\cif-chat\backend')

from services.cif_parser import CIFParser

try:
    p = CIFParser(r'D:\src\Ziang-Nan\晶体学-ZiangNan\cif-chat\tests\CaTiO3.cif')
    info = p.get_basic_info()
    print("CIF 解析成功:")
    print(info)
    print("\n结构数据前 500 字:")
    print(p.export_for_llm()[:500])
except Exception as e:
    print(f"CIF 解析失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n--- 测试 config ---")
try:
    from config import get_llm_config
    provider, config = get_llm_config()
    print(f"提供商: {provider}")
    print(f"模型: {config.get('model')}")
    print(f"base_url: {config.get('base_url')}")
    print(f"api_key 是否设置: {bool(config.get('api_key'))}")
except Exception as e:
    print(f"Config 错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
