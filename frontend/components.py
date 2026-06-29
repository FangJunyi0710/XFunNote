"""共享 UI 组件。"""

from __future__ import annotations

import json
import streamlit as st
from frontend.api import get_client


def init_session():
    """初始化 session_state 默认值。"""
    defaults = {
        "api_base_url": "http://localhost:8000",
        "selected_notebook": None,
        "query_results": None,
        "delete_preview": None,
        "delete_filter": None,
        "chat_messages": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def select_notebook(label: str = "选择笔记本") -> str | None:
    """下拉选择笔记本类型，返回选中的名称。"""
    api = get_client()
    try:
        notebooks = api.list_notebooks()
    except Exception as e:
        st.error(f"获取笔记本列表失败: {e}")
        return None

    if not notebooks:
        st.warning("没有可用的笔记本，请先定义笔记本类型或初始化数据库。")
        return None

    selected = st.selectbox(
        label,
        options=notebooks,
        key="notebook_selector",
    )
    return selected


def show_schema(notetype: str) -> list[dict] | None:
    """展示笔记本字段结构，返回 columns 列表。"""
    api = get_client()
    try:
        columns = api.get_schema(notetype)
    except Exception as e:
        st.error(f"获取 schema 失败: {e}")
        return None

    with st.expander("📋 字段结构", expanded=False):
        col_data = []
        for col in columns:
            col_data.append({
                "字段名": col.get("name", ""),
                "类型": col.get("type", ""),
                "必填": "✅" if col.get("required") else "",
                "默认值": str(col.get("default", "")),
            })
        st.dataframe(col_data, use_container_width=True, hide_index=True)

    return columns


def build_simple_filter(columns: list[dict]) -> dict | None:
    """构建简单筛选条件（字段=值）。"""
    if not columns:
        return None

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        field = st.selectbox(
            "筛选字段",
            options=["(不过滤)"] + [c["name"] for c in columns],
            key="filter_field",
        )
    if field == "(不过滤)":
        return None

    with col2:
        op = st.selectbox(
            "运算符",
            options=["$eq", "$ne", "$contains", "$gt", "$lt", "$gte", "$lte"],
            format_func=lambda x: {
                "$eq": "=",
                "$ne": "≠",
                "$contains": "包含",
                "$gt": ">",
                "$lt": "<",
                "$gte": "≥",
                "$lte": "≤",
            }[x],
            key="filter_op",
        )
    with col3:
        value = st.text_input("值", key="filter_value")

    if not value:
        return None

    return {field: {op: value}}


def display_results(data: dict, max_rows: int = 100):
    """以表格形式展示查询结果。"""
    count = data.get("count", 0)
    results = data.get("results", [])

    st.metric("匹配条目数", count)

    if count == 0:
        st.info("没有匹配的条目。")
        return

    if count > max_rows:
        st.warning(f"结果超过 {max_rows} 条，仅显示前 {max_rows} 条。")

    import pandas as pd

    df = pd.DataFrame(results[:max_rows])
    st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("📄 查看 JSON"):
        st.json(results[:max_rows])


def api_call(func, *args, **kwargs):
    """统一的 API 调用包装，自动处理异常。"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        st.error(str(e))
        return None
