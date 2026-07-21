"""测试 Column 和 DB 核心功能。"""

import re
import sqlite3

import pytest

from xfun.core.db import Column, DB, _check_addition_column, _check_existing_column, _TransactionContext, _ReadTransactionContext
from xfun.core.errors import SQLInvalidError


# ===================================================================
# Column
# ===================================================================

class TestColumn:
    def test_basic_column(self):
        col = Column("id", "TEXT", primary_key=True, nullable=False)
        assert col._sql == "id TEXT PRIMARY KEY NOT NULL"

    def test_nullable_column(self):
        col = Column("name", "TEXT", nullable=True)
        assert col._sql == "name TEXT"

    def test_index_column(self):
        col = Column("email", "TEXT", index=True)
        assert "INDEX" not in col._sql

    def test_auto_column(self):
        col = Column("created_at", "TEXT", auto=True, nullable=True)
        assert col._sql == "created_at TEXT"

    def test_invalid_column_name(self):
        with pytest.raises(SQLInvalidError):
            Column("123col", "TEXT")._sql

    def test_invalid_column_name_special_chars(self):
        with pytest.raises(SQLInvalidError):
            Column("col; DROP TABLE", "TEXT")._sql

    def test_dotted_column_name_valid(self):
        col = Column("table.column", "TEXT", nullable=True)
        assert col._sql == "table.column TEXT"

    def test_check_order_by_single(self):
        Column.check_order_by("month")

    def test_check_order_by_with_direction(self):
        Column.check_order_by("month ASC")
        Column.check_order_by("month DESC")

    def test_check_order_by_multiple(self):
        Column.check_order_by("month ASC, seq DESC")

    def test_check_order_by_invalid_direction(self):
        with pytest.raises(SQLInvalidError):
            Column.check_order_by("month INVALID")

    def test_check_order_by_invalid_name(self):
        with pytest.raises(SQLInvalidError):
            Column.check_order_by("123col")

    def test_check_valid_name(self):
        Column.check("valid_column")

    def test_check_invalid_name(self):
        with pytest.raises(SQLInvalidError):
            Column.check("invalid column")

    def test_check_empty_name(self):
        with pytest.raises(SQLInvalidError):
            Column.check("")


# ===================================================================
# Column 兼容性检查
# ===================================================================

class TestColumnCompatibility:
    def test_addition_column_nullable_not_pk(self):
        _check_addition_column(Column("new_col", "TEXT", nullable=True))

    def test_addition_column_not_null_raises(self):
        with pytest.raises(SQLInvalidError, match="不可为 NULL"):
            _check_addition_column(Column("new_col", "TEXT", nullable=False))

    def test_addition_column_pk_raises(self):
        with pytest.raises(SQLInvalidError, match="不可为 NULL"):
            _check_addition_column(Column("new_col", "TEXT", primary_key=True))
            _check_addition_column(Column("new_col", "TEXT", primary_key=True))
            _check_addition_column(Column("new_col", "TEXT", primary_key=True))

    def test_addition_column_invalid_name_raises(self):
        with pytest.raises(SQLInvalidError):
            _check_addition_column(Column("123col", "TEXT"))

    def test_addition_column_unique_raises(self):
        with pytest.raises(SQLInvalidError, match="不可为 NULL"):
            _check_addition_column(Column("new_col", "TEXT", unique=True))
            _check_addition_column(Column("new_col", "TEXT", unique=True))
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
        with db.transaction() as conn:
            conn.execute(
                "CREATE TABLE test_tb (id TEXT PRIMARY KEY NOT NULL, created_at TEXT NOT NULL, "
                "updated_at TEXT NOT NULL, tags TEXT NOT NULL, ai_tags TEXT NOT NULL, is_ai_gen INTEGER NOT NULL)"
            )
        db.table_infos.update({"test_tb": [
            Column("id", "TEXT", primary_key=True, nullable=False),
            Column("content", "TEXT", nullable=True),
            Column("created_at", "TEXT", nullable=False, auto=True),
            Column("updated_at", "TEXT", nullable=False, auto=True),
            Column("tags", "TEXT", nullable=False, auto=True),
            Column("ai_tags", "TEXT", nullable=False, auto=True),
            Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
        ]})
        db.init()
        with db.read_transaction() as conn:
            cols = [r["name"] for r in conn.execute("PRAGMA table_info(test_tb)")]
        assert "content" in cols

    def test_insert_sql(self, registry, db):
        sql = db._insert_sql("plan")
        assert sql.startswith("INSERT INTO plan")
        assert "content" in sql
        assert "month" in sql

    def test_select_sql(self, registry, db):
        sql = db._select_sql("plan", ["month", "done"])
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
        with db.transaction() as conn:
            conn.execute(
                "CREATE TABLE unique_idx_tb ("
                "id TEXT PRIMARY KEY NOT NULL, "
                "email TEXT UNIQUE NOT NULL, "
                "created_at TEXT NOT NULL, updated_at TEXT NOT NULL, "
                "tags TEXT NOT NULL, ai_tags TEXT NOT NULL, is_ai_gen INTEGER NOT NULL)"
            )
        db.table_infos.update({"unique_idx_tb": [
            Column("id", "TEXT", primary_key=True, nullable=False),
            Column("email", "TEXT", unique=True, index=True, nullable=False),
            Column("created_at", "TEXT", nullable=False, auto=True),
            Column("updated_at", "TEXT", nullable=False, auto=True),
            Column("tags", "TEXT", nullable=False, auto=True),
            Column("ai_tags", "TEXT", nullable=False, auto=True),
            Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
        ]})
        db.init()
        with db.read_transaction() as conn:
            indexes = [
                r["name"] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='unique_idx_tb'"
                )
            ]
        assert any("autoindex" in idx for idx in indexes), "UNIQUE 自动索引应存在"


class TestDBTypeConflict:
    def test_column_type_conflict(self, db):
        with db.transaction() as conn:
            conn.execute(
                "CREATE TABLE conflict_tb (id TEXT PRIMARY KEY NOT NULL, val INTEGER NOT NULL, "
                "created_at TEXT NOT NULL, updated_at TEXT NOT NULL, tags TEXT NOT NULL, "
                "ai_tags TEXT NOT NULL, is_ai_gen INTEGER NOT NULL)"
            )
        with pytest.raises(SQLInvalidError, match="类型冲突"):
            db.table_infos.update({"conflict_tb": [
                Column("id", "TEXT", primary_key=True, nullable=False),
                Column("val", "TEXT", nullable=False),
                Column("created_at", "TEXT", nullable=False, auto=True),
                Column("updated_at", "TEXT", nullable=False, auto=True),
                Column("tags", "TEXT", nullable=False, auto=True),
                Column("ai_tags", "TEXT", nullable=False, auto=True),
                Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
            ]})
            db.init()

    def test_nullable_constraint_conflict(self, db):
        with db.transaction() as conn:
            conn.execute("CREATE TABLE nullable_tb (id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, tags TEXT NOT NULL, ai_tags TEXT NOT NULL, is_ai_gen INTEGER NOT NULL)")
        with pytest.raises(SQLInvalidError, match="约束冲突|类型冲突"):
            db.table_infos.update({"nullable_tb": [Column("id", "TEXT", nullable=True), Column("created_at", "TEXT", nullable=False, auto=True), Column("updated_at", "TEXT", nullable=False, auto=True), Column("tags", "TEXT", nullable=False, auto=True), Column("ai_tags", "TEXT", nullable=False, auto=True), Column("is_ai_gen", "INTEGER", nullable=False, auto=True)]})
            db.init()
            db.table_infos.update({"nullable_tb": [
                Column("id", "TEXT", nullable=True),
                Column("created_at", "TEXT", nullable=False, auto=True),
                Column("updated_at", "TEXT", nullable=False, auto=True),
                Column("tags", "TEXT", nullable=False, auto=True),
                Column("ai_tags", "TEXT", nullable=False, auto=True),
                Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
            ]})
            db.init()
            db.table_infos.update({"nullable_tb": [
                Column("id", "TEXT", nullable=True),
                Column("created_at", "TEXT", nullable=False, auto=True),
                Column("updated_at", "TEXT", nullable=False, auto=True),
                Column("tags", "TEXT", nullable=False, auto=True),
                Column("ai_tags", "TEXT", nullable=False, auto=True),
                Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
            ]})
            db.init()

    def test_pk_constraint_conflict(self, db):
        with db.transaction() as conn:
            conn.execute("CREATE TABLE pk_tb (id TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, tags TEXT NOT NULL, ai_tags TEXT NOT NULL, is_ai_gen INTEGER NOT NULL)")
        with pytest.raises(SQLInvalidError, match="主键|类型冲突"):
            db.table_infos.update({"pk_tb": [Column("id", "TEXT", primary_key=True, nullable=False), Column("created_at", "TEXT", nullable=False, auto=True), Column("updated_at", "TEXT", nullable=False, auto=True), Column("tags", "TEXT", nullable=False, auto=True), Column("ai_tags", "TEXT", nullable=False, auto=True), Column("is_ai_gen", "INTEGER", nullable=False, auto=True)]})
            db.init()
            db.table_infos.update({"pk_tb": [
                Column("id", "TEXT", primary_key=True, nullable=False),
                Column("created_at", "TEXT", nullable=False, auto=True),
                Column("updated_at", "TEXT", nullable=False, auto=True),
                Column("tags", "TEXT", nullable=False, auto=True),
                Column("ai_tags", "TEXT", nullable=False, auto=True),
                Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
            ]})
            db.init()
            db.table_infos.update({"pk_tb": [
                Column("id", "TEXT", primary_key=True, nullable=False),
                Column("created_at", "TEXT", nullable=False, auto=True),
                Column("updated_at", "TEXT", nullable=False, auto=True),
                Column("tags", "TEXT", nullable=False, auto=True),
                Column("ai_tags", "TEXT", nullable=False, auto=True),
                Column("is_ai_gen", "INTEGER", nullable=False, auto=True),
            ]})
            db.init()

        ctx = _ReadTransactionContext.__new__(_ReadTransactionContext)
        ctx.db = None
        ctx.conn = None
        ctx.__exit__(None, None, None)

    def test_read_transaction_rollback_on_error(self, db):
        try:
            with db.read_transaction() as conn:
                raise ValueError("模拟异常")
        except ValueError:
            pass


class TestDBBackupReset:
    def test_backup_creates_file(self, db):
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
        import sqlite3
        with sqlite3.connect(path) as bak:
            row = bak.execute("SELECT COUNT(*) FROM plan").fetchone()
        assert row[0] == 1

    def test_backup_creates_backups_dir(self, db, tmp_path):
        from pathlib import Path
        new_path = str(tmp_path / "sub" / "test.db")
        from xfun.core.db import DB
        new_db = DB(new_path)
        new_db.table_infos.update(db.table_infos)
        import os
        os.makedirs(Path(new_path).parent, exist_ok=True)
        new_db.init()
        path = new_db.backup()
        assert os.path.isdir(Path(new_path).parent / "backups")

    def test_reset_clears_and_reinits(self, db):
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO plan (id, content, month, seq, no, done, created_at, updated_at, tags, ai_tags, is_ai_gen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("reset-1", "重置前数据", "2606", 1, "2606A", 0, "2026-01-01", "2026-01-01", "[]", "[]", 0),
            )
        db.reset()
        with db.read_transaction() as conn:
            for table in ("plan", "diary", "word", "accumulation", "aimemory"):
                cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                assert cnt == 0, f"表 {table} 应清空"
            cols = [r["name"] for r in conn.execute("PRAGMA table_info(plan)")]
        assert "content" in cols
        assert "month" in cols

    def test_reset_drops_and_creates_tables(self, tmp_path):
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
        db.table_infos.update({"test_nb": columns})
        db.init()
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
        import os
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO plan (id, content, month, seq, no, done, created_at, updated_at, tags, ai_tags, is_ai_gen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("restore-1", "恢复测试", "2606", 1, "2606A", 0, "2026-01-01", "2026-01-01", "[]", "[]", 0),
            )
        backup_path = db.backup()
        assert os.path.exists(backup_path)

        with db.transaction() as conn:
            conn.execute("DELETE FROM plan")

        result = db.restore(backup_path)
        assert result == backup_path

        with db.read_transaction() as conn:
            row = conn.execute("SELECT id FROM plan WHERE id = 'restore-1'").fetchone()
        assert row is not None

    def test_restore_raises_on_missing_file(self, db):
        import pytest
        with pytest.raises(FileNotFoundError, match="备份文件不存在"):
            db.restore("/nonexistent/path/backup.db")
