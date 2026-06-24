"""测试 AI Tools — query_entries / add_entries / update_entries / delete_entries。

注意：@tool 装饰器生成 StructuredTool 对象，需用 .invoke() 调用。
这些工具使用 xfun.db 模块级 DB，测试时需 monkeypatch 替换。
"""

import json

import pytest

import xfun
import xfun.ai.tools
from xfun.core import ops
from xfun.core.db import DB
from xfun.core.filter import Condition
from xfun.core.view import root_permission
from xfun.ai.tools import query_entries, add_entries, update_entries, delete_entries
from xfun.ai.schema import ViewModel, FilterModel


# ----------------------------------------------------------------
# 夹具：session 级共享临时 DB + 函数级清表
# ----------------------------------------------------------------

@pytest.fixture(scope="session")
def _shared_ai_db(registry):
    """session 级共享 DB：AI tools 测试用。"""
    import os, tempfile
    tmpf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmpf.close()
    test_db = DB(tmpf.name)
    test_db.init({name: nb.columns for name, nb in registry.items()})
    yield test_db, tmpf.name
    os.unlink(tmpf.name)


@pytest.fixture(autouse=True)
def _patch_db(_shared_ai_db, monkeypatch):
    """函数级：复用 session DB + 清表 + monkeypatch。"""
    test_db, _ = _shared_ai_db
    with test_db.transaction() as conn:
        existing = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        for table in list(test_db.table_infos):
            if table in existing:
                conn.execute(f"DELETE FROM {table}")
    monkeypatch.setattr(xfun, "db", test_db)
    monkeypatch.setattr(xfun.ai.tools, "db", test_db)


# ----------------------------------------------------------------
# 测试
# ----------------------------------------------------------------

class TestAITools:
    def _query(self, view_data: dict, notetype: str, **kwargs):
        view = ViewModel.model_validate(view_data)
        raw = query_entries.invoke({"view": view, "notetype": notetype, **kwargs})
        return json.loads(raw)

    def _add(self, notetype: str, entries: list):
        raw = add_entries.invoke({"notetype": notetype, "entries": entries})
        return json.loads(raw)

    def test_query_empty(self):
        result = self._query(
            {"plan": [{"columns": ["content", "month"], "filter": {"column": "_", "value": None, "op": "TRUE"}}]},
            "plan",
        )
        assert "results" in result
        assert result["results"] == []

    def test_add_and_query(self):
        result = self._add("plan", [{"content": "AI test", "month": "2606"}])
        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["content"] == "AI test"
        assert result["results"][0]["is_ai_gen"] == 1

        qr = self._query(
            {"plan": [{"columns": ["content", "month"], "filter": {"column": "_", "value": None, "op": "TRUE"}}]},
            "plan",
        )
        assert len(qr["results"]) >= 1

    def test_add_entries_with_autofill(self):
        result = self._add("plan", [{"content": "autofill test", "month": "2606"}])
        assert "results" in result
        entry = result["results"][0]
        assert entry["id"].startswith("plan-")
        assert entry["tags"] == "[]"
        assert entry["created_at"] is not None

    def test_update_entries_via_tool(self):
        """通过 update_entries.invoke 覆盖 _update (l.25) + update_entries (l.99-104)。"""
        add_result = self._add("plan", [{"content": "original", "month": "2606"}])
        entry_id = add_result["results"][0]["id"]

        filter_m = FilterModel.model_validate(
            [[{"column": "id", "value": [entry_id], "op": "IN"}]])
        upd_result = json.loads(update_entries.invoke(
            {"notetype": "plan", "filter": filter_m, "values": {"content": "updated"}}))
        assert "results" in upd_result
        assert upd_result["results"][0]["content"] == "updated"

    def test_delete_entries_via_tool(self):
        """通过 delete_entries.invoke 覆盖 _delete (l.28) + delete_entries (l.120-125)。"""
        add_result = self._add("plan", [{"content": "delete me", "month": "2606"}])
        entry_id = add_result["results"][0]["id"]

        filter_m = FilterModel.model_validate(
            [[{"column": "id", "value": [entry_id], "op": "IN"}]])
        del_result = json.loads(delete_entries.invoke(
            {"notetype": "plan", "filter": filter_m}))
        assert "results" in del_result
        assert len(del_result["results"]) == 1

    def test_query_unknown_table(self):
        result = self._query(
            {"nonexistent": [{"columns": ["content"], "filter": {"column": "_", "value": None, "op": "TRUE"}}]},
            "nonexistent",
        )
        assert "results" in result
        assert result["results"] == []

    def test_add_unknown_table(self):
        """向不存在的本子添加条目应返回 error。"""
        result = self._add("nonexistent", [{"content": "test"}])
        assert "error" in result

    def test_entries_are_ai_gen(self):
        result = self._add("plan", [{"content": "ai gen test", "month": "2606"}])
        assert result["results"][0]["is_ai_gen"] == 1

    def test_query_entries_error_handling(self):
        """query_entries 中 XFunError → error JSON (l.58-59)。"""
        view = ViewModel.model_validate({
            "plan": [{"columns": ["content"], "filter": {"column": "_", "value": None, "op": "TRUE"}}]
        })
        result = json.loads(query_entries.invoke({
            "view": view, "notetype": "plan", "order_by": "123invalid",
        }))
        assert "error" in result

    def test_update_entries_error_handling(self):
        """update_entries 中 XFunError → error JSON (l.103-104)。"""
        filter_m = FilterModel.model_validate(
            # 使用 filter 中非法列名触发 Column.check → InvalidSQLError
            [[{"column": "123invalid", "value": 1, "op": "="}]])
        result = json.loads(update_entries.invoke(
            {"notetype": "plan", "filter": filter_m, "values": {"content": "x"}}))
        assert "error" in result

    def test_delete_entries_error_handling(self):
        """delete_entries 中 XFunError → error JSON (l.124-125)。"""
        filter_m = FilterModel.model_validate(
            [[{"column": "123invalid", "value": 1, "op": "="}]])
        result = json.loads(delete_entries.invoke(
            {"notetype": "plan", "filter": filter_m}))
        assert "error" in result

    def test_update_entries_no_match(self):
        """update_entries 匹配 0 条 → 空 results。"""
        filter_m = FilterModel.model_validate(
            [[{"column": "id", "value": ["nonexistent"], "op": "IN"}]])
        upd_result = json.loads(update_entries.invoke(
            {"notetype": "plan", "filter": filter_m, "values": {"content": "x"}}))
        assert "results" in upd_result
        assert upd_result["results"] == []

    def test_delete_entries_no_match(self):
        """delete_entries 匹配 0 条 → 空 results。"""
        filter_m = FilterModel.model_validate(
            [[{"column": "id", "value": ["nonexistent"], "op": "IN"}]])
        del_result = json.loads(delete_entries.invoke(
            {"notetype": "plan", "filter": filter_m}))
        assert "results" in del_result
        assert del_result["results"] == []
