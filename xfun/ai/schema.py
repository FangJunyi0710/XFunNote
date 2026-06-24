"""
Pydantic 模型 — 为 Filter / View 生成 JSON Schema，供 AI 精准理解数据格式。

用法::

    from xfun.ai.schema import FilterModel, ViewModel, filter_schema_json
"""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field, RootModel, field_validator

from xfun.core.errors import InvalidConditionError, InvalidFilterError
from xfun.core.filter import Condition, Filter

def _inject_op_enum(schema: dict) -> None:
    """``json_schema_extra`` 钩子：向 ``op`` 字段注入动态枚举值。"""
    ops = list(Condition._op_registry.keys())
    schema["enum"] = ops

# ========== Condition ==========

class ConditionModel(BaseModel):
    """单个筛选条件 — 叶子节点。"""
    column: str = Field(description="列名")
    value: Any = Field(description="值")
    op: str = Field(
        default="=",
        description="运算符。其中 TRUE 和 FALSE 的用法是，将 column 和 value 填入任意占位符后，其返回永真或永假。",
        json_schema_extra=_inject_op_enum,
    )

    model_config = {"extra": "forbid"}

    @field_validator("op")
    @classmethod
    def _check_op(cls, v: str) -> str:
        if v not in Condition._op_registry:
            allowed = sorted(Condition._op_registry.keys())
            raise InvalidConditionError(f"不支持的操作符: {v}，支持: {allowed}")
        return v

    def to_condition(self) -> Condition:
        return Condition(column=self.column, value=self.value, op=self.op)


# ========== Filter (递归) ==========

class FilterModel(RootModel):
    """递归筛选条件 — 嵌套解析并转换为内部 Filter 类型。

    按优先级匹配以下三种形式（``oneOf``）：

    1. **Condition** — 单个条件: ``{"column":"x", "value":"y"}``
    2. **取反包装** — ``[条件/子筛选器, true/false表示是否取反]``
    3. **OR / AND 组合** — ``[[条件组1], [条件组2], ...]``，外层 OR 内层 AND 的 DNF 析取范式
    """

    root: ConditionModel | tuple["FilterModel", bool] | list[list["FilterModel"]] 

    def to_filter(self) -> Filter:
        """转换为内部 ``Filter`` 类型（用于 SQL 生成）。"""
        return _resolve_filter(self.root)


def _resolve_filter(val: Any) -> Filter:
    """递归将 Pydantic 模型值转换为内部 Filter。"""
    if isinstance(val, ConditionModel):
        return val.to_condition()
    if isinstance(val, tuple) and len(val) == 2 and isinstance(val[1], bool):
        inner, negate = val
        return (_resolve_filter(inner), negate)
    if isinstance(val, list):
        # 外层 list → OR，内层 list → AND
        return [[_resolve_filter(item) for item in group] for group in val]
    raise InvalidFilterError(val)


FilterModel.model_rebuild()


# ========== View ==========

class TableSpecModel(BaseModel):
    """单组查询规格：(列名列表, 筛选条件)"""
    columns: list[str] = Field(description="要查询的列名列表")
    filter: FilterModel = Field(description="行筛选条件")

    model_config = {"extra": "forbid"}


class ViewModel(RootModel):
    """查询视图 — ``{表名: [TableSpec, ...]}``，多组间 OR 关系。"""
    root: dict[str, list[TableSpecModel]]

    def to_view(self) -> dict[str, list[tuple[list[str], Filter]]]:
        """转换为内部 ``View`` 类型。"""
        result: dict[str, list[tuple[list[str], Filter]]] = {}
        for table, specs in self.root.items():
            result[table] = [(s.columns, s.filter.to_filter()) for s in specs]
        return result


# ========== JSON Schema 生成（供 prompt 嵌入） ==========

def filter_schema_json() -> dict:
    """返回 Filter 的 JSON Schema 字典。"""
    return FilterModel.model_json_schema()


def view_schema_json() -> dict:
    """返回 View 的 JSON Schema 字典。"""
    return ViewModel.model_json_schema()


# ========== 校验 + 解析（供 tools.py 使用） ==========

def parse_and_validate_view(view_json_str: str) -> dict[str, Any]:
    """校验并解析 View JSON → 内部 View 格式。

    Returns
    -------
    dict
        可直接作为 ``View`` 使用的 ``{表名: [(列列表, Filter), ...]}``。

    Raises
    ------
    pydantic.ValidationError
        JSON 不符合 ViewModel 定义时抛出。
    """
    model = ViewModel.model_validate_json(view_json_str)
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
