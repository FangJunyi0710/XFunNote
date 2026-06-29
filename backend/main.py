"""FastAPI 后端入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from xfun.core.errors import XFunError

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


@app.exception_handler(XFunError)
async def xfun_error_handler(request: Request, exc: XFunError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": str(exc)},
    )


app.include_router(notebooks.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(management.router, prefix="/api/v1")
