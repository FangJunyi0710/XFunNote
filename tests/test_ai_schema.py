"""测试 AI Schema：ConditionModel / FilterModel / ViewModel 的 Pydantic 校验与转换。"""

import json

import pytest
from pydantic import ValidationError
from xfun.core.errors import InvalidFilterError
from xfun.core.filter import Condition

# 加载 extras.py 注册的自定义运算符（TRUE, FALSE, JSON_CONTAINS, TEXT_SEARCH）
import xfun.core.extras  # noqa: F401

from xfun.ai.schema import (  # isort:skip
    ConditionModel,
    FilterModel,
    ViewModel,
    _resolve_filter,
    filter_schema_json,
    view_schema_json,
    parse_and_validate_view,
    parse_and_validate_filter,
)


class TestConditionModel:
    """ConditionModel — 单条件 Pydantic 模型。"""

    def test_basic(self):
        m = ConditionModel(column="content", value="hello")
        assert m.column == "content"
        assert m.value == "hello"
        assert m.op == "="

    def test_with_op(self):
        m = ConditionModel(column="age", value=18, op=">")
        assert m.op == ">"

    def test_to_condition(self):
        m = ConditionModel(column="tags", value=["a", "b"], op="IN")
        c = m.to_condition()
        assert isinstance(c, Condition)
        assert c.column == "tags"
        assert c.value == ["a", "b"]
        assert c.op == "IN"

    def test_invalid_op_raises(self):
        with pytest.raises(ValidationError, match="不支持的操作符"):
            ConditionModel(column="a", value=1, op="NOT_AN_OP")

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ConditionModel(column="a", value=1, unknown_field="x")

    def test_json_schema_contains_enum(self):
        schema = ConditionModel.model_json_schema()
        op_props = schema.get("properties", {}).get("op", {})
        assert "enum" in op_props
        assert "=" in op_props["enum"]
        assert ">" in op_props["enum"]
        assert "TRUE" in op_props["enum"]


class TestFilterModel:
    """FilterModel — 递归筛选条件。"""

    def test_single_condition(self):
        fm = FilterModel.model_validate({"column": "a", "value": 1})
        f = fm.to_filter()
        assert f == Condition("a", 1)

    def test_negate_tuple(self):
        fm = FilterModel.model_validate([{"column": "a", "value": 1}, True])
        f = fm.to_filter()
        assert f == (Condition("a", 1), True)

    def test_negate_false(self):
        fm = FilterModel.model_validate([{"column": "b", "value": 2}, False])
        f = fm.to_filter()
        assert f == (Condition("b", 2), False)

    def test_or_of_ands(self):
        fm = FilterModel.model_validate([
            [{"column": "a", "value": 1}],
            [{"column": "b", "value": 2}],
        ])
        f = fm.to_filter()
        assert f == [[Condition("a", 1)], [Condition("b", 2)]]

    def test_nested_in_and(self):
        fm = FilterModel.model_validate([
            [
                {"column": "a", "value": 1},
                [[{"column": "b", "value": 2}], [{"column": "c", "value": 3}]],
            ],
        ])
        f = fm.to_filter()
        assert f == [[
            Condition("a", 1),
            [[Condition("b", 2)], [Condition("c", 3)]],
        ]]

    def test_invalid_op_nested(self):
        with pytest.raises(ValidationError):
            FilterModel.model_validate([{"column": "x", "value": 1, "op": "BAD_OP"}])

    def test_empty_or(self):
        fm = FilterModel.model_validate([])
        assert fm.to_filter() == []

    def test_non_list_root_is_rejected(self):
        with pytest.raises(ValidationError):
            FilterModel.model_validate("string")


class TestResolveFilter:
    """_resolve_filter 直接调用。"""

    def test_condition_model(self):
        m = ConditionModel(column="x", value=10)
        assert _resolve_filter(m) == Condition("x", 10)

    def test_negate_tuple(self):
        inner = ConditionModel(column="x", value=1)
        assert _resolve_filter((inner, True)) == (Condition("x", 1), True)

    def test_nested_list(self):
        a = ConditionModel(column="a", value=1)
        b = ConditionModel(column="b", value=2)
        assert _resolve_filter([[a], [b]]) == [[Condition("a", 1)], [Condition("b", 2)]]

    def test_invalid_type_raises(self):
        with pytest.raises(InvalidFilterError):
            _resolve_filter(42)

    def test_invalid_tuple_raises(self):
        """元组但第二个元素不是 bool 应由 Pydantic 拦截，但直接传任意类型会触发 InvalidFilterError。"""
        # _resolve_filter 是按顺序检查的，三元组不匹配任何分支
        with pytest.raises(InvalidFilterError):
            _resolve_filter((ConditionModel(column="a", value=1), "not_bool"))


class TestViewModel:
    """ViewModel — 查询视图。"""

    def test_basic(self):
        vm = ViewModel.model_validate({
            "plan": [
                {
                    "columns": ["content", "month"],
                    "filter": {"column": "month", "value": "2606"},
                },
            ],
        })
        v = vm.to_view()
        assert "plan" in v
        assert len(v["plan"]) == 1
        cols, flt = v["plan"][0]
        assert cols == ["content", "month"]
        assert flt == Condition("month", "2606")

    def test_multiple_tables(self):
        vm = ViewModel.model_validate({
            "plan": [
                {"columns": ["content"], "filter": {"column": "done", "value": 0}},
            ],
            "diary": [
                {"columns": ["date", "mood"], "filter": {"column": "date", "value": "2026-06-24"}},
            ],
        })
        v = vm.to_view()
        assert set(v.keys()) == {"plan", "diary"}

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ViewModel.model_validate({
                "plan": [
                    {"columns": ["content"], "filter": {"column": "a", "value": 1}, "extra": "x"},
                ],
            })


class TestSchemaJson:
    """filter_schema_json / view_schema_json。"""

    def test_filter_schema_json_is_dict(self):
        schema = filter_schema_json()
        assert isinstance(schema, dict)
        assert "$defs" in schema or "$ref" in schema or "anyOf" in schema

    def test_view_schema_json_is_dict(self):
        schema = view_schema_json()
        assert isinstance(schema, dict)

    def test_filter_schema_has_op_enum(self):
        """Filter 的 JSON Schema 中 op 字段应有 enum。"""
        schema_json_str = json.dumps(filter_schema_json(), ensure_ascii=False)
        assert "TRUE" in schema_json_str
        assert "FALSE" in schema_json_str
        assert "IN" in schema_json_str


class TestParseAndValidate:
    """parse_and_validate_view / parse_and_validate_filter 集成测试。"""

    def test_validate_view_valid(self):
        v = parse_and_validate_view(
            '{"plan": [{"columns": ["content"], "filter": {"column": "done", "value": 1}}]}'
        )
        assert "plan" in v
        cols, flt = v["plan"][0]
        assert cols == ["content"]
        assert flt == Condition("done", 1)

    def test_validate_view_invalid_json(self):
        with pytest.raises(ValidationError):
            parse_and_validate_view(
                '{"plan": [{"columns": ["content"], "filter": {"column": "done", "op": "BAD"}}]}'
            )

    def test_validate_filter_valid(self):
        f = parse_and_validate_filter(
            '{"column": "content", "value": "hello", "op": "LIKE"}'
        )
        assert f == Condition("content", "hello", "LIKE")

    def test_validate_filter_invalid_op(self):
        with pytest.raises(ValidationError):
            parse_and_validate_filter(
                '{"column": "x", "value": 1, "op": "NO_SUCH_OP"}'
            )
