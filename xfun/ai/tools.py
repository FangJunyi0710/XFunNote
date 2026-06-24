"""
AI Tools — LangChain @tool 装饰的可调用工具（8个）。

每个函数被 ``@tool`` 装饰后自动生成 JSON Schema，
LangChain 负责参数解析和返回值序列化。
"""

import json
from typing import Any
from langchain_core.tools import tool

from pydantic import ValidationError

from xfun import db, registry
from xfun.core.filter import Condition, Filter
from xfun.core.view import View, view_and, view_to_sql, view_clean_columns, view_clean_filter, view_clean_update
from xfun.ai.schema import parse_and_validate_view
from xfun.ai.security import ai_read_view, ai_write_view
from .schema import FilterModel, ViewModel

@tool
def query_entries(
    view: ViewModel,
    table: str,
    order_by: str = "",
    limit: int = -1,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    查询条目（只读），自动与 AI_READ_VIEW 取交集限制行列。

    Parameters
    ----------
    table : str
        本子名：plan / diary / word / accumulation / aimemory。
    view_json : str
        View JSON 字符串，格式参见系统提示词中的 JSON Schema 定义（ViewSchema）。
        简要结构: ``{"表名": [{"columns": [...], "filter": <Filter>}, ...]}``。
    order_by : str
        排序列名，如 ``"created_at DESC"``，``seq ASC``。
    limit : int
        最多返回条数。
    offset : int
        偏移量。
    """
    if table not in registry:
        return json.dumps({"error": f"未知本子: {table}"}, ensure_ascii=False)

    try:
        user_view = parse_and_validate_view(view) if view else {table: []}
    except ValidationError as e:
        return json.dumps(
            {"error": f"view_json 格式错误: {e.errors()}"},
            ensure_ascii=False,
        )

    # 确保用户 view 包含目标表
    if table not in user_view:
        user_view[table] = []
    # 与 AI_READ_VIEW 取交集，限制行列权限
    safe_view = _clamp_with_ai_view(user_view)
    if table not in safe_view:
        return json.dumps([], ensure_ascii=False)

    with db.read_transaction() as conn:
        sql, params = view_to_sql(safe_view, db, table)
        if not sql:
            return json.dumps([], ensure_ascii=False)
        if order_by:
            from xfun.core.db import Column
            Column.check_order_by(order_by)
            sql += f" ORDER BY {order_by}"
        sql += f" LIMIT {limit} OFFSET {offset}"
        rows = conn.execute(sql, params).fetchall()

    result = [dict(r) for r in rows]
    return json.dumps(result, ensure_ascii=False, default=str)


@tool
def add_entries(table: str, entries: dict[str, Any]) -> None:
    """
    添加条目，自动注入 ``is_ai_gen=1``。

    自动根据 AI_WRITE_VIEW 的列白名单清洗传入字段，
    超出白名单的字段会被移除。

    Parameters
    ----------
    table : str
        本子名。
    entries_json : str
        JSON 数组，每个元素是一条目 dict。
    """
    if table not in registry:
        return json.dumps({"error": f"未知本子: {table}"}, ensure_ascii=False)

    entries: list[dict[str, Any]] = json.loads(entries_json)

    # 用 view_add 按 AI_WRITE_VIEW 列白名单清洗
    cleaned = view_clean_columns(ai_write_view(), table, entries)
    # AI 创建的条目标记
    for entry in cleaned:
        entry.setdefault("is_ai_gen", 1)

    nb = registry.notebook(table)
    with db.transaction() as conn:
        ids = nb.add(conn, cleaned)

    return json.dumps({"ids": ids, "count": len(ids)}, ensure_ascii=False)


@tool
def update_entries(table: str, filter: FilterModel, values: dict[str, Any]) -> None:
    """
    更新条目，仅允许修改 AI_WRITE_VIEW 白名单中的列和行。

    用 view_update 自动完成列清洗 + 行权限约束（AND 写白名单 filter）。

    Parameters
    ----------
    table : str
        本子名。
    entry_ids_json : str
        JSON 数组，要更新的条目 ID 列表。
    entry_json : str
        JSON 对象，要更新的字段。
    """
    if table not in registry:
        return json.dumps({"error": f"未知本子: {table}"}, ensure_ascii=False)

    entry_ids: list[str] = json.loads(entry_ids_json)
    entry: dict[str, Any] = json.loads(entry_json)

    id_filter: Filter = [[Condition("id", entry_ids, "IN")]]
    pairs = view_clean_update(ai_write_view(), table, id_filter, entry)

    if not pairs or all(not vals for _, vals in pairs):
        return json.dumps({"error": "没有可更新的字段"}, ensure_ascii=False)

    nb = registry.notebook(table)
    updated_ids: list[str] = []
    with db.transaction() as conn:
        for combined_filter, cleaned_values in pairs:
            if not cleaned_values:
                continue
            matching_ids = nb.list_ids(conn, combined_filter)
            if not matching_ids:
                continue
            nb.update(conn, matching_ids, cleaned_values)
            updated_ids.extend(matching_ids)

    if not updated_ids:
        return json.dumps({"error": "没有可更新的条目"}, ensure_ascii=False)

    return json.dumps({"updated_ids": updated_ids, "count": len(updated_ids)}, ensure_ascii=False)


@tool
def delete_entries(table: str, filter: FilterModel) -> None:
    """
    删除条目，仅允许删除 AI_WRITE_VIEW 范围内的条目。

    用 view_delete 自动将用户 ID filter 与写白名单 filter AND 组合。

    Parameters
    ----------
    table : str
        本子名。
    entry_ids_json : str
        JSON 数组，要删除的条目 ID 列表。
    confirm : bool
        确认删除，必须为 True。
    """
    if not confirm:
        return json.dumps({"error": "请设置 confirm=true 以确认删除"}, ensure_ascii=False)

    if table not in registry:
        return json.dumps({"error": f"未知本子: {table}"}, ensure_ascii=False)

    entry_ids: list[str] = json.loads(entry_ids_json)
    nb = registry.notebook(table)

    id_filter: Filter = [[Condition("id", entry_ids, "IN")]]
    combined_filter = view_clean_filter(ai_write_view(), table, id_filter)

    with db.read_transaction() as conn:
        valid_ids = nb.list_ids(conn, combined_filter)
        preview = nb.get_by_id(conn, valid_ids)

    if not valid_ids:
        return json.dumps({"error": "没有可删除的条目"}, ensure_ascii=False)

    with db.transaction() as conn:
        nb.delete(conn, valid_ids)

    return json.dumps(
        {
            "deleted_ids": valid_ids,
            "count": len(valid_ids),
            "preview": [
                {k: r.get(k) for k in ("id", "content") if k in r} for r in preview
            ],
        },
        ensure_ascii=False,
    )
