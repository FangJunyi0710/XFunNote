"""本子 CRUD 路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError

from backend.schemas import (
    EntryBatchResponse,
    EntryCreate,
    EntryDelete,
    EntryUpdate,
)
from backend.services import notebook_service as svc
from backend.deps import get_api_permission
from backend.permissions import ApiPermission
from xfun.ai.schema import ViewModel

router = APIRouter(tags=["notebooks"])


@router.get("/notebooks", summary="列出所有笔记本及字段结构", response_description="笔记本列表（含字段定义）")
def list_notebooks(api_perm: ApiPermission = Depends(get_api_permission)):
    return svc.list_notebooks()


@router.get("/notebooks/{name}/schema", summary="查看笔记本字段结构", response_description="字段定义列表")
def get_schema(name: str, api_perm: ApiPermission = Depends(get_api_permission)):
    return svc.get_schema(name)


def parse_view_param(view: str = Query(..., description="View JSON 字符串")) -> ViewModel:
    return ViewModel.model_validate_json(view)


@router.get("/notebooks/{name}/entries", summary="通用查询条目", response_description="匹配的条目列表（含总数）")
def query_entries(
    name: str,
    order_by: str = Query("", description="排序，如 `created_at DESC`"),
    limit: int = Query(100, ge=-1, description="最大返回条数，-1 不限"),
    offset: int = Query(0, ge=0, description="偏移量"),
    view_model: ViewModel = Depends(parse_view_param),
    api_perm: ApiPermission = Depends(get_api_permission),
):
    validated_view = view_model.to_view()
    results, total = svc.query_entries(name, api_perm.permission, validated_view,
                                       order_by, limit, offset)
    return EntryBatchResponse(count=total, results=results)


@router.post(
    "/notebooks/{name}/entries",
    status_code=status.HTTP_201_CREATED,
    summary="批量添加条目",
    response_description="新增条目的完整信息",
)
def add_entries(
    name: str,
    body: EntryCreate,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    results = svc.add_entries(name, body.entries, permission=api_perm.permission)
    return EntryBatchResponse(count=len(results), results=results)


@router.put("/notebooks/{name}/entries", summary="批量更新条目", response_description="更新后条目的完整信息")
def update_entries(
    name: str,
    body: EntryUpdate,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    results = svc.update_entries(name, body.filter, body.values,
                                  permission=api_perm.permission)
    return EntryBatchResponse(count=len(results), results=results)


@router.delete("/notebooks/{name}/entries", summary="批量删除条目", response_description="被删除条目的完整信息")
def delete_entries(
    name: str,
    body: EntryDelete,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    results = svc.delete_entries(name, body.filter, permission=api_perm.permission)
    return EntryBatchResponse(count=len(results), results=results)
