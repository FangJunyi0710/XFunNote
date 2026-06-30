"""共享 UI 组件 — 视图选择 + 筛选分页 + 交互表格。"""

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
    col_def: dict, field_cfg: dict, key_prefix: str, disabled: bool = False,
    value=None,
):
    """根据字段配置渲染对应的 widget，支持初始值。"""
    name = col_def.get("name", "")
    col_type = col_def.get("type", "TEXT")
    required = col_def.get("required", False) or field_cfg.get("required", False)
    widget = field_cfg.get("widget", "text_input")
    label = field_cfg.get("label", name)
    key = f"{key_prefix}_{name}"

    if required:
        label = f"{label} *"

    # 通过 session_state 设置初始值（仅当还未设置时）
    # widget 不传 value/index 参数，避免与 session_state 冲突
    if value is not None and key not in st.session_state:
        st.session_state[key] = value

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
        st.dataframe(rows, width='stretch', hide_index=True)


# ==================== Main Render Function ====================

def render_notebook_page(notebook_name: str):
    """配置驱动的完整笔记本页面 — 视图选择 + 筛选分页 + 交互表格。"""
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

    # ---- Sidebar: 仅视图下拉 ----
    selected_view_name = None
    view_columns = []
    view_filter = None
    view_sort = ""

    # 获取已保存的视图列表
    try:
        all_views = api.list_views()
    except Exception:
        all_views = []

    # 过滤出与当前 notebook 相关的视图
    related_views = []
    other_views = []
    for v in all_views:
        vname = v.get("name", "")
        try:
            vdata = api.get_view(vname)
        except Exception:
            continue
        if vdata and isinstance(vdata, dict) and notebook_name in vdata:
            related_views.append(vname)
        elif vdata is not None:
            other_views.append(vname)

    view_options = ["(手动配置)"] + sorted(related_views) + sorted(other_views)

    sel_key = f"{prefix}_sel_view"
    if sel_key not in st.session_state:
        st.session_state[sel_key] = 0

    with st.sidebar:
        selected_idx = st.selectbox(
            "📋 视图预设",
            options=range(len(view_options)),
            format_func=lambda i: view_options[i],
            key=sel_key,
            help="选择已保存的视图预设，或手动配置",
        )
    selected_label = view_options[selected_idx]

    if selected_label != "(手动配置)":
        selected_view_name = selected_label
        try:
            view_data = api.get_view(selected_view_name)
        except Exception:
            view_data = None

        if view_data and isinstance(view_data, dict):
            nb_views = view_data.get(notebook_name, [])
            if nb_views and isinstance(nb_views, list) and len(nb_views) > 0:
                first = nb_views[0]
                view_columns = first.get("columns", [])
                view_filter = first.get("filter")
                view_sort = first.get("sort", "")

        if view_columns:
            st.caption(
                f"已加载视图 `{selected_view_name}` → "
                f"{', '.join(view_columns[:6])}{'...' if len(view_columns) > 6 else ''}"
            )

    # ---- 筛选条件 ----
    with st.expander("🔍 筛选条件（叠加在视图之上）", expanded=False):
        n_filters_key = f"{prefix}_n_filters"
        if n_filters_key not in st.session_state:
            st.session_state[n_filters_key] = 1

        extra_filters = []
        op_map = {
            "=": "=", "!=": "!=", "包含": "LIKE",
            ">": ">", "<": "<", ">=": ">=", "<=": "<=",
        }

        for fi in range(st.session_state[n_filters_key]):
            fcol1, fcol2, fcol3 = st.columns([2, 1, 2])
            with fcol1:
                field = st.selectbox(
                    "字段" if fi == 0 else f"字段 #{fi+1}",
                    options=["(无)"] + all_cols,
                    key=f"{prefix}_flt_f{fi}",
                )
            with fcol2:
                op = st.selectbox(
                    "运算符" if fi == 0 else "运算符",
                    options=list(op_map.keys()),
                    key=f"{prefix}_flt_o{fi}",
                )
            with fcol3:
                value = st.text_input(
                    "值" if fi == 0 else "值",
                    key=f"{prefix}_flt_v{fi}",
                )
            if field != "(无)" and value:
                extra_filters.append({
                    "column": field,
                    "op": op_map[op],
                    "value": value,
                })

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("➕ 添加条件", width='stretch', key=f"{prefix}_add_flt"):
                st.session_state[n_filters_key] += 1
                st.rerun()
        with bcol2:
            if st.button("➖ 移除条件", width='stretch', key=f"{prefix}_del_flt",
                        disabled=st.session_state[n_filters_key] <= 1):
                st.session_state[n_filters_key] = max(1, st.session_state[n_filters_key] - 1)
                st.rerun()

    # ---- 排序 + 分页（可折叠） ----
    if f"{prefix}_limit" not in st.session_state:
        st.session_state[f"{prefix}_limit"] = 20
    if f"{prefix}_offset" not in st.session_state:
        st.session_state[f"{prefix}_offset"] = 0
    if f"{prefix}_should_query" not in st.session_state:
        st.session_state[f"{prefix}_should_query"] = True

    with st.expander("📐 排序与分页", expanded=False):
        s1, s2 = st.columns([2, 1])
        with s1:
            order_col = st.selectbox(
                "排序字段",
                options=[""] + all_cols,
                format_func=lambda x: "不排序" if x == "" else x,
                key=f"{prefix}_sort_c",
            )
        with s2:
            order_dir = st.selectbox(
                "方向", options=["ASC", "DESC"],
                key=f"{prefix}_sort_d",
                disabled=(order_col == ""),
            )
        order_by = f"{order_col} {order_dir}" if order_col else ""

        p1, p2 = st.columns(2)
        with p1:
            new_limit = st.number_input(
                "limit（返回条数）", min_value=1, max_value=1000,
                value=st.session_state[f"{prefix}_limit"],
                step=5, key=f"{prefix}_limit_inp",
            )
        with p2:
            new_offset = st.number_input(
                "offset（偏移量）", min_value=0, max_value=10000,
                value=st.session_state[f"{prefix}_offset"],
                step=st.session_state[f"{prefix}_limit"],
            )
        if new_limit != st.session_state[f"{prefix}_limit"]:
            st.session_state[f"{prefix}_limit"] = new_limit
            st.session_state[f"{prefix}_offset"] = 0
        if new_offset != st.session_state[f"{prefix}_offset"]:
            st.session_state[f"{prefix}_offset"] = new_offset

    effective_cols = (
        view_columns
        if view_columns
        else config.get("default_display", all_cols[:min(8, len(all_cols))])
    )

    # ---- 查询 + 新增按钮（并列） ----
    qb1, qb2 = st.columns(2)
    with qb1:
        if st.button("🔍 查询", type="primary", use_container_width=True, key=f"{prefix}_query_btn"):
            st.session_state[f"{prefix}_should_query"] = True
            st.rerun()
    with qb2:
        if st.session_state.get(f"{prefix}_sel_row") is None:
            if st.button("➕ 新增条目", use_container_width=True, key=f"{prefix}_add_top_btn"):
                st.session_state[f"{prefix}_sel_row"] = {}
                st.session_state[f"{prefix}_sel_idx"] = None
                st.rerun()

    # ---- 按需查询（不在编辑器模式且 should_query 时执行） ----
    current_sel = st.session_state.get(f"{prefix}_sel_row")
    should_query = st.session_state.get(f"{prefix}_should_query", False)
    if current_sel is None and should_query:
        # 合并 view filter + extra filters
        combined_filters = []
        if view_filter:
            combined_filters.append(view_filter)
        combined_filters.extend(extra_filters)

        # 始终构建 view JSON（filter 必填）
        section: dict = {"columns": effective_cols}
        if len(combined_filters) == 1:
            section["filter"] = combined_filters[0]
        elif len(combined_filters) > 1:
            section["filter"] = {"$and": combined_filters}
        else:
            # 无筛选条件 → 永真条件
            section["filter"] = {"column": "_", "value": None, "op": "TRUE"}
        view_obj: dict = {notebook_name: [section]}
        view_json = json.dumps(view_obj, ensure_ascii=False)

        limit = st.session_state.get(f"{prefix}_limit", 20)
        offset = st.session_state.get(f"{prefix}_offset", 0)

        try:
            result = api.query_entries(
                notebook_name, view=view_json,
                order_by=order_by or view_sort,
                limit=limit, offset=offset,
            )
            st.session_state[f"{prefix}_res"] = result
            st.session_state[f"{prefix}_should_query"] = False
        except Exception as e:
            st.error(f"查询失败: {e}")
            st.session_state[f"{prefix}_should_query"] = False

    # ---- 获取当前结果 ----
    results = st.session_state.get(f"{prefix}_res")
    rows = results.get("results", []) if results else []
    total_count = results.get("count", 0) if results else 0

    if results is not None:
        st.metric("匹配条目", total_count)

    # ---- 根据选中状态：显示卡片 或 条目编辑器 ----
    current_sel = st.session_state.get(f"{prefix}_sel_row")

    if current_sel is None:
        # ========== 卡片展示 ==========
        if rows:
            # 公共元字段集合（auto_fields + 跨 notebook 的通用字段→灰色小字）
            meta_fields: set = set(config.get("auto_fields", [])) | {"tags", "is_ai_gen", "ai_tags", "ai_note"}

            # effective_cols 中实际出现在数据中的字段
            present_cols = [c for c in effective_cols if c in rows[0]]

            # 主字段 = present_cols 中非元字段的部分（按 effective_cols 顺序）
            primary_fields = [c for c in present_cols if c not in meta_fields]
            # 如果全是元字段，直接展示全部
            if not primary_fields:
                primary_fields = present_cols[:3]

            # 灰色元字段（在 present_cols 中但不在 primary_fields 中）
            gray_fields = [c for c in present_cols if c not in primary_fields]

            st.subheader(f"📇 共 {len(rows)} 条结果")

            for idx, row in enumerate(rows):
                with st.container(border=True):
                    # ── 主字段（正常字号、加粗标题） ──
                    for field in primary_fields:
                        value = row.get(field, "")
                        fcfg = get_field_config(notebook_name, field)
                        label = fcfg.get("label", field)
                        display_val = str(value) if value is not None else "(空)"
                        if isinstance(value, str) and len(value) > 200:
                            display_val = value[:200] + "…"
                        st.markdown(f"**{label}**: {display_val}")

                    # ── 元字段（灰色小字） ──
                    if gray_fields:
                        parts = []
                        for field in gray_fields:
                            value = row.get(field, "")
                            fcfg = get_field_config(notebook_name, field)
                            label = fcfg.get("label", field)
                            display_val = str(value) if value is not None else "-"
                            if isinstance(value, str) and len(value) > 30:
                                display_val = value[:30] + "…"
                            parts.append(f"{label}: {display_val}")
                        st.markdown(
                            f"<span style='color: #999; font-size: 0.8em;'>{'  ·  '.join(parts)}</span>",
                            unsafe_allow_html=True,
                        )

                    # ── 查看详情按钮 ──
                    if st.button("📝 详情", key=f"{prefix}_card_sel_{idx}"):
                        st.session_state[f"{prefix}_sel_row"] = row
                        st.session_state[f"{prefix}_sel_idx"] = idx
                        st.rerun()
        elif results is not None:
            st.info("没有匹配的条目。")
    else:
        # ========== 统一条目编辑器（新增 / 编辑） ==========
        st.divider()

        if current_sel.get("id") is None:
            st.subheader("✏️ 新增条目")
            editor_mode = "add"
        else:
            st.subheader(f"✏️ 编辑条目 (ID: {current_sel.get('id')})")
            editor_mode = "edit"

        # 可编辑字段（非 auto_fields）
        edit_columns = [c for c in columns if c["name"] not in auto_fields]

        # 按两列分组
        field_groups = [edit_columns[i:i+2] for i in range(0, len(edit_columns), 2)]

        entry_data = {}
        row_key = current_sel.get("id", "new")

        for group in field_groups:
            row_cols = st.columns(len(group))
            for j, col_def in enumerate(group):
                name = col_def["name"]
                fcfg = get_field_config(notebook_name, name, col_def.get("type", "TEXT"))
                current_val = current_sel.get(name)
                with row_cols[j]:
                    val = _render_field_widget(
                        col_def, fcfg, f"{prefix}_edit_{row_key}",
                        value=current_val,
                    )
                    if fcfg.get("widget") == "checkbox":
                        entry_data[name] = val
                    elif val is not None and val != "":
                        entry_data[name] = val
                    else:
                        entry_data[name] = None

        # ---- 操作按钮 ----
        btn_cols = st.columns([2, 1, 1])

        with btn_cols[0]:
            if editor_mode == "add":
                if st.button("➕ 添加", type="primary", use_container_width=True, key=f"{prefix}_unified_add"):
                    valid = {k: v for k, v in entry_data.items() if v is not None and v != ""}
                    if not valid:
                        st.warning("请填写至少一个字段。")
                    else:
                        try:
                            r = api.add_entries(notebook_name, [valid])
                            st.success(f"✅ 成功添加 {r['count']} 条")
                            st.session_state[f"{prefix}_sel_row"] = None
                            st.session_state[f"{prefix}_res"] = None
                            st.session_state[f"{prefix}_should_query"] = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"添加失败: {e}")
            else:
                if st.button("💾 保存修改", type="primary", use_container_width=True, key=f"{prefix}_unified_save"):
                    changes = {k: v for k, v in entry_data.items() if v is not None and v != ""}
                    if not changes:
                        st.warning("没有要修改的字段。")
                    else:
                        try:
                            upd_filter = {"column": "id", "op": "=", "value": current_sel.get("id")}
                            r = api.update_entries(notebook_name, upd_filter, changes)
                            st.success(f"✅ 已更新 {r['count']} 条")
                            st.session_state[f"{prefix}_sel_row"] = None
                            st.session_state[f"{prefix}_res"] = None
                            st.session_state[f"{prefix}_should_query"] = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新失败: {e}")

        with btn_cols[1]:
            if editor_mode == "edit":
                if st.button("🗑️ 删除", type="secondary", use_container_width=True, key=f"{prefix}_unified_del"):
                    try:
                        del_filter = {"column": "id", "op": "=", "value": current_sel.get("id")}
                        r = api.delete_entries(notebook_name, del_filter)
                        st.success(f"✅ 已删除 {r['count']} 条")
                        st.session_state[f"{prefix}_sel_row"] = None
                        st.session_state[f"{prefix}_res"] = None
                        st.session_state[f"{prefix}_should_query"] = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"删除失败: {e}")

        with btn_cols[2]:
            if st.button("✖ 取消", use_container_width=True, key=f"{prefix}_unified_cancel"):
                st.session_state[f"{prefix}_sel_row"] = None
                st.session_state[f"{prefix}_should_query"] = True
                st.rerun()

    # ---- JSON 原始数据 ----
    if rows:
        with st.expander("📄 JSON 原始数据", expanded=False):
            st.json(rows[:50])

    # ---- 字段结构 ----
    _show_schema(columns)
