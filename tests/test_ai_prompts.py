"""测试 AI 提示词模块：SYSTEM_PROMPT 内容与辅助函数。

依赖全局 xfun.registry（模块加载时已初始化），仅验证生成结果的结构和关键内容。
"""

import re
import pytest

from xfun.ai.prompts import SYSTEM_PROMPT
from xfun.core.errors import PromptError


class TestSystemPromptContent:
    """SYSTEM_PROMPT 静态内容验证。"""

    def test_not_empty(self):
        assert SYSTEM_PROMPT
        assert len(SYSTEM_PROMPT) > 500

    def test_contains_role(self):
        assert "个人效率助手" in SYSTEM_PROMPT

    def test_contains_rules(self):
        """行为规则区域包含编号条目。"""
        assert "## 行为规则" in SYSTEM_PROMPT
        assert re.search(r'\d+\.\s+\*\*', SYSTEM_PROMPT)

    def test_contains_permission_sections(self):
        """应包含读取/写入白名单的 JSON 区域。"""
        assert "可查询字段范围" in SYSTEM_PROMPT
        assert "可修改字段范围" in SYSTEM_PROMPT

    def test_contains_notebook_infos(self):
        assert "plan" in SYSTEM_PROMPT
        assert "diary" in SYSTEM_PROMPT
        assert "word" in SYSTEM_PROMPT
        assert "accumulation" in SYSTEM_PROMPT
        assert "aimemory" in SYSTEM_PROMPT

    def test_contains_field_description_table(self):
        """字段说明表格应有表头。"""
        assert "| 字段名 | 所属本子 | 格式说明 | 作用 |" in SYSTEM_PROMPT

    def test_contains_ai_read_view(self):
        """应包含读白名单的 JSON。"""
        assert "可查询字段范围" in SYSTEM_PROMPT

    def test_contains_ai_write_view(self):
        """应包含写白名单的 JSON。"""
        assert "可修改字段范围" in SYSTEM_PROMPT

    def test_contains_field_descriptions(self):
        """字段说明应包含常见字段描述。"""
        assert "tags" in SYSTEM_PROMPT
        assert "ai_note" in SYSTEM_PROMPT
        assert "content" in SYSTEM_PROMPT

    def test_notebook_specific_fields_present(self):
        """各本子特有字段应出现在说明中。"""
        assert "date" in SYSTEM_PROMPT
        assert "mood" in SYSTEM_PROMPT
        assert "month" in SYSTEM_PROMPT
        assert "word" in SYSTEM_PROMPT
        assert "category" in SYSTEM_PROMPT
        assert "source" in SYSTEM_PROMPT


# ════════════════════════════════════════════════════════════
#  _field_description_section 错误分支测试
#  覆盖 prompts.py:93, 100 + errors.py:54 (PromptError)
# ════════════════════════════════════════════════════════════


def test_field_desc_count_mismatch_raises(monkeypatch):
    """覆盖 prompts.py:93 — _FIELD_DESC 字段数与实际列数不匹配"""
    # plan 有 5 个 _extra_columns，只给 2 个 field_desc 触发不匹配
    monkeypatch.setattr("xfun.ai.prompts._FIELD_DESC", {
        "plan": {
            "month": ("YYMM 格式", "计划月份"),
            "done":  ("0/1", "完成状态"),
        },
    })
    with pytest.raises(PromptError, match="字段"):
        from xfun.ai.prompts import _field_description_section
        _field_description_section()


def test_field_desc_column_not_exists_raises(monkeypatch):
    """覆盖 prompts.py:100 — _FIELD_DESC 中字段在列定义中不存在"""
    # 数量匹配（5 个）但其中一个字段名不对
    monkeypatch.setattr("xfun.ai.prompts._FIELD_DESC", {
        "plan": {
            "nonexistent": ("desc", "desc"),
            "done":        ("0/1", "完成状态"),
            "seq":         ("自动", "序号"),
            "no":          ("编号", "编号"),
            "status":      ("文本", "状态"),
        },
    })
    with pytest.raises(PromptError, match="不存在"):
        from xfun.ai.prompts import _field_description_section
        _field_description_section()
