"""本子 CRUD 路由。"""

from fastapi import APIRouter, HTTPException, Query, status

from backend.schemas import (
    EntryBatchResponse,
    EntryCreate,
    EntryDelete,
    EntryUpdate,
)
from backend.services import notebook_service as svc

router = APIRouter(tags=["notebooks"])


@router.get("/notebooks")
def list_notebooks():
    return svc.list_notebooks()


@router.get("/notebooks/{name}/schema")
def get_schema(name: str):
    return svc.get_schema(name)


@router.get("/notebooks/{name}/entries")
def query_entries(
    name: str,
    view: str | None = Query(None, description="View JSON 字符串"),
    order_by: str = Query("", description="排序，如 `created_at DESC`"),
    limit: int = Query(100, ge=-1, description="最大返回条数，-1 不限"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    results = svc.query_entries(name, view, order_by, limit, offset)
    return EntryBatchResponse(count=len(results), results=results)


@router.post(
    "/notebooks/{name}/entries",
    status_code=status.HTTP_201_CREATED,
)
def add_entries(name: str, body: EntryCreate):
    results = svc.add_entries(name, body.entries)
    return EntryBatchResponse(count=len(results), results=results)


@router.put("/notebooks/{name}/entries")
def update_entries(name: str, body: EntryUpdate):
    results = svc.update_entries(name, body.filter, body.values)
    return EntryBatchResponse(count=len(results), results=results)


@router.post("/notebooks/{name}/entries/preview-delete")
def preview_delete(name: str, body: EntryDelete):
    """删除预览：返回将被删除的条目，实际不删除。"""
    results = svc.delete_preview(name, body.filter)
    return EntryBatchResponse(count=len(results), results=results)


@router.delete("/notebooks/{name}/entries")
def delete_entries(name: str, body: EntryDelete):
    if not body.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="删除操作需要确认，请先调用 POST preview-delete 预览，确认后将 confirm 设为 true",
        )
    results = svc.delete_entries(name, body.filter)
    return EntryBatchResponse(count=len(results), results=results)
