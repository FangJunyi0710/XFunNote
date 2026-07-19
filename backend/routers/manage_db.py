"""数据库管理路由（初始化/备份/重置/恢复）—— 必须使用 ROOT_TOKEN 鉴权。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.deps import ApiPermission, require_root_token
from backend.services import management_service as svc
from xfun.config import PROJECT_ROOT

router = APIRouter(tags=["management-db"])


class ResetRequest(BaseModel):
    backup_first: bool = Field(
        default=True,
        description="重置前是否先备份",
    )


class RestoreRequest(BaseModel):
    backup_path: str = Field(
        ...,
        description="备份文件路径",
    )

@router.post("/db/init", summary="初始化数据库", description="建表/同步列/建索引")
def init_db(api_perm: ApiPermission = Depends(require_root_token)):
    msg = svc.init_database(api_perm.db)
    return {"message": msg}


@router.post("/db/backup", summary="在线热备份数据库", description="创建数据库的即时快照备份")
def backup_db(api_perm: ApiPermission = Depends(require_root_token)):
    msg = svc.backup_database(api_perm.db)
    return {"message": msg}


@router.post("/db/reset", summary="重置数据库", description="清空所有表并重新初始化")
def reset_db(
    body: ResetRequest = ResetRequest(),
    api_perm: ApiPermission = Depends(require_root_token)
):
    msg = svc.reset_database(api_perm.db, backup_first=body.backup_first)
    return {"message": msg}


@router.post("/db/restore", summary="从备份文件恢复数据库", description="从指定备份文件恢复数据库状态")
def restore_db(
    body: RestoreRequest,
    api_perm: ApiPermission = Depends(require_root_token)
):
    try:
        msg = svc.restore_database(api_perm.db, backup_path=body.backup_path)
        return {"message": msg}
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/db/backups", summary="列出所有备份文件", description="列出 data/backups/ 目录下所有备份文件")
def list_backups(api_perm: ApiPermission = Depends(require_root_token)):
    """列出 data/backups/ 目录下所有备份文件。"""
    backup_dir = PROJECT_ROOT / "data" / "backups"
    if not backup_dir.exists():
        return {"backups": []}
    files = sorted([str(f) for f in backup_dir.iterdir() if f.is_file()])
    return {"backups": files}
