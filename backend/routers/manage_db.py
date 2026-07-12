"""数据库管理路由（初始化/备份/重置）—— 必须使用 ROOT_TOKEN 鉴权。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.services import management_service as svc
from xfun.config import ROOT_TOKEN

router = APIRouter(tags=["management-db"])


class ResetRequest(BaseModel):
    backup_first: bool = Field(
        default=True,
        description="重置前是否先备份",
    )


def require_root_token(x_api_key: str = Header(alias="X-API-Key")):
    if x_api_key != ROOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要 ROOT_TOKEN 才能管理数据库",
        )
    return x_api_key


@router.post("/db/init")
def init_db(
    _=Depends(require_root_token),
):
    msg = svc.init_database()
    return {"message": msg}


@router.post("/db/backup")
def backup_db(
    _=Depends(require_root_token),
):
    msg = svc.backup_database()
    return {"message": msg}


@router.post("/db/reset")
def reset_db(
    body: ResetRequest = ResetRequest(),
    _=Depends(require_root_token),
):
    msg = svc.reset_database(backup_first=body.backup_first)
    return {"message": msg}
