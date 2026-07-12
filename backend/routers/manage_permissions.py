"""权限管理路由（基于数据库 _permissions 表）。"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.deps import require_perm
from backend.permissions import ApiPermission
from xfun import db as _db
from xfun.core import ops as _ops
from xfun.core.view import root_permission, full_view
from xfun.core.filter import Condition

_ROOT_PERM = root_permission(_db)

router = APIRouter(tags=["management-permissions"])


class PermissionCreateRequest(BaseModel):
    id: str = Field(description="权限标识，如 custom-editor")
    name: str = Field(description="可读名称")
    description: str | None = Field(default=None, description="描述")
    read_view: dict = Field(description="读 View JSON")
    write_view: dict = Field(description="写 View JSON")
    can_query: bool = Field(default=False)
    can_add: bool = Field(default=False)
    can_update: bool = Field(default=False)
    can_delete: bool = Field(default=False)
    can_ai_chat: bool = Field(default=False)
    can_manage_db: bool = Field(default=False)
    can_manage_views: bool = Field(default=False)
    can_manage_tokens: bool = Field(default=False)


class PermissionUpdateRequest(BaseModel):
    name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    read_view: dict | None = Field(default=None)
    write_view: dict | None = Field(default=None)
    can_query: bool | None = Field(default=None)
    can_add: bool | None = Field(default=None)
    can_update: bool | None = Field(default=None)
    can_delete: bool | None = Field(default=None)
    can_ai_chat: bool | None = Field(default=None)
    can_manage_db: bool | None = Field(default=None)
    can_manage_views: bool | None = Field(default=None)
    can_manage_tokens: bool | None = Field(default=None)


@router.get("/permissions")
def list_permissions(
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理权限")),
):
    with _db.read_transaction() as conn:
        return _ops.query(conn, _ROOT_PERM, "_permissions", full_view(_db), order_by="id ASC")


@router.get("/permissions/{permission_id}")
def get_permission_route(
    permission_id: str,
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理权限")),
):
    with _db.read_transaction() as conn:
        results = _ops.query(conn, _ROOT_PERM, "_permissions", full_view(_db),
                             Condition("id", permission_id, "="), limit=1)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限 {permission_id!r} 不存在",
        )
    return results[0]


@router.post("/permissions", status_code=status.HTTP_201_CREATED)
def create_permission_route(
    body: PermissionCreateRequest,
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理权限")),
):
    # 检查 id 是否已存在
    with _db.read_transaction() as conn:
        existing = _ops.query(conn, _ROOT_PERM, "_permissions", full_view(_db),
                              Condition("id", body.id, "="), limit=1)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"权限标识 {body.id!r} 已存在",
        )
    with _db.transaction() as conn:
        result = _ops.add(conn, _ROOT_PERM, "_permissions", [{
            "id": body.id,
            "name": body.name,
            "description": body.description,
            "read_view": json.dumps(body.read_view, ensure_ascii=False),
            "write_view": json.dumps(body.write_view, ensure_ascii=False),
            "can_query": 1 if body.can_query else 0,
            "can_add": 1 if body.can_add else 0,
            "can_update": 1 if body.can_update else 0,
            "can_delete": 1 if body.can_delete else 0,
            "can_ai_chat": 1 if body.can_ai_chat else 0,
            "can_manage_db": 1 if body.can_manage_db else 0,
            "can_manage_views": 1 if body.can_manage_views else 0,
            "can_manage_tokens": 1 if body.can_manage_tokens else 0,
        }])
    return result[0]


@router.put("/permissions/{permission_id}")
def update_permission_route(
    permission_id: str,
    body: PermissionUpdateRequest,
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理权限")),
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
    for field in ("can_query", "can_add", "can_update", "can_delete",
                  "can_ai_chat", "can_manage_db", "can_manage_views", "can_manage_tokens"):
        val = getattr(body, field, None)
        if val is not None:
            updates[field] = 1 if val else 0

    with _db.transaction() as conn:
        if updates:
            result = _ops.update(conn, _ROOT_PERM, "_permissions",
                                 Condition("id", permission_id, "="), updates)
        else:
            result = _ops.query(conn, _ROOT_PERM, "_permissions", full_view(_db),
                                Condition("id", permission_id, "="), limit=1)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限 {permission_id!r} 不存在",
        )
    return result[0]


@router.delete("/permissions/{permission_id}")
def delete_permission_route(
    permission_id: str,
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理权限")),
):
    with _db.transaction() as conn:
        result = _ops.delete(conn, _ROOT_PERM, "_permissions",
                             Condition("id", permission_id, "="))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限 {permission_id!r} 不存在",
        )
    return {"message": f"权限 {permission_id!r} 已删除"}
