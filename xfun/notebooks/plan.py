#!/usr/bin/env python3
# xfun/notebooks/plan.py — 计划本
"""
plan 本：以月份为分组，管理待办事项 / 目标条目。

每条记录包含：
- id        : 主键
- month     : 所属月份，如 "2606"
- content   : 事项内容
- done      : 是否完成
- created_at: 创建时间
"""

from typing import Any, Dict, List, Optional

from ..core.db import Column, Filter
from ..core.notebook import Notebook
from ..core.errors import EntryInvalidError


class PlanNotebook(Notebook):
    name    = "plan"
    columns = [
        Column("id",         "TEXT",    primary_key=True),
        Column("month",      "TEXT",    nullable=False, index=True),
        Column("content",    "TEXT",    nullable=False),
        Column("done",       "INTEGER", default=0),
        Column("created_at", "TEXT",    nullable=False),
    ]

    # ---- CRUD ----

    def add(self, entry: Dict[str, Any]) -> str:
        self._validate(entry)
        # TODO: db.insert(...) — 等 DB 实现后补上
        # 当前返回占位
        raise NotImplementedError("DB 尚未实现")

    def list(self, filters: List[Filter], *,
             order_by: Optional[str] = None,
             limit: int = 50,
             offset: int = 0) -> List[Dict[str, Any]]:
        if not filters:
            raise ValueError("filters 不能为空")
        # TODO: db.select(...) — 等 DB 实现后补上
        raise NotImplementedError("DB 尚未实现")

    def delete(self, entry_id: str) -> bool:
        # TODO: db.delete(...)
        raise NotImplementedError("DB 尚未实现")

    def search(self, query: str, *, limit: int = 50) -> List[Dict[str, Any]]:
        return self.list(
            [Filter("content", f"%{query}%", op="LIKE")],
            limit=limit,
        )

    # ---- 校验 ----

    def _validate(self, entry: Dict[str, Any]) -> None:
        """校验必填字段。"""
        for col in self.columns:
            if not col.nullable and col.name not in entry:
                raise EntryInvalidError(self.name, f"缺少必填字段 '{col.name}'")

    # ---- 摘要 ----

    def summary(self) -> str:
        """供 AI 使用的计划概览。"""
        # TODO: 统计各月 done/总数
        return "[plan] (暂无统计 — DB 尚未实现)"
