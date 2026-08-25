import sys
sys.path.insert(0, r'D:\src\Ziang-Nan\晶体学-ZiangNan\cif-chat\backend')

from services.cif_parser import CIFParser

p = CIFParser(r'D:\src\Ziang-Nan\晶体学-ZiangNan\cif-chat\tests\CaTiO3.cif')
t = p.export_for_llm()
print(f"Prompt length: {len(t)} chars")
print("\nPreview:")
print(t[:800])
