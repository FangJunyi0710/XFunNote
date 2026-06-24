"""
AI Tools — LangChain @tool 装饰的可调用工具。

CRUD 逻辑全部委托给内部函数 ``_query / _add / _update / _delete``，
这些函数自动完成安全约束（view_and / view_clean_*），新工具直接调用即可，不会遗漏。
"""

import json
from typing import Any
from langchain_core.tools import tool

from xfun import db, registry
from xfun.core.filter import Filter, Condition
from xfun.core.view import View, view_and, view_to_sql, view_clean_columns, view_clean_filter, view_clean_update
from xfun.ai.security import ai_read_view, ai_write_view
from xfun.core.errors import XFunError, ToolError
from .schema import FilterModel, ViewModel


# ════════════════════════════════════════════════════════════
#  内部 CRUD 函数 —— 校验 + 安全约束 + SQL 执行
#  接收已转换的内部类型（View / Filter），而非 Pydantic 模型。
#  新 CRUD 工具只需调用它们，自动获得权限保护。
# ════════════════════════════════════════════════════════════

def _query(conn, table: str, view: View, order_by: str = "", limit: int = -1, offset: int = 0) -> list[dict[str, Any]]:
    """查询条目。view 为内部 View，自动与 AI_READ_VIEW 取交集。conn 由调用方传入（read tx）。"""
    if table not in registry:
        raise ToolError(f"未知本子: {table}")
    if table not in view:
        view[table] = []

    safe_view = view_and(view, ai_read_view())
    if table not in safe_view:
        return []

    sql, params = view_to_sql(safe_view, db, table)
    if not sql:
        return []
    if order_by:
        from xfun.core.db import Column
        Column.check_order_by(order_by)
        sql += f" ORDER BY {order_by}"
    if limit > 0:
        sql += f" LIMIT {limit}"
        if offset > 0:
            sql += f" OFFSET {offset}"
    rows = conn.execute(sql, params).fetchall()

    return [dict(r) for r in rows]

def _add(conn, notetype: str, entries: list[dict[str, Any]]) -> list[str]:
    """添加条目。自动列白名单清洗 + is_ai_gen 注入。返回新 ID 列表。conn 为 write tx。"""
    if notetype not in registry:
        raise ToolError(f"未知本子: {notetype}")
    cleaned = view_clean_columns(ai_write_view(), notetype, entries)
    for e in cleaned:
        e.setdefault("is_ai_gen", 1)

    nb = registry[notetype]
    ids = nb.add(conn, cleaned)
    return ids


def _update(conn, notetype: str, filter: Filter, values: dict[str, Any]) -> list[str]:
    """更新条目。自动列清洗 + filter 与 AI_WRITE_VIEW 取交集。返回被更新 ID 列表。conn 为 write tx。"""
    if notetype not in registry:
        raise ToolError(f"未知本子: {notetype}")

    pairs = view_clean_update(ai_write_view(), notetype, filter, values)
    if not pairs or all(not vals for _, vals in pairs):
        raise ToolError("没有可更新的字段")

    nb = registry[notetype]
    updated_ids: list[str] = []
    for cf, cv in pairs:
        if not cv:
            continue
        ids = nb.list_ids(conn, cf)
        if not ids:
            continue
        nb.update(conn, ids, cv)
        updated_ids.extend(ids)
    if not updated_ids:
        raise ToolError("没有可更新的条目")
    return updated_ids

def _view_by_ids(conn, table: str, ids: list[str]) -> list[dict[str, Any]]:
    return _query(conn, table, {table: [([col.name for col in db.table_infos[table]], Condition("id", ids, "IN"))]})

def _delete(conn, notetype: str, filter: Filter) -> list[dict[str, Any]]:
    """删除条目。自动 filter 与 AI_WRITE_VIEW 取交集。返回 被删列表,。conn 为 write tx（可读可写）。"""
    if notetype not in registry:
        raise ToolError(f"未知本子: {notetype}")
    combined = view_clean_filter(ai_write_view(), notetype, filter)

    nb = registry[notetype]
    valid_ids = nb.list_ids(conn, combined)
    if not valid_ids:
        raise ToolError("没有可删除的条目")

    results = _view_by_ids(conn, notetype, valid_ids)
    nb.delete(conn, valid_ids)
    return results


#  @tool ：仅做 Pydantic 转换 + JSON 序列化

@tool
def query_entries(
    view: ViewModel,
    notetype: str,
    order_by: str = "",
    limit: int = -1,
    offset: int = 0,
) -> str:
    """
    查询条目（只读），自动与 AI_READ_VIEW 取交集限制行列。

    Parameters
    ----------
    view : ViewModel
        查询视图 Pydantic 模型，自动校验格式（字段名、运算符等）。
    notetype : str
        本子名：plan / diary / word / accumulation / aimemory。
    order_by : str
        排序列名，如 ``"created_at DESC"``。
    limit : int
        最多返回条数（<=0 表示不限制）。
    offset : int
        偏移量。
    """
    try:
        with db.read_transaction() as conn:
            rows = _query(conn, notetype, view.to_view(), order_by, limit, offset)
        return json.dumps({"results": rows}, ensure_ascii=False, default=str)
    except XFunError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def add_entries(notetype: str, entries: list[dict[str, Any]]) -> str:
    """
    添加条目，自动注入 ``is_ai_gen=1``，超出白名单的字段自动移除。

    Parameters
    ----------
    notetype : str
        本子名。
    entries : dict
        单条条目的字段值。
    """
    try:
        with db.transaction() as conn:
            ids = _add(conn, notetype, entries)
            results = _view_by_ids(conn, notetype, ids)
        return json.dumps({"results": results}, ensure_ascii=False, default=str)
    except XFunError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def update_entries(notetype: str, filter: FilterModel, values: dict[str, Any]) -> str:
    """
    更新条目，自动与 AI_WRITE_VIEW 取 filter 交集 + 列白名单清洗。

    Parameters
    ----------
    notetype : str
        本子名。
    filter : FilterModel
        筛选条件（Pydantic 模型），自动校验格式并转内部 Filter。
    values : dict
        要更新的字段值。
    """
    try:
        with db.transaction() as conn:
            ids = _update(conn, notetype, filter.to_filter(), values)
            results = _view_by_ids(conn, notetype, ids)
        return json.dumps({"results": results}, ensure_ascii=False, default=str)
    except XFunError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def delete_entries(notetype: str, filter: FilterModel) -> str:
    """
    删除条目，自动与 AI_WRITE_VIEW 取 filter 交集，仅删除有权限的条目。

    Parameters
    ----------
    notetype : str
        本子名。
    filter : FilterModel
        筛选条件（Pydantic 模型），自动校验格式并转内部 Filter。
    """
    try:
        with db.transaction() as conn:
            results = _delete(conn, notetype, filter.to_filter())
        return json.dumps({"results": results}, ensure_ascii=False, default=str)
    except XFunError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
