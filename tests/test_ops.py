"""测试 Ops 操作层 — 高维 CRUD。"""

import pytest

from xfun.core.ops import query, add, update, delete, count
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

    def test_update_with_restricted_write_view(self, registry, db):
        """写视图不允许更新列时 → cleaned_values 为空 → continue (l.44)。"""
        from xfun.core.view import View, full_view

        rview = full_view(db)  # 读权限需包含 plan
        # 写视图允许空列 — _clean_entry 会返回 {}，触发 continue
        wview: View = {"plan": [([], Condition("_", None, "TRUE"))]}
        perm = (rview, wview)

        with db.transaction() as conn:
            # 先插入一条记录准备更新
            full_perm = root_permission(db)
            from xfun.core.ops import add as ops_add
            results = ops_add(conn, full_perm, "plan",
                              [{"content": "test", "month": "2606"}])
            entry_id = results[0]["id"]

        with db.transaction() as conn:
            # 用受限写视图更新 — 写列集为空，cleaned_values == {} → continue
            updated = update(conn, perm, "plan",
                             Condition("id", [entry_id], "IN"),
                             {"content": "should be cleaned"})
        assert updated == []

    def test_count(self, registry, db):
        """count() 应返回满足条件的总条目数（忽略分页与排序）。"""
        perm = root_permission(db)
        with db.transaction() as conn:
            add(conn, perm, "plan", [
                {"content": "a", "month": "2606"},
                {"content": "b", "month": "2606"},
                {"content": "c", "month": "2607"},
            ])

        view_all: View = {"plan": [(["content", "month"], TRUE_CONDITION)]}
        with db.read_transaction() as conn:
            total = count(conn, perm, "plan", view_all)
        assert total == 3

        view_filtered: View = {"plan": [(["month"], Condition("month", "2606", "="))]}
        with db.read_transaction() as conn:
            filtered = count(conn, perm, "plan", view_filtered)
        assert filtered == 2

    def test_count_empty_result(self, registry, db):
        """count() 条件无匹配应返回 0。"""
        perm = root_permission(db)
        view: View = {"plan": [(["month"], Condition("month", "9999", "="))]}
        with db.read_transaction() as conn:
            result = count(conn, perm, "plan", view)
        assert result == 0

    def test_count_view_not_contain_table(self, registry, db):
        """count() 当 view 中不包含目标表时应返回 0（覆盖 view_to_sql 返回空 SQL 的分支）。"""
        perm = root_permission(db)
        view: View = {}  # 空 view，不包含 "plan" 表
        with db.read_transaction() as conn:
            result = count(conn, perm, "plan", view)
        assert result == 0
