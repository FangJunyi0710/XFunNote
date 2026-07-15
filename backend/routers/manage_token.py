"""Token 管理路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field

from datetime import datetime, timedelta

from backend.deps import get_api_permission
from backend.permissions import ApiPermission
from xfun import db as _db
from xfun.config import ROOT_TOKEN
from xfun.core import ops as _ops
from xfun.core.view import full_view, root_permission, view_to_json
from xfun.core.filter import Condition

router = APIRouter(tags=["management-tokens"])


class TokenCreateRequest(BaseModel):
    name: str = Field(description="Token 可读名称")
    permission: str = Field(description="权限标识，对应 _permission 表中的 id")
    shortcut: str | None = Field(default=None, description="可选的自定义快捷配对码", max_length=64)
    shortcut_ttl: int = Field(default=120, ge=10, le=86400, description="Shortcut 有效期（秒），默认 120 秒")


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


@router.get("/tokens", summary="列出所有 Token", response_description="Token 列表")
def list_token(
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.read_transaction() as conn:
        return _ops.query(conn, api_perm.permission, "_token", full_view(_db),
                          order_by="created_at DESC")


class TokenInfoResponse(BaseModel):
    """当前 Token 的基本信息（不含 token 明文和 permission id）"""
    name: str
    shortcut: str | None = None
    shortcut_expire_at: str | None = None
    expires_at: str | None = None
    created_at: str
    updated_at: str
    read_view: dict
    write_view: dict


@router.get("/tokens/info", summary="查询当前 Token 信息", response_description="当前 Token 的基本信息（含权限视图）")
def get_current_token_info(
    api_perm: ApiPermission = Depends(get_api_permission),
    x_api_key: str = Header(alias="X-API-Key"),
):
    """
    查询当前 API Key 的 Token 信息。
    返回 name、shortcut、shortcut_expire_at、expires_at、created_at、updated_at、read_view、write_view。
    使用 root_permission 二次查询 _token 表获取元数据。
    """

    perm = root_permission(_db)

    if x_api_key == ROOT_TOKEN:
        row = {"name": "ROOT_TOKEN", "created_at": "", "updated_at": ""}
    else:
        with _db.read_transaction() as conn:
            cols = ["name", "shortcut", "shortcut_expire_at", "expires_at",
                    "created_at", "updated_at"]
            results = _ops.query(conn, perm, "_token",
                                {"_token": [(cols, Condition("token", x_api_key, "="))]},
                                limit=1)
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token 在鉴权后被删除",
            )
        row = results[0]

    read_view = view_to_json(api_perm.permission[0])
    write_view = view_to_json(api_perm.permission[1])

    return TokenInfoResponse(
        name=row["name"],
        shortcut=row.get("shortcut"),
        shortcut_expire_at=row.get("shortcut_expire_at"),
        expires_at=row.get("expires_at"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        read_view=read_view,
        write_view=write_view,
    )


@router.get("/tokens/{token_id}", summary="获取指定 Token 详情", response_description="Token 完整记录")
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


@router.post("/tokens", status_code=status.HTTP_201_CREATED, summary="创建 Token", response_description="新创建的 Token 完整记录")
def create_token_route(
    body: TokenCreateRequest,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not _permission_exists(api_perm.permission, body.permission):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不存在的权限标识: {body.permission!r}",
        )

    entry = {
        "name": body.name,
        "permission": body.permission,
    }

    if body.shortcut is not None:
        entry["shortcut"] = body.shortcut
        entry["shortcut_expire_at"] = (datetime.now() + timedelta(seconds=body.shortcut_ttl)).isoformat()

    with _db.transaction() as conn:
        results = _ops.add(conn, api_perm.permission, "_token", [entry])

    return results[0]


@router.put("/tokens/{token_id}", summary="更新 Token", description="更新名称、权限、启用状态、过期时间等")
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


class ShortcutExchangeRequest(BaseModel):
    shortcut: str = Field(description="快捷配对码")


@router.post("/tokens/exchange", summary="通过 Shortcut 兑换完整 Token", description="无需鉴权，一次性使用")
def exchange_token_by_shortcut(
    body: ShortcutExchangeRequest,
):
    """
    通过 Shortcut 兑换完整 Token（无需鉴权）。

    原子操作：检查有效性 -> 返回完整 token 明文 -> 立即清空 shortcut（一次性）。
    """
    from xfun.utils.time_utils import now_str

    perm = root_permission(_db)

    with _db.transaction() as conn:
        cols = _db.cols("_token")
        results = _ops.query(conn, perm, "_token",
                             {"_token": [(cols, Condition("shortcut", body.shortcut, "="))]},
                             limit=1)
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shortcut 不存在或已被兑换",
            )

        row = results[0]

        # 检查是否过期
        expire_at = row.get("shortcut_expire_at")
        if expire_at and expire_at < now_str():
            # 过期：清空 shortcut 使其不再可兑
            _ops.update(conn, perm, "_token",
                        Condition("id", row["id"], "="),
                        {"shortcut": None, "shortcut_expire_at": None})
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Shortcut 已过期",
            )

        # 兑换成功：返回完整 token 并清空 shortcut
        token_value = row["token"]
        _ops.update(conn, perm, "_token",
                    Condition("id", row["id"], "="),
                    {"shortcut": None, "shortcut_expire_at": None})

    return {"token": token_value}


@router.delete("/tokens/{token_id}", summary="删除 Token", response_description="删除确认消息")
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
