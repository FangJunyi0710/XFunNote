"""测试 AI 安全沙箱 — 权限视图。"""

from xfun.ai.security import ai_permission, _AI_READ_FILTER, _AI_WRITE_FILTER
from xfun.core.filter import filter_to_sql
from xfun.core.view import View


class TestAISecurity:
    def test_ai_permission_returns_tuple(self):
        perm = ai_permission()
        assert len(perm) == 2
        rview, wview = perm
        assert isinstance(rview, dict)
        assert isinstance(wview, dict)

    def test_all_notebooks_in_read_view(self):
        rview, wview = ai_permission()
        assert "aimemory" in rview
        assert "aimemory" in wview

    def test_plan_in_read_view(self):
        rview, wview = ai_permission()
        assert "plan" in rview

    def test_read_filter_excludes_private(self):
        sql, params = filter_to_sql(_AI_READ_FILTER)
        assert "json_each" in sql or "私密" in str(params) or "私密" in sql

    def test_read_base_columns_present(self):
        """每个本子的读视图至少有一个字段白名单。"""
        rview, wview = ai_permission()
        for table in ("plan", "diary", "word", "accumulation"):
            assert table in rview
            for cols, _ in rview[table]:
                assert len(cols) > 0

    def test_accumulation_read_has_category(self):
        rview, wview = ai_permission()
        # accumulation 在 _AI_SPEC_READ_VIEW 中有 category/source/note
        plan_cols = []
        for cols, _ in rview.get("accumulation", []):
            plan_cols.extend(cols)
        assert "category" in plan_cols or "source" in plan_cols or "note" in plan_cols

    def test_aimemory_full_access(self):
        rview, wview = ai_permission()
        assert len(rview["aimemory"]) > 0
        assert len(wview["aimemory"]) > 0
