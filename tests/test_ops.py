"""测试 Ops 操作层 — 高维 CRUD。"""

import pytest

from xfun.core.ops import query, add, update, delete
from xfun.core.filter import Condition, TRUE_CONDITION
from xfun.core.view import View, root_permission


class TestOps:
    def test_add_and_query(self, registry, db):
        nb = registry["plan"]
        perm = root_permission(db)
        view: View = {"plan": [(["content", "month"], TRUE_CONDITION)]}

        with db.transaction() as conn:
            results = add(conn, perm, "plan", [{"content": "test", "month": "2606"}])
        assert len(results) == 1
        assert results[0]["content"] == "test"

        with db.read_transaction() as conn:
            qresults = query(conn, perm, "plan", view)
        assert len(qresults) == 1

    def test_query_with_filter(self, registry, db):
        nb = registry["plan"]
        perm = root_permission(db)

        with db.transaction() as conn:
            add(conn, perm, "plan", [
                {"content": "a", "month": "2606"},
                {"content": "b", "month": "2607"},
            ])

        view: View = {"plan": [(["content", "month"], TRUE_CONDITION)]}
        with db.read_transaction() as conn:
            results = query(conn, perm, "plan", view, order_by="content ASC")
        assert results[0]["content"] == "a"
        assert results[1]["content"] == "b"

    def test_query_with_limit(self, registry, db):
        perm = root_permission(db)
        with db.transaction() as conn:
            add(conn, perm, "plan", [
                {"content": f"item{i}", "month": "2606"}
                for i in range(10)
            ])
        view: View = {"plan": [(["content"], TRUE_CONDITION)]}
        with db.read_transaction() as conn:
            results = query(conn, perm, "plan", view, limit=3)
        assert len(results) == 3

    def test_update(self, registry, db):
        nb = registry["plan"]
        perm = root_permission(db)

        with db.transaction() as conn:
            results = add(conn, perm, "plan", [{"content": "old", "month": "2606"}])
            entry_id = results[0]["id"]

        with db.transaction() as conn:
            updated = update(conn, perm, "plan",
                             Condition("id", [entry_id], "IN"),
                             {"content": "new"})
        assert len(updated) == 1
        assert updated[0]["content"] == "new"

    def test_delete(self, registry, db):
        perm = root_permission(db)
        with db.transaction() as conn:
            results = add(conn, perm, "plan", [{"content": "delete", "month": "2606"}])
            entry_id = results[0]["id"]

        with db.transaction() as conn:
            deleted = delete(conn, perm, "plan",
                             Condition("id", [entry_id], "IN"))
        assert len(deleted) == 1
        assert deleted[0]["id"] == entry_id

        # 确认已删除
        with db.read_transaction() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM plan WHERE id=?", (entry_id,)).fetchone()
        assert row["cnt"] == 0

    def test_delete_with_filter_empty_result(self, registry, db):
        """删除不存在的条目应返回空列表且不报错。"""
        perm = root_permission(db)
        with db.transaction() as conn:
            deleted = delete(conn, perm, "plan", Condition("id", "nonexistent", "="))
        assert deleted == []

    def test_update_no_match(self, registry, db):
        """update 时 filter 匹配 0 条 → 空结果 (l.48)。"""
        perm = root_permission(db)
        with db.transaction() as conn:
            results = update(conn, perm, "plan",
                             Condition("id", "nonexistent", "="),
                             {"content": "whatever"})
        assert results == []
