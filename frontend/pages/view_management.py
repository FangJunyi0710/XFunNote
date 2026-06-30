"""视图管理页面 — 可视化编辑 View 预设，FSM 驱动。"""

from __future__ import annotations

import json

import streamlit as st
from transitions import Machine

from frontend.api import get_client


# ==================== FSM ====================

class ViewMgmtFSM:
    """视图管理页面的有限状态机。

    States:
        idle      - 未选择笔记本，仅显示预设 + 视图名称 + JSON 预览
        browsing  - 已选择笔记本，显示 Spec 列表 + 添加模式编辑器
        editing   - 正在编辑某条 Spec，显示修改/删除模式编辑器
    """

    def __init__(self):
        self.machine = Machine(
            model=self,
            states=["idle", "browsing", "editing"],
            initial="idle",
            auto_transitions=False,
            queued=False,
        )
        self.machine.add_transition("select_notebook", "idle", "browsing")
        self.machine.add_transition("deselect_notebook", ["browsing", "editing"], "idle")
        self.machine.add_transition("edit_spec", "browsing", "editing")
        self.machine.add_transition("save_edit", "editing", "browsing")
        self.machine.add_transition("cancel_edit", "editing", "browsing")


def get_store() -> dict:
    """获取或创建集中式状态存储。"""
    key = "vm_fsm"
    if key not in st.session_state:
        st.session_state[key] = {
            "fsm": ViewMgmtFSM(),
            "view_name": "",
            "view_data": {},
            "sel_nb": "",
            "sel_spec_idx": None,
            "col_sel": [],
            "filter_json": '{"column": "_", "op": "TRUE", "value": null}',
            "sort": "",
            "saved_view_names": [],
            "preset": "(自定义)",
            "prev_nb": "",
        }
    return st.session_state[key]


def _reset_editor(store: dict):
    """清空编辑器中的字段。"""
    store["col_sel"] = []
    store["filter_json"] = '{"column": "_", "op": "TRUE", "value": null}'
    store["sort"] = ""
    store["sel_spec_idx"] = None


# ==================== Preset Helpers ====================

def _build_preset_view(api, preset: str) -> dict:
    """为所有 notebook 构建 full_view 或 no_view。"""
    notebooks = api.list_notebooks()
    view_data: dict = {}
    for nb in notebooks:
        schema = api.get_schema(nb)
        all_cols = [c["name"] for c in schema]
        if preset == "full_view":
            view_data[nb] = [
                {"columns": all_cols, "filter": {"column": "_", "op": "TRUE", "value": None}}
            ]
        elif preset == "no_view":
            view_data[nb] = [
                {"columns": [], "filter": {"column": "_", "op": "FALSE", "value": None}}
            ]
    return view_data


# ==================== Spec CRUD ====================

def _add_spec(nb: str, store: dict):
    """添加一个新的 TableSpec。"""
    view_data = store["view_data"]
    try:
        flt = json.loads(store["filter_json"])
    except json.JSONDecodeError:
        st.warning("筛选条件 JSON 格式错误，使用默认 TRUE")
        flt = {"column": "_", "op": "TRUE", "value": None}
    specs = view_data.setdefault(nb, [])
    specs.append({
        "columns": list(store["col_sel"]),
        "filter": flt,
        "sort": store["sort"] or "",
    })
    _reset_editor(store)


def _update_spec(nb: str, idx: int, store: dict):
    """修改指定的 TableSpec。"""
    view_data = store["view_data"]
    specs = view_data.get(nb, [])
    if idx < 0 or idx >= len(specs):
        st.error(f"无效的索引: {idx}")
        return
    try:
        flt = json.loads(store["filter_json"])
    except json.JSONDecodeError:
        st.warning("筛选条件 JSON 格式错误，使用默认 TRUE")
        flt = {"column": "_", "op": "TRUE", "value": None}
    specs[idx] = {
        "columns": list(store["col_sel"]),
        "filter": flt,
        "sort": store["sort"] or "",
    }


def _delete_spec(nb: str, idx: int, store: dict):
    """删除指定的 TableSpec。"""
    view_data = store["view_data"]
    specs = view_data.get(nb, [])
    if 0 <= idx < len(specs):
        specs.pop(idx)
        if not specs:
            view_data.pop(nb, None)


# ==================== Save / Preview ====================

def _do_save(api, name: str, data: dict, store: dict):
    if not name:
        st.error("请输入视图名称")
        return
    try:
        api.save_view(name, data)
        st.success(f"✅ 视图 `{name}` 已保存")
        store["view_name"] = name
        store["saved_view_names"] = [v["name"] for v in (api.list_views() or [])]
        st.rerun()
    except Exception as e:
        st.error(f"保存失败: {e}")


def _do_preview(api, nb: str, data: dict):
    specs = data.get(nb, [])
    if not specs:
        st.warning(f"`{nb}` 暂无 TableSpec，无法预览")
        return
    try:
        view_json = json.dumps({nb: specs}, ensure_ascii=False)
        results = api.query_entries(nb, view=view_json, limit=20)
        rows = results.get("results", [])
        total = results.get("count", len(rows))
        st.success(f"预览完成 — 共 {total} 条 (显示前 {len(rows)} 条)")
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("无匹配条目")
    except Exception as e:
        st.error(f"预览失败: {e}")


# ==================== Sub-renderers ====================

def _render_top_bar(api, store: dict):
    """渲染预设选择 + 视图名称输入（所有状态共享）。"""
    preset_opts = ["(自定义)", "full_view", "no_view"] + store["saved_view_names"]
    presets_deduped = list(dict.fromkeys(preset_opts))

    col1, col2 = st.columns(2)
    with col1:
        sel_preset = st.selectbox(
            "📋 视图预设 / 已保存视图",
            options=presets_deduped,
            key="vm_preset_dropdown",
        )
        if sel_preset != store["preset"]:
            store["preset"] = sel_preset
            if sel_preset in ("full_view", "no_view"):
                store["view_data"] = _build_preset_view(api, sel_preset)
                store["sel_nb"] = ""
                _reset_editor(store)
                st.rerun()
            elif sel_preset in store["saved_view_names"]:
                try:
                    data = api.get_view(sel_preset)
                    if data:
                        store["view_data"] = data
                        store["view_name"] = sel_preset
                        store["sel_nb"] = ""
                        _reset_editor(store)
                        st.rerun()
                except Exception:
                    pass

    with col2:
        st.text_input(
            "📝 视图名称",
            value=store["view_name"],
            key="vm_name_input",
            placeholder="保存时使用的文件名",
        )


def _render_nb_selector(api, store: dict, fsm: ViewMgmtFSM):
    """渲染笔记本选择器，切换时自动重置编辑器 + 驱动 FSM。"""
    try:
        notebooks = api.list_notebooks()
    except Exception:
        notebooks = []

    sel_nb = st.selectbox(
        "📒 选择笔记本",
        options=[""] + notebooks,
        key="vm_nb_selector",
        format_func=lambda x: x if x else "— 请选择 —",
    )

    # 清空选择 → idle
    if not sel_nb:
        store["sel_nb"] = ""
        if fsm.state != "idle":
            fsm.deselect_notebook()
            st.rerun()
        return

    # 切换笔记本 → 重置编辑器
    if sel_nb != store["prev_nb"]:
        store["prev_nb"] = sel_nb
        store["sel_nb"] = sel_nb
        _reset_editor(store)
        if fsm.state == "idle":
            fsm.select_notebook()
        else:
            # 如果在 editing，退回到 browsing
            if fsm.state == "editing":
                fsm.cancel_edit()
        st.rerun()


def _render_spec_list(sel_nb: str, specs: list, store: dict, fsm: ViewMgmtFSM):
    """渲染当前笔记本的 TableSpec 列表 + radio 选择。"""
    st.subheader(f"📄 `{sel_nb}` 的 TableSpec 列表 ({len(specs)} 个)")

    if not specs:
        st.info("暂无 TableSpec，请在下方添加")
        return

    rows = []
    for i, spec in enumerate(specs):
        cols_str = ", ".join(spec.get("columns", [])) or "(无)"
        flt_raw = spec.get("filter", {})
        flt_str = json.dumps(flt_raw, ensure_ascii=False)
        rows.append({
            "序号": i,
            "列": cols_str[:80],
            "筛选条件 (JSON)": flt_str[:100],
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    spec_options = [f"#{i}: {r['列'][:40]}" for i, r in enumerate(rows)]
    sel_label = st.radio(
        "选择要编辑的 TableSpec",
        options=["(返回浏览)"] + spec_options,
        index=0,
        horizontal=True,
        key="vm_spec_radio",
    )

    if sel_label == "(返回浏览)":
        if store["sel_spec_idx"] is not None:
            _reset_editor(store)
            if fsm.state == "editing":
                fsm.cancel_edit()
                st.rerun()
    else:
        new_idx = int(sel_label.split(":")[0].lstrip("#"))
        if new_idx != store["sel_spec_idx"]:
            spec = specs[new_idx]
            store["sel_spec_idx"] = new_idx
            store["col_sel"] = spec.get("columns", [])
            store["filter_json"] = json.dumps(
                spec.get("filter", {}), ensure_ascii=False, indent=2
            )
            store["sort"] = spec.get("sort", "")
            if fsm.state == "browsing":
                fsm.edit_spec()
                st.rerun()


def _render_editor(sel_nb: str, all_cols: list, store: dict, fsm: ViewMgmtFSM, is_editing: bool):
    """渲染 TableSpec 编辑器（添加模式 / 修改模式）。"""
    st.divider()
    st.subheader("✏️ TableSpec 编辑器")

    # 列多选 — 切换笔记本时 _reset_editor 已清空 col_sel，默认永不出界
    current_cols = st.multiselect(
        "选择列 (TableSpec 中显示)",
        options=all_cols,
        default=store["col_sel"],
        key="vm_multiselect_cols",
    )
    if current_cols != store["col_sel"]:
        store["col_sel"] = current_cols

    st.text_area(
        "筛选条件 (JSON)",
        value=store["filter_json"],
        height=140,
        key="vm_filter_textarea",
        help=(
            "支持三种格式:\n"
            "1. 单个条件: {\"column\": \"month\", \"op\": \"=\", \"value\": \"2025-01\"}\n"
            "2. 多个 AND: [[{\"column\":...}, {\"column\":...}]]\n"
            "3. 多个 OR:  [[{\"column\":...}], [{\"column\":...}]]\n"
            "运算符: =, !=, >, <, >=, <=, LIKE, IN, NOT IN, BETWEEN, "
            "JSON_CONTAINS, JSON_NOT_CONTAINS, TEXT_SEARCH, TRUE, FALSE"
        ),
    )

    st.text_input(
        "排序 (预留)",
        value=store["sort"],
        key="vm_sort_text",
        placeholder="如 created_at DESC",
    )

    # ---- 操作按钮 ----
    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        if is_editing:
            if st.button("🔄 修改", type="primary", use_container_width=True, key="vm_btn_modify"):
                _update_spec(sel_nb, store["sel_spec_idx"], store)
                _reset_editor(store)
                fsm.save_edit()
                st.rerun()
        else:
            if st.button("➕ 添加", type="primary", use_container_width=True, key="vm_btn_add"):
                _add_spec(sel_nb, store)
                st.rerun()

    with bcol2:
        if is_editing:
            if st.button("🗑️ 删除", use_container_width=True, key="vm_btn_delete"):
                _delete_spec(sel_nb, store["sel_spec_idx"], store)
                _reset_editor(store)
                fsm.save_edit()
                st.rerun()

    with bcol3:
        if is_editing:
            if st.button("✖ 取消编辑", use_container_width=True, key="vm_btn_cancel"):
                _reset_editor(store)
                fsm.cancel_edit()
                st.rerun()


def _render_action_buttons(api, sel_nb: str, store: dict):
    """预览 & 保存按钮（仅 browsing 状态显示）。"""
    st.divider()
    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        if st.button("🔍 预览 (当前笔记本)", use_container_width=True, key="vm_btn_preview"):
            _do_preview(api, sel_nb, store["view_data"])

    with bcol2:
        if st.button("💾 保存", type="primary", use_container_width=True, key="vm_btn_save"):
            _do_save(api, store["view_name"], store["view_data"], store)

    with bcol3:
        if st.button("📋 另存为...", use_container_width=True, key="vm_btn_saveas"):
            new_name = f"{store['view_name']}_copy" if store['view_name'] else "unnamed_copy"
            _do_save(api, new_name, store["view_data"], store)


def _render_view_json_preview(store: dict):
    """以 expander 展示完整 View JSON。"""
    view_data = store["view_data"]
    if view_data:
        with st.expander("📄 完整 View JSON", expanded=False):
            st.json(view_data)


# ==================== State Dispatchers ====================

def _render_idle(api, store: dict, fsm: ViewMgmtFSM):
    """idle 状态：未选择笔记本。"""
    _render_top_bar(api, store)
    _render_nb_selector(api, store, fsm)
    st.info("请选择一个笔记本开始编辑视图")
    _render_view_json_preview(store)


def _render_browsing(api, store: dict, fsm: ViewMgmtFSM):
    """browsing 状态：已选择笔记本，可添加/浏览。"""
    sel_nb = store["sel_nb"]

    try:
        schema = api.get_schema(sel_nb)
        all_cols = [c["name"] for c in schema]
    except Exception:
        all_cols = []

    _render_top_bar(api, store)
    _render_nb_selector(api, store, fsm)

    # 如果选择器内触发了 deselect，此处 fsm.state 已变，提前返回
    if fsm.state == "idle":
        return

    specs = store["view_data"].get(sel_nb, [])
    _render_spec_list(sel_nb, specs, store, fsm)
    _render_editor(sel_nb, all_cols, store, fsm, is_editing=False)
    _render_action_buttons(api, sel_nb, store)
    _render_view_json_preview(store)


def _render_editing(api, store: dict, fsm: ViewMgmtFSM):
    """editing 状态：正在编辑某条 Spec。"""
    sel_nb = store["sel_nb"]

    try:
        schema = api.get_schema(sel_nb)
        all_cols = [c["name"] for c in schema]
    except Exception:
        all_cols = []

    _render_top_bar(api, store)
    _render_nb_selector(api, store, fsm)

    if fsm.state == "idle":
        return

    specs = store["view_data"].get(sel_nb, [])
    _render_spec_list(sel_nb, specs, store, fsm)
    _render_editor(sel_nb, all_cols, store, fsm, is_editing=True)
    _render_view_json_preview(store)


# ==================== Main Render ====================

def _render():
    st.title("👁️ 视图管理")
    api = get_client()
    store = get_store()
    fsm = store["fsm"]

    # 刷新已保存视图列表
    try:
        saved_views = api.list_views() or []
        store["saved_view_names"] = [v["name"] for v in saved_views]
    except Exception:
        store["saved_view_names"] = []

    # 根据 FSM 状态分发
    state = fsm.state

    if state == "idle":
        _render_idle(api, store, fsm)
    elif state == "browsing":
        _render_browsing(api, store, fsm)
    elif state == "editing":
        _render_editing(api, store, fsm)


# ==================== Entry Point ====================

_render()
