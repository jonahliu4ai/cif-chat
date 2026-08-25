import time
import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="CIF-Chat", layout="wide")
st.title("🔬 CIF-Chat: AI 晶体结构解析")

def stream_analysis(structure_text: str, placeholder):
    """流式获取 AI 分析，按服务器原始 chunk 边界读取"""
    t0 = time.time()
    resp = requests.post(
        f"{API_URL}/api/analyze/stream",
        json={"structure_text": structure_text},
        stream=True,
    )
    
    full_text = ""
    first_char = True
    
    # 按服务器发送的原始 chunk 边界读取（不强制拆成 1 字节）
    # OpenAI 流式通常每个 chunk 1-4 个字符，中文可能是 1-2 个字
    for chunk in resp.iter_content(chunk_size=None):
        if chunk:
            try:
                text = chunk.decode('utf-8')
            except UnicodeDecodeError:
                continue
            
            if text:
                if first_char:
                    first_char = False
                    ttft = time.time() - t0
                    placeholder.empty()
                    placeholder.info(f"🤖 模型已响应（首字等待 {ttft:.1f}s），正在生成分析...")
                full_text += text
                display_text = full_text.replace(r'\[', '$$').replace(r'\]', '$$')
                placeholder.markdown(display_text + "▌")
    
    final_text = full_text.replace(r'\[', '$$').replace(r'\]', '$$')
    placeholder.markdown(final_text)
    
    elapsed = time.time() - t0
    return elapsed

def preprocess_latex(text: str) -> str:
    text = text.replace(r'\[', '$$').replace(r'\]', '$$')
    text = text.replace(r'\(', '$').replace(r'\)', '$')
    return text

uploaded = st.file_uploader("上传 CIF 文件", type=["cif"])

if uploaded:
    with st.spinner("解析晶体结构中..."):
        files = {"file": (uploaded.name, uploaded.getvalue(), "chemical/x-cif")}
        resp = requests.post(f"{API_URL}/api/parse", files=files, timeout=15)
    
    if resp.status_code != 200:
        st.error(f"解析失败: {resp.text}")
        st.stop()
    
    data = resp.json()
    structure_text = data["structure_text"]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("📋 基本信息")
        info = data["basic_info"]
        st.write(f"**化学式**: {info['formula']}")
        st.write(f"**空间群**: {info['space_group']}")
        st.write(f"**晶胞**: {info['lattice']['a']:.3f} × {info['lattice']['b']:.3f} × {info['lattice']['c']:.3f} Å")
        st.write(f"**体积**: {info['lattice']['volume']:.1f} Å³")
    
    with col2:
        st.subheader("📝 AI 结构分析")
        analysis_placeholder = st.empty()
        analysis_placeholder.info("🤖 AI 正在分析晶体结构，请稍候...（长 prompt 可能需要 10-30 秒首字响应）")
    
    with st.expander("🔍 查看原始结构数据（Debug）"):
        st.text(structure_text)
    
    elapsed = stream_analysis(structure_text, analysis_placeholder)
    st.caption(f"⏱️ AI 分析总用时 {elapsed:.1f} 秒")
    
    st.subheader("💬 追问")
    question = st.text_input("对结构提问（如：DMF 是否配位到 Cu？）")
    if question:
        with st.spinner("思考中..."):
            try:
                t0 = time.time()
                chat_resp = requests.post(
                    f"{API_URL}/api/chat",
                    json={"structure_data": structure_text, "question": question},
                    timeout=30
                )
                elapsed = time.time() - t0
                if chat_resp.status_code == 200:
                    answer = preprocess_latex(chat_resp.json()["answer"])
                    st.markdown(answer)
                    st.caption(f"⏱️ 回答用时 {elapsed:.1f} 秒")
                else:
                    st.error(f"回答失败: {chat_resp.text}")
            except requests.exceptions.Timeout:
                st.error("回答超时，请稍后重试。")
