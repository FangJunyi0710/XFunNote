"""AI 对话页面。"""

import json
import streamlit as st
from frontend.components import get_client


def _api_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        st.error(str(e))
        return None


st.title("🤖 AI 对话")

# ---- Sidebar: AI Settings ----
with st.sidebar:
    st.subheader("🤖 AI 设置")

    api = get_client()
    try:
        perm = api.ai_permission()
        with st.expander("📋 AI 权限", expanded=False):
            st.json(perm)
    except Exception:
        pass

    max_iterations = st.slider(
        "最大工具调用轮次",
        min_value=1, max_value=50, value=10,
        help="AI 最多执行多少轮工具调用",
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0, max_value=1.0, value=0.7, step=0.05,
        help="控制随机性，越高越有创造性",
    )

    if st.button("🗑️ 清除对话", width='stretch'):
        st.session_state.global_chat_messages = []
        st.rerun()

# ---- Chat Interface ----

if not st.session_state.get("global_chat_messages"):
    st.session_state.global_chat_messages = []

for msg in st.session_state.global_chat_messages:
    role = msg.get("role", "user")
    content = msg.get("content", "")

    if role == "system":
        continue

    with st.chat_message(role):
        if role == "tool":
            tool_name = msg.get("name", "unknown")
            st.caption(f"🔧 工具调用: `{tool_name}`")
            try:
                tool_result = json.loads(content) if isinstance(content, str) else content
                st.json(tool_result)
            except Exception:
                st.text(content)
        else:
            st.markdown(content)

if prompt := st.chat_input("输入消息..."):
    st.session_state.global_chat_messages.append({"role": "user", "content": prompt})

    msgs = st.session_state.global_chat_messages[:]

    with st.spinner("AI 思考中..."):
        api = get_client()
        result = _api_call(
            api.ai_chat,
            messages=msgs,
            max_iterations=max_iterations,
            llm_kwargs={"temperature": temperature},
        )
        if result is not None:
            new_messages = result.get("messages", [])
            st.session_state.global_chat_messages = new_messages

    st.rerun()
