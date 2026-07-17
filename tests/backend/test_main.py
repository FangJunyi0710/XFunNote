"""测试 backend/main.py — 异常处理器等未覆盖分支。"""

from __future__ import annotations

import asyncio
import json
import sqlite3

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient


def _run_async(coro):
    """同步运行异步协程（未安装 pytest-asyncio 时的兼容方案）。"""
    return asyncio.run(coro)


class TestLifespan:
    """测试 lifespan context manager（启动 / 关闭）。"""

    def test_lifespan_yield(self, client):
        """请求正常处理证明 lifespan 的 yield 已被触发。"""
        resp = client.get("/api/v0/notebooks")
        assert resp.status_code == 200


class TestIntegrityErrorHandler:
    """测试 integrity_error_handler 的三个分支。"""

    def test_unique_constraint(self):
        """UNIQUE constraint failed → 409。"""
        from fastapi import Request
        from backend.main import integrity_error_handler

        async def _test():
            request = Request({"type": "http", "method": "POST", "path": "/test"})
            exc = sqlite3.IntegrityError("UNIQUE constraint failed: _permission.name")
            response = await integrity_error_handler(request, exc)
            assert response.status_code == status.HTTP_409_CONFLICT
            body = json.loads(response.body)
            assert "数据已存在" in body["detail"]

        _run_async(_test())

    def test_not_null_constraint(self):
        """NOT NULL constraint failed → 422。"""
        from fastapi import Request
        from backend.main import integrity_error_handler

        async def _test():
            request = Request({"type": "http", "method": "POST", "path": "/test"})
            exc = sqlite3.IntegrityError("NOT NULL constraint failed: _permission.name")
            response = await integrity_error_handler(request, exc)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
            body = json.loads(response.body)
            assert "缺少必填字段" in body["detail"]

        _run_async(_test())

    def test_other_integrity_error(self):
        """其他 IntegrityError → 400。"""
        from fastapi import Request
        from backend.main import integrity_error_handler

        async def _test():
            request = Request({"type": "http", "method": "POST", "path": "/test"})
            exc = sqlite3.IntegrityError("FOREIGN KEY constraint failed")
            response = await integrity_error_handler(request, exc)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            body = json.loads(response.body)
            assert "数据完整性错误" in body["detail"]

        _run_async(_test())


class TestUnhandledExceptionHandler:
    """测试全局兜底异常处理器。"""

    def test_unhandled_exception(self):
        """未捕获的 Exception → 500，不暴露内部信息。"""
        from fastapi import Request
        from backend.main import unhandled_exception_handler

        async def _test():
            request = Request({"type": "http", "method": "GET", "path": "/test"})
            exc = RuntimeError("内部错误")
            response = await unhandled_exception_handler(request, exc)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            body = json.loads(response.body)
            assert body["error"] == "Internal Server Error"
            # 不应包含异常详情
            assert "内部错误" not in json.dumps(body)

        _run_async(_test())


class TestHttpExceptionHandler:
    """测试 HTTPException 处理器。"""

    def test_with_detail(self):
        """带 detail 的 HTTPException。"""
        from fastapi import Request
        from backend.main import http_exception_handler

        async def _test():
            request = Request({"type": "http", "method": "GET", "path": "/test"})
            exc = HTTPException(status_code=404, detail="未找到资源")
            response = await http_exception_handler(request, exc)
            assert response.status_code == 404
            body = json.loads(response.body)
            assert body["detail"] == "未找到资源"

        _run_async(_test())

    def test_without_detail(self):
        """不带 detail 的 HTTPException → 使用 status phrase 作为 detail。"""
        from fastapi import Request
        from backend.main import http_exception_handler

        async def _test():
            request = Request({"type": "http", "method": "GET", "path": "/test"})
            exc = HTTPException(status_code=403)
            response = await http_exception_handler(request, exc)
            assert response.status_code == 403
            body = json.loads(response.body)
            # HTTPException 无 detail 时，FastAPI 默认用 status phrase
            assert body["detail"] == "Forbidden"

        _run_async(_test())


class TestRequestValidationErrorHandler:
    """测试 RequestValidationError 处理器。"""

    def test_validation_error_via_client(self, client):
        """通过 client 请求触发 Pydantic 校验失败 → 422 + 结构化 errors。"""
        resp = client.post(
            "/api/v0/notebooks/plan/entries",
            json={"entries": "not-a-list"},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        data = resp.json()
        assert "请求参数校验失败" in data["detail"]
        assert "errors" in data

    def test_validation_error_direct(self):
        """直接调用 validation_exception_handler。"""
        from fastapi import Request
        from fastapi.exceptions import RequestValidationError
        from backend.main import validation_exception_handler

        async def _test():
            request = Request({"type": "http", "method": "POST", "path": "/test"})
            # 构造一个模拟的 ValidationError
            from pydantic import ValidationError
            from pydantic import BaseModel, Field

            class TestModel(BaseModel):
                name: str = Field(min_length=1)

            try:
                TestModel(name="")
            except ValidationError as e:
                exc = RequestValidationError(e.errors())
                response = await validation_exception_handler(request, exc)
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
                body = json.loads(response.body)
                assert "errors" in body
                assert len(body["errors"]) >= 1

        _run_async(_test())
