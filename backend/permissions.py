"""API 权限定义 - 从数据库 _permissions 表加载。"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields

from xfun.core.permission import get_permission as _get_permission
from xfun.core.view import Permission, parse_view_json


@dataclass
class ApiPermission:
    """一个 API 权限。"""
    permission: Permission  # (read_view, write_view) 数据读写权限
    can_query: bool = False
    can_add: bool = False
    can_update: bool = False
    can_delete: bool = False
    can_ai_chat: bool = False
    can_manage_db: bool = False
    can_manage_views: bool = False
    can_manage_tokens: bool = False

    @classmethod
    def from_row(cls, row) -> ApiPermission:
        """从 _permissions 表的 Row 构造 ApiPermission。

        通过 dataclass.fields() 自动推导所有 can_* 布尔字段。
        """
        read_view = parse_view_json(json.loads(row["read_view"]))
        write_view = parse_view_json(json.loads(row["write_view"]))
        can_fields = [f.name for f in fields(cls) if f.name.startswith("can_")]
        kwargs = {f: bool(row[f]) for f in can_fields}
        return cls(permission=(read_view, write_view), **kwargs)


def get_api_permission_from_db(permission_id: str) -> ApiPermission | None:
    """从 _permissions 表查询权限定义（委托 domain 层）。"""
    row = _get_permission(permission_id)
    if row is None:
        return None
    return ApiPermission.from_row(row)
