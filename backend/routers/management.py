"""数据库管理与视图管理路由。"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.services import management_service as svc

router = APIRouter(tags=["management"])


# ---- 数据库管理 ----

@router.post("/db/init")
def init_db():
    msg = svc.init_database()
    return {"message": msg}


@router.post("/db/backup")
def backup_db():
    msg = svc.backup_database()
    return {"message": msg}


class ResetRequest(BaseModel):
    backup_first: bool = Field(
        default=True,
        description="重置前是否先备份",
    )


@router.post("/db/reset")
def reset_db(body: ResetRequest = ResetRequest()):
    msg = svc.reset_database(backup_first=body.backup_first)
    return {"message": msg}


# ---- 视图文件管理 ----

@router.get("/views")
def list_views():
    return svc.list_views()


@router.get("/views/{name}")
def get_view(name: str):
    view = svc.get_view(name)
    if view is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"视图 {name!r} 不存在",
        )
    return view


@router.put("/views/{name}")
def save_view(name: str, body: dict):
    svc.save_view(name, body)
    return {"message": f"视图 {name!r} 已保存"}


@router.delete("/views/{name}")
def delete_view(name: str):
    ok = svc.delete_view(name)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"视图 {name!r} 不存在",
        )
    return {"message": f"视图 {name!r} 已删除"}
