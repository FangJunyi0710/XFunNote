"""XFunNote Streamlit 前端 — 主入口（st.navigation）。"""
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from xfun.config import PROJECT_ROOT

assert PROJECT_ROOT == _PROJECT_ROOT

import streamlit as st

st.set_page_config(
    page_title="XFunNote",
    page_icon="📒",
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend.components import init_session, get_client

init_session()

# ==================== Global Sidebar ====================

with st.sidebar:
    st.header("⚙️ 连接配置")

    new_url = st.text_input(
        "后端地址",
        value=st.session_state.api_base_url,
        help="FastAPI 后端地址，默认 http://localhost:8000",
    )
    if new_url != st.session_state.api_base_url:
        st.session_state.api_base_url = new_url.rstrip("/")
        st.rerun()

    if st.button("🔍 测试连接", use_container_width=True):
        try:
            api = get_client()
            notebooks = api.list_notebooks()
            st.success(f"✅ 连接成功！{len(notebooks)} 个笔记本可用")
        except Exception as e:
            st.error(f"❌ 连接失败: {e}")

    st.divider()

    try:
        api = get_client()
        notebooks = api.list_notebooks()
        st.caption(f"📚 笔记本: {', '.join(notebooks) if notebooks else '(无)'}")
    except Exception:
        st.caption("📚 笔记本: (未连接)")

    st.divider()
    st.caption("XFunNote v2.0.0")

# ==================== Navigation ====================

plan_page = st.Page(
    "pages/notebook_plan.py", title="计划", icon="📋"
)
diary_page = st.Page(
    "pages/notebook_diary.py", title="日记", icon="📔"
)
word_page = st.Page(
    "pages/notebook_word.py", title="单词", icon="📖"
)
accumulation_page = st.Page(
    "pages/notebook_accumulation.py", title="积累", icon="📚"
)
aimemory_page = st.Page(
    "pages/notebook_aimemory.py", title="AI记忆", icon="🧠"
)
ai_chat_page = st.Page(
    "pages/ai_chat.py", title="AI 对话", icon="🤖"
)
management_page = st.Page(
    "pages/management.py", title="系统管理", icon="⚙️"
)

pg = st.navigation({
    "📒 笔记本": [
        plan_page, diary_page, word_page,
        accumulation_page, aimemory_page,
    ],
    "🛠️ 工具": [ai_chat_page, management_page],
})
pg.run()
