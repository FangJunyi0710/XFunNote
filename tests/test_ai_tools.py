"""测试 AI Tools 内部 CRUD 函数及 @tool 集成。

- 内部函数测试（_query / _add / _update / _delete）：直接调用，独立事务。
- @tool 集成测试（invoke）：走完整链路（Pydantic 校验 → 内部函数 → JSON 序列化）。

使用独立 DB 实例 + 全局 registry，每个测试方法独立事务，互不干扰。
"""

import json

import pytest

from xfun import registry
from xfun.core.errors import ToolError
from xfun.core.filter import Condition
from xfun.core.extras import TRUE_CONDITION

from xfun.ai.tools import _query, _add, _update, _delete, query_entries, add_entries, update_entries, delete_entries


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def ai_db(db):
    """用全局 registry 的全量表结构初始化测试 DB。"""
    db.init({name: nb.columns for name, nb in registry.items()})
    return db


@pytest.fixture
def sample_plan(ai_db):
    """在 plan 本子中插入 3 条样本数据。"""
    entries = [
        {"content": "任务一", "month": "2606", "done": 0},
        {"content": "任务二", "month": "2606", "done": 1},
        {"content": "任务三", "month": "2607", "done": 0},
    ]
    with ai_db.transaction() as conn:
        ids = _add(conn, "plan", entries)
    return ids


def _plan_view(*, cols: list[str] | None = None, flt=None):
    """构造一个针对 plan 表的查询 View，列名取自 AI_READ_VIEW 白名单。"""
    return {"plan": [(cols or ["content", "month", "done"], flt or TRUE_CONDITION)]}


# ── _add ─────────────────────────────────────────────────────────────

class TestAdd:
    def test_add_single(self, ai_db):
        with ai_db.transaction() as conn:
            ids = _add(conn, "plan", [{"content": "新任务", "month": "2606"}])
        assert len(ids) == 1
        assert isinstance(ids[0], str)

    def test_add_multiple(self, ai_db):
        entries = [
            {"content": "a", "month": "2606"},
            {"content": "b", "month": "2606"},
        ]
        with ai_db.transaction() as conn:
            ids = _add(conn, "plan", entries)
        assert len(ids) == 2

    def test_add_auto_injects_is_ai_gen(self, ai_db):
        with ai_db.transaction() as conn:
            ids = _add(conn, "plan", [{"content": "AI生成", "month": "2606"}])
        with ai_db.read_transaction() as conn:
            row = conn.execute("SELECT is_ai_gen FROM plan WHERE id = ?", (ids[0],)).fetchone()
        assert row["is_ai_gen"] == 1

    def test_add_strips_unknown_columns(self, ai_db):
        """超出写白名单的字段应被自动清洗。"""
        with ai_db.transaction() as conn:
            ids = _add(conn, "plan", [{"content": "测试", "month": "2606", "secret_field": "should_be_removed"}])
        with ai_db.read_transaction() as conn:
            cols = [desc[0] for desc in conn.execute("SELECT * FROM plan WHERE id = ?", (ids[0],)).description]
        assert "secret_field" not in cols

    def test_add_unknown_notebook_raises(self, ai_db):
        with pytest.raises(ToolError, match="未知本子"):
            with ai_db.transaction() as conn:
                _add(conn, "nonexistent_notebook", [{"content": "x"}])


# ── _query ────────────────────────────────────────────────────────────

class TestQuery:
    def test_query_all(self, ai_db, sample_plan):
        with ai_db.read_transaction() as conn:
            rows = _query(conn, "plan", _plan_view())
        assert len(rows) == 3

    def test_query_with_filter(self, ai_db, sample_plan):
        with ai_db.read_transaction() as conn:
            rows = _query(conn, "plan", _plan_view(
                flt=[[Condition("month", "2606", "=")]],
            ))
        assert len(rows) == 2

    def test_query_with_order_by(self, ai_db, sample_plan):
        with ai_db.read_transaction() as conn:
            rows = _query(conn, "plan", _plan_view(), order_by="created_at DESC")
        assert len(rows) == 3
        # 验证降序：后插入的 id 先出现
        ids_order = [r["id"] for r in rows]
        assert ids_order == list(reversed(sorted(ids_order)))

    def test_query_with_limit(self, ai_db, sample_plan):
        with ai_db.read_transaction() as conn:
            rows = _query(conn, "plan", _plan_view(), limit=2)
        assert len(rows) == 2

    def test_query_with_limit_and_offset(self, ai_db, sample_plan):
        with ai_db.read_transaction() as conn:
            rows = _query(conn, "plan", _plan_view(), limit=2, offset=1)
        assert len(rows) == 2

    def test_query_table_not_in_view(self, ai_db, sample_plan):
        """view 中未指定表名时，不报错，直接返回空。"""
        with ai_db.read_transaction() as conn:
            rows = _query(conn, "plan", {"other_table": [(["content"], TRUE_CONDITION)]})
        assert rows == []

    def test_query_unknown_notebook_raises(self, ai_db):
        with pytest.raises(ToolError, match="未知本子"):
            with ai_db.read_transaction() as conn:
                _query(conn, "BAD_TABLE", {"BAD_TABLE": []})

    def test_query_table_not_in_safe_view(self, ai_db, monkeypatch):
        """覆盖 tools.py:35 — ai_read_view 不包含目标表时返回 []"""
        monkeypatch.setattr("xfun.ai.tools.ai_read_view", lambda: {})
        with ai_db.read_transaction() as conn:
            rows = _query(conn, "plan", {"plan": [(["content"], TRUE_CONDITION)]})
        assert rows == []

    def test_query_view_to_sql_empty(self, ai_db, monkeypatch):
        """覆盖 tools.py:39 — view_to_sql 返回空时返回 []"""
        monkeypatch.setattr("xfun.ai.tools.view_to_sql",
                            lambda view, db, table: ("", []))
        with ai_db.read_transaction() as conn:
            rows = _query(conn, "plan", {"plan": [(["content"], TRUE_CONDITION)]})
        assert rows == []


# ── _update ──────────────────────────────────────────────────────────

class TestUpdate:
    def test_update_by_filter(self, ai_db, sample_plan):
        with ai_db.transaction() as conn:
            ids = _update(conn, "plan",
                [[Condition("month", "2606", "=")]],
                {"done": 1},
            )
        assert len(ids) == 2  # 2606 月份有 2 条

        with ai_db.read_transaction() as conn:
            for _id in ids:
                row = conn.execute("SELECT done FROM plan WHERE id = ?", (_id,)).fetchone()
                assert row["done"] == 1

    def test_update_all_matching(self, ai_db, sample_plan):
        with ai_db.transaction() as conn:
            ids = _update(conn, "plan",
                [[Condition("_", None, "TRUE")]],
                {"content": "已更新"},
            )
        assert len(ids) == 3

    def test_update_no_match_raises(self, ai_db):
        with pytest.raises(ToolError, match="没有可更新的条目"):
            with ai_db.transaction() as conn:
                _update(conn, "plan",
                    [[Condition("month", "2999", "=")]],
                    {"content": "无处更新"},
                )

    def test_update_no_updatable_fields_raises(self, ai_db, sample_plan):
        """不在写白名单中的字段应被清洗为空，触发异常。"""
        with pytest.raises(ToolError, match="没有可更新的字段"):
            with ai_db.transaction() as conn:
                _update(conn, "plan",
                    [[Condition("month", "2606", "=")]],
                    {"is_ai_gen": 0},  # is_ai_gen 不在写白名单中
                )

    def test_update_unknown_notebook_raises(self, ai_db):
        with pytest.raises(ToolError, match="未知本子"):
            with ai_db.transaction() as conn:
                _update(conn, "BAD", [[Condition("a", 1)]], {"content": "x"})


# ── _delete ──────────────────────────────────────────────────────────

class TestDelete:
    def test_delete_by_filter(self, ai_db, sample_plan):
        with ai_db.transaction() as conn:
            deleted = _delete(conn, "plan",
                [[Condition("month", "2607", "=")]],
            )
        assert len(deleted) == 1

        with ai_db.read_transaction() as conn:
            remaining = conn.execute("SELECT COUNT(*) AS cnt FROM plan").fetchone()
        assert remaining["cnt"] == 2

    def test_delete_no_match_raises(self, ai_db):
        with pytest.raises(ToolError, match="没有可删除的条目"):
            with ai_db.transaction() as conn:
                _delete(conn, "plan",
                    [[Condition("month", "2999", "=")]],
                )

    def test_delete_unknown_notebook_raises(self, ai_db):
        with pytest.raises(ToolError, match="未知本子"):
            with ai_db.transaction() as conn:
                _delete(conn, "BAD", [[Condition("a", 1)]])


# ════════════════════════════════════════════════════════════
#  @tool 集成测试 — 使用 tool.invoke() 走完整链路
#  自动完成 Pydantic 校验 → 内部 CRUD → JSON 序列化
# ════════════════════════════════════════════════════════════


class TestToolQueryEntries:
    """query_entries @tool 集成测试 — 自动 patch 全局 db 为测试实例。"""

    @pytest.fixture(autouse=True)
    def _patch_db(self, ai_db, monkeypatch):
        monkeypatch.setattr("xfun.ai.tools.db", ai_db)

    def test_query_returns_json(self, sample_plan):
        result = query_entries.invoke({
            "view": {"plan": [{"columns": ["content", "month", "done"],
                               "filter": {"column": "_", "value": None, "op": "TRUE"}}]},
            "notetype": "plan",
        })
        data = json.loads(result)
        assert "results" in data
        assert len(data["results"]) == 3

    def test_query_with_limit(self, sample_plan):
        result = query_entries.invoke({
            "view": {"plan": [{"columns": ["content", "month", "done"],
                               "filter": {"column": "_", "value": None, "op": "TRUE"}}]},
            "notetype": "plan",
            "limit": 2,
        })
        data = json.loads(result)
        assert len(data["results"]) == 2

    def test_query_unknown_notebook(self):
        result = query_entries.invoke({
            "view": {"bad": [{"columns": ["content"],
                              "filter": {"column": "_", "value": None, "op": "TRUE"}}]},
            "notetype": "BAD",
        })
        data = json.loads(result)
        assert "error" in data


class TestToolAddEntries:
    """add_entries @tool 集成测试 — 自动 patch 全局 db 为测试实例。"""

    @pytest.fixture(autouse=True)
    def _patch_db(self, ai_db, monkeypatch):
        monkeypatch.setattr("xfun.ai.tools.db", ai_db)

    def test_add_returns_json(self):
        result = add_entries.invoke({
            "notetype": "plan",
            "entries": [{"content": "invoke add test", "month": "2606"}],
        })
        data = json.loads(result)
        assert "results" in data
        assert len(data["results"]) == 1

    def test_add_unknown_notebook(self):
        result = add_entries.invoke({
            "notetype": "BAD",
            "entries": [{"content": "x"}],
        })
        data = json.loads(result)
        assert "error" in data


class TestToolUpdateEntries:
    """update_entries @tool 集成测试 — 自动 patch 全局 db 为测试实例。"""

    @pytest.fixture(autouse=True)
    def _patch_db(self, ai_db, monkeypatch):
        monkeypatch.setattr("xfun.ai.tools.db", ai_db)

    def test_update_returns_json(self, sample_plan):
        result = update_entries.invoke({
            "notetype": "plan",
            "filter": [[{"column": "month", "value": "2606", "op": "="}]],
            "values": {"done": 1},
        })
        data = json.loads(result)
        assert "results" in data
        assert len(data["results"]) == 2

    def test_update_no_match(self):
        result = update_entries.invoke({
            "notetype": "plan",
            "filter": [[{"column": "month", "value": "2999", "op": "="}]],
            "values": {"done": 1},
        })
        data = json.loads(result)
        assert "error" in data


class TestToolDeleteEntries:
    """delete_entries @tool 集成测试 — 自动 patch 全局 db 为测试实例。"""

    @pytest.fixture(autouse=True)
    def _patch_db(self, ai_db, monkeypatch):
        monkeypatch.setattr("xfun.ai.tools.db", ai_db)

    def test_delete_returns_json(self, sample_plan):
        result = delete_entries.invoke({
            "notetype": "plan",
            "filter": [[{"column": "month", "value": "2607", "op": "="}]],
        })
        data = json.loads(result)
        assert "results" in data
        assert len(data["results"]) == 1

    def test_delete_no_match(self):
        result = delete_entries.invoke({
            "notetype": "plan",
            "filter": [[{"column": "month", "value": "2999", "op": "="}]],
        })
        data = json.loads(result)
        assert "error" in data
