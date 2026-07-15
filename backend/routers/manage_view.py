"""视图管理路由（基于数据库 _view 表）。"""

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


@router.get("/views", summary="列出所有保存的视图", response_description="视图列表")
def list_view(
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.read_transaction() as conn:
        return _ops.query(conn, api_perm.permission, "_view", full_view(_db), order_by="name ASC")


@router.get("/views/{name}", summary="获取指定视图内容", response_description="视图的 JSON 数据")
def get_view_route(
    name: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.read_transaction() as conn:
        cols = _db.cols("_view")
        results = _ops.query(conn, api_perm.permission, "_view",
                             {"_view": [(cols, Condition("name", name, "="))]},
                             limit=1)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"视图 {name!r} 不存在",
        )
    return json.loads(results[0]["data"])


@router.put("/views/{name}", summary="保存或更新视图", description="不存在则创建，存在则覆盖")
def save_view_route(
    name: str,
    body: dict,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    json_data = json.dumps(body, ensure_ascii=False)
    with _db.transaction() as conn:
        cols = _db.cols("_view")
        existing = _ops.query(conn, api_perm.permission, "_view",
                              {"_view": [(cols, Condition("name", name, "="))]},
                              limit=1)
        if existing:
            _ops.update(conn, api_perm.permission, "_view",
                        Condition("name", name, "="), {"data": json_data})
        else:
            _ops.add(conn, api_perm.permission, "_view",
                     [{"name": name, "data": json_data}])
    return {"message": f"视图 {name!r} 已保存"}


@router.delete("/views/{name}", summary="删除指定视图", response_description="删除确认消息")
def delete_view_route(
    name: str,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    with _db.transaction() as conn:
        result = _ops.delete(conn, api_perm.permission, "_view",
                             Condition("name", name, "="))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"视图 {name!r} 不存在",
        )
    return {"message": f"视图 {name!r} 已删除"}
