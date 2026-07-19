"""测试 Pydantic AI Schema 模型。"""

import json

import pytest
from pydantic import ValidationError

from xfun.ai.schema import (
    ConditionModel,
    FilterModel,
    ViewModel,
    TableSpecModel,
    filter_schema_json,
    view_schema_json,
    parse_and_validate_filter,
    parse_and_validate_view,
    _resolve_filter,
)
from xfun.core.errors import FilterInvalidError, PromptError


class TestConditionModel:
    def test_valid_condition(self):
        m = ConditionModel(column="month", value="2606", op="=")
        c = m.to_condition()
        assert c.column == "month"
        assert c.value == "2606"
        assert c.op == "="

    def test_default_op(self):
        m = ConditionModel(column="a", value=1)
        assert m.op == "="

    def test_invalid_op(self):
        with pytest.raises(ValidationError):
            ConditionModel(column="a", value=1, op="NONEXISTENT")

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            ConditionModel(column="a", value=1, extra_field="x")


class TestFilterModel:
    def test_single_condition(self):
        """RootModel 传值时不套 root 键。"""
        fm = FilterModel.model_validate({"column": "month", "value": "2606"})
        flt = fm.to_filter()
        assert flt.column == "month"

    def test_or_and_combination(self):
        data = [
            [{"column": "a", "value": 1}, {"column": "b", "value": 2}],
            [{"column": "c", "value": 3}],
        ]
        fm = FilterModel.model_validate(data)
        flt = fm.to_filter()
        assert isinstance(flt, list)
        assert len(flt) == 2

    def test_negation_tuple(self):
        data = [{"column": "a", "value": 1}, True]
        fm = FilterModel.model_validate(data)
        flt = fm.to_filter()
        assert isinstance(flt, tuple)
        assert flt[1] is True

    def test_from_json(self):
        s = '{"column": "month", "value": "2606"}'
        flt = parse_and_validate_filter(s)
        assert flt.column == "month"


class TestViewModel:
    def test_valid_view(self):
        data = {
            "plan": [
                {
                    "columns": ["content", "month"],
                    "filter": {"column": "month", "value": "2606"},
                }
            ]
        }
        vm = ViewModel.model_validate(data)
        view = vm.to_view()
        assert "plan" in view
        assert len(view["plan"]) == 1
        cols, flt = view["plan"][0]
        assert "content" in cols
        assert "month" in cols

    def test_view_from_json(self):
        s = json.dumps({
            "plan": [
                {
                    "columns": ["content"],
                    "filter": {"column": "month", "value": "2606"},
                }
            ]
        })
        view = parse_and_validate_view(s)
        assert "plan" in view


class TestSchemaGeneration:
    def test_filter_schema_json(self):
        schema = filter_schema_json()
        assert "$defs" in schema or "$ref" in schema
        schema_str = json.dumps(schema)
        assert "=" in schema_str

    def test_view_schema_json(self):
        schema = view_schema_json()
        assert isinstance(schema, dict)


class TestTableSpecModel:
    def test_valid(self):
        spec = TableSpecModel(
            columns=["content"],
            filter=FilterModel.model_validate({"column": "month", "value": "2606"}),
        )
        assert spec.columns == ["content"]


class TestEdgeCases:
    """覆盖 schema.py + errors.py 剩余分支。"""

    def test_resolve_filter_invalid_value(self):
        """_resolve_filter(42) → FilterInvalidError (schema.py l.78)。"""
        with pytest.raises(FilterInvalidError):
            _resolve_filter(42)

    def test_prompt_error_instantiation(self):
        """PromptError 实例化 (errors.py l.54)。"""
        err = PromptError("测试")
        assert str(err) == "测试"
