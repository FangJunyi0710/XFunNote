"""测试 AIMemoryNotebook — AI 记忆本。"""

import pytest

from xfun.core.filter import Condition


class TestAIMemoryNotebook:
    def test_add_memory(self, registry, db):
        nb = registry["aimemory"]
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "aimemory", [{
                "content": "用户名叫小方",
                "title": "[事实]姓名",
                "source": "对话初始化",
            }])
        assert len(ids) == 1
        assert ids[0].startswith("aimemory-")

    def test_missing_title_raises(self, registry, db):
        nb = registry["aimemory"]
        with db.transaction() as conn:
            with pytest.raises(Exception):
                conn.db.add_entries(conn, "aimemory", [{"content": "no title"}])

    def test_query_by_title(self, registry, db):
        nb = registry["aimemory"]
        with db.transaction() as conn:
            conn.db.add_entries(conn, "aimemory", [
                {"content": "name", "title": "[事实]姓名"},
                {"content": "pref", "title": "[策略]偏好"},
            ])
        with db.transaction() as conn:
            ids = conn.db.list_ids(conn, "aimemory", [[Condition("title", "[事实]姓名", "=")]])
        assert len(ids) == 1

    def test_title_search_with_like(self, registry, db):
        nb = registry["aimemory"]
        with db.transaction() as conn:
            conn.db.add_entries(conn, "aimemory", [
                {"content": "fact1", "title": "[事实]时区"},
                {"content": "fact2", "title": "[事实]姓名"},
                {"content": "strat1", "title": "[策略]默认"},
            ])
        with db.transaction() as conn:
            ids = conn.db.list_ids(conn, "aimemory", [[Condition("title", "[事实]%", "LIKE")]])
        assert len(ids) == 2

    def test_source_optional(self, registry, db):
        nb = registry["aimemory"]
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "aimemory", [{"content": "info", "title": "[事实]测试"}])
        with db.transaction() as conn:
            row = conn.db.get_by_ids(conn, "aimemory", ids)[0]
        assert row["source"] is None
