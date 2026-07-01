"""Notebook 相关 — FSM、配置、渲染函数。"""
from __future__ import annotations

import json
import streamlit as st
from transitions import Machine

from frontend.api import get_client
from frontend.store import StoreProxy


# ==================== FSM ====================

class NotebookFSM:
    """Finite State Machine for notebook pages.

    States: idle -> browsing <-> adding/editing
    """

    def __init__(self):
        self.machine = Machine(
            model=self,
            states=["idle", "browsing", "adding", "editing"],
            initial="idle",
            auto_transitions=False,
            queued=False,
        )

        # Query
        self.machine.add_transition("do_query", "idle", "browsing")
        # Browse actions
        self.machine.add_transition("start_add", "browsing", "adding")
        self.machine.add_transition("start_edit", "browsing", "editing")
        # Save result -> browse
        self.machine.add_transition("save_add", "adding", "browsing")
        self.machine.add_transition("save_edit", "editing", "browsing")
        self.machine.add_transition("delete_entry", "editing", "browsing")
        # Cancel (from both adding and editing)
        self.machine.add_transition("cancel", ["adding", "editing"], "browsing")


def get_store(notebook_name: str) -> StoreProxy:
    """获取笔记本的扁平 key 单源存储。

    所有 key 为扁平格式：nb_{name}_{key}。
    """
    prefix = f"nb_{notebook_name}"
    defaults = {
        "fsm": NotebookFSM(),
        "limit": 20,
        "offset": 0,
        "n_filters": 1,
        "results": None,
        "sel_row": None,
        "sel_idx": None,
    }
    for key, value in defaults.items():
        full_key = f"{prefix}_{key}"
        if full_key not in st.session_state:
            st.session_state[full_key] = value
    return StoreProxy(prefix)


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
        st.dataframe(rows, width="stretch", hide_index=True)


# ==================== View Selector ====================

def _render_view_selector(api, notebook_name: str, prefix: str):
    """侧边栏视图下拉。返回 (view_columns, view_filter, view_sort)。"""
    view_columns, view_filter, view_sort = [], None, ""

    try:
        all_views = api.list_views()
    except Exception:
        all_views = []

    related_views, other_views = [], []
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
        try:
            view_data = api.get_view(selected_label)
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
                f"已加载视图 `{selected_label}` → "
                f"{', '.join(view_columns[:6])}{'...' if len(view_columns) > 6 else ''}"
            )

    return view_columns, view_filter, view_sort


# ==================== Filter Panel ====================

def _render_filter_panel(prefix: str, all_cols: list[str], store: dict) -> list[dict]:
    """筛选条件 expander。返回 extra_filters 列表。"""
    with st.expander("🔍 筛选条件（叠加在视图之上）", expanded=False):
        op_map = {
            "=": "=", "!=": "!=", "包含": "LIKE",
            ">": ">", "<": "<", ">=": ">=", "<=": "<=",
        }
        extra_filters = []

        for fi in range(store["n_filters"]):
            fcol1, fcol2, fcol3 = st.columns([2, 1, 2])
            with fcol1:
                field = st.selectbox(
                    "字段" if fi == 0 else f"字段 #{fi + 1}",
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
            if st.button("➕ 添加条件", width="stretch", key=f"{prefix}_add_flt"):
                store["n_filters"] += 1
                st.rerun()
        with bcol2:
            if st.button("➖ 移除条件", width="stretch", key=f"{prefix}_del_flt",
                         disabled=store["n_filters"] <= 1):
                store["n_filters"] = max(1, store["n_filters"] - 1)
                st.rerun()

        return extra_filters


# ==================== Sort & Pagination ====================

def _on_limit_change(prefix: str):
    """limit 变化时 offset 归零并清除结果。"""
    st.session_state[f"{prefix}_offset"] = 0
    st.session_state[f"{prefix}_results"] = None


def _on_offset_change(prefix: str):
    """offset 变化时清除结果。"""
    st.session_state[f"{prefix}_results"] = None


def _render_sort_pagination(prefix: str, all_cols: list[str], store: StoreProxy) -> str:
    """排序与分页 expander。返回 order_by 字符串。"""
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
            st.number_input(
                "limit（返回条数）", min_value=1, max_value=1000,
                value=store["limit"],
                step=5, key=f"{prefix}_limit",
                on_change=_on_limit_change, args=(prefix,),
            )
        with p2:
            # 当前页无结果时禁止增大 offset
            _results = store.get("results")
            _empty = _results is not None and len(_results.get("results", []) or []) == 0
            off_max = store["offset"] if _empty else 10000
            st.number_input(
                "offset（偏移量）", min_value=0, max_value=off_max,
                value=store["offset"],
                step=store["limit"],
                key=f"{prefix}_offset",
                on_change=_on_offset_change, args=(prefix,),
            )

        return order_by


# ==================== Query Execution ====================

def _execute_query(api, notebook_name: str, effective_cols: list[str],
                   view_filter, view_sort: str, extra_filters: list[dict],
                   order_by: str, store: dict):
    """执行查询并将结果写入 store['results']。"""
    combined_filters = []
    if view_filter:
        combined_filters.append(view_filter)
    combined_filters.extend(extra_filters)

    section: dict = {"columns": effective_cols}
    if len(combined_filters) == 1:
        section["filter"] = combined_filters[0]
    elif len(combined_filters) > 1:
        section["filter"] = {"$and": combined_filters}
    else:
        section["filter"] = {"column": "_", "value": None, "op": "TRUE"}

    view_obj: dict = {notebook_name: [section]}
    view_json = json.dumps(view_obj, ensure_ascii=False)

    try:
        store["results"] = api.query_entries(
            notebook_name, view=view_json,
            order_by=order_by or view_sort,
            limit=store["limit"], offset=store["offset"],
        )
    except Exception as e:
        st.error(f"查询失败: {e}")
        store["results"] = None


# ==================== Card List ====================

def _render_cards(notebook_name: str, config: dict, prefix: str,
                  effective_cols: list[str], rows: list[dict], store: dict):
    """渲染卡片列表（browsing 状态）。"""
    fsm = store["fsm"]
    meta_fields: set = set(config.get("auto_fields", [])) | {"tags", "is_ai_gen", "ai_tags", "ai_note"}
    present_cols = [c for c in effective_cols if c in rows[0]]
    primary_fields = [c for c in present_cols if c not in meta_fields]
    if not primary_fields:
        primary_fields = present_cols[:3]
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

            # ── 详情按钮 → start_edit ──
            if st.button("📝 详情", key=f"{prefix}_card_sel_{idx}"):
                store["sel_row"] = row
                store["sel_idx"] = idx
                fsm.start_edit()
                st.rerun()


# ==================== Editor (Add / Edit) ====================

def _render_editor(notebook_name: str, config: dict, prefix: str,
                   api, columns: list[dict], auto_fields: set, store: dict):
    """统一编辑器 — 新增或编辑条目。"""
    fsm = store["fsm"]
    current_sel = store["sel_row"] or {}

    if fsm.state == "adding":
        st.subheader("✏️ 新增条目")
        editor_mode = "add"
    else:
        st.subheader(f"✏️ 编辑条目 (ID: {current_sel.get('id')})")
        editor_mode = "edit"

    edit_columns = [c for c in columns if c["name"] not in auto_fields]
    field_groups = [edit_columns[i:i + 2] for i in range(0, len(edit_columns), 2)]

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
            if st.button("➕ 添加", type="primary", use_container_width=True,
                         key=f"{prefix}_unified_add"):
                valid = {k: v for k, v in entry_data.items()
                         if v is not None and v != ""}
                if not valid:
                    st.warning("请填写至少一个字段。")
                else:
                    try:
                        api.add_entries(notebook_name, [valid])
                        st.success("✅ 添加成功")
                        store["sel_row"] = None
                        store["sel_idx"] = None
                        store["results"] = None
                        fsm.save_add()
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加失败: {e}")
        else:
            if st.button("💾 保存修改", type="primary", use_container_width=True,
                         key=f"{prefix}_unified_save"):
                changes = {k: v for k, v in entry_data.items()
                           if v is not None and v != ""}
                if not changes:
                    st.warning("没有要修改的字段。")
                else:
                    try:
                        upd_filter = {"column": "id", "op": "=", "value": current_sel.get("id")}
                        api.update_entries(notebook_name, upd_filter, changes)
                        st.success("✅ 已更新")
                        store["sel_row"] = None
                        store["sel_idx"] = None
                        store["results"] = None
                        fsm.save_edit()
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新失败: {e}")

    with btn_cols[1]:
        if editor_mode == "edit":
            if st.button("🗑️ 删除", type="secondary", use_container_width=True,
                         key=f"{prefix}_unified_del"):
                try:
                    del_filter = {"column": "id", "op": "=", "value": current_sel.get("id")}
                    api.delete_entries(notebook_name, del_filter)
                    st.success("✅ 已删除")
                    store["sel_row"] = None
                    store["sel_idx"] = None
                    store["results"] = None
                    fsm.delete_entry()
                    st.rerun()
                except Exception as e:
                    st.error(f"删除失败: {e}")

    with btn_cols[2]:
        if st.button("✖ 取消", use_container_width=True,
                     key=f"{prefix}_unified_cancel"):
            store["sel_row"] = None
            store["sel_idx"] = None
            fsm.cancel()
            st.rerun()


# ==================== Main Render ====================

def render_notebook_page(notebook_name: str):
    """配置驱动的完整笔记本页面 — FSM 驱动。"""
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
    store = get_store(notebook_name)
    fsm = store["fsm"]

    # ---- Sidebar: View Selector ----
    view_columns, view_filter, view_sort = _render_view_selector(api, notebook_name, prefix)

    effective_cols = (
        view_columns if view_columns
        else config.get("default_display", all_cols[:min(8, len(all_cols))])
    )

    # ---- Filter Panel ----
    extra_filters = _render_filter_panel(prefix, all_cols, store)

    # ---- Sort & Pagination ----
    order_by = _render_sort_pagination(prefix, all_cols, store)

    # ---- Dispatch by FSM State ----
    state = fsm.state

    if state == "idle":
        # 首次进入页面自动触发查询
        _execute_query(api, notebook_name, effective_cols,
                       view_filter, view_sort, extra_filters, order_by, store)
        fsm.do_query()
        st.rerun()

    elif state == "browsing":
        # 查询 + 新增按钮
        qb1, qb2 = st.columns(2)
        with qb1:
            if st.button("🔍 查询", type="primary", use_container_width=True,
                         key=f"{prefix}_query_btn"):
                _execute_query(api, notebook_name, effective_cols,
                               view_filter, view_sort, extra_filters, order_by, store)
                st.rerun()
        with qb2:
            if st.button("➕ 新增条目", use_container_width=True,
                         key=f"{prefix}_add_top_btn"):
                store["sel_row"] = {}
                store["sel_idx"] = None
                fsm.start_add()
                st.rerun()

        # 自动查询（首次进入或重置后）
        if store["results"] is None:
            _execute_query(api, notebook_name, effective_cols,
                           view_filter, view_sort, extra_filters, order_by, store)

        results = store["results"]
        rows = results.get("results", []) if results else []
        total_count = results.get("count", 0) if results else 0

        # offset>0 且结果为空 → 自动回退一页
        if not rows and results is not None and store["offset"] > 0:
            store["offset"] = max(0, store["offset"] - store["limit"])
            store["results"] = None
            st.rerun()

        if results is not None:
            st.metric("匹配条目", total_count)

        if rows:
            _render_cards(notebook_name, config, prefix, effective_cols, rows, store)
        elif results is not None:
            st.info("没有匹配的条目。")

        # JSON 原始数据
        if rows:
            with st.expander("📄 JSON 原始数据", expanded=False):
                st.json(rows[:50])

    elif state in ("adding", "editing"):
        st.divider()
        _render_editor(notebook_name, config, prefix, api, columns, auto_fields, store)

    # ---- 字段结构（始终显示） ----
    _show_schema(columns)
