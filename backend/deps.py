"""FastAPI 依赖注入：Token 鉴权与 Permission 注入。"""

from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
import re

from fastapi import Depends, Header, HTTPException, status

from xfun import init_db
from xfun.config import PROJECT_ROOT, ROOT_TOKEN
from xfun.core.db import DB, Column
from xfun.utils.file_utils import get_db_path
from xfun.utils.time_utils import now_str
from xfun.core import ops as _ops
from xfun.core.view import DB_Permission, no_permission, parse_view_json, root_permission, full_view
from xfun.core.filter import Condition

# ── 工厂依赖（可复用权限校验） ──────────────────────────────────────────────

@dataclass
class ApiPermission:
    """一个 API 权限。"""
    token: str
    db: DB
    permission: DB_Permission

async def require_token(authorization: str = Header(alias="Authorization")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid authorization header. Must use Bearer scheme."
        )

    return authorization[len("Bearer "):]

async def get_api_permission(
    token: str = Depends(require_token),
    user: str = Header(alias="User"),
    allow_inactive: bool = False
) -> ApiPermission:
    """提取请求头信息并返回对应的 ApiPermission 对象。"""

    db_path = get_db_path(user)
    existing = Path(db_path).exists()
    db = DB(db_path)

    # 管理员启动密钥：绕过 _token 表，直接返回 root 权限
    if ROOT_TOKEN and token == ROOT_TOKEN:
        init_db(db)
        if not existing:
            db.init()
        return ApiPermission(token, db, root_permission(db))
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    init_db(db)

    # 查询 _token 表
    with db.read_transaction() as conn:
        token_res = _ops.query(conn, root_permission(db), "_token", {"_token": [(["permission","is_active","expires_at"],Condition("token", token, "="))]}, limit=1)

    if not token_res:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或未知的 Token",
        )
    
    token_res = token_res[0]

    if not token_res["is_active"]:
        if allow_inactive:
            return ApiPermission(token, db, no_permission(db))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已被停用",
        )

    if token_res["expires_at"] and token_res["expires_at"] < now_str():
        if allow_inactive:
            return ApiPermission(token, db, no_permission(db))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已过期",
        )

    with db.read_transaction() as conn:
        permission_res = _ops.query(conn, root_permission(db), "_permission", {"_permission": [(db.cols("_permission"), Condition("uuid", token_res["permission"], "="))]}, limit=1)

    if not permission_res:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"未知的权限标识",
        )
    
    permission_res = permission_res[0]

    read_view = parse_view_json(json.loads(permission_res["read_view"]))
    write_view = parse_view_json(json.loads(permission_res["write_view"]))
    return ApiPermission(token, db, (read_view, write_view))

async def require_root_token(api_perm: ApiPermission = Depends(get_api_permission)):
    if api_perm.token != ROOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要 ROOT_TOKEN 才能管理数据库",
        )
    return api_perm
