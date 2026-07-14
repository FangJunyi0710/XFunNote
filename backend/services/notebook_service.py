"""本子 CRUD 业务逻辑，封装 xfun.core.ops。"""

from typing import Any

from fastapi import HTTPException, status

from xfun import db, registry
from xfun.core import ops
from xfun.core.view import DB_Permission
from xfun.core.filter import TRUE_CONDITION, parse_filter_json


def list_notebooks() -> list[str]:
    return list(registry.keys())


def get_schema(notetype: str) -> list[dict]:
    _validate_notetype(notetype)
    from dataclasses import asdict
    return [asdict(c) for c in registry[notetype].columns]


def query_entries(
    notetype: str,
    permission: DB_Permission,
    view: dict | None,
    order_by: str = "",
    limit: int = 100,
    offset: int = 0,
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
    _validate_notetype(notetype)

    if view is None:
        nb = registry[notetype]
        view = {notetype: [([c.name for c in nb.columns], TRUE_CONDITION)]}

    with db.read_transaction() as conn:
        total = ops.count(conn, permission, notetype, view)
        results = ops.query(conn, permission, notetype, view,
                            order_by=order_by, limit=limit, offset=offset)
        return results, total


def add_entries(
    notetype: str,
    entries: list[dict],
    permission: DB_Permission,
) -> list[dict]:
    _validate_notetype(notetype)
    with db.transaction() as conn:
        return ops.add(conn, permission, notetype, entries)


def update_entries(
    notetype: str,
    filter_obj: Any,
    values: dict,
    permission: DB_Permission,
) -> list[dict]:
    _validate_notetype(notetype)
    flt = parse_filter_json(filter_obj)
    with db.transaction() as conn:
        return ops.update(conn, permission, notetype, flt, values)


def delete_entries(
    notetype: str,
    filter_obj: Any,
    permission: DB_Permission,
) -> list[dict]:
    _validate_notetype(notetype)
    flt = parse_filter_json(filter_obj)
    with db.transaction() as conn:
        return ops.delete(conn, permission, notetype, flt)


def _validate_notetype(notetype: str) -> None:
    if notetype not in registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未知笔记本类型: {notetype!r}，可用: {list(registry.keys())}",
        )
