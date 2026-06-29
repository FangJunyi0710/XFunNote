"""共享 UI 组件 — 配置驱动 + 通用笔记本渲染。"""

from __future__ import annotations

import json
import streamlit as st
from frontend.api import get_client


# ==================== Session Init ====================

def init_session():
    """初始化 session_state 默认值。"""
    defaults = {
        "api_base_url": "http://localhost:8000",
        "chat_messages": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ==================== Notebook Configs ====================

_BASE_FIELDS = {
    "id": {"label": "ID", "widget": "text_input", "auto": True, "hidden": True},
    "content": {"label": "内容", "widget": "text_area", "rows": 4},
    "created_at": {"label": "创建时间", "widget": "text_input", "auto": True},
    "updated_at": {"label": "更新时间", "widget": "text_input", "auto": True},
    "tags": {"label": "标签", "widget": "text_input", "placeholder": "逗号分隔"},
    "is_ai_gen": {"label": "AI生成", "widget": "checkbox"},
    "ai_tags": {"label": "AI标签", "widget": "text_input"},
    "ai_note": {"label": "AI备注", "widget": "text_area", "rows": 2},
}

NOTEBOOK_CONFIGS = {
    "plan": {
        "title": "计划",
        "icon": "📋",
        "auto_fields": ["id", "no", "seq", "created_at", "updated_at"],
        "default_display": ["no", "month", "content", "done", "status", "tags", "created_at"],
        "field_config": {
            **{k: v for k, v in _BASE_FIELDS.items()},
            "no": {"label": "编号", "widget": "text_input", "auto": True, "hidden": False},
            "seq": {"label": "序号", "widget": "text_input", "auto": True, "hidden": True},
            "month": {"label": "月份", "widget": "text_input", "placeholder": "2025-01", "required": True},
            "done": {"label": "已完成", "widget": "checkbox"},
            "status": {"label": "状态", "widget": "text_input"},
            "content": {"label": "内容", "widget": "text_area", "rows": 4},
        },
    },
    "diary": {
        "title": "日记",
        "icon": "📔",
        "auto_fields": ["id", "created_at", "updated_at"],
        "default_display": ["date", "content", "mood", "weather", "tags", "created_at"],
        "field_config": {
            **{k: v for k, v in _BASE_FIELDS.items()},
            "date": {"label": "日期", "widget": "text_input", "placeholder": "2025-01-01", "required": True},
            "mood": {"label": "心情", "widget": "select",
                     "options": ["😊 开心", "😐 平静", "😢 难过", "😠 生气", "😰 焦虑", "🤩 兴奋"]},
            "weather": {"label": "天气", "widget": "select",
                        "options": ["☀️ 晴", "⛅ 多云", "🌧️ 雨", "❄️ 雪", "🌬️ 风", "🌫️ 雾"]},
            "content": {"label": "内容", "widget": "text_area", "rows": 10},
        },
    },
    "word": {
        "title": "单词",
        "icon": "📖",
        "auto_fields": ["id", "created_at", "updated_at", "review_count", "performance", "next_review", "last_review"],
        "default_display": ["word", "part_of_speech", "phonetic", "content", "performance", "next_review", "tags"],
        "field_config": {
            **{k: v for k, v in _BASE_FIELDS.items()},
            "word": {"label": "单词", "widget": "text_input", "placeholder": "example", "required": True},
            "part_of_speech": {"label": "词性", "widget": "select",
                               "options": ["noun", "verb", "adjective", "adverb", "preposition", "conjunction", "pronoun", "interjection", "other"]},
            "phonetic": {"label": "音标", "widget": "text_input", "placeholder": "/ɪɡˈzæmpəl/"},
            "example": {"label": "例句", "widget": "text_area", "rows": 3},
            "review_count": {"label": "复习次数", "widget": "text_input", "auto": True, "hidden": True},
            "performance": {"label": "掌握度", "widget": "text_input", "auto": True, "hidden": True},
            "next_review": {"label": "下次复习", "widget": "text_input", "auto": True},
            "last_review": {"label": "上次复习", "widget": "text_input", "auto": True, "hidden": True},
            "related_words": {"label": "相关词", "widget": "text_input", "placeholder": "逗号分隔"},
            "content": {"label": "释义", "widget": "text_area", "rows": 4},
        },
    },
    "accumulation": {
        "title": "积累",
        "icon": "📚",
        "auto_fields": ["id", "created_at", "updated_at"],
        "default_display": ["category", "content", "source", "tags", "created_at"],
        "field_config": {
            **{k: v for k, v in _BASE_FIELDS.items()},
            "category": {"label": "分类", "widget": "text_input", "placeholder": "技术/生活/读书...", "required": True},
            "source": {"label": "来源", "widget": "text_input", "placeholder": "URL或书名"},
            "note": {"label": "备注", "widget": "text_area", "rows": 3},
            "content": {"label": "内容", "widget": "text_area", "rows": 6},
        },
    },
    "aimemory": {
        "title": "AI记忆",
        "icon": "🧠",
        "auto_fields": ["id", "created_at", "updated_at"],
        "default_display": ["title", "content", "source", "tags", "created_at"],
        "field_config": {
            **{k: v for k, v in _BASE_FIELDS.items()},
            "title": {"label": "标题", "widget": "text_input", "placeholder": "记忆标题", "required": True},
            "source": {"label": "来源", "widget": "text_input"},
            "content": {"label": "内容", "widget": "text_area", "rows": 6},
        },
    },
}


def get_notebook_config(name: str) -> dict:
    """获取笔记本配置。"""
    return NOTEBOOK_CONFIGS.get(name, {})


def get_field_config(notebook_name: str, col_name: str, col_type: str = "TEXT") -> dict:
    """获取某列的字段配置，合并笔记本配置与类型默认值。"""
    nb = NOTEBOOK_CONFIGS.get(notebook_name, {})
    fc = nb.get("field_config", {})
    if col_name in fc:
        return fc[col_name]
    if col_name in _BASE_FIELDS:
        return _BASE_FIELDS[col_name]
    # 类型回退
    cfg: dict = {"label": col_name, "widget": "text_input"}
    if col_type in ("BOOLEAN", "BOOL"):
        cfg["widget"] = "checkbox"
    elif col_type in ("INTEGER", "INT"):
        cfg["widget"] = "number_int"
    elif col_type in ("REAL", "FLOAT", "DOUBLE"):
        cfg["widget"] = "number_float"
    return cfg


# ==================== Widget Helpers ====================

def _render_field_widget(
    col_def: dict, field_cfg: dict, key_prefix: str, disabled: bool = False
):
    """根据字段配置渲染对应的 widget。"""
    name = col_def.get("name", "")
    col_type = col_def.get("type", "TEXT")
    required = col_def.get("required", False) or field_cfg.get("required", False)
    widget = field_cfg.get("widget", "text_input")
    label = field_cfg.get("label", name)
    key = f"{key_prefix}_{name}"

    if required:
        label = f"{label} *"

    if widget == "checkbox":
        return st.checkbox(label, key=key, disabled=disabled)
    elif widget == "text_area":
        rows = field_cfg.get("rows", 4)
        return st.text_area(label, key=key, height=rows * 25 + 12, disabled=disabled)
    elif widget == "select":
        options = field_cfg.get("options", [])
        return st.selectbox(label, options=options, key=key, disabled=disabled)
    elif widget == "number_int":
        return st.number_input(label, step=1, key=key, disabled=disabled)
    elif widget == "number_float":
        return st.number_input(label, step=0.1, key=key, disabled=disabled)
    else:  # text_input
        placeholder = field_cfg.get("placeholder", "")
        return st.text_input(label, key=key, placeholder=placeholder, disabled=disabled)


def _build_simple_filter(columns: list[dict], key_prefix: str) -> dict | None:
    """构建简单筛选条件控件。返回 filter dict 或 None。"""
    op_map = {
        "$eq": "=", "$ne": "!=", "$contains": "包含",
        "$gt": ">", "$lt": "<", "$gte": ">=", "$lte": "<=",
    }
    backend_op = {
        "$eq": "=", "$ne": "!=", "$contains": "LIKE",
        "$gt": ">", "$lt": "<", "$gte": ">=", "$lte": "<=",
    }

    c1, c2, c3 = st.columns([2, 1, 2])
    with c1:
        field = st.selectbox(
            "筛选字段",
            options=["(不过滤)"] + [c["name"] for c in columns],
            key=f"{key_prefix}_flt_f",
        )
    if field == "(不过滤)":
        return None
    with c2:
        op = st.selectbox(
            "运算符",
            options=list(op_map.keys()),
            format_func=lambda x: op_map[x],
            key=f"{key_prefix}_flt_o",
        )
    with c3:
        value = st.text_input("值", key=f"{key_prefix}_flt_v")
    if not value:
        return None
    return {"column": field, "op": backend_op[op], "value": value}


def _show_schema(columns: list[dict]):
    """在 expander 中展示字段结构。"""
    with st.expander("📋 字段结构", expanded=False):
        rows = []
        for c in columns:
            rows.append({
                "字段": c.get("name", ""),
                "类型": c.get("type", ""),
                "必填": "✅" if c.get("required") else "",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)


# ==================== Main Render Function ====================

def render_notebook_page(notebook_name: str):
    """配置驱动的完整笔记本 CRUD 页面。"""
    config = NOTEBOOK_CONFIGS.get(notebook_name)
    if not config:
        st.error(f"未知笔记本: {notebook_name}")
        return

    st.title(f"{config['icon']} {config['title']}笔记本")

    api = get_client()
    try:
        columns = api.get_schema(notebook_name)
    except Exception as e:
        st.error(f"获取 schema 失败: {e}")
        return

    if not columns:
        st.warning("无法获取字段信息")
        return

    all_cols = [c["name"] for c in columns]
    auto_fields = set(config.get("auto_fields", []))
    prefix = f"nb_{notebook_name}"

    # ---- Sidebar: View Settings ----
    with st.sidebar:
        st.header("👁️ 视图设置")

        default_disp = config.get("default_display", all_cols[: min(8, len(all_cols))])
        selected_cols = st.multiselect(
            "显示列",
            options=all_cols,
            default=[c for c in default_disp if c in all_cols],
            key=f"{prefix}_cols",
        )

        st.divider()
        st.caption("筛选条件")
        simple_filter = _build_simple_filter(columns, prefix)

        st.divider()
        c1, c2 = st.columns([2, 1])
        with c1:
            order_col = st.selectbox(
                "排序",
                options=[""] + all_cols,
                format_func=lambda x: "不排序" if x == "" else x,
                key=f"{prefix}_sort_c",
            )
        with c2:
            order_dir = st.selectbox(
                "方向", options=["ASC", "DESC"],
                key=f"{prefix}_sort_d",
                disabled=(order_col == ""),
            )
        order_by = f"{order_col} {order_dir}" if order_col else ""

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            limit = st.number_input(
                "条数", min_value=-1, value=100, step=10,
                key=f"{prefix}_lim", help="-1 = 不限制",
            )
        with c2:
            offset = st.number_input(
                "偏移", min_value=0, value=0, step=10,
                key=f"{prefix}_off",
            )

    # ---- Main Tabs ----
    tab_browse, tab_add, tab_update, tab_delete = st.tabs(
        ["📋 浏览", "➕ 添加", "✏️ 更新", "🗑️ 删除"]
    )

    # ===== BROWSE =====
    with tab_browse:
        _show_schema(columns)

        if st.button("🔍 查询", type="primary", key=f"{prefix}_q"):
            view_obj = None
            if simple_filter:
                view_obj = {
                    notebook_name: [{
                        "columns": selected_cols,
                        "filter": simple_filter,
                    }]
                }
            view_json = json.dumps(view_obj, ensure_ascii=False) if view_obj else None
            try:
                result = api.query_entries(
                    notebook_name, view=view_json,
                    order_by=order_by, limit=limit, offset=offset,
                )
                st.session_state[f"{prefix}_res"] = result
            except Exception as e:
                st.error(f"查询失败: {e}")

        results = st.session_state.get(f"{prefix}_res")
        if results:
            count = results.get("count", 0)
            rows = results.get("results", [])
            st.metric("匹配条目", count)
            if rows:
                import pandas as pd
                df = pd.DataFrame(rows)
                available = [c for c in selected_cols if c in df.columns]
                if available:
                    df = df[available]
                st.dataframe(df, use_container_width=True, hide_index=True)
                with st.expander("📄 JSON"):
                    st.json(rows[:50])
            else:
                st.info("没有匹配的条目。")

    # ===== ADD =====
    with tab_add:
        mode = st.radio(
            "输入模式", ["📝 表单", "📄 JSON"],
            horizontal=True, key=f"{prefix}_add_mode",
        )

        if mode == "📝 表单":
            form_fields = [c for c in columns if c["name"] not in auto_fields]

            n = st.number_input(
                "条目数量", min_value=1, max_value=20, value=1,
                key=f"{prefix}_add_n",
            )

            entries: list[dict] = []
            for i in range(int(n)):
                with st.expander(f"条目 #{i + 1}", expanded=(i == 0)):
                    entry: dict = {}
                    cols_per_row = 2
                    groups = [
                        form_fields[j : j + cols_per_row]
                        for j in range(0, len(form_fields), cols_per_row)
                    ]
                    for group in groups:
                        row_cols = st.columns(len(group))
                        for j, col_def in enumerate(group):
                            name = col_def["name"]
                            fcfg = get_field_config(
                                notebook_name, name,
                                col_def.get("type", "TEXT"),
                            )
                            with row_cols[j]:
                                val = _render_field_widget(
                                    col_def, fcfg, f"{prefix}_add_{i}",
                                )
                                if fcfg.get("widget") == "checkbox":
                                    entry[name] = val
                                elif val is not None and val != "":
                                    entry[name] = val
                    entries.append(entry)

            if st.button("✅ 提交", type="primary", key=f"{prefix}_add_btn"):
                valid = [e for e in entries if e]
                if not valid:
                    st.warning("请填写至少一个字段。")
                else:
                    try:
                        r = api.add_entries(notebook_name, valid)
                        st.success(f"✅ 成功添加 {r['count']} 条")
                        with st.expander("📄 详情"):
                            st.json(r["results"])
                    except Exception as e:
                        st.error(f"添加失败: {e}")
        else:
            st.caption("输入 JSON 数组，每项是字段→值的映射。")
            default_json = json.dumps(
                [{c["name"]: "" for c in columns if c["name"] not in auto_fields}],
                ensure_ascii=False, indent=2,
            )
            raw = st.text_area(
                "JSON", value=default_json, height=300,
                key=f"{prefix}_add_json",
            )
            if st.button("✅ 提交", type="primary", key=f"{prefix}_add_json_btn"):
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError as e:
                    st.error(f"JSON 错误: {e}")
                else:
                    if not isinstance(data, list):
                        st.error("JSON 必须是数组")
                    else:
                        try:
                            r = api.add_entries(notebook_name, data)
                            st.success(f"✅ 成功添加 {r['count']} 条")
                        except Exception as e:
                            st.error(f"添加失败: {e}")

    # ===== UPDATE =====
    with tab_update:
        st.subheader("1️⃣ 筛选目标")

        c1, c2 = st.columns(2)
        with c1:
            uf = st.selectbox(
                "字段", options=all_cols, key=f"{prefix}_upd_f",
            )
        with c2:
            uv = st.text_input("值", key=f"{prefix}_upd_v")

        upd_filter = None
        if uv:
            upd_filter = {"column": uf, "op": "=", "value": uv}

        if upd_filter and st.button("🔍 查询匹配", key=f"{prefix}_upd_q"):
            vobj = {notebook_name: [{"columns": all_cols, "filter": upd_filter}]}
            try:
                r = api.query_entries(
                    notebook_name,
                    view=json.dumps(vobj, ensure_ascii=False),
                )
                st.session_state[f"{prefix}_upd_m"] = r
            except Exception as e:
                st.error(f"查询失败: {e}")

        matches = st.session_state.get(f"{prefix}_upd_m")
        if matches:
            st.metric("将更新条目数", matches["count"])
            if matches["count"] > 0:
                st.dataframe(
                    matches["results"][:20],
                    use_container_width=True, hide_index=True,
                )

        st.divider()
        st.subheader("2️⃣ 设置新值")

        upd_vals: dict = {}
        groups = [
            columns[i : i + 3] for i in range(0, len(columns), 3)
        ]
        for group in groups:
            row_cols = st.columns(len(group))
            for j, col_def in enumerate(group):
                name = col_def["name"]
                with row_cols[j]:
                    en = st.checkbox(f"更新 {name}", key=f"{prefix}_upd_en_{name}")
                    if en:
                        fcfg = get_field_config(
                            notebook_name, name,
                            col_def.get("type", "TEXT"),
                        )
                        val = _render_field_widget(
                            col_def, fcfg, f"{prefix}_upd_val",
                        )
                        upd_vals[name] = val

        if upd_filter and upd_vals:
            st.warning(
                f"将对筛选匹配的条目更新：{', '.join(upd_vals.keys())}"
            )
            if st.button("✅ 确认更新", type="primary", key=f"{prefix}_upd_go"):
                try:
                    r = api.update_entries(notebook_name, upd_filter, upd_vals)
                    st.success(f"✅ 成功更新 {r['count']} 条")
                    st.session_state[f"{prefix}_upd_m"] = None
                except Exception as e:
                    st.error(f"更新失败: {e}")

    # ===== DELETE =====
    with tab_delete:
        st.caption("安全流程：先预览再确认删除。")

        c1, c2 = st.columns(2)
        with c1:
            df = st.selectbox(
                "筛选字段", options=all_cols, key=f"{prefix}_del_f",
            )
        with c2:
            dv = st.text_input("筛选值", key=f"{prefix}_del_v")

        del_filter = None
        if dv:
            del_filter = {"column": df, "op": "=", "value": dv}

        if del_filter and st.button("👁️ 预览", key=f"{prefix}_del_p"):
            try:
                r = api.preview_delete(notebook_name, del_filter)
                st.session_state[f"{prefix}_del_prv"] = r
                st.session_state[f"{prefix}_del_flt"] = del_filter
            except Exception as e:
                st.error(f"预览失败: {e}")

        preview = st.session_state.get(f"{prefix}_del_prv")
        if preview:
            cnt = preview["count"]
            st.metric("将删除条目数", cnt)
            if cnt > 0:
                st.dataframe(
                    preview["results"], use_container_width=True,
                    hide_index=True,
                )
                st.error(f"⚠️ 此操作将**永久删除**上述 {cnt} 条记录！")

                confirm = st.text_input(
                    "输入 DELETE 确认", key=f"{prefix}_del_cfm",
                )
                if st.button(
                    "🗑️ 确认删除", type="primary",
                    disabled=(confirm != "DELETE"),
                    key=f"{prefix}_del_go",
                ):
                    try:
                        saved_filter = st.session_state.get(f"{prefix}_del_flt")
                        r = api.delete_entries(notebook_name, saved_filter)
                        st.success(f"✅ 成功删除 {r['count']} 条")
                        st.session_state[f"{prefix}_del_prv"] = None
                        st.session_state[f"{prefix}_del_flt"] = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"删除失败: {e}")
