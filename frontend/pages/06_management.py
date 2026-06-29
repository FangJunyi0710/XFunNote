"""系统管理页面 — 数据库管理 + 视图文件管理。"""

import json
import streamlit as st
from frontend.components import get_client, api_call

st.set_page_config(page_title="系统管理 - XFunNote", page_icon="⚙️", layout="wide")

st.title("⚙️ 系统管理")

tab1, tab2 = st.tabs(["🗄️ 数据库管理", "📁 视图文件管理"])

# ==================== 数据库管理 ====================

with tab1:
    st.subheader("数据库操作")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 初始化数据库", use_container_width=True):
            api = get_client()
            result = api_call(api.init_db)
            if result:
                st.success(result.get("message", "初始化完成"))

    with col2:
        if st.button("💾 热备份", use_container_width=True):
            api = get_client()
            result = api_call(api.backup_db)
            if result:
                st.success(result.get("message", "备份完成"))

    with col3:
        st.warning("⚠️ 重置将清空所有数据")
        backup_first = st.checkbox("重置前先备份", value=True, key="reset_backup")
        if st.button("🗑️ 重置数据库", type="primary", use_container_width=True):
            confirm = st.checkbox(
                "我确认要重置数据库（此操作不可撤销）",
                key="reset_confirm",
            )
            if confirm:
                api = get_client()
                result = api_call(api.reset_db, backup_first=backup_first)
                if result:
                    st.success(result.get("message", "重置完成"))
                    st.rerun()

    st.divider()
    st.caption(
        "💡 提示：初始化数据库会创建缺失的表和列；"
        "备份生成带时间戳的副本文件；重置会清空所有表结构。"
    )

# ==================== 视图文件管理 ====================

with tab2:
    st.subheader("视图文件管理")

    api = get_client()
    views = api_call(api.list_views)
    if views is None:
        st.stop()

    if views:
        view_names = [v["name"] for v in views]
        selected_view = st.selectbox(
            "选择视图文件",
            options=["(新建)"] + view_names,
            key="view_selector",
        )
    else:
        selected_view = "(新建)"
        st.info("暂无保存的视图文件。")

    if selected_view == "(新建)":
        view_name = st.text_input("视图名称", placeholder="my_view", key="view_new_name")
        view_content = st.text_area(
            "视图 JSON",
            value="{}",
            height=300,
            key="view_new_content",
        )
    else:
        view_name = selected_view
        view_data = api_call(api.get_view, view_name) or {}
        view_content = st.text_area(
            "视图 JSON",
            value=json.dumps(view_data, ensure_ascii=False, indent=2),
            height=300,
            key="view_edit_content",
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 保存视图", type="primary", use_container_width=True):
            if not view_name:
                st.error("请输入视图名称")
            else:
                try:
                    data = json.loads(view_content)
                    api = get_client()
                    result = api_call(api.save_view, view_name, data)
                    if result:
                        st.success(f"视图 `{view_name}` 已保存")
                        st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"JSON 格式错误: {e}")

    with col2:
        if selected_view != "(新建)":
            if st.button("🗑️ 删除视图", use_container_width=True):
                if st.checkbox("确认删除", key="view_delete_confirm"):
                    api = get_client()
                    result = api_call(api.delete_view, view_name)
                    if result:
                        st.success(f"视图 `{view_name}` 已删除")
                        st.rerun()

    with col3:
        if st.button("🔄 刷新列表", use_container_width=True):
            st.rerun()
