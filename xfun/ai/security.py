"""
AI 安全沙箱。

定义 AI 可以读取/修改的数据范围，防止 AI 误操作影响用户手工数据。
"""

from typing import List

from xfun import registry
from xfun.core.filter import Condition, Filter, TRUE_CONDITION
from xfun.core.view import View, view_or

_AI_READ_FILTER: Filter = TRUE_CONDITION

_AI_WRITE_FILTER: Filter =[[_AI_READ_FILTER, 
    TRUE_CONDITION
]]

_READ_BASE_COLUMNS: list[str] = ["id", "content", "tags", "created_at", "updated_at", "ai_tags", "ai_note"]
_WRITE_BASE_COLUMNS: list[str] = ["content", "ai_tags", "ai_note"]

_AI_SPEC_READ_VIEW: View = {
    "diary": [(["date", "mood", "weather"], _AI_READ_FILTER)],
    "word": [(["word", "part_of_speech", "phonetic", "example", "related_words", "review_count", "performance", "next_review", "last_review"], _AI_READ_FILTER)],
    "accumulation": [(["category", "source", "note"], _AI_READ_FILTER)],
    "plan": [(["no", "month", "done"], _AI_READ_FILTER)],
}

_AI_SPEC_WRITE_VIEW: View = {
    "diary": [(["date", "mood", "weather"], _AI_WRITE_FILTER)],
    "word": [(["word", "part_of_speech", "phonetic", "example", "related_words", "performance", "next_review"], _AI_WRITE_FILTER)],
    "accumulation": [(["category", "source", "note"], _AI_WRITE_FILTER)],
    "plan": [(["month", "done"], _AI_WRITE_FILTER)],
}


def _ai_comm_read_view() -> View:
    result: View = {}
    for nb in registry:
        result[nb.name] = [(_READ_BASE_COLUMNS, _AI_READ_FILTER)]
    result["aimemory"] = [([c.name for c in registry.notebook("aimemory").columns], TRUE_CONDITION)]
    return result

def ai_read_view() -> View:
    return view_or(_AI_SPEC_READ_VIEW, _ai_comm_read_view())


def _ai_comm_write_view() -> View:
    result: View = {}
    for nb in registry:
        result[nb.name] = [(_WRITE_BASE_COLUMNS, _AI_WRITE_FILTER)]
    result["aimemory"] = [(_WRITE_BASE_COLUMNS + ["title", "source"], TRUE_CONDITION)]
    return result

def ai_write_view() -> View:
    return view_or(_AI_SPEC_WRITE_VIEW, _ai_comm_write_view())

