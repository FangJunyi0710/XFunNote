import json
from typing import Any
from langchain_core.tools import tool

from xfun import db, registry
from xfun.core import ops
from xfun.core.filter import Condition
from xfun.core.view import View, root_permission, view_to_json
from xfun.ai.security import ai_permission
from xfun.core.errors import XFunError, ToolError
from .schema import FilterModel, ViewModel


def _query(conn, table: str, view: View, order_by: str = "", limit: int = -1, offset: int = 0) -> list[dict]:
    return ops.query(conn, ai_permission(), table, view, order_by, limit, offset)


def _add(conn, notetype: str, entries: list[dict]) -> list[dict]:
    if notetype not in registry:
        raise ToolError(f"不支持的笔记类型: {notetype}")
    results = ops.add(conn, ai_permission(), notetype, entries)
    ids = [r["id"] for r in results if "id" in r]
    return ops.update(conn, root_permission(conn.db), notetype, Condition("id", ids, "IN"), {"is_ai_gen": 1})


def _update(conn, notetype: str, filter, values: dict) -> list[dict]:
    return ops.update(conn, ai_permission(), notetype, filter, values)


def _delete(conn, notetype: str, filter) -> list[dict]:
    return ops.delete(conn, ai_permission(), notetype, filter)


# ---- 事务 + 异常处理辅助 ----

def _with_read_tool(impl) -> str:
    """只读事务 + XFunError 处理，返回 JSON。"""
    try:
        with db.read_transaction() as conn:
            results = impl(conn)
        return json.dumps({"results": results}, ensure_ascii=False, default=str)
    except XFunError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def _with_write_tool(impl) -> str:
    """写事务 + XFunError 处理，返回 JSON。"""
    try:
        with db.transaction() as conn:
            results = impl(conn)
        return json.dumps({"results": results}, ensure_ascii=False, default=str)
    except XFunError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def query_entries(
    view: ViewModel,
    notetype: str,
    order_by: str = "",
    limit: int = -1,
    offset: int = 0,
) -> str:
    """查询笔记条目。

    根据字段、条件筛选查询指定笔记类型的条目，支持排序、分页。

    Args:
        view: 查询视图，指定要查询的字段和筛选条件。
              注意：view 会被读取权限视图清洗，不在读取白名单中的条目将被移除、字段将被置空。
        notetype: 笔记类型。
        order_by: 排序字段，可选。格式如 "created_at DESC"、"updated_at ASC"。
        limit: 最大返回条数，-1 表示不限制。
        offset: 偏移量，用于分页。

    Returns:
        JSON 字符串，包含 results 列表或 error 信息。
    """
    return _with_read_tool(lambda conn: _query(conn, notetype, view.to_view(), order_by, limit, offset))


@tool
def add_entries(notetype: str, entries: list[dict[str, Any]]) -> str:
    """添加笔记条目。

    向指定笔记类型中批量新增条目。

    Args:
        notetype: 笔记类型。
        entries: 待添加的条目列表，每个条目是一个字段名到字段值的字典。
                 注意：entries 会被写入权限视图清洗，不在写入白名单中的字段将被移除。

    Returns:
        JSON 字符串，包含 results（新增条目的完整信息，含 id）或 error。
    """
    return _with_write_tool(lambda conn: _add(conn, notetype, entries))


@tool
def update_entries(notetype: str, filter: FilterModel, values: dict[str, Any]) -> str:
    """更新笔记条目。

    按条件筛选匹配的条目，批量更新指定字段的值。

    Args:
        notetype: 笔记类型。
        filter: 筛选条件，决定哪些条目被更新。
        values: 要更新的字段值字典，键为字段名，值为新值。
                注意：values 会被写入权限视图清洗，不在写入白名单中的字段将被忽略。

    Returns:
        JSON 字符串，包含 results（更新后条目的完整信息）或 error。
    """
    return _with_write_tool(lambda conn: _update(conn, notetype, filter.to_filter(), values))


@tool
def delete_entries(notetype: str, filter: FilterModel) -> str:
    """删除笔记条目。

    按条件筛选匹配的条目并永久删除。

    Args:
        notetype: 笔记类型。
        filter: 筛选条件，决定哪些条目被删除。

    Returns:
        JSON 字符串，包含 results（被删除条目的完整信息）或 error。
    """
    return _with_write_tool(lambda conn: _delete(conn, notetype, filter.to_filter()))


@tool
def get_ai_permission() -> str:
    """获取当前 AI 可读/可写字段的完整权限白名单（JSON 格式）。

    当你对某个字段是否可查询或可修改不确定时，调用此工具获取详细约束。

    Returns:
        JSON 字符串，包含 read 和 write 两个权限视图。
        格式：{"read": {...}, "write": {...}}
    """
    read_view, write_view = ai_permission()
    return json.dumps({
        "read": view_to_json(read_view),
        "write": view_to_json(write_view),
    }, ensure_ascii=False, default=str)
