"""视图管理页面 — 可视化编辑 View 预设，FSM 驱动。"""
from __future__ import annotations

import json

import streamlit as st
from transitions import Machine

from frontend.api import get_client
from frontend.components import render_filter_editor
from frontend.store import StoreProxy


# ==================== FSM ====================

class ViewMgmtFSM:
    """视图管理页面的有限状态机。

    States:
        idle      - 未选择笔记本，仅显示预设 + 视图名称 + JSON 预览
        browsing  - 已选择笔记本，显示 Spec 列表 + 添加模式编辑器
        editing   - 正在编辑某条 Spec，显示修改/删除模式编辑器
    """

    def __init__(self):
        self._sel_spec_idx: int | None = None
        self.machine = Machine(
            model=self,
            states=["idle", "browsing", "editing", "reset_pending"],
            initial="idle",
            auto_transitions=False,
            queued=False,
        )
        self.machine.add_transition("select_notebook", "idle", "browsing", after=self._clear_spec_idx)
        self.machine.add_transition("deselect_notebook", ["browsing", "editing"], "idle", after=self._clear_spec_idx)
        self.machine.add_transition("edit_spec", "browsing", "editing")
        self.machine.add_transition("save_edit", "editing", "reset_pending", after=self._clear_spec_idx)
        self.machine.add_transition("cancel_edit", "editing", "reset_pending", after=self._clear_spec_idx)
        self.machine.add_transition("finish_add", "browsing", "reset_pending", after=self._clear_spec_idx)
        self.machine.add_transition("reset_done", "reset_pending", "browsing", after=self._clear_spec_idx)

    @property
    def sel_spec_idx(self) -> int | None:
        return self._sel_spec_idx

    @sel_spec_idx.setter
    def sel_spec_idx(self, value: int | None):
        self._sel_spec_idx = value

    def _clear_spec_idx(self):
        self._sel_spec_idx = None


def get_store() -> StoreProxy:
    """获取或创建视图管理页面的扁平 key 单源存储。"""
    prefix = "vm"
    defaults = {
        "fsm": ViewMgmtFSM(),
        "view_name": "",
        "view_data": {},
        "sel_nb": "",
        "col_sel": [],
        "filter_json": '{"column": "_", "op": "TRUE", "value": null}',
        "sort": "",
        "saved_view_names": [],
        "preset": "full_view",
        "prev_nb": "",
    }
    for key, value in defaults.items():
        full_key = f"{prefix}_{key}"
        if full_key not in st.session_state:
            st.session_state[full_key] = value
    return StoreProxy("vm")


def _reset_editor(store: StoreProxy):
    """清空编辑器中的字段。"""
    store["col_sel"] = []
    store["filter_json"] = '{"column": "_", "op": "TRUE", "value": null}'
    store["sort"] = ""


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

def _add_spec(nb: str, store: StoreProxy, fsm: ViewMgmtFSM):
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
    fsm.finish_add()


def _update_spec(nb: str, idx: int, store: StoreProxy):
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


def _delete_spec(nb: str, idx: int, store: StoreProxy):
    """删除指定的 TableSpec。"""
    view_data = store["view_data"]
    specs = view_data.get(nb, [])
    if 0 <= idx < len(specs):
        specs.pop(idx)
        if not specs:
            view_data.pop(nb, None)


def _move_spec(nb: str, idx: int, direction: int, store: StoreProxy):
    """移动 Spec 顺序。direction: -1 上移, +1 下移。"""
    view_data = store["view_data"]
    specs = view_data.get(nb, [])
    target = idx + direction
    if 0 <= target < len(specs):
        specs[idx], specs[target] = specs[target], specs[idx]


# ==================== Save / Preview ====================

def _do_save(api, name: str, data: dict, store: StoreProxy):
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
            st.dataframe(rows, width='stretch', hide_index=True)
        else:
            st.info("无匹配条目")
    except Exception as e:
        st.error(f"预览失败: {e}")


# ==================== Callbacks (on_change) ====================

def _on_preset_change(api, store: StoreProxy):
    """预设下拉变化：构建预设视图或加载已保存视图。"""
    sel = st.session_state["vm_preset"]
    store["preset"] = sel
    if sel in ("full_view", "no_view"):
        store["view_data"] = _build_preset_view(api, sel)
        _reset_editor(store)
    elif sel in store["saved_view_names"]:
        try:
            data = api.get_view(sel)
            if data:
                store["view_data"] = data
                store["view_name"] = sel
                _reset_editor(store)
        except Exception:
            pass


def _on_nb_change(fsm: ViewMgmtFSM, store: StoreProxy):
    """笔记本选择器变化：驱动 FSM + 重置编辑器。"""
    sel = st.session_state["vm_sel_nb"]
    prev = store.get("prev_nb", "")
    if sel != prev:
        store["prev_nb"] = sel
        store["sel_nb"] = sel
        _reset_editor(store)
        if fsm.state == "idle":
            fsm.select_notebook()
        elif fsm.state == "editing":
            fsm.cancel_edit()


# ==================== Sub-renderers ====================

def _render_top_bar(api, store: StoreProxy):
    """渲染预设选择 + 视图名称输入（所有状态共享）。"""
    preset_opts = ["full_view", "no_view"] + sorted(store["saved_view_names"])
    presets_deduped = list(dict.fromkeys(preset_opts))

    col1, col2 = st.columns(2)
    with col1:
        st.selectbox(
            "📋 视图预设 / 已保存视图",
            options=presets_deduped,
            key="vm_preset",
            on_change=_on_preset_change, args=(api, store),
        )

    with col2:
        st.text_input(
            "📝 视图名称",
            key="vm_view_name",
            placeholder="保存时使用的文件名",
        )


def _render_nb_selector(api, store: StoreProxy, fsm: ViewMgmtFSM):
    """渲染笔记本选择器。"""
    try:
        notebooks = api.list_notebooks()
    except Exception:
        notebooks = []

    st.selectbox(
        "📒 选择笔记本",
        options=notebooks,
        index=0,
        key="vm_sel_nb",
        on_change=_on_nb_change, args=(fsm, store),
    )


def _render_spec_list(sel_nb: str, specs: list, store: StoreProxy, fsm: ViewMgmtFSM):
    """渲染当前笔记本的 TableSpec 列表 + 上移/下移 + radio 选择。"""
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

    # 上移/下移按钮
    move_cols = st.columns(len(specs) + 1)
    for i in range(len(specs)):
        with move_cols[i]:
            sub = st.columns(2)
            with sub[0]:
                if i > 0 and st.button(f"⬆", key=f"vm_up_{i}", help="上移"):
                    _move_spec(sel_nb, i, -1, store)
                    if fsm.state == "editing":
                        fsm.cancel_edit()
                    st.rerun()
            with sub[1]:
                if i < len(specs) - 1 and st.button(f"⬇", key=f"vm_down_{i}", help="下移"):
                    _move_spec(sel_nb, i, 1, store)
                    if fsm.state == "editing":
                        fsm.cancel_edit()
                    st.rerun()

    st.dataframe(rows, width='stretch', hide_index=True)

    spec_options = [f"#{i}: {r['列'][:40]}" for i, r in enumerate(rows)]
    bcol1, bcol2 = st.columns([1, 4])
    with bcol1:
        if st.button("✖ 返回浏览", key="vm_back_to_browse", help="退出编辑模式回到浏览"):
            if fsm.sel_spec_idx is not None:
                _reset_editor(store)
                if fsm.state == "editing":
                    fsm.cancel_edit()
                    st.rerun()
    with bcol2:
        sel_label = st.radio(
            "选择要编辑的 TableSpec",
            options=spec_options,
            index=0,
            horizontal=True,
            key="vm_spec_radio",
        )

    new_idx = int(sel_label.split(":")[0].lstrip("#"))
    if new_idx != fsm.sel_spec_idx:
        spec = specs[new_idx]
        fsm.sel_spec_idx = new_idx
        store["col_sel"] = spec.get("columns", [])
        store["filter_json"] = json.dumps(
            spec.get("filter", {}), ensure_ascii=False, indent=2
        )
        store["sort"] = spec.get("sort", "")
        if fsm.state == "browsing":
            fsm.edit_spec()
            st.rerun()


def _render_editor(sel_nb: str, all_cols: list, store: StoreProxy, fsm: ViewMgmtFSM, is_editing: bool):
    """渲染 TableSpec 编辑器（添加模式 / 修改模式）。"""
    st.divider()
    st.subheader("✏️ TableSpec 编辑器")

    # 列多选 — 切换笔记本时 _reset_editor 已清空 col_sel，默认永不出界
    st.multiselect(
        "选择列 (TableSpec 中显示)",
        options=all_cols,
        key="vm_col_sel",
    )

    render_filter_editor(key="vm_filter_json")

    st.text_input(
        "排序 (预留)",
        key="vm_sort",
        placeholder="如 created_at DESC",
    )

    # ---- 操作按钮 ----
    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        if is_editing:
            if st.button("🔄 修改", type="primary", width='stretch', key="vm_btn_modify"):
                _update_spec(sel_nb, fsm.sel_spec_idx, store)
                fsm.save_edit()
                st.rerun()
        else:
            if st.button("➕ 添加", type="primary", width='stretch', key="vm_btn_add"):
                _add_spec(sel_nb, store, fsm)
                st.rerun()

    with bcol2:
        if is_editing:
            if st.button("🗑️ 删除", width='stretch', key="vm_btn_delete"):
                _delete_spec(sel_nb, fsm.sel_spec_idx, store)
                fsm.save_edit()
                st.rerun()

    with bcol3:
        if is_editing:
            if st.button("✖ 取消编辑", width='stretch', key="vm_btn_cancel"):
                fsm.cancel_edit()
                st.rerun()


def _render_action_buttons(api, sel_nb: str, store: StoreProxy):
    """预览 & 保存按钮（仅 browsing 状态显示）。"""
    st.divider()
    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        if st.button("🔍 预览 (当前笔记本)", width='stretch', key="vm_btn_preview"):
            _do_preview(api, sel_nb, store["view_data"])

    with bcol2:
        if st.button("💾 保存", type="primary", width='stretch', key="vm_btn_save"):
            _do_save(api, store["view_name"], store["view_data"], store)

    with bcol3:
        if st.button("📋 另存为...", width='stretch', key="vm_btn_saveas"):
            new_name = f"{store['view_name']}_copy" if store['view_name'] else "unnamed_copy"
            _do_save(api, new_name, store["view_data"], store)


def _render_view_json_preview(store: StoreProxy):
    """以 expander 展示完整 View JSON。"""
    view_data = store["view_data"]
    if view_data:
        with st.expander("📄 完整 View JSON", expanded=False):
            st.json(view_data)


# ==================== State Dispatchers ====================

def _render_idle(api, store: StoreProxy, fsm: ViewMgmtFSM):
    """idle 状态：未选择笔记本。"""
    _render_top_bar(api, store)
    _render_nb_selector(api, store, fsm)
    st.info("请选择一个笔记本开始编辑视图")
    _render_view_json_preview(store)


def _render_browsing(api, store: StoreProxy, fsm: ViewMgmtFSM):
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


def _render_editing(api, store: StoreProxy, fsm: ViewMgmtFSM):
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

    # 自动构建预设视图：当预设为 full_view/no_view 且 view_data 尚未构建时
    if store["preset"] in ("full_view", "no_view") and not store["view_data"]:
        store["view_data"] = _build_preset_view(api, store["preset"])

    # 确保默认选中第一个笔记本（在状态分发之前，使空闲→浏览能立即生效）
    try:
        notebooks = api.list_notebooks()
    except Exception:
        notebooks = []
    if notebooks and (not store["sel_nb"] or store["sel_nb"] not in notebooks):
        store["sel_nb"] = notebooks[0]
        store["prev_nb"] = notebooks[0]

    # 空闲且已有默认笔记本 → 自动进入浏览状态
    if fsm.state == "idle" and store["sel_nb"]:
        fsm.select_notebook()

    # 延迟复位：按钮触发后，在下一轮 widget 创建之前复位编辑器
    if fsm.state == "reset_pending":
        _reset_editor(store)
        fsm.reset_done()

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
