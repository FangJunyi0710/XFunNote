"""测试核心查询逻辑：Condition 运算符、build_where AND/OR 组合、自定义运算符注册。"""

import pytest
from xfun.core.db import Column, Condition, build_where, DB
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

    def test_negate_wraps_not(self):
        sql, params = Condition("done", 1, "=", negate=True).to_sql()
        assert sql == "NOT (done = ?)" and params == [1]

    def test_like(self):
        sql, params = Condition("col", "%test%", "LIKE").to_sql()
        assert sql == "col LIKE ?" and params == ["%test%"]


class TestConditionEdgeCases:
    """边界：非法输入应有的保护。"""

    def test_null_with_non_null_op_raises(self):
        with pytest.raises(InvalidConditionError):
            Condition("col", None, ">").to_sql()

    def test_empty_in_raises(self):
        with pytest.raises(InvalidConditionError):
            Condition("col", [], "IN").to_sql()

    def test_unknown_op_raises(self):
        with pytest.raises(InvalidConditionError):
            Condition("col", "val", "UNKNOWN_OP").to_sql()

    def test_invalid_column_name_raises(self):
        with pytest.raises(InvalidSQLError):
            Condition("bad col", "val").to_sql()


class TestBuildWhere:
    """核心：二维 Filter → WHERE 子句是否正确。"""

    def test_empty(self):
        assert build_where([]) == ("", [])

    def test_and_group(self):
        sql, params = build_where([[Condition("a", 1), Condition("b", 2)]])
        assert "(a = ? AND b = ?)" in sql

    def test_or_of_ands(self):
        sql, params = build_where([
            [Condition("a", 1)],
            [Condition("b", 2)],
        ])
        assert sql.count("OR") == 1

    def test_null_in_filter(self):
        sql, params = build_where([[Condition("ai_note", None, "=")]])
        assert "IS NULL" in sql


class TestCheckOrderBy:
    """Column.check_order_by 对 ASC/DESC 的校验。"""

    def test_single_column_with_direction(self):
        Column.check_order_by("month ASC")  # 不抛异常即通过

    def test_multi_column(self):
        Column.check_order_by("month ASC, seq DESC")

    def test_single_column_no_direction(self):
        Column.check_order_by("month")

    def test_invalid_direction_raises(self):
        with pytest.raises(InvalidSQLError, match="INVALID"):
            Column.check_order_by("month INVALID")


class TestBetweenEdgeCases:
    """BETWEEN 运算符的非法输入。"""

    def test_between_none_value_raises(self):
        with pytest.raises(InvalidConditionError):
            Condition("col", [None, 10], "BETWEEN").to_sql()

    def test_between_partial_none_raises(self):
        with pytest.raises(InvalidConditionError):
            Condition("col", [None, None], "BETWEEN").to_sql()

    def test_between_wrong_length_raises(self):
        with pytest.raises(InvalidConditionError):
            Condition("col", [1, 2, 3], "BETWEEN").to_sql()


class TestBuildWhereEdgeCases:
    """build_where 边界情况。"""

    def test_empty_group_skipped(self):
        sql, params = build_where([[]])
        assert sql == "" and params == []

    def test_mixed_empty_and_normal(self):
        sql, params = build_where([
            [Condition("a", 1)],
            [],
        ])
        assert "a = ?" in sql and params == [1]


class TestDBInit:
    """DB.init 集成测试。"""

    def test_init_creates_tables(self, registry, tmp_path):
        db = DB(db_path=str(tmp_path / "init_test.db"))
        db.init(registry)
        with db.read_transaction() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        table_names = {r["name"] for r in rows}
        assert "plan" in table_names


class TestTransactionContext:
    """事务上下文管理器的边界分支。"""

    def test_write_exit_without_enter(self, db):
        """_TransactionContext.__exit__ 时 conn 为 None 应直接返回。"""
        from xfun.core.db import _TransactionContext
        ctx = _TransactionContext(db)
        # 未调用 __enter__，直接调用 __exit__
        ctx.__exit__(None, None, None)  # 不抛异常即通过

    def test_read_exit_without_enter(self, db):
        """_ReadTransactionContext.__exit__ 时 conn 为 None 应直接返回。"""
        from xfun.core.db import _ReadTransactionContext
        ctx = _ReadTransactionContext(db)
        ctx.__exit__(None, None, None)

    def test_read_transaction_rollback_on_error(self, db):
        """只读事务在异常时也应回滚。"""
        from xfun.core.db import _ReadTransactionContext
        import sqlite3
        conn = db._connect()
        conn.execute("CREATE TABLE IF NOT EXISTS _test_t (id INT)")
        conn.close()
        with pytest.raises(RuntimeError):
            with _ReadTransactionContext(db) as conn:
                conn.execute("INSERT INTO _test_t VALUES (1)")
                raise RuntimeError("rollback read!")
        # 读事务的回滚不会影响之前的写（WAL 模式下），只验证不抛异常


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

    def test_custom_with_negate(self):
        @Condition.register_op("@@")
        def handler(col, val, op):
            return f"to_tsvector({col}) @@ to_tsquery(?)", [val]
        try:
            sql, _ = Condition("content", "hello", "@@", negate=True).to_sql()
            assert sql.startswith("NOT (")
        finally:
            Condition._op_registry.pop("@@", None)
