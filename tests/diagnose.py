import requests
import time

API_URL = "http://localhost:8000"
CIF_PATH = r"D:\src\Ziang-Nan\晶体学-ZiangNan\cif-chat\tests\CaTiO3.cif"

def test_with_timeout():
    print("=" * 50)
    print("诊断：测试 API 各端点")
    print("=" * 50)
    
    # 测试 1: /api/parse
    print("\n[1/3] 测试 /api/parse ...")
    start = time.time()
    try:
        with open(CIF_PATH, "rb") as f:
            resp = requests.post(f"{API_URL}/api/parse", files={"file": ("CaTiO3.cif", f)}, timeout=10)
        elapsed = time.time() - start
        if resp.status_code == 200:
            data = resp.json()
            print(f"   成功 ({elapsed:.1f}s)")
            print(f"   化学式: {data['basic_info']['formula']}")
            structure_text = data["structure_text"]
        else:
            print(f"   失败: {resp.status_code} - {resp.text}")
            return
    except Exception as e:
        print(f"   异常: {type(e).__name__}: {e}")
        return
    
    # 测试 2: /api/analyze（timeout=120s，匹配后端）
    print("\n[2/3] 测试 /api/analyze (timeout=120s) ...")
    print("   如果超过 30s 还没返回，说明模型处理确实慢")
    start = time.time()
    try:
        resp = requests.post(f"{API_URL}/api/analyze", json={"structure_text": structure_text}, timeout=125)
        elapsed = time.time() - start
        if resp.status_code == 200:
            print(f"   成功 ({elapsed:.1f}s)")
            print(f"   AI 分析前 300 字: {resp.json()['analysis'][:300]}...")
        else:
            print(f"   失败: {resp.status_code} - {resp.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"   超时 (120s 内未返回)")
        print("   建议：换 SiliconFlow 上的轻量模型，如 Qwen/Qwen2.5-7B-Instruct")
    except Exception as e:
        print(f"   异常: {type(e).__name__}: {e}")
    
    # 测试 3: /api/chat
    print("\n[3/3] 测试 /api/chat (timeout=30s) ...")
    start = time.time()
    try:
        resp = requests.post(f"{API_URL}/api/chat", json={
            "structure_data": structure_text,
            "question": "Ti 的配位数是多少？"
        }, timeout=30)
        elapsed = time.time() - start
        if resp.status_code == 200:
            print(f"   成功 ({elapsed:.1f}s)")
            print(f"   回答: {resp.json()['answer'][:100]}...")
        else:
            print(f"   失败: {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        print(f"   异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_with_timeout()
