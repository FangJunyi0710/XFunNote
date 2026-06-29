"""删除条目页面 — 遵循安全流程：先预览再确认。"""

import json
import streamlit as st
from frontend.components import get_client, select_notebook, show_schema, api_call

st.set_page_config(page_title="删除条目 - XFunNote", page_icon="🗑️", layout="wide")

st.title("🗑️ 删除条目")
st.caption("安全流程：先预览将被删除的条目，确认后再执行删除。")

notebook = select_notebook()
if not notebook:
    st.stop()

columns = show_schema(notebook)
if columns is None:
    st.stop()

st.divider()

# ---- 步骤 1: 设置筛选条件 ----

st.subheader("1️⃣ 筛选要删除的条目")

col1, col2 = st.columns(2)

with col1:
    filter_mode = st.radio(
        "筛选模式",
        options=["简单筛选", "JSON 筛选"],
        horizontal=True,
        key="delete_filter_mode",
    )

if filter_mode == "简单筛选":
    with col1:
        filter_field = st.selectbox(
            "字段",
            options=[c["name"] for c in columns],
            key="delete_filter_field",
        )
    with col2:
        filter_value = st.text_input("值", key="delete_filter_value")

    if filter_value:
        filter_obj = {"column": filter_field, "op": "=", "value": filter_value}
    else:
        filter_obj = None
        st.info("请输入筛选值。")
else:
    filter_json_raw = st.text_area(
        "筛选 JSON",
        placeholder='{"column": "字段名", "op": "=", "value": "值"}',
        height=120,
        key="delete_filter_json",
    )
    try:
        filter_obj = json.loads(filter_json_raw) if filter_json_raw.strip() else None
    except json.JSONDecodeError:
        filter_obj = None
        st.error("JSON 格式错误")

st.divider()

# ---- 步骤 2: 预览 ----

st.subheader("2️⃣ 预览将删除的条目")

if filter_obj and st.button("👁️ 预览", key="delete_preview_btn", use_container_width=True):
    api = get_client()
    result = api_call(api.preview_delete, notebook, filter_obj)
    if result is not None:
        st.session_state.delete_preview = result
        st.session_state.delete_filter = filter_obj

if st.session_state.get("delete_preview"):
    data = st.session_state.delete_preview
    st.metric("将被删除的条目数", data["count"])

    if data["count"] == 0:
        st.info("没有匹配的条目将被删除。")
    else:
        st.dataframe(data["results"], use_container_width=True, hide_index=True)

        st.divider()

        # ---- 步骤 3: 确认删除 ----
        st.subheader("3️⃣ 确认删除")
        st.error(
            f"⚠️ 此操作将**永久删除**上述 {data['count']} 条记录，无法恢复！"
        )

        confirm_text = st.text_input(
            "请输入 DELETE 确认删除",
            placeholder="DELETE",
            key="delete_confirm_text",
        )

        if st.button(
            "🗑️ 确认删除",
            type="primary",
            disabled=(confirm_text != "DELETE"),
            use_container_width=True,
        ):
            api = get_client()
            result = api_call(
                api.delete_entries, notebook, st.session_state.delete_filter
            )
            if result is not None:
                st.success(f"✅ 成功删除 {result['count']} 条记录！")
                st.session_state.delete_preview = None
                st.session_state.delete_filter = None
                st.rerun()
