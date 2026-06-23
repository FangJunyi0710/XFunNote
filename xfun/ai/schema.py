"""
Pydantic 模型 — 为 Filter / View 生成 JSON Schema，供 AI 精准理解数据格式。

用法::

    from xfun.ai.schema import FilterModel, ViewSchema, filter_schema_text
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Tuple, Union
from pydantic import BaseModel, Field, RootModel

from xfun.core.filter import Condition, Filter


# ========== Condition ==========

class ConditionSchema(BaseModel):
    """单个筛选条件 — 叶子节点。"""
    column: str = Field(description="列名")
    value: Any = Field(default=None, description="值（IN / BETWEEN 时为列表）")
    op: str = Field(
        default="=",
        description="运算符: =, !=, >, <, >=, <=, LIKE, NOT LIKE, IN, NOT IN, BETWEEN",
    )

    model_config = {"extra": "forbid"}

    def to_condition(self) -> Condition:
        return Condition(column=self.column, value=self.value, op=self.op)


# ========== Filter (递归) ==========

class FilterModel(RootModel):
    """递归筛选条件 — 嵌套解析并转换为内部 Filter 类型。

    按优先级匹配以下三种形式（``oneOf``）：

    1. **Condtion** — 单个条件: ``{"column":"x", "value":"y"}``
    2. **取反包装** — ``[条件/子筛选器, true/false]``
    3. **OR / AND 组合** — ``[[条件组1], [条件组2], ...]``，外层 OR 内层 AND
    """

    root: Union[
        ConditionSchema,
        Tuple["FilterModel", bool],
        List[List["FilterModel"]],
    ]

    def to_filter(self) -> Filter:
        """转换为内部 ``Filter`` 类型（用于 SQL 生成）。"""
        return _resolve_filter(self.root)


def _resolve_filter(val: Any) -> Filter:
    """递归将 Pydantic 模型值转换为内部 Filter。"""
    if isinstance(val, ConditionSchema):
        return val.to_condition()
    if isinstance(val, tuple) and len(val) == 2 and isinstance(val[1], bool):
        inner, negate = val
        return (_resolve_filter(inner), negate)
    if isinstance(val, list):
        # 外层 list → OR，内层 list → AND
        return [[_resolve_filter(item) for item in group] for group in val]
    raise ValueError(f"无法识别的 Filter 结构: {type(val)}")


FilterModel.model_rebuild()


# ========== View ==========

class TableSpecSchema(BaseModel):
    """单组查询规格：(列名列表, 筛选条件)"""
    columns: List[str] = Field(description="要查询的列名列表")
    filter: FilterModel = Field(description="行筛选条件")

    model_config = {"extra": "forbid"}


class ViewSchema(RootModel):
    """查询视图 — ``{表名: [TableSpec, ...]}``，多组间 OR 关系。"""
    root: Dict[str, List[TableSpecSchema]]

    def to_view(self) -> Dict[str, List[Tuple[List[str], Filter]]]:
        """转换为内部 ``View`` 类型。"""
        result: Dict[str, List[Tuple[List[str], Filter]]] = {}
        for table, specs in self.root.items():
            result[table] = [(s.columns, s.filter.to_filter()) for s in specs]
        return result


# ========== JSON Schema 生成（供 prompt 嵌入） ==========

def filter_schema_text() -> str:
    """返回 Filter 的完整 JSON Schema 文本。"""
    schema = FilterModel.model_json_schema()
    return json.dumps(schema, indent=2, ensure_ascii=False)


def view_schema_text() -> str:
    """返回 View 的完整 JSON Schema 文本。"""
    schema = ViewSchema.model_json_schema()
    return json.dumps(schema, indent=2, ensure_ascii=False)


# ========== 校验 + 解析（供 tools.py 使用） ==========

def parse_and_validate_view(view_json_str: str) -> Dict[str, Any]:
    """校验并解析 View JSON → 内部 View 格式。

    Returns
    -------
    dict
        可直接作为 ``View`` 使用的 ``{表名: [(列列表, Filter), ...]}``。

    Raises
    ------
    pydantic.ValidationError
        JSON 不符合 ViewSchema 定义时抛出。
    """
    model = ViewSchema.model_validate_json(view_json_str)
    return model.to_view()


def parse_and_validate_filter(filter_json_str: str) -> Filter:
    """校验并解析 Filter JSON → 内部 Filter。

    Raises
    ------
    pydantic.ValidationError
        JSON 不符合 FilterModel 定义时抛出。
    """
    model = FilterModel.model_validate_json(filter_json_str)
    return model.to_filter()


# ========== 便捷校验（仅测试/调试用） ==========

def validate_filter_json(json_str: str) -> bool:
    """返回 True / False，不抛异常。"""
    try:
        FilterModel.model_validate_json(json_str)
        return True
    except Exception:
        return False


def validate_view_json(json_str: str) -> bool:
    """返回 True / False，不抛异常。"""
    try:
        ViewSchema.model_validate_json(json_str)
        return True
    except Exception:
        return False
