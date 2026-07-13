"""API 权限定义 - 从数据库 _permission 表加载。"""

from __future__ import annotations

import json
from dataclasses import dataclass

from xfun import db as _db
from xfun.core import ops as _ops
from xfun.core.view import DB_Permission, parse_view_json, root_permission, full_view
from xfun.core.filter import Condition

_ROOT_PERM = root_permission(_db)


@dataclass
class ApiPermission:
    """一个 API 权限。"""
    permission: DB_Permission  # (read_view, write_view) 数据读写权限

    @classmethod
    def from_row(cls, row) -> ApiPermission:
        """从 _permission 表的 Row 构造 ApiPermission。"""
        read_view = parse_view_json(json.loads(row["read_view"]))
        write_view = parse_view_json(json.loads(row["write_view"]))
        return cls(permission=(read_view, write_view))


def get_api_permission_from_db(permission_id: str) -> ApiPermission | None:
    """从 _permission 表查询权限定义。"""
    with _db.read_transaction() as conn:
        results = _ops.query(conn, _ROOT_PERM, "_permission", {"_permission": [(_db.cols("_permission"), Condition("id", permission_id, "="))]}, limit=1)

    if not results:
        return None
    return ApiPermission.from_row(results[0])
