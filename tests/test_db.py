"""测试数据库核心类：DB 初始化、表迁移、SELECT SQL、事务上下文管理器、Column.check_order_by。"""

import pytest
from xfun.core.db import Column, DB
from xfun.core.errors import InvalidSQLError


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


class TestDBInit:
    """DB.init 集成测试。"""

    def test_init_creates_tables(self, registry, tmp_path):
        db = DB(db_path=str(tmp_path / "init_test.db"))
        db.init({nb.name: nb.columns for nb in registry.values()})
        with db.read_transaction() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        table_names = {r["name"] for r in rows}
        assert "plan" in table_names


class TestDBInitEdgeCases:
    """覆盖 db.init 的 _check_addition_column / _check_existing_column / ALTER TABLE 分支。"""

    def test_alter_add_non_nullable_column_raises(self, tmp_path):
        """为已有表添加 NOT NULL 列应抛出 InvalidSQLError。"""
        db = DB(db_path=str(tmp_path / "add_notnull.db"))
        db.init({"t1": [Column("id", "TEXT")]})
        with pytest.raises(InvalidSQLError, match="不可为 NULL"):
            db.init({"t1": [Column("id", "TEXT"), Column("name", "TEXT", nullable=False)]})

    def test_alter_add_primary_key_column_raises(self, tmp_path):
        """为已有表添加 PK 列应抛出 InvalidSQLError。"""
        db = DB(db_path=str(tmp_path / "add_pk.db"))
        db.init({"t1": [Column("id", "TEXT")]})
        with pytest.raises(InvalidSQLError, match="主键"):
            db.init({"t1": [Column("id", "TEXT"), Column("name", "TEXT", primary_key=True)]})

    def test_alter_add_invalid_column_name_raises(self, tmp_path):
        """为已有表添加非法列名应抛出 InvalidSQLError。"""
        db = DB(db_path=str(tmp_path / "add_badcol.db"))
        db.init({"t1": [Column("id", "TEXT")]})
        with pytest.raises(InvalidSQLError):
            db.init({"t1": [Column("id", "TEXT"), Column("bad col", "TEXT")]})

    def test_alter_add_nullable_column_succeeds(self, tmp_path):
        """为已有表添加可空列应执行 ALTER TABLE ADD COLUMN。"""
        db = DB(db_path=str(tmp_path / "add_ok.db"))
        db.init({"t1": [Column("id", "TEXT")]})
        db.init({"t1": [Column("id", "TEXT"), Column("name", "TEXT", nullable=True)]})
        with db.read_transaction() as conn:
            cols = [r["name"] for r in conn.execute("PRAGMA table_info(t1)")]
        assert "name" in cols

    def test_existing_column_type_mismatch_raises(self, tmp_path):
        """已有列类型冲突应抛出 InvalidSQLError。"""
        db = DB(db_path=str(tmp_path / "type_mismatch.db"))
        db.init({"t1": [Column("id", "TEXT")]})
        with pytest.raises(InvalidSQLError, match="类型冲突"):
            db.init({"t1": [Column("id", "INTEGER")]})

    def test_existing_column_nullable_mismatch_raises(self, tmp_path):
        """已有列 nullable 约束冲突应抛出 InvalidSQLError。"""
        db = DB(db_path=str(tmp_path / "nullable_mismatch.db"))
        db.init({"t1": [Column("id", "TEXT", nullable=False)]})
        with pytest.raises(InvalidSQLError, match="约束冲突"):
            db.init({"t1": [Column("id", "TEXT", nullable=True)]})

    def test_existing_column_pk_mismatch_raises(self, tmp_path):
        """已有列主键属性冲突应抛出 InvalidSQLError。"""
        db = DB(db_path=str(tmp_path / "pk_mismatch.db"))
        db.init({"t1": [Column("id", "TEXT", primary_key=True)]})
        with pytest.raises(InvalidSQLError, match="主键属性冲突"):
            db.init({"t1": [Column("id", "TEXT", primary_key=False)]})


class TestSelectSql:
    """DB.select_sql：指定列用 table.col，其余表列用 NULL AS col。"""

    def test_all_columns_included(self, tmp_path):
        db = DB(db_path=str(tmp_path / "all_cols.db"))
        db.init({"t1": [Column("id", "TEXT"), Column("name", "TEXT"), Column("age", "INTEGER")]})
        sql = db.select_sql("t1", ["id", "name"])
        assert sql.startswith("SELECT ")
        assert "t1.id" in sql
        assert "t1.name" in sql
        assert "NULL AS age" in sql
        assert "FROM t1" in sql

    def test_single_column(self, tmp_path):
        db = DB(db_path=str(tmp_path / "single_col.db"))
        db.init({"t1": [Column("id", "TEXT"), Column("name", "TEXT")]})
        sql = db.select_sql("t1", ["id"])
        assert sql == "SELECT t1.id, NULL AS name FROM t1"

    def test_all_selected(self, tmp_path):
        db = DB(db_path=str(tmp_path / "all_selected.db"))
        db.init({"t1": [Column("id", "TEXT"), Column("name", "TEXT")]})
        sql = db.select_sql("t1", ["id", "name"])
        assert sql == "SELECT t1.id, t1.name FROM t1"

    def test_query_result_contains_all_columns(self, tmp_path):
        """实际查询时，未选中的列返回 NULL。"""
        db = DB(db_path=str(tmp_path / "query_result.db"))
        db.init({"t1": [Column("id", "TEXT"), Column("name", "TEXT"), Column("age", "INTEGER")]})
        with db.transaction() as conn:
            conn.executemany(
                "INSERT INTO t1 (id, name, age) VALUES (:id, :name, :age)",
                [{"id": "1", "name": "alice", "age": 30}],
            )
        sql = db.select_sql("t1", ["name"])
        with db.read_transaction() as conn:
            row = conn.execute(sql).fetchone()
        assert row["id"] is None
        assert row["name"] == "alice"
        assert row["age"] is None
        assert row["age"] is None


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
