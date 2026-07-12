"""数据库管理与视图/Token/权限管理路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.services import management_service as svc
from backend.deps import get_api_permission
from backend.permissions import ApiPermission
from xfun import token_service
from xfun import view_service
from xfun import permission_service

router = APIRouter(tags=["management"])


# ---- 数据库管理 ----

@router.post("/db/init")
def init_db(
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_db:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理数据库",
        )
    msg = svc.init_database()
    return {"message": msg}


@router.post("/db/backup")
def backup_db(
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_db:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理数据库",
        )
    msg = svc.backup_database()
    return {"message": msg}


class ResetRequest(BaseModel):
    backup_first: bool = Field(
        default=True,
        description="重置前是否先备份",
    )


@router.post("/db/reset")
def reset_db(
    body: ResetRequest = ResetRequest(),
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_db:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理数据库",
        )
    msg = svc.reset_database(backup_first=body.backup_first)
    return {"message": msg}


# ---- 视图管理（基于数据库 _views 表） ----

@router.get("/views")
def list_views(
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_views:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理视图",
        )
    return view_service.list_views()


@router.get("/views/{name}")
def get_view(
    name: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_views:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理视图",
        )
    view = view_service.get_view(name)
    if view is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"视图 {name!r} 不存在",
        )
    return view


@router.put("/views/{name}")
def save_view(
    name: str,
    body: dict,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_views:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理视图",
        )
    view_service.save_view(name, body)
    return {"message": f"视图 {name!r} 已保存"}


@router.delete("/views/{name}")
def delete_view(
    name: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_views:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理视图",
        )
    ok = view_service.delete_view(name)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"视图 {name!r} 不存在",
        )
    return {"message": f"视图 {name!r} 已删除"}


# ---- Token 管理 ----

class TokenCreateRequest(BaseModel):
    name: str = Field(description="Token 可读名称")
    permission: str = Field(description="权限标识，对应 _permissions 表中的 id")


class TokenUpdateRequest(BaseModel):
    name: str | None = Field(default=None, description="Token 可读名称")
    permission: str | None = Field(default=None, description="权限标识")
    is_active: bool | None = Field(default=None, description="是否启用")
    expires_at: str | None = Field(default=None, description="过期时间，ISO 格式字符串或 null")


@router.get("/tokens")
def list_tokens(
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理 Token",
        )
    return token_service.list_tokens()


@router.get("/tokens/{token_id}")
def get_token(
    token_id: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理 Token",
        )
    token = token_service.get_token(token_id)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token {token_id!r} 不存在",
        )
    return token


@router.post("/tokens", status_code=status.HTTP_201_CREATED)
def create_token(
    body: TokenCreateRequest,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理 Token",
        )
    try:
        result = token_service.create_token(name=body.name, permission=body.permission)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result


@router.put("/tokens/{token_id}")
def update_token(
    token_id: str,
    body: TokenUpdateRequest,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理 Token",
        )
    try:
        result = token_service.update_token(
            token_id=token_id,
            name=body.name,
            permission=body.permission,
            is_active=body.is_active,
            expires_at=body.expires_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token {token_id!r} 不存在",
        )
    return result


@router.delete("/tokens/{token_id}")
def delete_token(
    token_id: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理 Token",
        )
    ok = token_service.delete_token(token_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token {token_id!r} 不存在",
        )
    return {"message": f"Token 已删除"}


# ---- 权限管理（基于数据库 _permissions 表） ----

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
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理权限",
        )
    return permission_service.list_permissions()


@router.get("/permissions/{permission_id}")
def get_permission(
    permission_id: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理权限",
        )
    perm = permission_service.get_permission(permission_id)
    if perm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限 {permission_id!r} 不存在",
        )
    return perm


@router.post("/permissions", status_code=status.HTTP_201_CREATED)
def create_permission(
    body: PermissionCreateRequest,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理权限",
        )
    # 检查 id 是否已存在
    existing = permission_service.get_permission(body.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"权限标识 {body.id!r} 已存在",
        )
    try:
        result = permission_service.create_permission(
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
def update_permission(
    permission_id: str,
    body: PermissionUpdateRequest,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理权限",
        )
    result = permission_service.update_permission(
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
def delete_permission(
    permission_id: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理权限",
        )
    ok = permission_service.delete_permission(permission_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限 {permission_id!r} 不存在",
        )
    return {"message": f"权限 {permission_id!r} 已删除"}
