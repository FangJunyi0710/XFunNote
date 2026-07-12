"""FastAPI 后端入口。"""
import sys
from pathlib import Path

from xfun.core.errors import XFunError

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from xfun.config import PROJECT_ROOT

assert PROJECT_ROOT == _PROJECT_ROOT

import http
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routers import (
    notebooks,
    ai,
    manage_db,
    manage_views,
    manage_tokens,
    manage_permissions,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：确保数据库已初始化（xfun.__init__ 导入时会自动初始化）
    yield
    # 关闭时：无需特殊清理


app = FastAPI(
    title="XFunNote API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """全局 HTTPException 处理器：保留 detail 供前端使用。"""
    content = {"error": http.HTTPStatus(exc.status_code).phrase}
    if exc.detail:
        content["detail"] = exc.detail
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(XFunError)
async def xfun_error_handler(request: Request, exc: XFunError):
    """XFunError 处理器：将领域异常转为 422，保留错误消息。"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": http.HTTPStatus(422).phrase,
            "detail": str(exc),
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic 模型校验失败处理器：返回结构化字段错误供前端表单高亮。"""
    errors = []
    for err in exc.errors():
        loc = [str(loc) for loc in err["loc"] if loc not in ("body", "query")]
        field = ".".join(loc) if loc else "-"
        errors.append({"field": field, "message": err["msg"]})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": http.HTTPStatus(422).phrase,
            "detail": "请求参数校验失败",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """兜底处理器：防止未捕获异常泄漏内部信息。"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": http.HTTPStatus(500).phrase},
    )


app.include_router(notebooks.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(manage_db.router, prefix="/api/v1")
app.include_router(manage_views.router, prefix="/api/v1")
app.include_router(manage_tokens.router, prefix="/api/v1")
app.include_router(manage_permissions.router, prefix="/api/v1")
