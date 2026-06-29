"""添加条目页面。"""

import json
import streamlit as st
from frontend.components import get_client, select_notebook, show_schema, api_call

st.set_page_config(page_title="添加条目 - XFunNote", page_icon="➕", layout="wide")

st.title("➕ 添加条目")

notebook = select_notebook()
if not notebook:
    st.stop()

columns = show_schema(notebook)
if columns is None:
    st.stop()

st.divider()

# ---- 模式选择 ----
mode = st.radio(
    "输入模式",
    options=["📝 表单模式", "📄 JSON 模式"],
    horizontal=True,
)

if mode == "📝 表单模式":
    st.subheader("条目编辑")

    entry_count = st.number_input(
        "条目数量", min_value=1, max_value=20, value=1, step=1,
        help="可一次添加多条",
    )

    entries = []
    for i in range(int(entry_count)):
        with st.expander(f"条目 #{i + 1}", expanded=(i == 0)):
            entry = {}
            cols_per_row = 3
            col_groups = [
                columns[j : j + cols_per_row]
                for j in range(0, len(columns), cols_per_row)
            ]
            for group in col_groups:
                row = st.columns(len(group))
                for j, col_def in enumerate(group):
                    name = col_def["name"]
                    col_type = col_def.get("type", "TEXT")
                    required = col_def.get("required", False)
                    label = f"{name}{' *' if required else ''}"

                    with row[j]:
                        if col_type in ("BOOLEAN", "BOOL"):
                            val = st.checkbox(label, key=f"add_{i}_{name}")
                        elif col_type in ("INTEGER", "INT"):
                            val = st.number_input(
                                label, step=1, key=f"add_{i}_{name}"
                            )
                        elif col_type in ("REAL", "FLOAT", "DOUBLE"):
                            val = st.number_input(
                                label, step=0.1, key=f"add_{i}_{name}"
                            )
                        else:
                            val = st.text_input(label, key=f"add_{i}_{name}")

                        if val != "" and val is not None:
                            entry[name] = val

            entries.append(entry)

    if st.button("✅ 提交添加", type="primary", use_container_width=True):
        valid_entries = [e for e in entries if e]
        if not valid_entries:
            st.warning("至少需要填写一个条目的字段。")
        else:
            api = get_client()
            result = api_call(api.add_entries, notebook, valid_entries)
            if result is not None:
                st.success(f"✅ 成功添加 {result['count']} 条记录！")
                with st.expander("📄 查看新增条目"):
                    st.json(result["results"])

else:
    st.subheader("JSON 模式")
    st.markdown("输入条目 JSON 数组，每个元素为字段名→值的映射。")

    default_json = json.dumps(
        [{c["name"]: "" for c in columns}],
        ensure_ascii=False,
        indent=2,
    )
    json_input = st.text_area(
        "条目 JSON",
        value=default_json,
        height=300,
        key="add_json_input",
    )

    if st.button("✅ 提交添加", type="primary", use_container_width=True):
        try:
            entries = json.loads(json_input)
            if not isinstance(entries, list):
                st.error("JSON 必须是数组格式")
            else:
                api = get_client()
                result = api_call(api.add_entries, notebook, entries)
                if result is not None:
                    st.success(f"✅ 成功添加 {result['count']} 条记录！")
                    with st.expander("📄 查看新增条目"):
                        st.json(result["results"])
        except json.JSONDecodeError as e:
            st.error(f"JSON 格式错误: {e}")
