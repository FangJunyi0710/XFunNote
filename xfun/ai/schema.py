"""
Pydantic 模型 — 为 Filter / View 生成 JSON Schema，供 AI 精准理解数据格式。

用法::

    from xfun.ai.schema import FilterModel, ViewModel, filter_schema_json
"""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field, RootModel, field_validator

from xfun.core.errors import FilterInvalidError
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
            raise ValueError(f"不支持的操作符: {v}，支持: {allowed}")
        return v

    def to_condition(self) -> Condition:
        return Condition(column=self.column, value=self.value, op=self.op)


# ========== Filter (递归) ==========

class FilterModel(RootModel):
    """
    筛选条件 — 两层列表（DNF 析取范式）。
    - 外层 = OR（并集），内层 = AND（交集）。
    - 取反：`[子Filter, true]`。

    格式对照：
    | 意图 | 正确写法 | 错误写法 |
    |---|---|---|
    | A 且 B | `[[condA, condB]]` | `[condA, condB]`（结构错误，解析会失败） |
    | A 或 B | `[[condA], [condB]]` | `[[condA, condB]]`（这是且） |
    
    ⚠️ 区分取反与组合：
    - 取反：`[cond, true]`（一层，第二个元素是布尔值）
    - 组合：`[[cond1, cond2], [...], ...]`（两层列表，基本元素是 cond）

    嵌套示例：`[[condA, [condB, true]]]` 表示 (A) 且 (非 B)。

    其中上述所有 condA 等均可以是任意 Filter 结构，支持嵌套组合。
    若解析失败，请检查层数是否匹配上述示例。
    """

    root: ConditionModel | tuple["FilterModel", bool] | list[list["FilterModel"]] 

    def to_filter(self) -> Filter:
        """转换为内部 ``Filter`` 类型（用于 SQL 生成）。"""
        return _resolve_filter(self.root)


def _resolve_filter(val: Any) -> Filter:
    """递归将 Pydantic 模型值转换为内部 Filter。"""
    if isinstance(val, ConditionModel):
        return val.to_condition()
    if isinstance(val, FilterModel):
        return _resolve_filter(val.root)
    if isinstance(val, tuple) and len(val) == 2 and isinstance(val[1], bool):
        inner, negate = val
        return (_resolve_filter(inner), negate)
    if isinstance(val, list):
        # 外层 list → OR，内层 list → AND
        return [[_resolve_filter(item) for item in group] for group in val]
    raise FilterInvalidError(val)


FilterModel.model_rebuild()


# ========== View ==========

class TableSpecModel(BaseModel):
    """单组查询规格：(列名列表, 筛选条件)"""
    columns: list[str] = Field(description="要查询的列名列表")
    filter: FilterModel = Field(description="行筛选条件")

    model_config = {"extra": "forbid"}


class ViewModel(RootModel):
    """
    查询视图：`{表名: [TableSpec, ...]}`。
    - 列表内各 TableSpec 为 **OR** 关系（并集），不可嵌套。
    - 例：`{"plan": [spec1, spec2]}` 表示查询计划表中满足 spec1 **或** spec2 的条目。
    """
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
