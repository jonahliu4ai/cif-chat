import time
import hashlib
import streamlit as st
import streamlit.components.v1 as components
import requests
import py3Dmol

API_URL = "http://localhost:8000"

st.set_page_config(page_title="CIF-Chat", layout="wide")
st.title("🔬 CIF-Chat: AI 晶体结构解析")


# ========== 3D 结构可视化 ==========
def render_3d_structure(cif_content: str, style: str = "ball-stick", width: int = 400, height: int = 400) -> str:
    """使用 py3Dmol 生成 CIF 结构的 3D 视图 HTML"""
    view = py3Dmol.view(data=cif_content, format='cif', width=width, height=height)

    if style == "ball-stick":
        view.setStyle({'sphere': {'radius': 0.3}, 'stick': {'radius': 0.15}})
    elif style == "spacefill":
        view.setStyle({'sphere': {'radius': 0.8}})
    elif style == "stick":
        view.setStyle({'stick': {'radius': 0.2}})
    elif style == "line":
        view.setStyle({'line': {}})
    else:
        view.setStyle({'sphere': {'radius': 0.3}})

    view.zoomTo()
    return view._make_html()


# ========== AI 分析 ==========
def stream_analysis(structure_text: str, placeholder) -> float:
    """流式获取 AI 分析。分析完成后将结果写入 session_state。"""
    t0 = time.time()
    resp = requests.post(
        f"{API_URL}/api/analyze/stream",
        json={"structure_text": structure_text},
        stream=True,
    )

    full_text = ""
    first_char = True

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
    # 缓存结果，防止 rerun 时重复调用
    st.session_state.ai_analysis_result = final_text
    st.session_state.ai_analysis_elapsed = elapsed
    return elapsed


def preprocess_latex(text: str) -> str:
    text = text.replace(r'\[', '$$').replace(r'\]', '$$')
    text = text.replace(r'\(', '$').replace(r'\)', '$')
    return text


# ========== Session State 初始化 ==========
if "current_file_hash" not in st.session_state:
    st.session_state.current_file_hash = ""
if "ai_analysis_result" not in st.session_state:
    st.session_state.ai_analysis_result = ""
if "ai_analysis_elapsed" not in st.session_state:
    st.session_state.ai_analysis_elapsed = 0.0


# ========== 主界面 ==========
uploaded = st.file_uploader("上传 CIF 文件", type=["cif"])

if uploaded:
    # 计算文件 hash 用于判断是否是新文件
    file_bytes = uploaded.getvalue()
    file_hash = hashlib.md5(file_bytes).hexdigest()

    # 如果上传了新文件，清空旧缓存
    if file_hash != st.session_state.current_file_hash:
        st.session_state.current_file_hash = file_hash
        st.session_state.ai_analysis_result = ""
        st.session_state.ai_analysis_elapsed = 0.0

    with st.spinner("解析晶体结构中..."):
        files = {"file": (uploaded.name, file_bytes, "chemical/x-cif")}
        resp = requests.post(f"{API_URL}/api/parse", files=files, timeout=15)

    if resp.status_code != 200:
        st.error(f"解析失败: {resp.text}")
        st.stop()

    data = resp.json()
    structure_text = data["structure_text"]
    cif_content = file_bytes.decode('utf-8')

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("📋 基本信息")
        info = data["basic_info"]
        st.write(f"**化学式**: {info['formula']}")
        st.write(f"**空间群**: {info['space_group']}")
        st.write(f"**晶胞**: {info['lattice']['a']:.3f} × {info['lattice']['b']:.3f} × {info['lattice']['c']:.3f} Å")
        st.write(f"**体积**: {info['lattice']['volume']:.1f} Å³")

        # ===== 3D 结构可视化 Panel =====
        st.subheader("🧬 3D 结构视图")
        style_option = st.selectbox(
            "显示样式",
            ["ball-stick (球棍)", "spacefill (空间填充)", "stick (棍状)", "line (线框)"],
            index=0,
            key="style_selectbox",  # 显式 key 避免 widget 冲突
        )
        style_map = {
            "ball-stick (球棍)": "ball-stick",
            "spacefill (空间填充)": "spacefill",
            "stick (棍状)": "stick",
            "line (线框)": "line",
        }
        selected_style = style_map[style_option]

        try:
            html_3d = render_3d_structure(cif_content, style=selected_style, width=380, height=380)
            components.html(html_3d, height=400, scrolling=False)
        except Exception as e:
            st.error(f"3D 视图生成失败: {type(e).__name__}: {e}")

    with col2:
        st.subheader("📝 AI 结构分析")
        analysis_placeholder = st.empty()

        # 判断是否已有缓存结果
        if st.session_state.ai_analysis_result:
            # 直接显示缓存，不重新调用 LLM
            analysis_placeholder.markdown(st.session_state.ai_analysis_result)
            st.caption(f"⏱️ AI 分析总用时 {st.session_state.ai_analysis_elapsed:.1f} 秒（已缓存）")
        else:
            # 首次分析
            analysis_placeholder.info("🤖 AI 正在分析晶体结构，请稍候...（长 prompt 可能需要 10-30 秒首字响应）")

            with st.expander("🔍 查看原始结构数据（Debug）"):
                st.text(structure_text)

            elapsed = stream_analysis(structure_text, analysis_placeholder)
            if elapsed > 0:
                st.caption(f"⏱️ AI 分析总用时 {elapsed:.1f} 秒")

    # 追问区域放在 col2 下方（全宽）
    st.subheader("💬 追问")
    question = st.text_input("对结构提问（如：DMF 是否配位到 Cu？）", key="chat_input")
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
