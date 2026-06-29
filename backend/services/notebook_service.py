"""本子 CRUD 业务逻辑，封装 xfun.core.ops。"""

from typing import Any

from fastapi import HTTPException, status

from xfun import db, registry
from xfun.core import ops
from xfun.core.view import Permission, root_permission
from xfun.core.filter import TRUE_CONDITION, parse_filter_json


def list_notebooks() -> list[str]:
    return list(registry.keys())


def get_schema(notetype: str) -> list[dict]:
    _validate_notetype(notetype)
    from dataclasses import asdict
    return [asdict(c) for c in registry[notetype].columns]


def query_entries(
    notetype: str,
    view: dict | None,
    order_by: str = "",
    limit: int = 100,
    offset: int = 0,
    permission: Permission | None = None,
) -> list[dict]:
    """查询条目。

    Parameters
    ----------
    view : dict | None
        内部 View 格式：``{表名: [(列列表, Filter), ...]}``。
        若为 None，默认查询所有列、无筛选。
    """
    _validate_notetype(notetype)
    perm = permission or root_permission(db)

    if view is None:
        nb = registry[notetype]
        view = {notetype: [([c.name for c in nb.columns], TRUE_CONDITION)]}

    with db.read_transaction() as conn:
        return ops.query(conn, perm, notetype, view,
                         order_by=order_by, limit=limit, offset=offset)


def add_entries(
    notetype: str,
    entries: list[dict],
    permission: Permission | None = None,
) -> list[dict]:
    _validate_notetype(notetype)
    perm = permission or root_permission(db)
    with db.transaction() as conn:
        return ops.add(conn, perm, notetype, entries)


def update_entries(
    notetype: str,
    filter_obj: Any,
    values: dict,
    permission: Permission | None = None,
) -> list[dict]:
    _validate_notetype(notetype)
    perm = permission or root_permission(db)
    flt = parse_filter_json(filter_obj)
    with db.transaction() as conn:
        return ops.update(conn, perm, notetype, flt, values)


def delete_entries(
    notetype: str,
    filter_obj: Any,
    permission: Permission | None = None,
) -> list[dict]:
    _validate_notetype(notetype)
    perm = permission or root_permission(db)
    flt = parse_filter_json(filter_obj)
    with db.transaction() as conn:
        return ops.delete(conn, perm, notetype, flt)


def delete_preview(
    notetype: str,
    filter_obj: Any,
    permission: Permission | None = None,
) -> list[dict]:
    """删除前预览：只查不删，返回匹配的条目。"""
    _validate_notetype(notetype)
    perm = permission or root_permission(db)
    flt = parse_filter_json(filter_obj)
    nb = registry[notetype]

    # 用写权限视图的 filter 清洗，返回和实际删除一致的条目
    from xfun.core.view import view_clean_filter
    combined = view_clean_filter(perm[1], nb.name, flt)
    preview_view = {notetype: [([c.name for c in nb.columns], combined)]}

    with db.read_transaction() as conn:
        return ops.query(conn, perm, notetype, preview_view)


def _validate_notetype(notetype: str) -> None:
    if notetype not in registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未知笔记本类型: {notetype!r}，可用: {list(registry.keys())}",
        )
