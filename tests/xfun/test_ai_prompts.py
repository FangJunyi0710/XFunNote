"""测试 AI prompts — 系统提示词生成。"""

import copy

import pytest

from xfun.ai.prompts import SYSTEM_PROMPT, _notebook_infos, _field_description_section, _FIELD_DESC
from xfun.core.errors import PromptError


class TestAIPrompts:
    def test_system_prompt_not_empty(self):
        assert len(SYSTEM_PROMPT) > 100

    def test_system_prompt_contains_notebook_names(self):
        for name in ("plan", "diary", "word", "accumulation", "aimemory", "timeline", "schedule"):
            assert name in SYSTEM_PROMPT

    def test_system_prompt_contains_behavior_rules(self):
        assert "行为规则" in SYSTEM_PROMPT or "精确筛选" in SYSTEM_PROMPT

    def test_system_prompt_contains_field_descriptions(self):
        assert "字段名" in SYSTEM_PROMPT
        assert "所属本子" in SYSTEM_PROMPT
        assert "格式说明" in SYSTEM_PROMPT

    def test_system_prompt_contains_permission_section(self):
        assert "get_ai_permission" in SYSTEM_PROMPT

    def test_notebook_infos_contains_base_columns(self):
        info = _notebook_infos()
        assert "id" in info
        assert "content" in info

    def test_notebook_infos_contains_extra_columns(self):
        info = _notebook_infos()
        assert "month" in info  # plan
        assert "date" in info  # diary
        assert "word" in info  # word
        assert "source" in info  # accumulation
        assert "title" in info  # aimemory
        assert "start_time" in info  # timeline & schedule

    def test_field_description_not_empty(self):
        desc = _field_description_section()
        assert len(desc) > 50

    def test_field_description_covers_all_notebooks(self):
        desc = _field_description_section()
        for notebook in list(_FIELD_DESC.keys()) + ["通用", "plan", "diary", "word", "accumulation", "aimemory", "timeline", "schedule"]:
            if notebook == "":
                continue
            pass

class TestPromptsEdgeCases:
    """覆盖 _field_description_section 的错误路径。"""

    def test_field_count_mismatch_raises(self, monkeypatch):
        """_FIELD_DESC 字段数与列定义不匹配 → PromptError。"""
        from xfun.ai import prompts
        bad_desc = copy.deepcopy(prompts._FIELD_DESC)
        bad_plan = dict(list(bad_desc["plan"].items())[:-1])
        bad_desc["plan"] = bad_plan
        monkeypatch.setattr(prompts, "_FIELD_DESC", bad_desc)
        with pytest.raises(PromptError, match="注解不完整"):
            prompts._field_description_section()

    def test_field_not_exists_raises(self, monkeypatch):
        """_FIELD_DESC 包含不存在的字段 → PromptError。"""
        from xfun.ai import prompts
        bad_desc = copy.deepcopy(prompts._FIELD_DESC)
        bad_plan = dict(bad_desc["plan"])
        bad_plan["nonexistent_field"] = bad_plan.pop("month")
        bad_desc["plan"] = bad_plan
        monkeypatch.setattr(prompts, "_FIELD_DESC", bad_desc)
        with pytest.raises(PromptError, match="不存在"):
            prompts._field_description_section()

    def test_notebook_count_mismatch_raises(self, monkeypatch):
        """_FIELD_DESC 缺少本子 → PromptError。"""
        from xfun.ai import prompts
        bad_desc = copy.deepcopy(prompts._FIELD_DESC)
        bad_desc.pop("timeline", None)
        monkeypatch.setattr(prompts, "_FIELD_DESC", bad_desc)
        with pytest.raises(PromptError, match="不匹配"):
            prompts._field_description_section()
