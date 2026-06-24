"""测试 Notebook 基类 CRUD。"""

import re

import pytest

from xfun.core.db import Column, DB
from xfun.core.notebook import Notebook, BASE_COLUMNS
from xfun.core.filter import Condition, filter_to_sql
from xfun.core.errors import EntryInvalidError


class SimpleNotebook(Notebook):
    """用于测试的简单 Notebook 子类。"""
    name = "test_nb"
    _extra_columns = [
        Column("category", "TEXT", nullable=False),
        Column("score", "REAL", nullable=True),
    ]


# ===================================================================
# Notebook 基类
# ===================================================================

class TestNotebookBase:
    def test_columns_merged(self):
        nb = SimpleNotebook()
        assert len(nb.columns) == len(BASE_COLUMNS) + 2
        assert nb.columns[-2].name == "category"
        assert nb.columns[-1].name == "score"
        for i, bc in enumerate(BASE_COLUMNS):
            assert nb.columns[i].name == bc.name

    def test_repr(self):
        nb = SimpleNotebook()
        assert repr(nb) == "<Notebook:test_nb>"

    def test_str(self):
        nb = SimpleNotebook()
        assert str(nb) == "test_nb"

    def test_name_empty_by_default(self):
        class Unnamed(Notebook):
            pass
        assert str(Unnamed()) == "Unnamed"


# ===================================================================
# Notebook CRUD（使用 db 夹具直接操作表）
# ===================================================================

class TestNotebookCRUD:
    NB_NAME = "test_nb"

    @pytest.fixture
    def nb(self, db):
        db.init({self.NB_NAME: SimpleNotebook().columns})
        return SimpleNotebook()

    def _add_test_entries(self, nb, db, entries):
        """辅助：在单独事务中添加条目并返回 ID。"""
        with db.transaction() as conn:
            return nb.add(conn, entries)

    def _get_by_ids(self, nb, db, ids):
        """辅助：在单独事务中查询。"""
        with db.transaction() as conn:
            return nb.get_by_ids(conn, ids)

    def test_add(self, nb, db):
        ids = self._add_test_entries(nb, db, [{"content": "hello", "category": "greeting"}])
        assert len(ids) == 1
        assert ids[0].startswith("test_nb-")

    def test_add_multiple(self, nb, db):
        ids = self._add_test_entries(nb, db, [
            {"content": "a", "category": "cat1"},
            {"content": "b", "category": "cat2"},
        ])
        assert len(ids) == 2

    def test_autofill_defaults(self, nb, db):
        ids = self._add_test_entries(nb, db, [{"content": "test", "category": "cat"}])
        row = self._get_by_ids(nb, db, ids)[0]
        assert row["tags"] == "[]"
        assert row["ai_tags"] == "[]"
        assert row["is_ai_gen"] == 0
        assert row["created_at"] is not None
        assert row["updated_at"] is not None

    def test_add_missing_required_field(self, nb, db):
        with db.transaction() as conn:
            with pytest.raises(EntryInvalidError):
                nb.add(conn, [{"content": "missing category"}])

    def test_get_by_ids(self, nb, db):
        ids = self._add_test_entries(nb, db, [
            {"content": "a", "category": "c1"},
            {"content": "b", "category": "c2"},
        ])
        rows = self._get_by_ids(nb, db, ids)
        assert len(rows) == 2
        assert rows[0]["content"] == "a"
        assert rows[1]["content"] == "b"
        assert rows[0]["id"] == ids[0]
        assert rows[1]["id"] == ids[1]

    def test_get_by_ids_empty(self, nb, db):
        with db.transaction() as conn:
            rows = nb.get_by_ids(conn, [])
        assert rows == []

    def test_get_by_ids_nonexistent(self, nb, db):
        with db.transaction() as conn:
            rows = nb.get_by_ids(conn, ["nonexistent"])
        assert rows == []

    def test_get_by_ids_partial(self, nb, db):
        ids = self._add_test_entries(nb, db, [{"content": "a", "category": "c1"}])
        with db.transaction() as conn:
            rows = nb.get_by_ids(conn, ids + ["nonexistent"])
        assert len(rows) == 1

    def test_list_ids_with_filter(self, nb, db):
        self._add_test_entries(nb, db, [
            {"content": "a", "category": "urgent"},
            {"content": "b", "category": "normal"},
            {"content": "c", "category": "urgent"},
        ])
        with db.transaction() as conn:
            ids = nb.list_ids(conn, [[Condition("category", "urgent", "=")]])
        assert len(ids) == 2

    def test_list_ids_empty_filter(self, nb, db):
        self._add_test_entries(nb, db, [
            {"content": "a", "category": "c1"},
            {"content": "b", "category": "c2"},
        ])
        with db.transaction() as conn:
            ids = nb.list_ids(conn, [[]])
        assert len(ids) == 2

    def test_list_ids_with_order_by(self, nb, db):
        self._add_test_entries(nb, db, [
            {"content": "b", "category": "c2"},
            {"content": "a", "category": "c1"},
        ])
        # 用单次事务包装查询
        with db.transaction() as conn:
            ids = nb.list_ids(conn, [[]], order_by="content ASC")
            rows = nb.get_by_ids(conn, ids)
        assert rows[0]["content"] == "a"

    def test_list_ids_with_limit(self, nb, db):
        self._add_test_entries(nb, db, [
            {"content": f"item{i}", "category": "cat"}
            for i in range(10)
        ])
        with db.transaction() as conn:
            limited = nb.list_ids(conn, [[]], limit=3)
        assert len(limited) == 3

    def test_list_ids_with_offset(self, nb, db):
        self._add_test_entries(nb, db, [
            {"content": f"item{i}", "category": "cat"}
            for i in range(10)
        ])
        with db.transaction() as conn:
            all_ids = nb.list_ids(conn, [[]])
            offset_ids = nb.list_ids(conn, [[]], offset=5)
        assert len(offset_ids) == 5
        assert offset_ids == all_ids[5:]

    def test_delete(self, nb, db):
        ids = self._add_test_entries(nb, db, [{"content": "delete me", "category": "cat"}])
        with db.transaction() as conn:
            nb.delete(conn, ids)
        rows = self._get_by_ids(nb, db, ids)
        assert rows == []

    def test_delete_empty(self, nb, db):
        with db.transaction() as conn:
            nb.delete(conn, [])

    def test_update(self, nb, db):
        ids = self._add_test_entries(nb, db, [{"content": "old", "category": "cat"}])
        with db.transaction() as conn:
            nb.update(conn, ids, {"content": "new"})
        row = self._get_by_ids(nb, db, ids)[0]
        assert row["content"] == "new"

    def test_update_multiple_ids(self, nb, db):
        ids = self._add_test_entries(nb, db, [
            {"content": "a", "category": "c1"},
            {"content": "b", "category": "c2"},
        ])
        with db.transaction() as conn:
            nb.update(conn, ids, {"category": "common"})
        rows = self._get_by_ids(nb, db, ids)
        assert rows[0]["category"] == "common"
        assert rows[1]["category"] == "common"

    def test_update_empty(self, nb, db):
        with db.transaction() as conn:
            nb.update(conn, [], {"content": "new"})

    def test_update_autofills_updated_at(self, nb, db):
        ids = self._add_test_entries(nb, db, [{"content": "old", "category": "cat"}])
        with db.transaction() as conn:
            row = nb.get_by_ids(conn, ids)[0]
            old_updated = row["updated_at"]
        with db.transaction() as conn:
            nb.update(conn, ids, {"content": "new"})
        row = self._get_by_ids(nb, db, ids)[0]
        assert row["updated_at"] != old_updated
