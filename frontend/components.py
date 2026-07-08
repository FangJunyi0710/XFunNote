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


def render_filter_editor(
    key: str,
    height: int = 140,
    label: str = "筛选条件 (JSON)",
    placeholder: str = '{"column": "month", "op": "=", "value": "2025-01"}',
    disabled: bool = False,
) -> str:
    """统一的筛选条件 JSON 编辑器。

    参数:
        key:        Streamlit widget key（调用方需保证唯一）
        height:     text_area 高度，默认 140
        label:      标签文字
        placeholder: 占位提示
        disabled:   是否禁用

    返回:
        当前输入的 JSON 字符串（原始字符串，调用方自行解析）。
    """
    return st.text_area(
        label,
        height=height,
        key=key,
        placeholder=placeholder,
        disabled=disabled,
        help=(
            "输入筛选条件 JSON。支持三种格式:\n"
            "1. 单个条件: {\"column\": \"month\", \"op\": \"=\", \"value\": \"2025-01\"}\n"
            "2. 多个 AND: [[{\"column\":...}, {\"column\":...}]]\n"
            "3. 多个 OR:  [[{\"column\":...}], [{\"column\":...}]]\n"
            "运算符: =, !=, >, <, >=, <=, LIKE, IN, NOT IN, BETWEEN, "
            "JSON_CONTAINS, JSON_NOT_CONTAINS, TEXT_SEARCH, TRUE, FALSE"
        ),
    )
