"""FastAPI 依赖注入：API Key 鉴权与 Permission 注入。"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from xfun.config import ADMIN_API_KEY
from xfun.core.token import get_token_by_value
from xfun.utils.time_utils import now_str

from backend.permissions import ApiPermission, get_api_permission_from_db

# ── 工厂依赖（可复用权限校验） ──────────────────────────────────────────────


def require_perm(attr: str, detail: str):
    """返回 FastAPI 依赖，校验 api_perm.{attr} 是否为 True。

    用法: Depends(require_perm("can_manage_db", "无权管理数据库"))

    返回 ApiPermission 实例，供后续业务逻辑使用。
    """

    async def _require(
        api_perm: ApiPermission = Depends(get_api_permission),
    ) -> ApiPermission:
        if not getattr(api_perm, attr):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail,
            )
        return api_perm

    return _require


async def get_api_permission(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> ApiPermission:
    """提取 API Key 并返回对应的 ApiPermission 对象。

    鉴权流程：
    1. 未提供 token → 401
    2. 匹配 ADMIN_API_KEY（env 配置）→ root 权限
    3. 查询 _tokens 表
       3a. token 不存在 → 401
       3b. is_active=0 → 401
       3c. expires_at 已过期 → 401
       3d. permission id 在 _permissions 表中不存在 → 500
    4. 正常 → 返回 ApiPermission
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 API Key，请在请求头中提供 X-API-Key",
        )

    # 管理员启动密钥：绕过 _tokens 表，直接返回 root 权限
    if ADMIN_API_KEY and x_api_key == ADMIN_API_KEY:
        return _lookup_permission("root")

    # 查询 _tokens 表
    row = get_token_by_value(x_api_key)

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或未知的 API Key",
        )

    if not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key 已被停用",
        )

    if row["expires_at"] and row["expires_at"] < now_str():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key 已过期",
        )

    return _lookup_permission(row["permission"])


def _lookup_permission(permission_id: str) -> ApiPermission:
    """按 _permissions.id 查询权限定义，查不到则抛 401。"""
    perm = get_api_permission_from_db(permission_id)
    if perm is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"未知的权限标识: {permission_id!r}",
        )
    return perm

