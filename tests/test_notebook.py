"""测试 Notebook CRUD 集成：增删改查在主流程上是否正常工作。"""

import pytest
from xfun.core.db import Column
from xfun.core.filter import Condition
from xfun.core.errors import EntryInvalidError
from xfun.core.notebook import Notebook, BASE_COLUMNS


class _EmptyColumnsNotebook(Notebook):
    """没有列的 notebook，用于测试 init_table 空列分支。"""
    name = "empty_nb"

    @property
    def columns(self):
        return []


class TestCRUD:
    """验证完整 CRUD 流程走通，而不是逐行检查基类代码。"""

    def test_add_then_get(self, db, test_nb):
        db.init({test_nb.name: test_nb.columns})
        with db.transaction() as conn:
            ids = test_nb.add(conn, [
                {"content": "hello", "title": "A"},
                {"content": "world", "title": "B"},
            ])
        assert len(ids) == 2
        assert ids[0] != ids[1]

        with db.read_transaction() as conn:
            results = test_nb.get_by_ids(conn, ids)
        assert len(results) == 2
        assert results[0]["title"] == "A"

    def test_add_then_list_with_filter(self, db, test_nb):
        db.init({test_nb.name: test_nb.columns})
        with db.transaction() as conn:
            test_nb.add(conn, [
                {"content": "A", "title": "X"},
                {"content": "B", "title": "Y"},
                {"content": "C", "title": "Z"},
            ])
        with db.read_transaction() as conn:
            ids = test_nb.list_ids(conn, [[Condition("title", "Y")]])
        assert len(ids) == 1

    def test_add_then_delete(self, db, test_nb):
        db.init({test_nb.name: test_nb.columns})
        with db.transaction() as conn:
            ids = test_nb.add(conn, [
                {"content": "A", "title": "X"},
                {"content": "B", "title": "Y"},
            ])
            test_nb.delete(conn, [ids[0]])
        with db.read_transaction() as conn:
            remaining = test_nb.get_by_ids(conn, ids)
        assert len(remaining) == 1

    def test_add_then_update(self, db, test_nb):
        db.init({test_nb.name: test_nb.columns})
        with db.transaction() as conn:
            ids = test_nb.add(conn, [{"content": "A", "title": "X"}])
            test_nb.update(conn, ids, {"title": "Y"})
        with db.read_transaction() as conn:
            result = test_nb.get_by_ids(conn, ids)
        assert result[0]["title"] == "Y"
        assert result[0]["content"] == "A"  # 未更新字段不变


class TestValidate:
    """验证必填字段检查生效。"""

    def test_missing_required_raises(self, test_nb):
        with pytest.raises(EntryInvalidError):
            test_nb._validate({"content": "hello"})  # 缺 title


class TestNotebookEdgeCases:
    """Notebook 基类的边界分支覆盖。"""

    def test_get_by_id_empty(self, db, test_nb):
        """空 ID 列表应直接返回 []。"""
        with db.read_transaction() as conn:
            assert test_nb.get_by_ids(conn, []) == []

    def test_init_table_empty_columns(self, db):
        """没有列的 notebook，init 应直接返回。"""
        nb = _EmptyColumnsNotebook()
        db.init({nb.name: nb.columns})  # 不抛异常即通过

    def test_list_with_order_by(self, db, test_nb):
        """list 传入 order_by 参数。"""
        db.init({test_nb.name: test_nb.columns})
        with db.transaction() as conn:
            test_nb.add(conn, [
                {"content": "C", "title": "Z"},
                {"content": "A", "title": "X"},
                {"content": "B", "title": "Y"},
            ])
        with db.read_transaction() as conn:
            ids = test_nb.list_ids(conn, [], order_by="title ASC")
        with db.read_transaction() as conn:
            results = test_nb.get_by_ids(conn, ids)
        assert [r["title"] for r in results] == ["X", "Y", "Z"]

    def test_delete_empty(self, db, test_nb):
        """空列表 delete 应无操作。"""
        db.init({test_nb.name: test_nb.columns})
        with db.transaction() as conn:
            test_nb.delete(conn, [])  # 不抛异常即通过

    def test_update_empty(self, db, test_nb):
        """空列表 update 应无操作。"""
        db.init({test_nb.name: test_nb.columns})
        with db.transaction() as conn:
            test_nb.update(conn, [], {"title": "X"})  # 不抛异常即通过

    def test_repr(self, test_nb):
        assert repr(test_nb) == "<Notebook:test_nb>"

    def test_str(self, test_nb):
        assert str(test_nb) == "test_nb"

    def test_str_fallback(self):
        """name 为空时使用类名。"""
        class _NoName(Notebook):
            pass
        nb = _NoName()
        assert str(nb) == "_NoName"


class TestTransaction:
    """验证回滚语义正确。"""

    def test_rollback_undoes_insert(self, db, test_nb):
        # 先建表
        db.init({test_nb.name: test_nb.columns})
        # 插入操作在另一个事务中回滚
        with pytest.raises(RuntimeError):
            with db.transaction() as conn:
                test_nb.add(conn, [{"content": "hello", "title": "A"}])
                raise RuntimeError("rollback!")
        # 回滚后表还在但无数据
        with db.read_transaction() as conn:
            rows = conn.execute("SELECT * FROM test_nb").fetchall()
        assert len(rows) == 0
