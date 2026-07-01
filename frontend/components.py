"""共享 UI 组件。"""
import streamlit as st


def init_session():
    """初始化 session_state 默认值（global_ 前缀）。"""
    defaults = {
        "global_api_base_url": "http://localhost:8000",
        "global_chat_messages": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
