from typing import Any

from .db import Column
from .filter import Filter, Condition
from .view import (
    DB_Permission,
    View,
    view_and,
    view_clean_add,
    view_clean_delete,
    view_clean_update,
    view_to_sql,
)


def query(conn, permission: DB_Permission, table: str, query_view: View, order_by: str = "", limit: int = -1, offset: int = 0) -> list[dict[str, Any]]:
    rview, wview = permission
    sql, params = view_to_sql(view_and(query_view, rview), conn.db, table)
    if not sql:
        return []
    if order_by:
        Column.check_order_by(order_by)
        sql += f" ORDER BY {order_by}"
    sql += f" LIMIT {limit} OFFSET {offset}"
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def count(conn, permission: DB_Permission, table: str, query_view: View) -> int:
    """查询满足 view 条件的总条目数（忽略分页与排序）。"""
    rview, wview = permission
    sql, params = view_to_sql(view_and(query_view, rview), conn.db, table)
    if not sql:
        return 0
    count_sql = f"SELECT COUNT(*) FROM ({sql}) AS cnt"
    row = conn.execute(count_sql, params).fetchone()
    return row[0]

def _query_by_ids(conn, permission: DB_Permission, table: str, ids: list[str]) -> list[dict[str, Any]]:
    return query(conn, permission, table, {table: [(conn.db.cols(table), Condition("id", ids, "IN"))]})

def add(conn, permission: DB_Permission, table: str, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rview, wview = permission
    cleaned = view_clean_add(wview, table, entries)
    ids = conn.db.add_entries(conn, table, cleaned)
    return _query_by_ids(conn, permission, table, ids)


def update(conn, permission: DB_Permission, table: str, filter: Filter, values: dict[str, Any]) -> list[dict[str, Any]]:
    rview, wview = permission
    update_pairs = view_clean_update(wview, table, filter, values)
    all_ids: list[str] = []
    for combined_filter, cleaned_values in update_pairs:
        if not cleaned_values:
            continue
        ids = conn.db.list_ids(conn, table, combined_filter)
        if not ids:
            continue
        all_ids.extend(ids)
        conn.db.update_entries(conn, table, ids, cleaned_values)
    return _query_by_ids(conn, permission, table, all_ids)


def delete(conn, permission: DB_Permission, table: str, filter: Filter) -> list[dict[str, Any]]:
    rview, wview = permission
    combined_filter = view_clean_delete(wview, table, filter)
    ids = conn.db.list_ids(conn, table, combined_filter)
    entries = _query_by_ids(conn, permission, table, ids)
    conn.db.delete_entries(conn, table, ids)
    return entries
