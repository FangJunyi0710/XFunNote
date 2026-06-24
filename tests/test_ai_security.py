"""测试 AI 安全沙箱：ai_read_view / ai_write_view 返回的 View 结构。"""

import pytest

from xfun.core.filter import Condition, TRUE_CONDITION
from xfun.core.view import view_to_json
from xfun.ai.security import ai_read_view, ai_write_view


class TestAiReadView:
    """AI 读取权限 View。"""

    def test_returns_view(self):
        v = ai_read_view()
        assert isinstance(v, dict)
        assert len(v) > 0

    def test_contains_all_notebooks(self):
        v = ai_read_view()
        for name in ("plan", "diary", "word", "accumulation", "aimemory"):
            assert name in v, f"缺少本子 {name}"

    def test_each_notebook_has_specs(self):
        v = ai_read_view()
        for table, specs in v.items():
            assert len(specs) >= 1
            for cols, flt in specs:
                assert isinstance(cols, list)
                assert len(cols) > 0

    def test_common_columns_present(self):
        """所有本子都应有基础列（id, content 等）。"""
        v = ai_read_view()
        for table, specs in v.items():
            if table == "aimemory":
                continue  # aimemory 有权限看到所有列
            all_cols = {c for cols, _ in specs for c in cols}
            assert "id" in all_cols
            assert "content" in all_cols

    def test_plan_has_no_and_seq(self):
        """plan 本子应有 no, month, done 列，且无 seq 列（不在白名单中）。"""
        v = ai_read_view()
        plan_cols = {c for cols, _ in v["plan"] for c in cols}
        assert "no" in plan_cols
        assert "month" in plan_cols
        assert "done" in plan_cols
        assert "seq" not in plan_cols

    def test_aimemory_has_all_columns(self):
        """aimemory 本子可读所有列。"""
        v = ai_read_view()
        aimem_cols = {c for cols, _ in v["aimemory"] for c in cols}
        assert "id" in aimem_cols
        assert "content" in aimem_cols
        assert "title" in aimem_cols
        assert "source" in aimem_cols

    def test_contains_private_filter(self):
        """阅读 filter 应排除含 '私密' 标签的数据。"""
        v = ai_read_view()
        for table, specs in v.items():
            if table == "aimemory":
                continue  # aimemory 用 TRUE_CONDITION，无过滤
            for cols, flt in specs:
                flt_str = str(flt)
                assert "私密" in flt_str or flt is TRUE_CONDITION

    def test_json_serializable(self):
        v = ai_read_view()
        json_obj = view_to_json(v)
        import json
        dumped = json.dumps(json_obj, ensure_ascii=False)
        assert isinstance(dumped, str)


class TestAiWriteView:
    """AI 写入权限 View。"""

    def test_returns_view(self):
        v = ai_write_view()
        assert isinstance(v, dict)
        assert len(v) > 0

    def test_contains_all_notebooks(self):
        v = ai_write_view()
        for name in ("plan", "diary", "word", "accumulation", "aimemory"):
            assert name in v, f"缺少本子 {name}"

    def test_no_system_columns_in_write(self):
        """写白名单不应包含系统自动管理的列。"""
        v = ai_write_view()
        for table, specs in v.items():
            all_cols = {c for cols, _ in specs for c in cols}
            assert "id" not in all_cols, f"{table} 写白名单不应有 id"
            assert "is_ai_gen" not in all_cols, f"{table} 写白名单不应有 is_ai_gen"
            assert "created_at" not in all_cols
            assert "updated_at" not in all_cols

    def test_aimemory_write_has_title_source(self):
        v = ai_write_view()
        aimem_cols = {c for cols, _ in v["aimemory"] for c in cols}
        assert "title" in aimem_cols
        assert "source" in aimem_cols

    def test_diary_write_has_mood_weather(self):
        v = ai_write_view()
        diary_cols = {c for cols, _ in v["diary"] for c in cols}
        assert "date" in diary_cols
        assert "mood" in diary_cols
        assert "weather" in diary_cols

    def test_word_write_has_performance(self):
        v = ai_write_view()
        word_cols = {c for cols, _ in v["word"] for c in cols}
        assert "performance" in word_cols
        assert "next_review" in word_cols

    def test_json_serializable(self):
        v = ai_write_view()
        json_obj = view_to_json(v)
        import json
        dumped = json.dumps(json_obj, ensure_ascii=False)
        assert isinstance(dumped, str)
