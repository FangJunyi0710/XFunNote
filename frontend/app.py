"""XFunNote Streamlit 前端 — 主入口。"""

import streamlit as st

st.set_page_config(
    page_title="XFunNote",
    page_icon="📒",
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend.components import init_session, get_client

init_session()

# ==================== 侧边栏 ====================

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
    st.caption("XFunNote v0.1.0")

# ==================== 主页面 ====================

st.title("📒 XFunNote")
st.markdown("### 智能笔记本管理系统")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    #### 📋 浏览查询
    查看笔记本字段结构，使用视图和筛选条件查询条目，
    支持排序和分页。
    """)

with col2:
    st.markdown("""
    #### 🛠️ 数据操作
    添加新条目、批量更新已有数据、安全删除条目。
    删除前可预览确认。
    """)

with col3:
    st.markdown("""
    #### 🤖 AI 对话
    使用自然语言操作笔记本。
    AI 可自动查询、添加、更新和删除数据。
    """)

st.divider()

st.info(
    "💡 **快速开始**：使用左侧导航栏进入各功能模块。"
    "确保 FastAPI 后端已启动（`uvicorn backend.main:app --reload`）。"
)
