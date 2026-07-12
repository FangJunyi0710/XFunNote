"""请求/响应模型的 Pydantic Schema。"""

from __future__ import annotations
from typing import Any

from pydantic import BaseModel, Field


# ===== 通用 =====

class ErrorResponse(BaseModel):
    error: str = Field(description="错误信息")


class SuccessResponse(BaseModel):
    message: str = Field(description="操作结果信息")


# ===== 本子 CRUD =====

class EntryCreate(BaseModel):
    """添加条目请求体。"""
    entries: list[dict[str, Any]] = Field(
        description="条目列表，每个元素为字段名到值的映射",
        min_length=1,
    )


class EntryUpdate(BaseModel):
    """更新条目请求体。"""
    filter: Any = Field(description="筛选条件，Filter JSON 格式")
    values: dict[str, Any] = Field(
        description="要更新的字段值字典",
        min_length=1,
    )


class EntryDelete(BaseModel):
    """删除条目请求体。"""
    filter: Any = Field(description="筛选条件，Filter JSON 格式")


class EntryBatchResponse(BaseModel):
    """批量操作返回。"""
    count: int = Field(description="影响的条目数")
    results: list[dict[str, Any]] = Field(description="条目详情列表")
