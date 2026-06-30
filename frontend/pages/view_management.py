"""视图管理页面 — 可视化编辑 View 预设。"""

from __future__ import annotations

import json

import streamlit as st

from frontend.api import get_client


# ==================== Session State Init ====================

def _init_state():
    defaults = {
        "vm_preset": "(自定义)",
        "vm_view_name": "",
        "vm_view_data": {},
        "vm_selected_nb": "",
        "vm_selected_spec_idx": None,
        "vm_col_sel": [],
        "vm_filter_json": '{"column": "_", "op": "TRUE", "value": null}',
        "vm_sort": "",
        "vm_saved_view_names": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _reset_editor():
    st.session_state.vm_col_sel = []
    st.session_state.vm_filter_json = '{"column": "_", "op": "TRUE", "value": null}'
    st.session_state.vm_sort = ""
    st.session_state.vm_selected_spec_idx = None


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

def _add_spec(nb: str):
    view_data = st.session_state.vm_view_data
    try:
        flt = json.loads(st.session_state.vm_filter_json)
    except json.JSONDecodeError:
        st.warning("筛选条件 JSON 格式错误，使用默认 TRUE")
        flt = {"column": "_", "op": "TRUE", "value": None}
    specs = view_data.setdefault(nb, [])
    specs.append({
        "columns": list(st.session_state.vm_col_sel),
        "filter": flt,
        "sort": st.session_state.vm_sort or "",
    })
    _reset_editor()


def _update_spec(nb: str, idx: int):
    view_data = st.session_state.vm_view_data
    specs = view_data.get(nb, [])
    if idx < 0 or idx >= len(specs):
        st.error(f"无效的索引: {idx}")
        return
    try:
        flt = json.loads(st.session_state.vm_filter_json)
    except json.JSONDecodeError:
        st.warning("筛选条件 JSON 格式错误，使用默认 TRUE")
        flt = {"column": "_", "op": "TRUE", "value": None}
    specs[idx] = {
        "columns": list(st.session_state.vm_col_sel),
        "filter": flt,
        "sort": st.session_state.vm_sort or "",
    }
    _reset_editor()


def _delete_spec(nb: str, idx: int):
    view_data = st.session_state.vm_view_data
    specs = view_data.get(nb, [])
    if 0 <= idx < len(specs):
        specs.pop(idx)
        if not specs:
            view_data.pop(nb, None)
    _reset_editor()


# ==================== Save / Preview ====================

def _do_save(api, name: str, data: dict):
    if not name:
        st.error("请输入视图名称")
        return
    try:
        api.save_view(name, data)
        st.success(f"✅ 视图 `{name}` 已保存")
        st.session_state.vm_view_name = name
        st.session_state.vm_saved_view_names = [v["name"] for v in (api.list_views() or [])]
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


# ==================== Main Render ====================

def _render():
    st.title("👁️ 视图管理")
    api = get_client()
    _init_state()

    # ── 刷新已保存视图列表 ──
    try:
        saved_views = api.list_views() or []
        st.session_state.vm_saved_view_names = [v["name"] for v in saved_views]
    except Exception:
        saved_views = []
        st.session_state.vm_saved_view_names = []

    # ════════════════════════════════════════════════
    # 第一行：预设下拉 + 视图名称
    # ════════════════════════════════════════════════
    col1, col2 = st.columns(2)
    with col1:
        preset_opts = ["(自定义)", "full_view", "no_view"] + st.session_state.vm_saved_view_names
        presets_deduped = list(dict.fromkeys(preset_opts))  # 去重

        sel_preset = st.selectbox(
            "📋 视图预设 / 已保存视图",
            options=presets_deduped,
            key="vm_preset_dropdown",
        )

        if sel_preset != st.session_state.vm_preset:
            st.session_state.vm_preset = sel_preset
            if sel_preset in ("full_view", "no_view"):
                st.session_state.vm_view_data = _build_preset_view(api, sel_preset)
                _reset_editor()
                st.rerun()
            elif sel_preset in st.session_state.vm_saved_view_names:
                try:
                    data = api.get_view(sel_preset)
                    if data:
                        st.session_state.vm_view_data = data
                        st.session_state.vm_view_name = sel_preset
                        _reset_editor()
                        st.rerun()
                except Exception:
                    pass

    with col2:
        st.text_input(
            "📝 视图名称",
            value=st.session_state.vm_view_name,
            key="vm_name_input",
            placeholder="保存时使用的文件名",
        )

    # ════════════════════════════════════════════════
    # 笔记本选择
    # ════════════════════════════════════════════════
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

    if not sel_nb:
        st.info("请选择一个笔记本开始编辑视图")
        _render_view_json_preview()
        return

    # 获取 schema
    try:
        schema = api.get_schema(sel_nb)
        all_cols = [c["name"] for c in schema]
    except Exception:
        all_cols = []

    # 当前编辑中的 View 数据
    view_data: dict = st.session_state.vm_view_data
    specs = view_data.get(sel_nb, [])
    sel_idx = st.session_state.vm_selected_spec_idx

    # ════════════════════════════════════════════════
    # 当前 TableSpec 列表
    # ════════════════════════════════════════════════
    st.subheader(f"📄 `{sel_nb}` 的 TableSpec 列表 ({len(specs)} 个)")

    if specs:
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

        # 选中某行 — 用 radio 或 selectbox
        spec_options = [f"#{i}: {r['列'][:40]}" for i, r in enumerate(rows)]
        sel_label = st.radio(
            "选择要编辑的 TableSpec",
            options=["(添加新 Spec)"] + spec_options,
            index=0 if sel_idx is None else sel_idx + 1,
            horizontal=True,
            key="vm_spec_radio",
        )
        if sel_label == "(添加新 Spec)":
            if sel_idx is not None:
                st.session_state.vm_selected_spec_idx = None
                _reset_editor()
                st.rerun()
        else:
            new_idx = int(sel_label.split(":")[0].lstrip("#"))
            if new_idx != sel_idx:
                spec = specs[new_idx]
                st.session_state.vm_selected_spec_idx = new_idx
                st.session_state.vm_col_sel = spec.get("columns", [])
                st.session_state.vm_filter_json = json.dumps(
                    spec.get("filter", {}), ensure_ascii=False, indent=2
                )
                st.session_state.vm_sort = spec.get("sort", "")
                st.rerun()
    else:
        st.info("暂无 TableSpec，请在下方添加")
        st.session_state.vm_selected_spec_idx = None

    # ════════════════════════════════════════════════
    # TableSpec 编辑器
    # ════════════════════════════════════════════════
    st.divider()
    st.subheader("✏️ TableSpec 编辑器")

    is_editing = st.session_state.vm_selected_spec_idx is not None

    # 列多选 — 与 session_state 双向绑定
    current_cols = st.multiselect(
        "选择列 (TableSpec 中显示)  ",
        options=all_cols,
        default=st.session_state.vm_col_sel,
        key="vm_multiselect_cols",
    )
    if current_cols != st.session_state.vm_col_sel:
        st.session_state.vm_col_sel = current_cols

    # 筛选条件 JSON
    st.text_area(
        "筛选条件 (JSON)",
        value=st.session_state.vm_filter_json,
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

    # 排序
    st.text_input(
        "排序 (预留)",
        value=st.session_state.vm_sort,
        key="vm_sort_text",
        placeholder="如 created_at DESC",
    )

    # ── 操作按钮 ──
    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        if is_editing:
            if st.button("🔄 修改", type="primary", use_container_width=True, key="vm_btn_modify"):
                _update_spec(sel_nb, st.session_state.vm_selected_spec_idx)
                st.rerun()
        else:
            if st.button("➕ 添加", type="primary", use_container_width=True, key="vm_btn_add"):
                _add_spec(sel_nb)
                st.rerun()

    with bcol2:
        if is_editing:
            if st.button("🗑️ 删除", use_container_width=True, key="vm_btn_delete"):
                _delete_spec(sel_nb, st.session_state.vm_selected_spec_idx)
                st.rerun()

    with bcol3:
        if is_editing:
            if st.button("✖ 取消编辑", use_container_width=True, key="vm_btn_cancel"):
                _reset_editor()
                st.rerun()

    # ════════════════════════════════════════════════
    # 预览 & 保存
    # ════════════════════════════════════════════════
    st.divider()
    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        view_name = st.session_state.vm_view_name
        if st.button("🔍 预览 (当前笔记本)", use_container_width=True, key="vm_btn_preview"):
            _do_preview(api, sel_nb, view_data)

    with bcol2:
        if st.button("💾 保存", type="primary", use_container_width=True, key="vm_btn_save"):
            _do_save(api, view_name, view_data)

    with bcol3:
        if st.button("📋 另存为...", use_container_width=True, key="vm_btn_saveas"):
            new_name = f"{view_name}_copy" if view_name else "unnamed_copy"
            _do_save(api, new_name, view_data)

    # ════════════════════════════════════════════════
    # 完整 View JSON 预览
    # ════════════════════════════════════════════════
    _render_view_json_preview()


def _render_view_json_preview():
    """以 expander 展示完整 View JSON。"""
    view_data = st.session_state.vm_view_data
    if view_data:
        with st.expander("📄 完整 View JSON", expanded=False):
            st.json(view_data)


# ==================== Entry Point ====================

_render()
