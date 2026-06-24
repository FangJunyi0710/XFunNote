"""测试筛选逻辑：Condition 运算符、filter_to_sql 递归 AND/OR 组合、自定义运算符注册、parse_filter_json。"""

import json

import pytest
from xfun.core.filter import Condition, filter_to_sql, parse_filter_json, filter_to_json, TRUE_CONDITION
from xfun.core.errors import InvalidConditionError, InvalidSQLError

# 加载 extras.py 中注册的自定义运算符（JSON_CONTAINS, TEXT_SEARCH, TRUE, FALSE）
import xfun.core.extras  # noqa: F401


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


# ===================================================================
# extras.py 自定义运算符
# ===================================================================


class TestExtrasJsonContains:
    """JSON_CONTAINS / JSON_NOT_CONTAINS 运算符。"""

    def test_json_contains(self):
        sql, params = Condition("tags", "Python", "JSON_CONTAINS").to_sql()
        assert sql == "EXISTS (SELECT 1 FROM json_each(tags) WHERE value = ?)"
        assert params == ["Python"]

    def test_json_contains_none(self):
        """值为 None 时对应 SQLite 的 IS NULL 匹配。"""
        sql, params = Condition("tags", None, "JSON_CONTAINS").to_sql()
        assert sql == "EXISTS (SELECT 1 FROM json_each(tags) WHERE value = ?)"
        assert params == [None]

    def test_json_not_contains(self):
        sql, params = Condition("tags", "Java", "JSON_NOT_CONTAINS").to_sql()
        expected = "NOT EXISTS (SELECT 1 FROM json_each(tags) WHERE value = ?)"
        assert sql == expected
        assert params == ["Java"]

    def test_json_not_contains_none(self):
        sql, params = Condition("tags", None, "JSON_NOT_CONTAINS").to_sql()
        assert "NOT EXISTS" in sql
        assert params == [None]


class TestExtrasTextSearch:
    """TEXT_SEARCH 运算符。"""

    def test_text_search(self):
        sql, params = Condition("content", "hello", "TEXT_SEARCH").to_sql()
        assert sql == "content LIKE ?"
        assert params == ["%hello%"]

    def test_text_search_empty(self):
        """空字符串搜索 → %% 匹配所有。"""
        sql, params = Condition("content", "", "TEXT_SEARCH").to_sql()
        assert sql == "content LIKE ?"
        assert params == ["%%"]

    def test_text_search_special_chars(self):
        """含特殊字符的文本仍应正确参数化（防止注入）。"""
        sql, params = Condition("content", "it's 100%", "TEXT_SEARCH").to_sql()
        assert params == ["%it's 100%%"]


class TestExtrasLogical:
    """TRUE / FALSE 逻辑常量运算符。"""

    def test_true(self):
        sql, params = Condition("_", None, "TRUE").to_sql()
        assert sql == "1=1"
        assert params == []

    def test_true_ignores_column_and_value(self):
        """TRUE 应完全忽略 column/value，仅返回恒真。"""
        sql, params = Condition("anything", "ignored", "TRUE").to_sql()
        assert sql == "1=1"
        assert params == []

    def test_false(self):
        sql, params = Condition("_", None, "FALSE").to_sql()
        assert sql == "1=0"
        assert params == []

    def test_false_ignores_column_and_value(self):
        sql, params = Condition("anything", 42, "FALSE").to_sql()
        assert sql == "1=0"
        assert params == []


class TestExtrasInFilter:
    """自定义运算符嵌入 Filter 结构中的组合行为。"""

    def test_json_contains_in_and_group(self):
        sql, params = filter_to_sql(
            [[Condition("tags", "Python", "JSON_CONTAINS"), Condition("a", 1)]]
        )
        assert "json_each" in sql
        assert "AND" in sql
        assert params == ["Python", 1]

    def test_true_and_condition(self):
        """TRUE 与普通条件 AND 组合。"""
        sql, params = filter_to_sql(
            [[Condition("a", 1), Condition("_", None, "TRUE")]]
        )
        # TRUE 在 AND 组中不改变语义
        assert "1=1" in sql
        assert params == [1]

    def test_false_in_filter_shuts_down(self):
        """FALSE 在 AND 组中使条件永假。"""
        sql, params = filter_to_sql(
            [[Condition("a", 1), Condition("_", None, "FALSE")]]
        )
        assert "1=0" in sql
        assert params == [1]

    def test_text_search_or_group(self):
        sql, params = filter_to_sql([
            [Condition("content", "AI", "TEXT_SEARCH")],
            [Condition("content", "Python", "TEXT_SEARCH")],
        ])
        assert "LIKE" in sql
        assert sql.count("OR") == 1
        assert params == ["%AI%", "%Python%"]


class TestExtrasIntegration:
    """集成测试：在真实 SQLite DB 上验证运算符可用。"""

    def test_json_contains_matches(self, db):
        with db.transaction() as conn:
            conn.execute("CREATE TABLE _t_json (id INT, tags TEXT)")
            conn.execute("INSERT INTO _t_json VALUES (1, '[\"Python\",\"AI\"]')")
            conn.execute("INSERT INTO _t_json VALUES (2, '[\"Java\"]')")
            conn.execute("INSERT INTO _t_json VALUES (3, '[]')")

        sql, params = Condition("tags", "Python", "JSON_CONTAINS").to_sql()
        with db.read_transaction() as conn:
            rows = conn.execute(
                f"SELECT id FROM _t_json WHERE {sql}", params
            ).fetchall()
        assert [r[0] for r in rows] == [1]

    def test_json_not_contains_excludes(self, db):
        with db.transaction() as conn:
            conn.execute("CREATE TABLE _t_jnot (id INT, tags TEXT)")
            conn.execute("INSERT INTO _t_jnot VALUES (1, '[\"Python\",\"AI\"]')")
            conn.execute("INSERT INTO _t_jnot VALUES (2, '[\"Java\"]')")

        sql, params = Condition("tags", "Python", "JSON_NOT_CONTAINS").to_sql()
        with db.read_transaction() as conn:
            rows = conn.execute(
                f"SELECT id FROM _t_jnot WHERE {sql}", params
            ).fetchall()
        assert [r[0] for r in rows] == [2]

    def test_text_search_matches(self, db):
        with db.transaction() as conn:
            conn.execute("CREATE TABLE _t_ts (id INT, content TEXT)")
            conn.execute("INSERT INTO _t_ts VALUES (1, 'hello world')")
            conn.execute("INSERT INTO _t_ts VALUES (2, 'goodbye')")

        sql, params = Condition("content", "hello", "TEXT_SEARCH").to_sql()
        with db.read_transaction() as conn:
            rows = conn.execute(
                f"SELECT id FROM _t_ts WHERE {sql}", params
            ).fetchall()
        assert [r[0] for r in rows] == [1]

    def test_true_does_not_filter(self, db):
        """TRUE 条件不应过滤任何行。"""
        with db.transaction() as conn:
            conn.execute("CREATE TABLE _t_true (id INT)")
            conn.execute("INSERT INTO _t_true VALUES (1)")
            conn.execute("INSERT INTO _t_true VALUES (2)")

        sql, params = Condition("_", None, "TRUE").to_sql()
        with db.read_transaction() as conn:
            rows = conn.execute(
                f"SELECT id FROM _t_true WHERE {sql}", params
            ).fetchall()
        assert len(rows) == 2

    def test_false_filters_all(self, db):
        """FALSE 条件应过滤所有行。"""
        with db.transaction() as conn:
            conn.execute("CREATE TABLE _t_false (id INT)")
            conn.execute("INSERT INTO _t_false VALUES (1)")

        sql, params = Condition("_", None, "FALSE").to_sql()
        with db.read_transaction() as conn:
            rows = conn.execute(
                f"SELECT id FROM _t_false WHERE {sql}", params
            ).fetchall()
        assert len(rows) == 0


# =====================================================================
# filter_to_json / convert_filter_to_object
# =====================================================================

class TestFilterToJson:
    def test_condition_to_dict(self):
        """Condition 转为 dict。"""
        obj = filter_to_json(Condition("col", "val", "="))
        assert obj == {"column": "col", "value": "val", "op": "="}

    def test_condition_with_default_op(self):
        """op 省略时（默认 =）也包含在 dict 中。"""
        obj = filter_to_json(Condition("col", 1))
        assert obj == {"column": "col", "value": 1, "op": "="}

    def test_true_condition(self):
        """TRUE_CONDITION 转为 dict。"""
        obj = filter_to_json(TRUE_CONDITION)
        assert obj == {"column": "_", "value": None, "op": "TRUE"}

    def test_negate_tuple(self):
        """取反元组 (Filter, True) 转为 [inner, True]。"""
        obj = filter_to_json((Condition("col", 1, "="), True))
        assert obj == [{"column": "col", "value": 1, "op": "="}, True]

    def test_negate_tuple_false(self):
        """取反元组 (Filter, False) 转为 [inner, False]。"""
        obj = filter_to_json((Condition("col", 1, ">"), False))
        assert obj == [{"column": "col", "value": 1, "op": ">"}, False]

    def test_nested_and_or(self):
        """AND/OR 嵌套结构转为嵌套 list。"""
        flt = [[Condition("a", 1), Condition("b", 2)], [Condition("c", 3)]]
        obj = filter_to_json(flt)
        assert obj == [
            [{"column": "a", "value": 1, "op": "="}, {"column": "b", "value": 2, "op": "="}],
            [{"column": "c", "value": 3, "op": "="}],
        ]

    def test_json_serializable(self):
        """返回对象可被 json.dumps 正常处理。"""
        obj = filter_to_json([[Condition("a", 1), (Condition("b", 2), True)]])
        dumped = json.dumps(obj, ensure_ascii=False)
        assert isinstance(dumped, str)
        assert "a" in dumped
