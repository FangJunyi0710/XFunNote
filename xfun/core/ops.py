from typing import Any

from .. import registry
from .db import Column
from .filter import Filter, Condition
from .view import (
    Permission,
    View,
    view_and,
    view_clean_columns,
    view_clean_filter,
    view_clean_update,
    view_to_sql,
)

def query(conn, permission: Permission, table: str, query_view: View, order_by: str = "", limit: int = -1, offset: int = 0) -> list[dict[str, Any]]:
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

def _query_by_ids(conn, permission: Permission, table: str, ids: list[str]) -> list[dict[str, Any]]:
    return query(conn, permission, table, {table: [([col.name for col in conn.db.table_infos[table]], Condition("id", ids, "IN"))]})

def add(conn, permission: Permission, notetype: str, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rview, wview = permission
    nb = registry[notetype]
    cleaned = view_clean_columns(wview, nb.name, entries)
    ids = nb.add(conn, cleaned)
    return _query_by_ids(conn, permission, notetype, ids)


def update(conn, permission: Permission, notetype: str, filter: Filter, values: dict[str, Any]) -> list[dict[str, Any]]:
    rview, wview = permission
    nb = registry[notetype]
    update_pairs = view_clean_update(wview, nb.name, filter, values)
    all_ids: list[str] = []
    for combined_filter, cleaned_values in update_pairs:
        if not cleaned_values:
            continue
        ids = nb.list_ids(conn, combined_filter)
        if not ids:
            continue
        all_ids.extend(ids)
        nb.update(conn, ids, cleaned_values)
    return _query_by_ids(conn, permission, notetype, all_ids)


def delete(conn, permission: Permission, notetype: str, filter: Filter) -> list[dict[str, Any]]:
    rview, wview = permission
    nb = registry[notetype]
    combined_filter = view_clean_filter(wview, nb.name, filter)
    ids = nb.list_ids(conn, combined_filter)
    entries = _query_by_ids(conn, permission, notetype, ids)
    nb.delete(conn, ids)
    return entries
