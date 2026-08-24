"""Token 特殊端点路由（info / exchange）—— 无法用通用 CRUD 表达的专属逻辑。"""

from __future__ import annotations
from functools import partial
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.deps import get_api_permission, ApiPermission
from xfun import init_db
from xfun.config import ROOT_TOKEN
from xfun.core import ops as _ops
from xfun.core.db import DB
from xfun.core.view import root_permission, view_to_json
from xfun.core.filter import Condition
from xfun.utils.file_utils import get_db_path
from xfun.utils.time_utils import now_str

router = APIRouter(tags=["tokens"])


class TokenInfoResponse(BaseModel):
    """当前 Token 的基本信息（不含 token 明文和 permission id）。"""
    name: str
    shortcut: str | None = None
    shortcut_expire_at: str | None = None
    expires_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    is_active: bool
    read_view: dict
    write_view: dict


@router.get("/tokens/info", summary="查询当前 Token 信息", response_description="当前 Token 的基本信息（含权限视图）")
def get_current_token_info(
    api_perm: ApiPermission = Depends(partial(get_api_permission, allow_inactive=True)),
):
    """
    查询当前 Token 信息。
    使用 root_permission 二次查询 _token 表获取元数据。
    """
    perm = root_permission(api_perm.db)

    if api_perm.token != ROOT_TOKEN:
        with api_perm.db.read_transaction() as conn:
            cols = ["name", "shortcut", "shortcut_expire_at", "expires_at",
                    "created_at", "updated_at", "is_active"]
            results = _ops.query(conn, perm, "_token",
                                {"_token": [(cols, Condition("token", api_perm.token, "="))]},
                                limit=1)

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token 在鉴权后被删除",
            )
        row = results[0]
    else:
        row = {}

    read_view = view_to_json(api_perm.permission[0])
    write_view = view_to_json(api_perm.permission[1])

    return TokenInfoResponse(
        name=row.get("name", "ROOT_TOKEN"),
        shortcut=row.get("shortcut"),
        shortcut_expire_at=row.get("shortcut_expire_at"),
        expires_at=row.get("expires_at"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        is_active=bool(row.get("is_active", True)),
        read_view=read_view,
        write_view=write_view,
    )


class ShortcutExchangeRequest(BaseModel):
    shortcut: str = Field(description="快捷配对码")


@router.post("/tokens/exchange", summary="通过 Shortcut 兑换完整 Token", description="无需鉴权，一次性使用")
def exchange_token_by_shortcut(
    body: ShortcutExchangeRequest,
    user: str = Header(alias="User"),
):
    """
    通过 Shortcut 兑换完整 Token（无需鉴权）。

    原子操作：检查有效性 -> 返回完整 token 明文 -> 立即清空 shortcut（一次性）。
    """
    db_path = get_db_path(user)
    if not Path(db_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    db = DB(db_path)
    init_db(db)

    perm = root_permission(db)

    with db.transaction() as conn:
        cols = db.cols("_token")
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
