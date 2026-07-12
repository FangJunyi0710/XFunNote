"""数据库管理路由（初始化/备份/重置）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.services import management_service as svc
from backend.deps import require_perm
from backend.permissions import ApiPermission

router = APIRouter(tags=["management-db"])


class ResetRequest(BaseModel):
    backup_first: bool = Field(
        default=True,
        description="重置前是否先备份",
    )


@router.post("/db/init")
def init_db(
    api_perm: ApiPermission = Depends(require_perm("can_manage_db", "当前 API Key 无权管理数据库")),
):
    msg = svc.init_database()
    return {"message": msg}


@router.post("/db/backup")
def backup_db(
    api_perm: ApiPermission = Depends(require_perm("can_manage_db", "当前 API Key 无权管理数据库")),
):
    msg = svc.backup_database()
    return {"message": msg}


@router.post("/db/reset")
def reset_db(
    body: ResetRequest = ResetRequest(),
    api_perm: ApiPermission = Depends(require_perm("can_manage_db", "当前 API Key 无权管理数据库")),
):
    msg = svc.reset_database(backup_first=body.backup_first)
    return {"message": msg}
