"""API 客户端：封装所有 backend 接口调用。"""

from __future__ import annotations

import httpx
from typing import Any


class APIClient:
    """XFunNote FastAPI 后端的 HTTP 客户端。"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @staticmethod
    def _handle(response: httpx.Response) -> Any:
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise Exception(f"API 错误 ({response.status_code}): {detail}")
        return response.json()

    # ==================== 本子 CRUD ====================

    def list_notebooks(self) -> list[str]:
        with httpx.Client(timeout=30) as client:
            return self._handle(client.get(self._url("/api/v1/notebooks")))

    def get_schema(self, notetype: str) -> list[dict]:
        with httpx.Client(timeout=30) as client:
            return self._handle(
                client.get(self._url(f"/api/v1/notebooks/{notetype}/schema"))
            )

    def query_entries(
        self,
        notetype: str,
        view: str | None = None,
        order_by: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        params: dict[str, Any] = {
            "order_by": order_by,
            "limit": limit,
            "offset": offset,
        }
        if view:
            params["view"] = view
        with httpx.Client(timeout=60) as client:
            return self._handle(
                client.get(
                    self._url(f"/api/v1/notebooks/{notetype}/entries"),
                    params=params,
                )
            )

    def add_entries(self, notetype: str, entries: list[dict]) -> dict:
        with httpx.Client(timeout=60) as client:
            return self._handle(
                client.post(
                    self._url(f"/api/v1/notebooks/{notetype}/entries"),
                    json={"entries": entries},
                )
            )

    def update_entries(
        self, notetype: str, filter_obj: Any, values: dict
    ) -> dict:
        with httpx.Client(timeout=60) as client:
            return self._handle(
                client.put(
                    self._url(f"/api/v1/notebooks/{notetype}/entries"),
                    json={"filter": filter_obj, "values": values},
                )
            )

    def preview_delete(self, notetype: str, filter_obj: Any) -> dict:
        with httpx.Client(timeout=60) as client:
            return self._handle(
                client.post(
                    self._url(
                        f"/api/v1/notebooks/{notetype}/entries/preview-delete"
                    ),
                    json={"filter": filter_obj, "confirm": False},
                )
            )

    def delete_entries(self, notetype: str, filter_obj: Any) -> dict:
        with httpx.Client(timeout=60) as client:
            return self._handle(
                client.request(
                    "DELETE",
                    self._url(f"/api/v1/notebooks/{notetype}/entries"),
                    json={"filter": filter_obj, "confirm": True},
                )
            )

    # ==================== AI ====================

    def ai_chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        max_iterations: int = 10,
        llm_kwargs: dict | None = None,
    ) -> dict:
        with httpx.Client(timeout=300) as client:
            body: dict[str, Any] = {
                "messages": messages,
                "max_iterations": max_iterations,
            }
            if system_prompt:
                body["system_prompt"] = system_prompt
            if llm_kwargs:
                body["llm_kwargs"] = llm_kwargs
            return self._handle(
                client.post(self._url("/api/v1/ai/chat"), json=body)
            )

    def ai_permission(self) -> dict:
        with httpx.Client(timeout=30) as client:
            return self._handle(
                client.get(self._url("/api/v1/ai/permission"))
            )

    # ==================== 视图管理 ====================

    def list_views(self) -> list[dict]:
        with httpx.Client(timeout=30) as client:
            return self._handle(client.get(self._url("/api/v1/views")))

    def get_view(self, name: str) -> dict | None:
        with httpx.Client(timeout=30) as client:
            resp = client.get(self._url(f"/api/v1/views/{name}"))
            if resp.status_code == 404:
                return None
            return self._handle(resp)

    def save_view(self, name: str, data: dict) -> dict:
        with httpx.Client(timeout=30) as client:
            return self._handle(
                client.put(self._url(f"/api/v1/views/{name}"), json=data)
            )

    def delete_view(self, name: str) -> dict:
        with httpx.Client(timeout=30) as client:
            return self._handle(
                client.delete(self._url(f"/api/v1/views/{name}"))
            )

    # ==================== 数据库管理 ====================

    def init_db(self) -> dict:
        with httpx.Client(timeout=60) as client:
            return self._handle(client.post(self._url("/api/v1/db/init")))

    def backup_db(self) -> dict:
        with httpx.Client(timeout=60) as client:
            return self._handle(client.post(self._url("/api/v1/db/backup")))

    def reset_db(self, backup_first: bool = True) -> dict:
        with httpx.Client(timeout=60) as client:
            return self._handle(
                client.post(
                    self._url("/api/v1/db/reset"),
                    json={"backup_first": backup_first},
                )
            )


def get_client() -> APIClient:
    """从 session_state 获取 API 客户端实例。"""
    import streamlit as st

    base_url = st.session_state.get("global_api_base_url", "http://localhost:8000")
    return APIClient(base_url)
