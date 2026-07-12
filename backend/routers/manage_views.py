"""视图管理路由（基于数据库 _views 表）。"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status

from backend.deps import get_api_permission
from backend.permissions import ApiPermission
from xfun import db as _db
from xfun.core import ops as _ops
from xfun.core.view import full_view
from xfun.core.filter import Condition

router = APIRouter(tags=["management-views"])


@router.get("/views")
def list_views(
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.read_transaction() as conn:
        return _ops.query(conn, api_perm.permission, "_views", full_view(_db), order_by="name ASC")


@router.get("/views/{name}")
def get_view_route(
    name: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.read_transaction() as conn:
        results = _ops.query(conn, api_perm.permission, "_views", full_view(_db),
                             Condition("name", name, "="), limit=1)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"视图 {name!r} 不存在",
        )
    return json.loads(results[0]["data"])


@router.put("/views/{name}")
def save_view_route(
    name: str,
    body: dict,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    json_data = json.dumps(body, ensure_ascii=False)
    with _db.transaction() as conn:
        existing = _ops.query(conn, api_perm.permission, "_views", full_view(_db),
                              Condition("name", name, "="), limit=1)
        if existing:
            _ops.update(conn, api_perm.permission, "_views",
                        Condition("name", name, "="), {"data": json_data})
        else:
            _ops.add(conn, api_perm.permission, "_views",
                     [{"name": name, "data": json_data}])
    return {"message": f"视图 {name!r} 已保存"}


@router.delete("/views/{name}")
def delete_view_route(
    name: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.transaction() as conn:
        result = _ops.delete(conn, api_perm.permission, "_views",
                             Condition("name", name, "="))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"视图 {name!r} 不存在",
        )
    return {"message": f"视图 {name!r} 已删除"}
