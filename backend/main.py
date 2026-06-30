"""FastAPI 后端入口。"""
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from xfun.config import PROJECT_ROOT

assert PROJECT_ROOT == _PROJECT_ROOT

import http
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routers import notebooks, ai, management


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
    """全局 HTTPException 处理器：仅返回标准 HTTP 状态短语，剥离原 detail。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": http.HTTPStatus(exc.status_code).phrase},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """兜底处理器：防止未捕获异常泄漏内部信息。"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error"},
    )


app.include_router(notebooks.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(management.router, prefix="/api/v1")
