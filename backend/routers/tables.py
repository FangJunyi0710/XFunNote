"""表 CRUD 路由。"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.schemas import (
    EntryBatchResponse,
    EntryCreate,
    EntryDelete,
    EntryUpdate,
)
from backend.services import table_service as svc
from backend.deps import get_api_permission, ApiPermission
from xfun.core.filter import Filter, parse_filter_json

router = APIRouter(tags=["tables"])


@router.get("/tables", summary="列出所有表及字段结构", response_description="表列表（含字段定义）")
def list_tables(api_perm: ApiPermission = Depends(get_api_permission)):
    return svc.list_tables(api_perm.db)


@router.get("/tables/{name}/schema", summary="查看表字段结构", response_description="字段定义列表")
def get_schema(name: str, api_perm: ApiPermission = Depends(get_api_permission)):
    return svc.get_schema(api_perm.db, name)


def parse_filter_param(filter: str = Query("", description='筛选 JSON，如 {"col":"id","op":"=","val":1}')) -> Filter | None:
    if not filter.strip():
        return None
    try:
        return parse_filter_json(json.loads(filter))
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"filter 不是合法 JSON: {e}",
        )


@router.get("/tables/{name}/entries", summary="通用查询条目", response_description="匹配的条目列表（含总数）")
def query_entries(
    name: str,
    order_by: str = Query("", description="排序，如 `created_at DESC`"),
    limit: int = Query(ge=-1, description="最大返回条数，-1 不限"),
    offset: int = Query(0, ge=0, description="偏移量"),
    view: str = Query("", description="视图名称；为空表示全表"),
    filter: Filter | None = Depends(parse_filter_param),
    api_perm: ApiPermission = Depends(get_api_permission),
):
    stored_view = svc.resolve_view(api_perm.db, api_perm.permission, view) if view else None
    results, total = svc.query_entries(api_perm.db, name, api_perm.permission, stored_view,
                                       limit, offset, order_by, filter=filter)
    return EntryBatchResponse(count=total, results=results)


@router.post(
    "/tables/{name}/entries",
    status_code=status.HTTP_201_CREATED,
    summary="批量添加条目",
    response_description="新增条目的完整信息",
)
def add_entries(
    name: str,
    body: EntryCreate,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    results = svc.add_entries(api_perm.db, name, body.entries, permission=api_perm.permission)
    return EntryBatchResponse(count=len(results), results=results)


@router.put("/tables/{name}/entries", summary="批量更新条目", response_description="更新后条目的完整信息")
def update_entries(
    name: str,
    body: EntryUpdate,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    results = svc.update_entries(api_perm.db, name, body.filter, body.values, permission=api_perm.permission)
    return EntryBatchResponse(count=len(results), results=results)


@router.delete("/tables/{name}/entries", summary="批量删除条目", response_description="被删除条目的完整信息")
def delete_entries(
    name: str,
    body: EntryDelete,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    results = svc.delete_entries(api_perm.db, name, body.filter, permission=api_perm.permission)
    return EntryBatchResponse(count=len(results), results=results)
