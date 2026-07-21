#!/usr/bin/env python3
"""FastAPI 后端入口。"""
import http
import sqlite3
import sys
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from xfun.core.errors import XFunError
from xfun.config import PROJECT_ROOT, SHOW_DOCS, UVICORN_RELOAD, VERSION, BACKEND_PORT

assert PROJECT_ROOT == _PROJECT_ROOT

API_PREFIX = f"/api/v{VERSION.split('.')[0]}"

from backend.routers import (
    notebooks,
    ai,
    manage_db,
    manage_view,
    manage_token,
    manage_permission,
    manage_filter,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：确保数据库已初始化（xfun.__init__ 导入时会自动初始化）
    yield
    # 关闭时：无需特殊清理


app = FastAPI(
    title="XFunNote API",
    description=f"""
XFunNote 是一个轻量级、无模式的笔记系统后端。

## 功能特性

- **📓 本子 CRUD** — 对任意笔记本进行增删改查操作，支持视图筛选与分页
- **🤖 AI 对话** — 集成 LLM 的智能对话与工具调用（查询/添加/更新/删除条目）
- **🔑 Token 管理** — API 密钥的创建、更新、删除与 Shortcut 快捷兑换
- **🛡️ 权限管理** — 基于 View 的细粒度读写权限控制
- **👁️ 视图管理** — 保存/加载自定义查询视图
- **🔍 筛选管理** — 保存/加载自定义筛选条件
- **💾 数据库管理** — 初始化、备份、恢复、重置

## 鉴权方式

所有 API（除 `POST {API_PREFIX}/tokens/exchange` 和 `/docs` 外）需要在 HTTP 头中携带 `Authorization: Bearer Token`。

- **ROOT_TOKEN**：超级管理员权限，在 `.env` 文件中设置
- **普通 Token**：通过 `POST {API_PREFIX}/tokens` 创建，可绑定不同权限级别

## 数据模型

- **笔记本（Notebook）**：由代码注册的动态表，无固定 Schema
- **系统表**：`_token`（令牌）、`_permission`（权限）、`_view`（视图）、`_filter`（筛选）
""",
    summary="XFunNote 无模式笔记系统 API",
    version=VERSION,
    contact={
        "name": "FangJunyi0710",
        "url": "https://github.com/FangJunyi0710",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
    lifespan=lifespan,
    docs_url="/docs" if SHOW_DOCS else None,
    redoc_url="/redoc" if SHOW_DOCS else None,
    openapi_url="/openapi.json" if SHOW_DOCS else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[], # 禁止所有跨域访问
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


@app.exception_handler(sqlite3.IntegrityError)
async def integrity_error_handler(request: Request, exc: sqlite3.IntegrityError):
    """SQLite IntegrityError 处理器：UNIQUE 冲突 → 409，NOT NULL 冲突 → 422。"""
    error_msg = str(exc)
    if "UNIQUE constraint failed" in error_msg:
        status_code = status.HTTP_409_CONFLICT
        detail = f"数据已存在: {error_msg}"
    elif "NOT NULL constraint failed" in error_msg:
        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
        detail = f"缺少必填字段: {error_msg}"
    else:
        status_code = status.HTTP_400_BAD_REQUEST
        detail = f"数据完整性错误: {error_msg}"
    return JSONResponse(
        status_code=status_code,
        content={"error": http.HTTPStatus(status_code).phrase, "detail": detail},
    )


@app.exception_handler(XFunError)
async def xfun_error_handler(request: Request, exc: XFunError):
    """XFunError 处理器：将领域异常转为 422，保留错误消息。"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": http.HTTPStatus(422).phrase,
            "detail": f"请求参数校验失败：{errors}",
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """兜底处理器：防止未捕获异常泄漏内部信息。"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": http.HTTPStatus(500).phrase},
    )


app.include_router(notebooks.router, prefix=API_PREFIX)
app.include_router(ai.router, prefix=API_PREFIX)
app.include_router(manage_db.router, prefix=API_PREFIX)
app.include_router(manage_view.router, prefix=API_PREFIX)
app.include_router(manage_token.router, prefix=API_PREFIX)
app.include_router(manage_permission.router, prefix=API_PREFIX)
app.include_router(manage_filter.router, prefix=API_PREFIX)

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=BACKEND_PORT,
        reload=UVICORN_RELOAD,
    )

# TODO 前端在权限被拒时根据 ops 返回值提示
# TODO 增加导入导出功能
# TODO 实现完整的 filter 编辑器
# TODO 前端实现真正的视图筛选
# TODO 添加流式返回 AI 结果的路由及前端支持
# TODO 前端分各个本子做精致的数据呈现：点击本子进入仪表盘页面，再点击进入条目列表页面
# TODO 前端 AI 对话添加历史对话、Agent选择与编辑等页面
# TODO 前端添加排序设置页面
# TODO 前端添加 .env 编辑管理页面
# TODO Docker 化方案与快速部署 Termux 到手机、apk 打包等
# TODO QQ 机器人推送与定时任务：自动定期备份等
# TODO pyproject.toml 内容很少（缺少项目元数据、依赖声明等）
# TODO CI/CD 配置
# TODO 前端选择时应提供筛选出仅选择条目的视图便于更好呈现
# TODO 提供获取预定义 permission 的接口
# TODO 添加 SSE 事件驱动的后端避免轮询
# TODO 添加前端 shortcut 兑换确认页面，且未被兑换的 token 状态为停用以增强安全
# TODO 部署时注意 HSTS 等安全机制
# TODO 前端编辑条目提供更合适的文本框，带记忆功能。
# TODO 前端增加卡片详情页
# TODO 前端添加操作日志等历史记录
# TODO 支持未来添加虚拟本子临时以本子形态展示数据
# TODO 前端将所有AI相关数据移入AI部分
# TODO 前端添加标签编辑器、AI note等的移入移出等
