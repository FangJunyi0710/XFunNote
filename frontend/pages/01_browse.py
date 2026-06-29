"""浏览查询页面。"""

import json
import streamlit as st
from frontend.components import (
    get_client,
    select_notebook,
    show_schema,
    build_simple_filter,
    display_results,
    api_call,
)

st.set_page_config(page_title="浏览查询 - XFunNote", page_icon="📋", layout="wide")

st.title("📋 浏览与查询")

notebook = select_notebook()
if not notebook:
    st.stop()

columns = show_schema(notebook)
if columns is None:
    st.stop()

st.divider()

# ---- 查询参数 ----

tab1, tab2 = st.tabs(["🎯 简单查询", "📝 高级 JSON"])

with tab1:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("选择列")
        all_cols = [c["name"] for c in columns]
        selected_cols = st.multiselect(
            "要显示的列（留空=全部）",
            options=all_cols,
            default=all_cols[: min(8, len(all_cols))],
            key="query_selected_cols",
        )

    with col_right:
        st.subheader("筛选条件")
        simple_filter = build_simple_filter(columns)

    # 排序
    col1, col2 = st.columns([2, 1])
    with col1:
        order_col = st.selectbox(
            "排序字段",
            options=[""] + all_cols,
            format_func=lambda x: "不排序" if x == "" else x,
            key="order_col",
        )
    with col2:
        order_dir = st.selectbox(
            "排序方向",
            options=["ASC", "DESC"],
            key="order_dir",
            disabled=(order_col == ""),
        )

    order_by = f"{order_col} {order_dir}" if order_col else ""

    # 分页
    col1, col2 = st.columns(2)
    with col1:
        limit = st.number_input("每页条数", min_value=-1, value=100, step=10,
                                help="-1 表示不限制")
    with col2:
        offset = st.number_input("偏移量", min_value=0, value=0, step=10)

    # 构建 view JSON
    view_obj = None
    if selected_cols or simple_filter:
        from xfun.core.filter import TRUE_CONDITION
        flt = simple_filter or TRUE_CONDITION
        view_obj = {notebook: [selected_cols or [], flt]}

    view_json = json.dumps(view_obj, ensure_ascii=False) if view_obj else None

with tab2:
    st.markdown("直接输入 View JSON（留空=查询全部）")
    view_json_raw = st.text_area(
        "View JSON",
        value=view_json or "",
        height=200,
        key="query_view_json_advanced",
        placeholder='{"笔记本名": [["列1","列2"], {"字段": {"$eq": "值"}}]}',
    )
    if view_json_raw.strip():
        view_json = view_json_raw.strip()
    else:
        view_json = None

# ---- 执行查询 ----

if st.button("🔍 查询", type="primary", use_container_width=True):
    api = get_client()
    result = api_call(
        api.query_entries,
        notetype=notebook,
        view=view_json,
        order_by=order_by,
        limit=limit,
        offset=offset,
    )
    if result is not None:
        st.session_state.query_results = result

# ---- 展示结果 ----

if st.session_state.get("query_results"):
    st.divider()
    st.subheader("📊 查询结果")
    display_results(st.session_state.query_results)
