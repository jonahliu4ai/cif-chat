import requests
import sys

API_URL = "http://localhost:8000"
CIF_PATH = r"D:\src\Ziang-Nan\晶体学-ZiangNan\cif-chat\tests\CaTiO3.cif"

def test_parse():
    print("=" * 50)
    print("测试 1: /api/parse (CIF 解析)")
    print("=" * 50)
    
    with open(CIF_PATH, "rb") as f:
        resp = requests.post(f"{API_URL}/api/parse", files={"file": ("CaTiO3.cif", f, "chemical/x-cif")})
    
    if resp.status_code != 200:
        print(f"❌ 失败: {resp.status_code} - {resp.text}")
        return None
    
    data = resp.json()
    print(f"✅ 成功")
    print(f"   化学式: {data['basic_info']['formula']}")
    print(f"   空间群: {data['basic_info']['space_group']}")
    print(f"   结构数据长度: {len(data['structure_text'])} 字符")
    return data["structure_text"]


def test_analyze(structure_text: str):
    print("\n" + "=" * 50)
    print("测试 2: /api/analyze (LLM 分析)")
    print("=" * 50)
    
    print("正在调用 LLM，请等待...")
    resp = requests.post(f"{API_URL}/api/analyze", json={"structure_text": structure_text})
    
    if resp.status_code != 200:
        print(f"❌ 失败: {resp.status_code} - {resp.text}")
        return
    
    data = resp.json()
    print(f"✅ 成功")
    print(f"   AI 分析长度: {len(data['analysis'])} 字符")
    print(f"\n前 300 字预览:\n{data['analysis'][:300]}...")


def test_chat(structure_text: str):
    print("\n" + "=" * 50)
    print("测试 3: /api/chat (追问)")
    print("=" * 50)
    
    question = "Ti 的配位数是多少？"
    print(f"问题: {question}")
    print("正在调用 LLM，请等待...")
    
    resp = requests.post(f"{API_URL}/api/chat", json={
        "structure_data": structure_text,
        "question": question
    })
    
    if resp.status_code != 200:
        print(f"❌ 失败: {resp.status_code} - {resp.text}")
        return
    
    data = resp.json()
    print(f"✅ 成功")
    print(f"回答: {data['answer'][:200]}...")


if __name__ == "__main__":
    print("CIF-Chat API 测试脚本")
    print("确保后端已启动: uvicorn main:app --reload")
    print()
    
    structure_text = test_parse()
    if structure_text:
        test_analyze(structure_text)
        test_chat(structure_text)
    else:
        print("\n⚠️ /api/parse 失败，跳过后续测试")
        sys.exit(1)
