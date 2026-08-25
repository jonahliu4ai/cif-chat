import time
import tempfile
import os
import hashlib
import streamlit as st
import streamlit.components.v1 as components
import py3Dmol

from cif_parser import CIFParser
from llm_client import LLMClient
from prompt_templates import STRUCTURE_DESCRIPTION


st.set_page_config(page_title="CIF-Chat", layout="wide")
st.title("🔬 CIF-Chat: AI 晶体结构解析")


# ========== 访问控制 ==========
def check_access():
    """检查用户是否已通过密码验证"""
    try:
        access_pwd = st.secrets.get("access", {}).get("password", "")
    except Exception:
        access_pwd = ""

    if not access_pwd:
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        with st.form("login"):
            st.markdown("### 🔒 请输入访问密码")
            pwd_input = st.text_input("密码", type="password")
            submitted = st.form_submit_button("进入")
            if submitted:
                if pwd_input == access_pwd:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("密码错误")
        st.stop()

    return True


check_access()


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
    elif style == "cartoon":
        view.setStyle({'cartoon': {'color': 'spectrum'}})
    else:
        view.setStyle({'sphere': {'radius': 0.3}})

    view.zoomTo()
    return view._make_html()


# ========== 流式分析 ==========
def stream_analysis(structure_text: str, placeholder) -> float:
    """流式获取 AI 分析。分析完成后将结果写入 session_state。"""
    t0 = time.time()

    try:
        llm = LLMClient()
    except ValueError as e:
        placeholder.error(f"⚠️ {e}")
        placeholder.info("请确认已配置 API Key（本地: `.streamlit/secrets.toml` / 云端: Streamlit Cloud Settings → Secrets）")
        return 0.0

    full_text = ""
    first_char = True

    try:
        for text in llm.chat_stream(
            system_prompt="You are a helpful crystallography assistant.",
            user_prompt=STRUCTURE_DESCRIPTION.format(structure_data=structure_text),
            timeout=120,
        ):
            if first_char:
                first_char = False
                ttft = time.time() - t0
                placeholder.empty()
                placeholder.info(f"🤖 模型已响应（首字等待 {ttft:.1f}s），正在生成分析...")
            full_text += text
            display_text = full_text.replace(r'\[', '$$').replace(r'\]', '$$')
            placeholder.markdown(display_text + "▌")
    except Exception as e:
        placeholder.error(f"分析失败: {type(e).__name__}: {e}")
        st.session_state.ai_analysis_result = ""
        return time.time() - t0

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
st.markdown("欢迎！上传 CIF 文件，AI 将为你解析晶体结构。")

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
        with tempfile.NamedTemporaryFile(delete=False, suffix=".cif") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            parser = CIFParser(tmp_path)
            data = {
                "filename": uploaded.name,
                "basic_info": parser.get_basic_info(),
                "structure_text": parser.export_for_llm(),
            }
            cif_content = file_bytes.decode('utf-8')
        except Exception as e:
            st.error(f"解析失败: {type(e).__name__}: {e}")
            st.stop()
        finally:
            os.unlink(tmp_path)

    structure_text = data["structure_text"]

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
            key="style_selectbox",
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
            analysis_placeholder.info("🤖 AI 正在分析晶体结构，请稍候...")

            with st.expander("🔍 查看原始结构数据（Debug）"):
                st.text(structure_text)

            elapsed = stream_analysis(structure_text, analysis_placeholder)
            if elapsed > 0:
                st.caption(f"⏱️ AI 分析总用时 {elapsed:.1f} 秒")

    st.subheader("💬 追问")
    question = st.text_input("对结构提问（如：DMF 是否配位到 Cu？）", key="chat_input")
    if question:
        with st.spinner("思考中..."):
            try:
                t0 = time.time()
                llm = LLMClient()
                prompt = f"""Based on the following crystal structure data, answer the user's question.

Structure Data:
{structure_text}

User Question: {question}
"""
                answer = llm.chat(
                    system_prompt="You are a crystallography expert. Answer concisely and accurately.",
                    user_prompt=prompt,
                    timeout=120,
                )
                elapsed = time.time() - t0
                st.markdown(preprocess_latex(answer))
                st.caption(f"⏱️ 回答用时 {elapsed:.1f} 秒")
            except Exception as e:
                st.error(f"回答失败: {type(e).__name__}: {e}")
