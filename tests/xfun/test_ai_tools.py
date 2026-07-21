"""测试 AI Tools — 使用 monkeypatch 设置 xfun.db。"""
import os
import tempfile
import pytest
import xfun
from xfun.core.db import DB
from xfun.core.view import root_permission
from xfun.ai.tools import make_tools
from xfun.core.errors import ToolError
from xfun.ai.schema import ViewModel

@pytest.fixture(scope="session")
def shared_db(registry):
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = DB(tmp.name)
    for name, nb in registry.items():
        db.register_hooks(name, pre_add=nb._pre_add, validate=nb._validate, autofill=nb._autofill)
    db.table_infos.update({name: nb.columns for name, nb in registry.items()})
    db.init()
    yield db
    os.unlink(tmp.name)

@pytest.fixture(autouse=True)
def patch_db(shared_db, monkeypatch):
    # 清表
    with shared_db.transaction() as conn:
        existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in list(shared_db.table_infos):
            if table in existing:
                conn.execute(f"DELETE FROM {table}")
    # 设置 xfun.db
    monkeypatch.setattr(xfun, "db", shared_db)
    # 修复 _with_read_tool 和 _with_write_tool 的调用，注入 shared_db
    def _with_read(impl):
        with shared_db.read_transaction() as conn:
            return impl(conn)
    def _with_write(impl):
        with shared_db.transaction() as conn:
            return impl(conn)
    monkeypatch.setattr(xfun.ai.tools, "_with_read_tool", _with_read)
    monkeypatch.setattr(xfun.ai.tools, "_with_write_tool", _with_write)
    # 设置全局变量以便其他模块引用
    import xfun.ai.tools as tools_mod
    tools_mod.db = shared_db
    # 生成工具
    perm = root_permission(shared_db)
    tools = make_tools(
        ["query_entries", "add_entries", "update_entries", "delete_entries", "get_ai_permission"],
        perm
    )
    return {t.name: t for t in tools}

class TestAITools:
    @pytest.fixture(autouse=True)
    def setup(self, patch_db):
        self.tools = patch_db

    def _tool(self, name):
        return self.tools[name]

    def test_query_empty(self):
        view = ViewModel.model_validate({"plan": [{"columns": ["content"], "filter": {"column": "_", "value": None, "op": "TRUE"}}]})
        result = self._tool("query_entries").invoke({"view": view, "notetype": "plan"})
        assert result["results"] == []

    def test_add_and_query(self):
        add = self._tool("add_entries").invoke({"notetype": "plan", "entries": [{"content": "AI test", "month": "2606"}]})
        assert len(add["results"]) == 1
        assert add["results"][0]["is_ai_gen"] == 1
        view = ViewModel.model_validate({"plan": [{"columns": ["content"], "filter": {"column": "_", "value": None, "op": "TRUE"}}]})
        qr = self._tool("query_entries").invoke({"view": view, "notetype": "plan"})
        assert len(qr["results"]) == 1

    def test_add_entries_with_autofill(self):
        result = self._tool("add_entries").invoke({"notetype": "plan", "entries": [{"content": "autofill", "month": "2606"}]})
        entry = result["results"][0]
        assert "id" in entry and entry["id"].startswith("plan-")
        assert "no" in entry

    def test_update_entries_via_tool(self):
        add = self._tool("add_entries").invoke({"notetype": "plan", "entries": [{"content": "to update", "month": "2606"}]})
        eid = add["results"][0]["id"]
        upd = self._tool("update_entries").invoke({
            "notetype": "plan",
            "filter": {"column": "id", "value": eid, "op": "="},
            "values": {"content": "updated"}
        })
        assert upd["results"][0]["content"] == "updated"

    def test_delete_entries_via_tool(self):
        add = self._tool("add_entries").invoke({"notetype": "plan", "entries": [{"content": "to delete", "month": "2606"}]})
        eid = add["results"][0]["id"]
        del_res = self._tool("delete_entries").invoke({
            "notetype": "plan",
            "filter": {"column": "id", "value": eid, "op": "="}
        })
        assert len(del_res["results"]) == 1

    def test_query_unknown_table(self):
        view = ViewModel.model_validate({})
        with pytest.raises(Exception):
            self._tool("query_entries").invoke({"view": view, "notetype": "unknown"})

    def test_add_unknown_table(self):
        with pytest.raises(Exception):
            self._tool("add_entries").invoke({"notetype": "unknown", "entries": [{}]})

    def test_entries_are_ai_gen(self):
        self._tool("add_entries").invoke({"notetype": "plan", "entries": [{"content": "ai", "month": "2606"}]})
        view = ViewModel.model_validate({"plan": [{"columns": ["is_ai_gen"], "filter": {"column": "is_ai_gen", "value": 1, "op": "="}}]})
        qr = self._tool("query_entries").invoke({"view": view, "notetype": "plan"})
        assert len(qr["results"]) == 1

    def test_update_entries_no_match(self):
        res = self._tool("update_entries").invoke({
            "notetype": "plan",
            "filter": {"column": "id", "value": "nonexistent", "op": "="},
            "values": {"content": "nope"}
        })
        assert len(res["results"]) == 0

    def test_delete_entries_no_match(self):
        res = self._tool("delete_entries").invoke({
            "notetype": "plan",
            "filter": {"column": "id", "value": "nonexistent", "op": "="}
        })
        assert len(res["results"]) == 0

    def test_make_tools_unknown_name(self, shared_db):
        with pytest.raises(ToolError):
            make_tools(["unknown"], root_permission(shared_db))
    def test_get_ai_permission(self):
        perm = self._tool("get_ai_permission").invoke({})
        assert "read" in perm and "write" in perm
