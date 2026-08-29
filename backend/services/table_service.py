"""表 CRUD 业务逻辑，封装 xfun.core.ops。"""

import json
from dataclasses import asdict
from typing import Any

from fastapi import HTTPException, status

from xfun.core import ops
from xfun.core.db import DB
from xfun.core.view import DB_Permission, parse_view_json
from xfun.core.filter import TRUE_CONDITION, Condition, Filter, parse_filter_json


def list_tables(db: DB) -> list[dict]:
    result = []
    for name, cols in db.table_infos.items():
        columns = [asdict(c) for c in cols]
        result.append({
            "table_name": name,
            "columns": columns,
        })
    return result


def get_schema(db: DB, table: str) -> list[dict]:
    _validate_table(db, table)
    return [asdict(c) for c in db.table_infos[table]]


def resolve_view(db: DB, permission: DB_Permission, name: str) -> dict:
    """按名称从 _view 表读取视图，受 permission 对 _view 的读权限约束。"""
    with db.read_transaction() as conn:
        rows = ops.query(conn, permission, "_view",
                         {"_view": [(db.cols("_view"), Condition(col="name", val=name, op="="))]},
                         limit=1)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"视图不存在: {name!r}",
        )
    try:
        return parse_view_json(json.loads(rows[0].get("data")))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"视图数据无效: {name!r}",
        )


def query_entries(
    db: DB,
    table: str,
    permission: DB_Permission,
    view: dict | None,
    limit: int,
    offset: int = 0,
    order_by: str = "",
    filter: Filter | None = None,
) -> tuple[list[dict], int]:
    """查询条目。

    Parameters
    ----------
    view : dict | None
        内部 View 格式：``{表名: [(列列表, Filter), ...]}``。
        若为 None，默认查询所有列、无筛选。
    filter_obj : Filter | None
        临时筛选（已解析的 Filter），与 view 各 spec 取 AND。

    Returns
    -------
    tuple[list[dict], int]
        (条目列表, 总记录数)
    """
    _validate_table(db, table)

    if view is None:
        view = {table: [(db.cols(table), TRUE_CONDITION)]}

    if filter is not None:
        view = {
            t: [(cols, [[flt, filter]] if t == table else flt) for cols, flt in specs]
            for t, specs in view.items()
        }

    with db.read_transaction() as conn:
        total = ops.count(conn, permission, table, view)
        results = ops.query(conn, permission, table, view,
                            order_by=order_by, limit=limit, offset=offset)
        return results, total


def add_entries(
    db: DB,
    table: str,
    entries: list[dict],
    permission: DB_Permission,
) -> list[dict]:
    _validate_table(db, table)
    with db.transaction() as conn:
        return ops.add(conn, permission, table, entries)


def update_entries(
    db: DB,
    table: str,
    filter_obj: Any,
    values: dict,
    permission: DB_Permission,
) -> list[dict]:
    _validate_table(db, table)
    flt = parse_filter_json(filter_obj)
    with db.transaction() as conn:
        return ops.update(conn, permission, table, flt, values)


def delete_entries(
    db: DB,
    table: str,
    filter_obj: Any,
    permission: DB_Permission,
) -> list[dict]:
    _validate_table(db, table)
    flt = parse_filter_json(filter_obj)
    with db.transaction() as conn:
        return ops.delete(conn, permission, table, flt)


def _validate_table(db: DB, table: str) -> None:
    if table not in db.table_infos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未知表: {table!r}，可用: {list(db.table_infos.keys())}",
        )
