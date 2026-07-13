"""权限管理路由（基于数据库 _permission 表）。"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.deps import get_api_permission
from backend.permissions import ApiPermission
from xfun import db as _db
from xfun.core import ops as _ops
from xfun.core.view import full_view
from xfun.core.filter import Condition

router = APIRouter(tags=["management-permissions"])


class PermissionCreateRequest(BaseModel):
    id: str = Field(description="权限标识，如 custom-editor")
    name: str = Field(description="可读名称")
    description: str | None = Field(default=None, description="描述")
    read_view: dict = Field(description="读 View JSON")
    write_view: dict = Field(description="写 View JSON")


class PermissionUpdateRequest(BaseModel):
    name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    read_view: dict | None = Field(default=None)
    write_view: dict | None = Field(default=None)


@router.get("/permissions")
def list_permission(
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.read_transaction() as conn:
        return _ops.query(conn, api_perm.permission, "_permission", full_view(_db), order_by="id ASC")


@router.get("/permissions/{permission_id}")
def get_permission_route(
    permission_id: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.read_transaction() as conn:
        cols = _db.cols("_permission")
        results = _ops.query(conn, api_perm.permission, "_permission",
                             {"_permission": [(cols, Condition("id", permission_id, "="))]},
                             limit=1)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限 {permission_id!r} 不存在",
        )
    return results[0]


@router.post("/permissions", status_code=status.HTTP_201_CREATED)
def create_permission_route(
    body: PermissionCreateRequest,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.transaction() as conn:
        result = _ops.add(conn, api_perm.permission, "_permission", [{
            "id": body.id,
            "name": body.name,
            "description": body.description,
            "read_view": json.dumps(body.read_view, ensure_ascii=False),
            "write_view": json.dumps(body.write_view, ensure_ascii=False),
        }])
    return result[0]


@router.put("/permissions/{permission_id}")
def update_permission_route(
    permission_id: str,
    body: PermissionUpdateRequest,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    updates: dict = {}

    if body.name is not None:
        updates["name"] = body.name
    if body.description is not None:
        updates["description"] = body.description
    if body.read_view is not None:
        updates["read_view"] = json.dumps(body.read_view, ensure_ascii=False)
    if body.write_view is not None:
        updates["write_view"] = json.dumps(body.write_view, ensure_ascii=False)

    with _db.transaction() as conn:
        if updates:
            result = _ops.update(conn, api_perm.permission, "_permission",
                                 Condition("id", permission_id, "="), updates)
        else:
            cols = _db.cols("_permission")
            result = _ops.query(conn, api_perm.permission, "_permission",
                                {"_permission": [(cols, Condition("id", permission_id, "="))]},
                                limit=1)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限 {permission_id!r} 不存在",
        )
    return result[0]


@router.delete("/permissions/{permission_id}")
def delete_permission_route(
    permission_id: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.transaction() as conn:
        result = _ops.delete(conn, api_perm.permission, "_permission",
                             Condition("id", permission_id, "="))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限 {permission_id!r} 不存在",
        )
    return {"message": f"权限 {permission_id!r} 已删除"}
