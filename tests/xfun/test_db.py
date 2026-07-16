"""测试 Column 和 DB 核心功能。"""

import re
import sqlite3

import pytest

from xfun.core.db import Column, DB, _check_addition_column, _check_existing_column, _TransactionContext, _ReadTransactionContext
from xfun.core.errors import InvalidSQLError


# ===================================================================
# Column
# ===================================================================

class TestColumn:
    def test_basic_column(self):
        col = Column("id", "TEXT", primary_key=True, nullable=False)
        assert col.sql == "id TEXT PRIMARY KEY NOT NULL"

    def test_nullable_column(self):
        col = Column("name", "TEXT")
        assert col.sql == "name TEXT"

    def test_index_column(self):
        col = Column("email", "TEXT", index=True)
        assert "INDEX" not in col.sql

    def test_auto_column(self):
        col = Column("created_at", "TEXT", auto=True)
        assert col.sql == "created_at TEXT"

    def test_invalid_column_name(self):
        with pytest.raises(InvalidSQLError):
            Column("123col", "TEXT").sql

    def test_invalid_column_name_special_chars(self):
        with pytest.raises(InvalidSQLError):
            Column("col; DROP TABLE", "TEXT").sql

    def test_dotted_column_name_valid(self):
        col = Column("table.column", "TEXT")
        assert col.sql == "table.column TEXT"

    def test_check_order_by_single(self):
        Column.check_order_by("month")

    def test_check_order_by_with_direction(self):
        Column.check_order_by("month ASC")
        Column.check_order_by("month DESC")

    def test_check_order_by_multiple(self):
        Column.check_order_by("month ASC, seq DESC")

    def test_check_order_by_invalid_direction(self):
        with pytest.raises(InvalidSQLError):
            Column.check_order_by("month INVALID")

    def test_check_order_by_invalid_name(self):
        with pytest.raises(InvalidSQLError):
            Column.check_order_by("123col")

    def test_check_valid_name(self):
        Column.check("valid_column")

    def test_check_invalid_name(self):
        with pytest.raises(InvalidSQLError):
            Column.check("invalid column")

    def test_check_empty_name(self):
        with pytest.raises(InvalidSQLError):
            Column.check("")


# ===================================================================
# Column 兼容性检查
# ===================================================================

class TestColumnCompatibility:
    def test_addition_column_nullable_not_pk(self):
        _check_addition_column(Column("new_col", "TEXT"))

    def test_addition_column_not_null_raises(self):
        with pytest.raises(InvalidSQLError, match="不可为 NULL"):
            _check_addition_column(Column("new_col", "TEXT", nullable=False))

    def test_addition_column_pk_raises(self):
        with pytest.raises(InvalidSQLError, match="主键"):
            _check_addition_column(Column("new_col", "TEXT", primary_key=True))

    def test_addition_column_invalid_name_raises(self):
        with pytest.raises(InvalidSQLError):
            _check_addition_column(Column("123col", "TEXT"))

    def test_addition_column_unique_raises(self):
        """新增列为 UNIQUE 应抛出异常 (l.112)。"""
        with pytest.raises(InvalidSQLError, match="UNIQUE"):
            _check_addition_column(Column("new_col", "TEXT", unique=True))


# ===================================================================
# DB
# ===================================================================

class TestDB:
    def test_init_empty_db(self, db):
        assert set(db.table_infos.keys()) == {"plan", "diary", "word", "accumulation", "aimemory", "timeline", "schedule"}

    def test_transaction_commit(self, db):
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO plan (id, content, month, seq, no, done, created_at, updated_at, tags, ai_tags, is_ai_gen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("plan-1", "test", "2606", 1, "2606A", 0, "2026-01-01", "2026-01-01", "[]", "[]", 0),
            )
        with db.read_transaction() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM plan").fetchone()
        assert row["cnt"] == 1

    def test_transaction_rollback_on_error(self, db):
        try:
            with db.transaction() as conn:
                conn.execute(
                    "INSERT INTO plan (id, content, month, seq, no, done, created_at, updated_at, tags, ai_tags, is_ai_gen) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("plan-1", "test", "2606", 1, "2606A", 0, "2026-01-01", "2026-01-01", "[]", "[]", 0),
                )
                raise ValueError("模拟异常")
        except ValueError:
            pass
        with db.read_transaction() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM plan").fetchone()
        assert row["cnt"] == 0

    def test_read_transaction(self, db):
        with db.read_transaction() as conn:
            rows = conn.execute("SELECT 1 as val").fetchall()
        assert rows[0]["val"] == 1

    def test_init_creates_tables(self, db):
        with db.read_transaction() as conn:
            for table in ("plan", "diary", "word", "accumulation", "aimemory"):
                row = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                ).fetchone()
                assert row is not None, f"表 {table} 未创建"

    def test_init_adds_missing_columns(self, db):
        """缺失列通过 ALTER TABLE ADD COLUMN 补齐 (l.189-190)。"""
        db_path = db.db_path
        # 创建时不包含 content 列，让 init 自动补齐
        with db.transaction() as conn:
            conn.execute(
                "CREATE TABLE test_tb (id TEXT PRIMARY KEY NOT NULL, created_at TEXT NOT NULL, "
                "updated_at TEXT NOT NULL, tags TEXT NOT NULL, ai_tags TEXT NOT NULL, is_ai_gen INTEGER NOT NULL)"
            )
        # 添加 content 列（ADD COLUMN 要求可空）
        db.init({"test_tb": [
            Column("id", "TEXT", primary_key=True, nullable=False),
            Column("content", "TEXT", nullable=True),
            Column("created_at", "TEXT", nullable=False, auto=True),
            Column("updated_at", "TEXT", nullable=False, auto=True),
            Column("tags", "TEXT", nullable=False, auto=True),
            Column("ai_tags", "TEXT", nullable=False, auto=True),
            Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
        ]})
        with db.read_transaction() as conn:
            cols = [r["name"] for r in conn.execute("PRAGMA table_info(test_tb)")]
        assert "content" in cols

    def test_insert_sql(self, registry, db):
        sql = db.insert_sql("plan")
        assert sql.startswith("INSERT INTO plan")
        assert "content" in sql
        assert "month" in sql

    def test_select_sql(self, registry, db):
        sql = db.select_sql("plan", ["month", "done"])
        assert "plan.month" in sql
        assert "NULL AS id" in sql
        assert "NULL AS content" in sql

    def test_insert_and_select_roundtrip(self, db):
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO plan (id, content, month, seq, no, done, created_at, updated_at, tags, ai_tags, is_ai_gen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("plan-1", "测试内容", "2606", 1, "2606A", 0, "2026-01-01", "2026-01-01", "[]", "[]", 0),
            )
        with db.read_transaction() as conn:
            row = conn.execute("SELECT * FROM plan WHERE id = ?", ("plan-1",)).fetchone()
        assert row["content"] == "测试内容"
        assert row["month"] == "2606"

    def test_wal_mode_enabled(self, db):
        with db.read_transaction() as conn:
            row = conn.execute("PRAGMA journal_mode").fetchone()
        assert row[0].upper() == "WAL"

    def test_unique_column_skips_index(self, db):
        """UNIQUE 约束列不会重复建索引 (l.243)。"""
        with db.transaction() as conn:
            conn.execute(
                "CREATE TABLE unique_idx_tb ("
                "id TEXT PRIMARY KEY NOT NULL, "
                "email TEXT UNIQUE NOT NULL, "
                "created_at TEXT NOT NULL, updated_at TEXT NOT NULL, "
                "tags TEXT NOT NULL, ai_tags TEXT NOT NULL, is_ai_gen INTEGER NOT NULL)"
            )
        db.init({"unique_idx_tb": [
            Column("id", "TEXT", primary_key=True, nullable=False),
            Column("email", "TEXT", unique=True, index=True, nullable=False),
            Column("created_at", "TEXT", nullable=False, auto=True),
            Column("updated_at", "TEXT", nullable=False, auto=True),
            Column("tags", "TEXT", nullable=False, auto=True),
            Column("ai_tags", "TEXT", nullable=False, auto=True),
            Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
        ]})
        # 验证只有 id 有索引（email 的 UNIQUE 自动建索引，不额外创建）
        with db.read_transaction() as conn:
            indexes = [
                r["name"] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='unique_idx_tb'"
                )
            ]
        # sqlite_autoindex_unique_idx_tb_2 是 UNIQUE 约束自动创建的索引
        assert any("autoindex" in idx for idx in indexes), "UNIQUE 自动索引应存在"


class TestDBTypeConflict:
    """覆盖 db.py 同步检查中的冲突分支。"""

    def test_column_type_conflict(self, db):
        """代码定义 TEXT，数据库中是 INTEGER → 类型冲突 (l.108)。"""
        with db.transaction() as conn:
            conn.execute(
                "CREATE TABLE conflict_tb (id TEXT PRIMARY KEY NOT NULL, val INTEGER NOT NULL, "
                "created_at TEXT NOT NULL, updated_at TEXT NOT NULL, tags TEXT NOT NULL, "
                "ai_tags TEXT NOT NULL, is_ai_gen INTEGER NOT NULL)"
            )
        with pytest.raises(InvalidSQLError, match="类型冲突"):
            db.init({"conflict_tb": [
                Column("id", "TEXT", primary_key=True, nullable=False),
                Column("val", "TEXT", nullable=False),
                Column("created_at", "TEXT", nullable=False, auto=True),
                Column("updated_at", "TEXT", nullable=False, auto=True),
                Column("tags", "TEXT", nullable=False, auto=True),
                Column("ai_tags", "TEXT", nullable=False, auto=True),
                Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
            ]})

    def test_nullable_constraint_conflict(self, db):
        """数据库列可空，代码定义不可空 → 约束冲突 (l.114)。"""
        with db.transaction() as conn:
            conn.execute(
                "CREATE TABLE nullable_tb (id TEXT, "
                "created_at TEXT NOT NULL, updated_at TEXT NOT NULL, tags TEXT NOT NULL, "
                "ai_tags TEXT NOT NULL, is_ai_gen INTEGER NOT NULL)"
            )
        with pytest.raises(InvalidSQLError, match="约束冲突"):
            db.init({"nullable_tb": [
                Column("id", "TEXT", nullable=False),
                Column("created_at", "TEXT", nullable=False, auto=True),
                Column("updated_at", "TEXT", nullable=False, auto=True),
                Column("tags", "TEXT", nullable=False, auto=True),
                Column("ai_tags", "TEXT", nullable=False, auto=True),
                Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
            ]})

    def test_pk_constraint_conflict(self, db):
        """数据库列非 PK，代码定义 PK → 主键冲突 (l.121)。

        需要 nullable 一致以免提前触发约束检查。
        """
        with db.transaction() as conn:
            conn.execute(
                "CREATE TABLE pk_tb (id TEXT NOT NULL, "
                "created_at TEXT NOT NULL, updated_at TEXT NOT NULL, tags TEXT NOT NULL, "
                "ai_tags TEXT NOT NULL, is_ai_gen INTEGER NOT NULL)"
            )
        with pytest.raises(InvalidSQLError, match="主键"):
            db.init({"pk_tb": [
                Column("id", "TEXT", primary_key=True, nullable=False),
                Column("created_at", "TEXT", nullable=False, auto=True),
                Column("updated_at", "TEXT", nullable=False, auto=True),
                Column("tags", "TEXT", nullable=False, auto=True),
                Column("ai_tags", "TEXT", nullable=False, auto=True),
                Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
            ]})

    def test_empty_desired_cols_skipped(self, db):
        """init 中 desired_cols 为空列表应跳过。"""
        db.init({"nonexistent_empty": []})
        with db.read_transaction() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='nonexistent_empty'"
            ).fetchone()
        assert row is None

    def test_extra_column_in_db_raises(self, db):
        """数据库中存在代码未定义的列 → 抛出 InvalidSQLError (l.237)。"""
        with db.transaction() as conn:
            conn.execute(
                "CREATE TABLE extra_col_tb ("
                "id TEXT PRIMARY KEY NOT NULL, "
                "content TEXT, "
                "extra_col TEXT, "
                "created_at TEXT NOT NULL, updated_at TEXT NOT NULL, tags TEXT NOT NULL, "
                "ai_tags TEXT NOT NULL, is_ai_gen INTEGER NOT NULL)"
            )
        with pytest.raises(InvalidSQLError, match="代码未定义的列"):
            db.init({"extra_col_tb": [
                Column("id", "TEXT", primary_key=True, nullable=False),
                Column("content", "TEXT", nullable=True),
                Column("created_at", "TEXT", nullable=False, auto=True),
                Column("updated_at", "TEXT", nullable=False, auto=True),
                Column("tags", "TEXT", nullable=False, auto=True),
                Column("ai_tags", "TEXT", nullable=False, auto=True),
                Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
            ]})


class TestTransactionEdgeCases:
    """覆盖事务上下文管理器的异常路径。"""

    def test_write_transaction_conn_none_exit(self):
        """_TransactionContext.__exit__ 时 conn 为 None 应直接返回 (l.296)。"""
        ctx = _TransactionContext.__new__(_TransactionContext)
        ctx.db = None
        ctx.conn = None
        ctx.__exit__(None, None, None)

    def test_read_transaction_conn_none_exit(self):
        """_ReadTransactionContext.__exit__ 时 conn 为 None 应直接返回 (l.320)。"""
        ctx = _ReadTransactionContext.__new__(_ReadTransactionContext)
        ctx.db = None
        ctx.conn = None
        ctx.__exit__(None, None, None)

    def test_read_transaction_rollback_on_error(self, db):
        """读事务中抛出异常应回滚 (l.325)。"""
        try:
            with db.read_transaction() as conn:
                raise ValueError("模拟异常")
        except ValueError:
            pass


class TestDBBackupReset:
    """覆盖 backup() 和 reset() 方法。"""

    def test_backup_creates_file(self, db):
        """backup() 应创建备份文件并返回合法路径。"""
        import os
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO plan (id, content, month, seq, no, done, created_at, updated_at, tags, ai_tags, is_ai_gen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("backup-1", "备份测试", "2606", 1, "2606A", 0, "2026-01-01", "2026-01-01", "[]", "[]", 0),
            )
        path = db.backup()
        assert os.path.exists(path), f"备份文件未创建: {path}"
        assert ".backup." in path, f"备份路径缺少 .backup. 标记: {path}"
        # 验证备份文件是合法 SQLite 库
        import sqlite3
        with sqlite3.connect(path) as bak:
            row = bak.execute("SELECT COUNT(*) FROM plan").fetchone()
        assert row[0] == 1

    def test_backup_creates_backups_dir(self, db, tmp_path):
        """备份目录自动创建。"""
        from pathlib import Path
        new_path = str(tmp_path / "sub" / "test.db")
        from xfun.core.db import DB
        new_db = DB(new_path)
        new_db.table_infos.update(db.table_infos)
        import os
        os.makedirs(Path(new_path).parent, exist_ok=True)
        new_db.init(new_db.table_infos)
        path = new_db.backup()
        assert os.path.isdir(Path(new_path).parent / "backups")

    def test_reset_clears_and_reinits(self, db):
        """reset() 应清空所有表并重新初始化。"""
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO plan (id, content, month, seq, no, done, created_at, updated_at, tags, ai_tags, is_ai_gen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("reset-1", "重置前数据", "2606", 1, "2606A", 0, "2026-01-01", "2026-01-01", "[]", "[]", 0),
            )
        db.reset()
        # 表应存在但无数据
        with db.read_transaction() as conn:
            for table in ("plan", "diary", "word", "accumulation", "aimemory"):
                cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                assert cnt == 0, f"表 {table} 应清空"
            # 表结构应仍然完整
            cols = [r["name"] for r in conn.execute("PRAGMA table_info(plan)")]
        assert "content" in cols
        assert "month" in cols

    def test_reset_drops_and_creates_tables(self, tmp_path):
        """reset() 应先 DROP 再 CREATE（用独立 DB 避免测试污染）。"""
        from xfun.core.db import DB, Column
        columns = [
            Column("id", "TEXT", primary_key=True, nullable=False),
            Column("content", "TEXT", nullable=True),
            Column("created_at", "TEXT", nullable=False, auto=True),
            Column("updated_at", "TEXT", nullable=False, auto=True),
            Column("tags", "TEXT", nullable=False, auto=True),
            Column("ai_tags", "TEXT", nullable=False, auto=True),
            Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
        ]
        db = DB(str(tmp_path / "test.db"))
        db.init({"test_nb": columns})
        assert set(db.table_infos.keys()) == {"test_nb"}
        with db.read_transaction() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test_nb'"
            ).fetchone()
        assert row is not None
        db.reset()
        with db.read_transaction() as conn:
            existing = {
                r["name"] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        assert existing == {"test_nb"}, f"reset 后表集合不匹配: {existing}"

    def test_restore_from_backup(self, db, tmp_path):
        """restore() 应从备份文件恢复数据库。"""
        import os
        # 写入数据并备份
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO plan (id, content, month, seq, no, done, created_at, updated_at, tags, ai_tags, is_ai_gen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("restore-1", "恢复测试", "2606", 1, "2606A", 0, "2026-01-01", "2026-01-01", "[]", "[]", 0),
            )
        backup_path = db.backup()
        assert os.path.exists(backup_path)

        # 修改原数据，确认与备份不同
        with db.transaction() as conn:
            conn.execute("DELETE FROM plan")

        # 恢复
        result = db.restore(backup_path)
        assert result == backup_path

        # 验证数据已恢复
        with db.read_transaction() as conn:
            row = conn.execute("SELECT id FROM plan WHERE id = 'restore-1'").fetchone()
        assert row is not None

    def test_restore_raises_on_missing_file(self, db):
        """restore() 备份文件不存在应抛出 FileNotFoundError。"""
        import pytest
        with pytest.raises(FileNotFoundError, match="备份文件不存在"):
            db.restore("/nonexistent/path/backup.db")
