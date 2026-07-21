"""测试 AIMemoryNotebook — AI 记忆本。"""

import pytest

from xfun.core.filter import Condition
from xfun.core.errors import EntryInvalidError


class TestAIMemoryNotebook:
    def test_add_memory(self, registry, db):
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "aimemory", [{
                "content": "用户名叫小方",
                "title": "[事实]姓名",
                "source": "对话初始化",
            }])
        assert len(ids) == 1
        assert ids[0].startswith("aimemory-")

    def test_missing_title_raises(self, registry, db):
        with db.transaction() as conn:
            with pytest.raises(EntryInvalidError, match="缺少必填字段 'title'"):
                conn.db.add_entries(conn, "aimemory", [{
                    "content": "no title",
                    "source": "测试"
                }])

    def test_query_by_title(self, registry, db):
        with db.transaction() as conn:
            conn.db.add_entries(conn, "aimemory", [
                {"content": "name", "title": "[事实]姓名", "source": "t1"},
                {"content": "pref", "title": "[策略]偏好", "source": "t2"},
            ])
        with db.transaction() as conn:
            ids = conn.db.list_ids(conn, "aimemory", [[Condition("title", "[事实]姓名", "=")]])
        assert len(ids) == 1

    def test_title_search_with_like(self, registry, db):
        with db.transaction() as conn:
            conn.db.add_entries(conn, "aimemory", [
                {"content": "fact1", "title": "[事实]时区", "source": "t1"},
                {"content": "fact2", "title": "[事实]姓名", "source": "t2"},
                {"content": "strat1", "title": "[策略]默认", "source": "t3"},
            ])
        with db.transaction() as conn:
            ids = conn.db.list_ids(conn, "aimemory", [[Condition("title", "[事实]%", "LIKE")]])
        assert len(ids) == 2

    def test_source_optional(self, registry, db):
        # source 是必填字段，测试应验证其必填性
        with db.transaction() as conn:
            with pytest.raises(EntryInvalidError, match="缺少必填字段 'source'"):
                conn.db.add_entries(conn, "aimemory", [{"content": "info", "title": "[事实]测试"}])
