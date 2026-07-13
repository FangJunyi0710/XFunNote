"""测试 Condition / Filter 筛选引擎。"""

import json
import pytest

from xfun.core.filter import (
    Condition,
    Filter,
    filter_to_sql,
    filter_to_json,
    parse_filter_json,
)
from xfun.core.errors import InvalidConditionError, InvalidFilterError, InvalidSQLError


# ===================================================================
# Condition — 基础运算符
# ===================================================================

class TestConditionBuiltin:
    def test_eq(self):
        cond = Condition("a", 1, "=")
        sql, params = cond.to_sql()
        assert sql == "a = ?"
        assert params == [1]

    def test_neq(self):
        cond = Condition("a", 1, "!=")
        sql, params = cond.to_sql()
        assert sql == "a != ?"
        assert params == [1]

    def test_gt(self):
        cond = Condition("a", 5, ">")
        sql, params = cond.to_sql()
        assert sql == "a > ?"
        assert params == [5]

    def test_lt(self):
        cond = Condition("a", 3, "<")
        sql, params = cond.to_sql()
        assert sql == "a < ?"
        assert params == [3]

    def test_gte(self):
        cond = Condition("a", 10, ">=")
        sql, params = cond.to_sql()
        assert sql == "a >= ?"
        assert params == [10]

    def test_lte(self):
        cond = Condition("a", 10, "<=")
        sql, params = cond.to_sql()
        assert sql == "a <= ?"
        assert params == [10]

    def test_like(self):
        cond = Condition("a", "%test%", "LIKE")
        sql, params = cond.to_sql()
        assert sql == "a LIKE ?"
        assert params == ["%test%"]

    def test_not_like(self):
        cond = Condition("a", "%test%", "NOT LIKE")
        sql, params = cond.to_sql()
        assert sql == "a NOT LIKE ?"
        assert params == ["%test%"]

    def test_in_list(self):
        cond = Condition("a", [1, 2, 3], "IN")
        sql, params = cond.to_sql()
        assert sql == "a IN (?, ?, ?)"
        assert params == [1, 2, 3]

    def test_in_empty_list(self):
        cond = Condition("a", [], "IN")
        sql, params = cond.to_sql()
        assert sql == "1=0"  # 空 IN → 永假
        assert params == []

    def test_not_in_list(self):
        cond = Condition("a", [1, 2], "NOT IN")
        sql, params = cond.to_sql()
        assert sql == "a NOT IN (?, ?)"
        assert params == [1, 2]

    def test_not_in_empty_list(self):
        cond = Condition("a", [], "NOT IN")
        sql, params = cond.to_sql()
        assert sql == "1=1"  # 空 NOT IN → 永真
        assert params == []

    def test_between(self):
        cond = Condition("a", [1, 10], "BETWEEN")
        sql, params = cond.to_sql()
        assert sql == "a BETWEEN ? AND ?"
        assert params == [1, 10]

    def test_between_not_list(self):
        cond = Condition("a", 5, "BETWEEN")
        with pytest.raises(InvalidConditionError):
            cond.to_sql()

    def test_between_not_two_elements(self):
        cond = Condition("a", [5], "BETWEEN")
        with pytest.raises(InvalidConditionError):
            cond.to_sql()

    def test_between_none_lower(self):
        cond = Condition("a", [None, 5], "BETWEEN")
        sql, params = cond.to_sql()
        assert sql == "1=0"  # 任意端点为 None → 永假
        assert params == []

    def test_null_eq(self):
        cond = Condition("a", None, "=")
        sql, params = cond.to_sql()
        assert sql == "a IS NULL"
        assert params == []

    def test_null_neq(self):
        cond = Condition("a", None, "!=")
        sql, params = cond.to_sql()
        assert sql == "a IS NOT NULL"
        assert params == []

    def test_null_with_other_op_raises(self):
        cond = Condition("a", None, ">")
        with pytest.raises(InvalidConditionError):
            cond.to_sql()

    def test_in_not_list_raises(self):
        cond = Condition("a", "not_a_list", "IN")
        with pytest.raises(InvalidConditionError):
            cond.to_sql()

    def test_duplicates_removed_in_in(self):
        cond = Condition("a", [1, 1, 2, 2, 3], "IN")
        sql, params = cond.to_sql()
        assert sql == "a IN (?, ?, ?)"
        assert sorted(params) == [1, 2, 3]

    def test_unknown_op_raises(self):
        cond = Condition("a", 1, "UNKNOWN_OP")
        with pytest.raises(InvalidConditionError):
            cond.to_sql()

    def test_invalid_column_raises(self):
        cond = Condition("123col", 1, "=")
        with pytest.raises(InvalidSQLError):
            cond.to_sql()


# ===================================================================
# Filter — 递归结构
# ===================================================================

class TestFilter:
    def test_single_condition(self):
        flt = Condition("a", 1, "=")
        sql, params = filter_to_sql(flt)
        assert sql == "a = ?"
        assert params == [1]

    def test_simple_or(self):
        # [[Condition("a", 1), Condition("b", 2)]]
        flt: Filter = [[Condition("a", 1), Condition("b", 2)]]
        sql, params = filter_to_sql(flt)
        # 外层 wrap：((a = ?) AND (b = ?))
        assert "(a = ?) AND (b = ?)" in sql
        assert params == [1, 2]

    def test_or_groups(self):
        # [[Condition("a", 1)], [Condition("b", 2)]]
        flt: Filter = [[Condition("a", 1)], [Condition("b", 2)]]
        sql, params = filter_to_sql(flt)
        # ((a = ?)) OR ((b = ?))
        assert "(a = ?)" in sql
        assert "(b = ?)" in sql
        assert params == [1, 2]

    def test_complex_or_and(self):
        flt: Filter = [
            [Condition("a", 1), Condition("b", 2)],
            [Condition("c", 3)],
        ]
        sql, params = filter_to_sql(flt)
        assert "(a = ?) AND (b = ?)" in sql
        assert "(c = ?)" in sql
        assert params == [1, 2, 3]

    def test_negate_tuple(self):
        flt: Filter = (Condition("a", 1, "="), True)
        sql, params = filter_to_sql(flt)
        assert sql == "NOT (a = ?)"
        assert params == [1]

    def test_double_negate(self):
        flt: Filter = ((Condition("a", 1, "="), True), True)
        sql, params = filter_to_sql(flt)
        # 当前实现不折叠双重否定
        assert "a = ?" in sql or "NOT (NOT (a = ?))" == sql
        assert params == [1]

    def test_empty_filter(self):
        sql, params = filter_to_sql([[]])
        assert sql == "(1=1)"
        assert params == []

    def test_empty_inner_group_skipped(self):
        flt: Filter = [[Condition("a", 1)], []]
        sql, params = filter_to_sql(flt)
        assert "(a = ?)" in sql
        assert params == [1]

    def test_negation_in_group(self):
        flt: Filter = [[(Condition("a", 1, "="), True)]]
        sql, params = filter_to_sql(flt)
        assert "NOT (a = ?)" in sql
        assert params == [1]

    def test_filter_works_in_db(self, db):
        """验证 filter 生成的 SQL 在实际数据库中可执行。"""
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO plan (id, content, month, seq, no, done, created_at, updated_at, tags, ai_tags, is_ai_gen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("plan-1", "hello", "2606", 1, "2606A", 0, "2026-01-01", "2026-01-01", "[]", "[]", 0),
            )
            conn.execute(
                "INSERT INTO plan (id, content, month, seq, no, done, created_at, updated_at, tags, ai_tags, is_ai_gen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("plan-2", "world", "2607", 1, "2607A", 0, "2026-01-01", "2026-01-01", "[]", "[]", 0),
            )
        flt: Filter = [[Condition("month", "2606", "=")]]
        sql, params = filter_to_sql(flt)
        full_sql = f"SELECT id FROM plan WHERE {sql}"
        with db.read_transaction() as conn:
            rows = conn.execute(full_sql, params).fetchall()
        assert len(rows) == 1
        assert rows[0]["id"] == "plan-1"


# ===================================================================
# 序列化 / 反序列化
# ===================================================================

class TestFilterSerialization:
    def test_filter_to_json_condition(self):
        cond = Condition("month", "2606", "=")
        js = filter_to_json(cond)
        assert js == {"column": "month", "value": "2606", "op": "="}

    def test_filter_to_json_complex(self):
        flt: Filter = [
            [Condition("a", 1), Condition("b", 2)],
            [Condition("c", 3)],
        ]
        js = filter_to_json(flt)
        assert isinstance(js, list)
        assert len(js) == 2
        assert js[0] == [
            {"column": "a", "value": 1, "op": "="},
            {"column": "b", "value": 2, "op": "="},
        ]

    def test_filter_to_json_negate(self):
        flt: Filter = (Condition("a", 1, "="), True)
        js = filter_to_json(flt)
        assert js == [{"column": "a", "value": 1, "op": "="}, True]

    def test_parse_filter_json_condition(self):
        s = '{"column": "month", "value": "2606", "op": "="}'
        flt = parse_filter_json(json.loads(s))
        assert isinstance(flt, Condition)
        assert flt.column == "month"
        assert flt.value == "2606"

    def test_parse_filter_json_complex(self):
        s = '[[{"column": "a", "value": 1}, {"column": "b", "value": 2}], [{"column": "c", "value": 3}]]'
        flt = parse_filter_json(json.loads(s))
        assert isinstance(flt, list)
        assert len(flt) == 2
        assert len(flt[0]) == 2
        assert flt[0][0].column == "a"

    def test_convert_filter_object_condition(self):
        obj = {"column": "month", "value": "2606", "op": "="}
        c = parse_filter_json(obj)
        assert isinstance(c, Condition)
        assert c.column == "month"

    def test_convert_filter_object_invalid(self):
        with pytest.raises(InvalidFilterError):
            parse_filter_json(42)

    def test_convert_filter_object_invalid_inner(self):
        with pytest.raises(InvalidFilterError):
            parse_filter_json([42])

    def test_invalid_op_raises(self):
        cond = Condition("a", 1, "NONEXISTENT")
        with pytest.raises(InvalidConditionError):
            cond.to_sql()


# ===================================================================
# 边缘分支
# ===================================================================

class TestFilterEdgeCases:
    """覆盖 filter.py 中剩余未覆盖的行。"""

    def test_tuple_with_empty_inner_clause(self):
        """(空筛选, True) → 返回 "NOT ((1=1))"。"""
        flt: Filter = ([[]], True)
        sql, params = filter_to_sql(flt)
        assert sql == "NOT ((1=1))"
        assert params == []

    def test_and_group_skip_empty_item(self):
        """AND 组中某项解析为空应跳过 (l.149)。"""
        flt: Filter = [[Condition("a", 1, "="), [[]]]]
        sql, params = filter_to_sql(flt)
        assert "(a = ?)" in sql
        assert params == [1]

    def test_empty_list_filter_returns_1_0(self):
        """空列表作为 filter → 返回 "1=0" (l.157)。"""
        sql, params = filter_to_sql([])
        assert sql == "1=0"
        assert params == []

    def test_custom_op_returns_empty_clause_in_tuple(self):
        """自定义运算符返回空 clause → tuple 分支使用 "1=0" (l.136-137)。"""
        from xfun.core.filter import Condition

        @Condition.register_op("EMPTY_TUPLE")
        def _empty_tuple(column, value, op):
            return "", []

        flt: Filter = (Condition("x", None, "EMPTY_TUPLE"), False)
        sql, params = filter_to_sql(flt)
        assert sql == "1=0"
        assert params == []

    def test_custom_op_returns_empty_clause_in_and_group(self):
        """自定义运算符返回空 clause → and 组使用 "1=0" (l.148-149)。"""
        from xfun.core.filter import Condition

        @Condition.register_op("EMPTY_AND")
        def _empty_and(column, value, op):
            return "", []

        flt: Filter = [[Condition("x", None, "EMPTY_AND")]]
        sql, params = filter_to_sql(flt)
        assert sql == "((1=0))"
        assert params == []


class TestConvertFilterEdge:
    """覆盖 parse_filter_json 中的 tuple+bool 分支 (l.168)。"""

    def test_convert_filter_tuple_with_bool(self):
        obj = [{"column": "a", "value": 1}, True]
        result = parse_filter_json(obj)
        assert isinstance(result, tuple)
        assert result[1] is True
