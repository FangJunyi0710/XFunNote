"""视图管理路由（基于数据库 _views 表）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.deps import get_api_permission
from backend.permissions import ApiPermission
from xfun.core import view

router = APIRouter(tags=["management-views"])


@router.get("/views")
def list_views(
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_views:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理视图",
        )
    return view.list_views()


@router.get("/views/{name}")
def get_view_route(
    name: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_views:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理视图",
        )
    v = view.get_view(name)
    if v is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"视图 {name!r} 不存在",
        )
    return v


@router.put("/views/{name}")
def save_view_route(
    name: str,
    body: dict,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_views:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理视图",
        )
    view.save_view(name, body)
    return {"message": f"视图 {name!r} 已保存"}


@router.delete("/views/{name}")
def delete_view_route(
    name: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    if not api_perm.can_manage_views:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前 API Key 无权管理视图",
        )
    ok = view.delete_view(name)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"视图 {name!r} 不存在",
        )
    return {"message": f"视图 {name!r} 已删除"}
