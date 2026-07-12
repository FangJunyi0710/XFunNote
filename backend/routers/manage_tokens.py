"""Token 管理路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.deps import require_perm
from backend.permissions import ApiPermission
from xfun.core import token

router = APIRouter(tags=["management-tokens"])


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
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理 Token")),
):
    return token.list_tokens()


@router.get("/tokens/{token_id}")
def get_token_route(
    token_id: str,
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理 Token")),
):
    t = token.get_token(token_id)
    if t is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token {token_id!r} 不存在",
        )
    return t


@router.post("/tokens", status_code=status.HTTP_201_CREATED)
def create_token_route(
    body: TokenCreateRequest,
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理 Token")),
):
    try:
        result = token.create_token(name=body.name, permission=body.permission)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result


@router.put("/tokens/{token_id}")
def update_token_route(
    token_id: str,
    body: TokenUpdateRequest,
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理 Token")),
):
    try:
        result = token.update_token(
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
def delete_token_route(
    token_id: str,
    api_perm: ApiPermission = Depends(require_perm("can_manage_tokens", "当前 API Key 无权管理 Token")),
):
    ok = token.delete_token(token_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token {token_id!r} 不存在",
        )
    return {"message": f"Token 已删除"}
