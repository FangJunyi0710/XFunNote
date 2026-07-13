"""Token 管理路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.deps import get_api_permission
from backend.permissions import ApiPermission
from xfun import db as _db
from xfun.core import ops as _ops
from xfun.core.view import full_view
from xfun.core.filter import Condition

router = APIRouter(tags=["management-tokens"])


class TokenCreateRequest(BaseModel):
    name: str = Field(description="Token 可读名称")
    permission: str = Field(description="权限标识，对应 _permission 表中的 id")


class TokenUpdateRequest(BaseModel):
    name: str | None = Field(default=None, description="Token 可读名称")
    permission: str | None = Field(default=None, description="权限标识")
    is_active: bool | None = Field(default=None, description="是否启用")
    expires_at: str | None = Field(default=None, description="过期时间，ISO 格式字符串或 null")


def _permission_exists(perm, permission_id: str) -> bool:
    """检查 _permission 表中是否存在指定 id。"""
    with _db.read_transaction() as conn:
        cols = _db.cols("_permission")
        results = _ops.query(conn, perm, "_permission",
                             {"_permission": [(cols, Condition("id", permission_id, "="))]},
                             limit=1)
    return len(results) > 0


@router.get("/tokens")
def list_token(
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.read_transaction() as conn:
        return _ops.query(conn, api_perm.permission, "_token", full_view(_db),
                          order_by="created_at DESC")


@router.get("/tokens/{token_id}")
def get_token_route(
    token_id: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.read_transaction() as conn:
        cols = _db.cols("_token")
        results = _ops.query(conn, api_perm.permission, "_token",
                             {"_token": [(cols, Condition("id", token_id, "="))]},
                             limit=1)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token {token_id!r} 不存在",
        )
    return results[0]


@router.post("/tokens", status_code=status.HTTP_201_CREATED)
def create_token_route(
    body: TokenCreateRequest,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not _permission_exists(api_perm.permission, body.permission):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不存在的权限标识: {body.permission!r}",
        )

    with _db.transaction() as conn:
        results = _ops.add(conn, api_perm.permission, "_token", [{
            "name": body.name,
            "permission": body.permission,
        }])

    return results[0]


@router.put("/tokens/{token_id}")
def update_token_route(
    token_id: str,
    body: TokenUpdateRequest,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    updates: dict = {}

    if body.name is not None:
        updates["name"] = body.name
    if body.permission is not None:
        if not _permission_exists(api_perm.permission, body.permission):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不存在的权限标识: {body.permission!r}",
            )
        updates["permission"] = body.permission
    if body.is_active is not None:
        updates["is_active"] = 1 if body.is_active else 0
    if body.expires_at is not None:
        updates["expires_at"] = body.expires_at

    with _db.transaction() as conn:
        if updates:
            result = _ops.update(conn, api_perm.permission, "_token",
                                 Condition("id", token_id, "="), updates)
        else:
            cols = _db.cols("_token")
            result = _ops.query(conn, api_perm.permission, "_token",
                                {"_token": [(cols, Condition("id", token_id, "="))]},
                                limit=1)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token {token_id!r} 不存在",
        )
    return result[0]


@router.delete("/tokens/{token_id}")
def delete_token_route(
    token_id: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.transaction() as conn:
        result = _ops.delete(conn, api_perm.permission, "_token",
                             Condition("id", token_id, "="))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token {token_id!r} 不存在",
        )
    return {"message": f"Token 已删除"}
