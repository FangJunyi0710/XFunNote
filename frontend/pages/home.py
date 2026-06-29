"""XFunNote 封面 — 欢迎页。"""
import streamlit as st

st.title("📒 XFunNote")

st.markdown("""
### 欢迎使用 XFunNote

智能笔记本管理系统 — 配置驱动的多类型数据管理，支持筛选、分页、交互式编辑。
""")

st.divider()

# ---- 笔记本入口卡片 ----
st.subheader("📒 笔记本")
cols = st.columns(5)
notebooks = [
    ("📋", "计划", "月度计划与任务管理"),
    ("📔", "日记", "日记记录与心情追踪"),
    ("📖", "单词", "单词学习与间隔复习"),
    ("📚", "积累", "知识积累与分类整理"),
    ("🧠", "AI记忆", "AI 辅助记忆管理"),
]
for i, (icon, title, desc) in enumerate(notebooks):
    with cols[i]:
        with st.container(border=True):
            st.markdown(f"### {icon}")
            st.markdown(f"**{title}**")
            st.caption(desc)

st.divider()

# ---- 工具入口 ----
st.subheader("🛠️ 工具")
tcols = st.columns(2)
with tcols[0]:
    with st.container(border=True):
        st.markdown("### 🤖 AI 对话")
        st.caption("与 AI 助手对话，智能管理笔记本数据。支持工具调用，可直接操作数据库。")
with tcols[1]:
    with st.container(border=True):
        st.markdown("### ⚙️ 系统管理")
        st.caption("数据库初始化/备份/重置，以及视图文件的新建、编辑与删除。")

st.divider()
st.caption("💡 点击左侧导航栏进入各功能页面。连接配置请前往 「系统管理」 页面。")
