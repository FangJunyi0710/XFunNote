"""表 CRUD 业务逻辑，封装 xfun.core.ops。"""

from typing import Any

from fastapi import HTTPException, status

from xfun.core import ops
from xfun.core.db import DB
from xfun.core.view import DB_Permission
from xfun.core.filter import TRUE_CONDITION, parse_filter_json


def list_tables(db: DB) -> list[dict]:
    from dataclasses import asdict
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
    from dataclasses import asdict
    return [asdict(c) for c in db.table_infos[table]]


def query_entries(
    db: DB,
    table: str,
    permission: DB_Permission,
    view: dict | None,
    limit: int,
    offset: int = 0,
    order_by: str = "",
) -> tuple[list[dict], int]:
    """查询条目。

    Parameters
    ----------
    view : dict | None
        内部 View 格式：``{表名: [(列列表, Filter), ...]}``。
        若为 None，默认查询所有列、无筛选。

    Returns
    -------
    tuple[list[dict], int]
        (条目列表, 总记录数)
    """
    _validate_table(db, table)

    if view is None:
        view = {table: [(db.cols(table), TRUE_CONDITION)]}

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
