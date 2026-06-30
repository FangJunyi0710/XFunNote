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

# ── 全局字体：仿终端等宽字体 Ubuntu Mono ──
st.markdown("""
<style>
@import url('https://fonts.loli.net/css2?family=Ubuntu+Mono&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

html, body, [class*="css"], [class*="st-"] {
    font-family: 'Ubuntu Mono', 'Courier New', monospace !important;
}

/* 用 :not 精确排除图标 */
[data-testid^="stIcon"],
[data-testid^="stIcon"] *,
[class*="material-symbols"],
[class*="material-icons"] {
    font-family: "Material Symbols Outlined", "Material Icons" !important;
}
</style>
""", unsafe_allow_html=True)

from frontend.components import init_session

init_session()

# ==================== Navigation ====================

home_page = st.Page(
    "pages/home.py", title="主页", icon="🏠",
)
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
view_mgmt_page = st.Page(
    "pages/view_management.py", title="视图管理", icon="👁️"
)

pg = st.navigation({
    "🏠 首页": [home_page],
    "📒 笔记本": [
        plan_page, diary_page, word_page,
        accumulation_page, aimemory_page,
    ],
    "🛠️ 工具": [ai_chat_page, management_page, view_mgmt_page],
})
pg.run()
