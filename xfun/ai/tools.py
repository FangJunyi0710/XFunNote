"""
AI Tools — LangChain @tool 装饰的可调用工具（8个）。

每个函数被 ``@tool`` 装饰后自动生成 JSON Schema，
LangChain 负责参数解析和返回值序列化。
"""

import json
from typing import Any, Dict, List

from langchain_core.tools import tool

from xfun import db, registry
from xfun.core.view import View, view_and, view_to_sql, parse_view_json
from xfun.ai.security import (
    AI_READ_VIEW,
    AI_WRITE_VIEW,
    writable_columns,
    write_filter,
    system_columns,
)

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def _clamp_with_ai_view(user_view: View) -> View:
    """将用户 View 与 AI_READ_VIEW 做交集，限制 AI 只能读取白名单内的行列。"""
    return view_and(user_view, AI_READ_VIEW)


@tool
def query_entries(
    table: str,
    view_json: str,
    order_by: str = "",
    limit: int = 50,
    offset: int = 0,
) -> str:
    """
    查询条目（只读），自动与 AI_READ_VIEW 取交集限制行列。

    Parameters
    ----------
    table : str
        本子名：plan / diary / word / accumulation。
    view_json : str
        View JSON 字符串，格式为 ``{"表名": [[列名列表, 筛选条件], ...]}``。
        筛选条件格式同 Filter JSON，如 ``[{"column":"month","value":"2606"}]``。
    order_by : str
        排序列名，如 ``"created_at DESC"``。
    limit : int
        最多返回条数。
    offset : int
        偏移量。
    """
    if table not in registry:
        return json.dumps({"error": f"未知本子: {table}"}, ensure_ascii=False)

    user_view = parse_view_json(view_json, table) if view_json else {table: []}
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
def add_entries(table: str, entries_json: str) -> str:
    """
    添加条目，自动注入 ``is_ai_gen=1``。

    Parameters
    ----------
    table : str
        本子名。
    entries_json : str
        JSON 数组，每个元素是一条目 dict。
    """
    if table not in registry:
        return json.dumps({"error": f"未知本子: {table}"}, ensure_ascii=False)

    entries: List[Dict[str, Any]] = json.loads(entries_json)
    nb = registry.notebook(table)

    for entry in entries:
        entry.setdefault("is_ai_gen", 1)
        # 移除 AI 禁止写入的系统列
        for sc in system_columns(table):
            entry.pop(sc, None)

    with db.transaction() as conn:
        ids = nb.add(conn, entries)

    return json.dumps({"ids": ids, "count": len(ids)}, ensure_ascii=False)


@tool
def update_entries(table: str, entry_ids_json: str, entry_json: str) -> str:
    """
    更新条目，仅允许修改 ``AI_WRITABLE_COLUMNS`` 中的列。

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

    entry_ids: List[str] = json.loads(entry_ids_json)
    entry: Dict[str, Any] = json.loads(entry_json)

    # 只允许修改白名单列
    _writable = writable_columns(table)
    filtered_entry = {k: v for k, v in entry.items() if k in _writable}
    if not filtered_entry and entry:
        return json.dumps({"error": f"没有可写的列（白名单：{', '.join(_writable)}）"}, ensure_ascii=False)

    nb = registry.notebook(table)
    with db.read_transaction() as conn:
        existing_ids = nb.list(conn, write_filter(table))
        valid_ids = [eid for eid in entry_ids if eid in existing_ids]

    if not valid_ids:
        return json.dumps({"error": "没有可更新的条目（不在 AI 可写范围内）"}, ensure_ascii=False)

    with db.transaction() as conn:
        nb.update(conn, valid_ids, filtered_entry)

    return json.dumps({"updated_ids": valid_ids, "count": len(valid_ids)}, ensure_ascii=False)


@tool
def delete_entries(table: str, entry_ids_json: str, confirm: bool = False) -> str:
    """
    删除条目，仅允许删除 AI 创建的条目。

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

    entry_ids: List[str] = json.loads(entry_ids_json)
    nb = registry.notebook(table)

    with db.read_transaction() as conn:
        existing_ids = nb.list(conn, write_filter(table))
        valid_ids = [eid for eid in entry_ids if eid in existing_ids]
        preview = nb.get_by_id(conn, valid_ids)

    if not valid_ids:
        return json.dumps({"error": "没有可删除的条目（不在 AI 可写范围内）"}, ensure_ascii=False)

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


@tool
def manage_tags(table: str, entry_ids_json: str, mode: str, tags_json: str) -> str:
    """
    管理条目标签：添加、移除或替换。

    Parameters
    ----------
    table : str
        本子名。
    entry_ids_json : str
        JSON 数组，条目 ID 列表。
    mode : str
        操作模式：``add`` / ``remove`` / ``set``。
    tags_json : str
        JSON 数组，标签列表。
    """
    if table not in registry:
        return json.dumps({"error": f"未知本子: {table}"}, ensure_ascii=False)

    entry_ids: List[str] = json.loads(entry_ids_json)
    tags: List[str] = json.loads(tags_json)

    if mode not in ("add", "remove", "set"):
        return json.dumps({"error": f"未知模式: {mode}，可选: add / remove / set"}, ensure_ascii=False)

    nb = registry.notebook(table)

    with db.read_transaction() as conn:
        existing_ids = nb.list(conn, write_filter(table))
        valid_ids = [eid for eid in entry_ids if eid in existing_ids]
        rows = nb.get_by_id(conn, valid_ids)

    updated = []
    with db.transaction() as conn:
        for row in rows:
            current_tags: List[str] = json.loads(row.get("tags") or "[]")
            if mode == "add":
                for tag in tags:
                    if tag not in current_tags:
                        current_tags.append(tag)
            elif mode == "remove":
                current_tags = [t for t in current_tags if t not in tags]
            else:  # set
                current_tags = list(tags)

            nb.update(
                conn, [row["id"]], {"tags": json.dumps(current_tags, ensure_ascii=False)}
            )
            updated.append({"id": row["id"], "tags": current_tags})

    return json.dumps({"updated": updated, "count": len(updated)}, ensure_ascii=False)


@tool
def add_ai_note(table: str, entry_id: str, note: str) -> str:
    """
    追加 AI 备注到条目（保留已有内容）。

    Parameters
    ----------
    table : str
        本子名。
    entry_id : str
        条目 ID。
    note : str
        要追加的备注内容。
    """
    if table not in registry:
        return json.dumps({"error": f"未知本子: {table}"}, ensure_ascii=False)

    nb = registry.notebook(table)

    with db.read_transaction() as conn:
        existing_ids = nb.list(conn, write_filter(table))
        if entry_id not in existing_ids:
            return json.dumps({"error": "条目不在 AI 可写范围内"}, ensure_ascii=False)
        rows = nb.get_by_id(conn, [entry_id])
        if not rows:
            return json.dumps({"error": "条目不存在"}, ensure_ascii=False)
        current_note = rows[0].get("ai_note") or ""

    new_note = (current_note + "\n---\n" + note).strip() if current_note else note

    with db.transaction() as conn:
        nb.update(conn, [entry_id], {"ai_note": new_note})

    return json.dumps({"id": entry_id, "ai_note": new_note}, ensure_ascii=False)


@tool
def search_memories(keyword: str = "", category: str = "") -> str:
    """
    跨本子检索 AI 内容。

    Parameters
    ----------
    keyword : str
        关键词（LIKE 匹配 ``content`` 字段）。
    category : str
        积累本分类筛选。
    """
    from xfun.core.filter import Condition

    results: Dict[str, list] = {}

    for table_name in ["plan", "diary", "word", "accumulation"]:
        if table_name not in AI_READ_VIEW:
            continue
        # 获取 AI_READ_VIEW 中该表的列白名单
        ai_cols = list({c for spec in AI_READ_VIEW[table_name] for c in spec[0]})

        conditions: List = [Condition("is_ai_gen", 1)]
        if keyword:
            conditions.append(Condition("content", f"%{keyword}%", "LIKE"))
        if category and table_name == "accumulation":
            conditions.append(Condition("category", category))

        user_view: View = {table_name: [(ai_cols, [conditions])]}
        safe_view = _clamp_with_ai_view(user_view)
        if table_name not in safe_view:
            continue

        with db.read_transaction() as conn:
            sql, params = view_to_sql(safe_view, db, table_name)
            if not sql:
                continue
            sql += f" LIMIT 20"
            rows = conn.execute(sql, params).fetchall()

        results[table_name] = [dict(r) for r in rows]

    return json.dumps(results, ensure_ascii=False, default=str)


@tool
def save_memory(content: str, source: str = "", note: str = "") -> str:
    """
    保存内容到积累本（自动分类为 ``AI记忆``）。

    Parameters
    ----------
    content : str
        记忆内容。
    source : str
        来源。
    note : str
        备注。
    """
    nb = registry.notebook("accumulation")
    entry: Dict[str, Any] = {
        "content": content,
        "category": "AI记忆",
        "is_ai_gen": 1,
    }
    if source:
        entry["source"] = source
    if note:
        entry["note"] = note

    with db.transaction() as conn:
        ids = nb.add(conn, [entry])

    return json.dumps({"id": ids[0]}, ensure_ascii=False)
