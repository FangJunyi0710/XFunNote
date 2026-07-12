"""权限管理路由（基于数据库 _permissions 表）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.deps import require_perm
from backend.permissions import ApiPermission
from xfun.core import permission

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
    return permission.list_permissions()


@router.get("/permissions/{permission_id}")
def get_permission_route(
    permission_id: str,
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理权限")),
):
    perm = permission.get_permission(permission_id)
    if perm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限 {permission_id!r} 不存在",
        )
    return perm


@router.post("/permissions", status_code=status.HTTP_201_CREATED)
def create_permission_route(
    body: PermissionCreateRequest,
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理权限")),
):
    # 检查 id 是否已存在
    existing = permission.get_permission(body.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"权限标识 {body.id!r} 已存在",
        )
    try:
        result = permission.create_permission(
            permission_id=body.id,
            name=body.name,
            description=body.description,
            read_view=body.read_view,
            write_view=body.write_view,
            can_query=body.can_query,
            can_add=body.can_add,
            can_update=body.can_update,
            can_delete=body.can_delete,
            can_ai_chat=body.can_ai_chat,
            can_manage_db=body.can_manage_db,
            can_manage_views=body.can_manage_views,
            can_manage_tokens=body.can_manage_tokens,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result


@router.put("/permissions/{permission_id}")
def update_permission_route(
    permission_id: str,
    body: PermissionUpdateRequest,
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理权限")),
):
    result = permission.update_permission(
        permission_id=permission_id,
        name=body.name,
        description=body.description,
        read_view=body.read_view,
        write_view=body.write_view,
        can_query=body.can_query,
        can_add=body.can_add,
        can_update=body.can_update,
        can_delete=body.can_delete,
        can_ai_chat=body.can_ai_chat,
        can_manage_db=body.can_manage_db,
        can_manage_views=body.can_manage_views,
        can_manage_tokens=body.can_manage_tokens,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限 {permission_id!r} 不存在",
        )
    return result


@router.delete("/permissions/{permission_id}")
def delete_permission_route(
    permission_id: str,
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理权限")),
):
    ok = permission.delete_permission(permission_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限 {permission_id!r} 不存在",
        )
    return {"message": f"权限 {permission_id!r} 已删除"}
