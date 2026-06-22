"""测试筛选逻辑：Condition 运算符、filter_to_sql 递归 AND/OR 组合、自定义运算符注册、parse_filter_json。"""

import json

import pytest
from xfun.core.filter import Condition, filter_to_sql, parse_filter_json
from xfun.core.errors import InvalidConditionError, InvalidSQLError


class TestConditionSqlGeneration:
    """核心：条件 → SQL 片段的转换是否正确。"""

    def test_basic_comparison(self):
        sql, params = Condition("col", "val", "=").to_sql()
        assert sql == "col = ?" and params == ["val"]

    def test_null_handling(self):
        sql, params = Condition("col", None, "=").to_sql()
        assert sql == "col IS NULL" and params == []

    def test_not_null(self):
        sql, params = Condition("col", None, "!=").to_sql()
        assert sql == "col IS NOT NULL" and params == []

    def test_in_list(self):
        sql, params = Condition("col", ["a", "b"], "IN").to_sql()
        assert sql == "col IN (?, ?)" and params == ["a", "b"]

    def test_between(self):
        sql, params = Condition("col", [1, 10], "BETWEEN").to_sql()
        assert sql == "col BETWEEN ? AND ?" and params == [1, 10]

    def test_like(self):
        sql, params = Condition("col", "%test%", "LIKE").to_sql()
        assert sql == "col LIKE ?" and params == ["%test%"]


class TestConditionEdgeCases:
    """边界：非法输入应有的保护。"""

    def test_null_with_non_null_op_raises(self):
        with pytest.raises(InvalidConditionError):
            Condition("col", None, ">").to_sql()

    def test_empty_in_is_false(self):
        """空 IN 列表应生成 1=0（永假）。"""
        sql, params = Condition("col", [], "IN").to_sql()
        assert sql == "1=0" and params == []

    def test_empty_not_in_is_true(self):
        """空 NOT IN 列表应生成 1=1（永真）。"""
        sql, params = Condition("col", [], "NOT IN").to_sql()
        assert sql == "1=1" and params == []

    def test_non_list_in_raises(self):
        with pytest.raises(InvalidConditionError):
            Condition("col", "not_a_list", "IN").to_sql()

    def test_unknown_op_raises(self):
        with pytest.raises(InvalidConditionError):
            Condition("col", "val", "UNKNOWN_OP").to_sql()

    def test_invalid_column_name_raises(self):
        with pytest.raises(InvalidSQLError):
            Condition("bad col", "val").to_sql()


class TestToSql:
    """核心：Filter → WHERE 子句是否正确。"""

    def test_empty(self):
        assert filter_to_sql([]) == ("", [])

    def test_and_group(self):
        sql, params = filter_to_sql([[Condition("a", 1), Condition("b", 2)]])
        assert "(a = ?) AND (b = ?)" in sql
        assert params == [1, 2]

    def test_or_of_ands(self):
        sql, params = filter_to_sql([
            [Condition("a", 1)],
            [Condition("b", 2)],
        ])
        assert sql.count("OR") == 1
        assert params == [1, 2]

    def test_null_in_filter(self):
        sql, params = filter_to_sql([[Condition("ai_note", None, "=")]])
        assert "IS NULL" in sql

    # ---- 嵌套子 Filter ----

    def test_nested_filter_in_and(self):
        """子 Filter（含多 OR 组）在 AND 组内应被括号包裹保护优先级。"""
        sql, params = filter_to_sql([
            [Condition("a", 1), [[Condition("b", 2)], [Condition("c", 3)]]],
        ])
        assert "((b = ?)) OR ((c = ?))" in sql
        assert params == [1, 2, 3]

    def test_nested_filter_single_and(self):
        """子 Filter 只有一组 AND。"""
        sql, params = filter_to_sql([
            [Condition("a", 1), [[Condition("b", 2), Condition("c", 3)]]],
        ])
        assert params == [1, 2, 3]

    def test_deeply_nested(self):
        """多层嵌套 Filter。"""
        sql, params = filter_to_sql([
            [Condition("a", 1), [[Condition("b", 2), [[Condition("c", 3)]]]]],
        ])
        assert params == [1, 2, 3]

    # ---- 最外层取反元组 ----

    def test_negate_outer_true(self):
        """最外层 (Filter, True) 包裹 NOT。"""
        sql, params = filter_to_sql(([[Condition("a", 1)]], True))
        assert sql.startswith("NOT ")
        assert params == [1]

    def test_negate_outer_false(self):
        """最外层 (Filter, False) 不取反。"""
        sql, params = filter_to_sql(([[Condition("a", 1)]], False))
        assert not sql.startswith("NOT ")
        assert params == [1]

    def test_negate_with_nested_filter(self):
        """取反 + 嵌套子 Filter 组合。"""
        sql, params = filter_to_sql(([
            [Condition("a", 1), [[Condition("b", 2)], [Condition("c", 3)]]],
        ], True))
        assert sql.startswith("NOT ")
        assert "((b = ?)) OR ((c = ?))" in sql
        assert params == [1, 2, 3]

    def test_negate_deeply_nested(self):
        """取反 + 多层嵌套。"""
        sql, params = filter_to_sql(([
            [Condition("a", 1), [[Condition("b", 2), [[Condition("c", 3)]]]]],
        ], True))
        assert sql.startswith("NOT ")
        assert params == [1, 2, 3]

    def test_negate_empty_returns_empty(self):
        """([], True) → clause 为空，直接返回 ("", [])。"""
        sql, params = filter_to_sql(([], True))
        assert sql == "" and params == []

    def test_negate_or_group(self):
        """取反一组 OR 条件。"""
        sql, params = filter_to_sql(([
            [Condition("a", 1)],
            [Condition("b", 2)],
        ], True))
        assert sql.startswith("NOT ")
        assert sql.count("OR") == 1
        assert params == [1, 2]


class TestBetweenEdgeCases:
    """BETWEEN 运算符的边界。"""

    def test_between_none_value_raises(self):
        """[None, 10] → 1=0。"""
        sql, params = Condition("col", [None, 10], "BETWEEN").to_sql()
        assert sql == "1=0" and params == []

    def test_between_partial_none_raises(self):
        """[None, None] → 1=0。"""
        sql, params = Condition("col", [None, None], "BETWEEN").to_sql()
        assert sql == "1=0" and params == []

    def test_between_wrong_length_raises(self):
        """长度不为 2 仍应抛异常。"""
        with pytest.raises(InvalidConditionError):
            Condition("col", [1, 2, 3], "BETWEEN").to_sql()

    def test_between_non_list_raises(self):
        """非列表类型仍应抛异常。"""
        with pytest.raises(InvalidConditionError):
            Condition("col", "not_a_list", "BETWEEN").to_sql()


class TestToSqlEdgeCases:
    """to_sql 边界情况。"""

    def test_empty_group_skipped(self):
        sql, params = filter_to_sql([[]])
        assert sql == "" and params == []

    def test_mixed_empty_and_normal(self):
        sql, params = filter_to_sql([
            [Condition("a", 1)],
            [],
        ])
        assert "(a = ?)" in sql and params == [1]

    def test_nested_empty_filter(self):
        """内层空 Filter 不贡献 AND 子句。"""
        sql, params = filter_to_sql([[Condition("a", 1), []]])
        assert "(a = ?)" in sql and params == [1]


class TestCustomOperator:
    """验证运算符注册机制可用。"""

    def test_register_and_use(self):
        @Condition.register_op("@>")
        def handler(col, val, op):
            return f"{col} @> ?", [val]
        try:
            sql, _ = Condition("tags", "keyword", "@>").to_sql()
            assert sql == "tags @> ?"
        finally:
            Condition._op_registry.pop("@>", None)


class TestParseFilterJson:
    """parse_filter_json: JSON → Filter 结构的正确转换。"""

    def test_single_condition(self):
        f = parse_filter_json('[[{"column": "a", "value": 1, "op": "="}]]')
        assert f == [[Condition("a", 1, "=")]]

    def test_default_op(self):
        f = parse_filter_json('[[{"column": "a", "value": 1}]]')
        assert f == [[Condition("a", 1)]]

    def test_and_group(self):
        f = parse_filter_json('''[[
            {"column": "a", "value": 1},
            {"column": "b", "value": 2}
        ]]''')
        assert f == [[Condition("a", 1), Condition("b", 2)]]

    def test_or_of_ands(self):
        f = parse_filter_json('''[
            [{"column": "a", "value": 1}],
            [{"column": "b", "value": 2}]
        ]''')
        assert f == [[Condition("a", 1)], [Condition("b", 2)]]

    def test_negate_tuple_in_and(self):
        f = parse_filter_json('''[[
            [{"column": "a", "value": 1}, true]
        ]]''')
        assert f == [[(Condition("a", 1), True)]]

    def test_negate_false_in_and(self):
        """negate=False 的元组对应 JSON 的 false。"""
        f = parse_filter_json('''[[
            [{"column": "b", "value": 2}, false]
        ]]''')
        assert f == [[(Condition("b", 2), False)]]

    def test_outer_negate_tuple(self):
        """顶层取反：([[cond]], True) 由 [[[cond]], true] 表示。"""
        f = parse_filter_json('[[[{"column": "a", "value": 1}]], true]')
        assert f == ([[Condition("a", 1)]], True)

    def test_outer_negate_empty(self):
        f = parse_filter_json('[[], true]')
        assert f == ([], True)

    def test_nested_filter_in_and(self):
        f = parse_filter_json('''[[
            {"column": "a", "value": 1},
            [[{"column": "b", "value": 2}], [{"column": "c", "value": 3}]]
        ]]''')
        assert f == [[
            Condition("a", 1),
            [[Condition("b", 2)], [Condition("c", 3)]]
        ]]

    def test_empty(self):
        assert parse_filter_json('[]') == []

    def test_integration_with_to_sql(self):
        """解析后再 to_sql，结果应与手动构造一致。"""
        f = parse_filter_json('''[[
            {"column": "name", "value": "alice"},
            {"column": "age", "value": 30, "op": ">"}
        ]]''')
        sql, params = filter_to_sql(f)
        assert sql == "((name = ?) AND (age > ?))"
        assert params == ["alice", 30]

    def test_integration_or_of_ands(self):
        f = parse_filter_json('''[
            [{"column": "status", "value": "active"}],
            [{"column": "role", "value": "admin"}]
        ]''')
        sql, params = filter_to_sql(f)
        assert "(status = ?)" in sql
        assert "(role = ?)" in sql
        assert "OR" in sql
        assert params == ["active", "admin"]

    def test_integration_with_negate(self):
        """解析 + 取反 + to_sql 整体流程。"""
        f = parse_filter_json('[[[{"column": "a", "value": 1}]], true]')
        sql, params = filter_to_sql(f)
        assert sql.startswith("NOT ")
        assert "(a = ?)" in sql
        assert params == [1]

    def test_invalid_json_raises(self):
        """不合法的 JSON 由 json.loads 抛 json.JSONDecodeError。"""
        with pytest.raises(json.JSONDecodeError):
            parse_filter_json('not valid json')

    def test_top_level_scalar_raises(self):
        """顶层非列表/非字典/非否定元组应抛 ValueError。"""
        with pytest.raises(ValueError):
            parse_filter_json('"string"')

    def test_and_group_bad_item_raises(self):
        """AND 组内出现无法识别的元素应抛 ValueError。"""
        with pytest.raises(ValueError):
            parse_filter_json('[[{"column": "a", "value": 1}, "string"]]')

    def test_and_group_not_list_raises(self):
        """AND 组应始终为列表，否则抛 ValueError。"""
        with pytest.raises(ValueError):
            parse_filter_json('[{"column": "a", "value": 1}]')
