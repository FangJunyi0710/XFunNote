"""更新条目页面。"""

import json
import streamlit as st
from frontend.components import get_client, select_notebook, show_schema, api_call

st.set_page_config(page_title="更新条目 - XFunNote", page_icon="✏️", layout="wide")

st.title("✏️ 更新条目")

notebook = select_notebook()
if not notebook:
    st.stop()

columns = show_schema(notebook)
if columns is None:
    st.stop()

st.divider()

# ---- 步骤 1: 筛选要更新的条目 ----

st.subheader("1️⃣ 筛选目标条目")

col1, col2 = st.columns(2)

with col1:
    filter_mode = st.radio(
        "筛选模式",
        options=["简单筛选", "JSON 筛选"],
        horizontal=True,
        key="update_filter_mode",
    )

if filter_mode == "简单筛选":
    with col1:
        filter_field = st.selectbox(
            "字段",
            options=[c["name"] for c in columns],
            key="update_filter_field",
        )
    with col2:
        filter_value = st.text_input("值", key="update_filter_value")

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
        key="update_filter_json",
    )
    try:
        filter_obj = json.loads(filter_json_raw) if filter_json_raw.strip() else None
    except json.JSONDecodeError:
        filter_obj = None
        st.error("JSON 格式错误")

# 先查询匹配条目
if filter_obj and st.button("🔍 查询匹配条目", key="update_query_btn"):
    view_obj = {notebook: [{"columns": [c["name"] for c in columns], "filter": filter_obj}]}
    api = get_client()
    result = api_call(
        api.query_entries,
        notetype=notebook,
        view=json.dumps(view_obj, ensure_ascii=False),
    )
    if result is not None:
        st.session_state.update_matches = result

if st.session_state.get("update_matches"):
    data = st.session_state.update_matches
    st.metric("将更新条目数", data["count"])
    if data["count"] > 0:
        st.dataframe(data["results"][:20], use_container_width=True, hide_index=True)
        if data["count"] > 20:
            st.caption(f"... 共 {data['count']} 条")

# ---- 步骤 2: 选择要更新的字段和值 ----

st.divider()
st.subheader("2️⃣ 设置更新值")

update_fields = {}
cols_per_row = 3
col_groups = [
    columns[i : i + cols_per_row] for i in range(0, len(columns), cols_per_row)
]
for group in col_groups:
    row = st.columns(len(group))
    for j, col_def in enumerate(group):
        name = col_def["name"]
        with row[j]:
            enable = st.checkbox(f"更新 {name}", key=f"update_enable_{name}")
            if enable:
                col_type = col_def.get("type", "TEXT")
                if col_type in ("BOOLEAN", "BOOL"):
                    val = st.checkbox(f"{name} 新值", key=f"update_val_{name}")
                elif col_type in ("INTEGER", "INT"):
                    val = st.number_input(
                        f"{name} 新值", step=1, key=f"update_val_{name}"
                    )
                elif col_type in ("REAL", "FLOAT", "DOUBLE"):
                    val = st.number_input(
                        f"{name} 新值", step=0.1, key=f"update_val_{name}"
                    )
                else:
                    val = st.text_input(f"{name} 新值", key=f"update_val_{name}")
                update_fields[name] = val

# ---- 执行更新 ----

st.divider()

if filter_obj and update_fields:
    st.warning(
        f"将对 **筛选匹配的条目** 更新以下字段：{', '.join(update_fields.keys())}"
    )
    if st.button("✅ 确认更新", type="primary", use_container_width=True):
        api = get_client()
        result = api_call(
            api.update_entries, notebook, filter_obj, update_fields
        )
        if result is not None:
            st.success(f"✅ 成功更新 {result['count']} 条记录！")
            with st.expander("📄 查看更新后条目"):
                st.json(result["results"])
            st.session_state.update_matches = None
else:
    st.info("请先筛选目标条目并选择要更新的字段。")
