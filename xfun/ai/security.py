"""
AI 安全沙箱。

定义 AI 可以读取/修改的数据范围，防止 AI 误操作影响用户手工数据。
"""

from typing import List

from xfun.core.filter import Condition, Filter
from xfun.core.view import View


# ========== 行级读权限（View 白名单） ==========
# AI 只能读取 AI 自己创建的行（is_ai_gen=1），且只能访问以下列
AI_READ_VIEW: View = {
    "plan":        [(
        ["id", "content", "tags", "ai_tags", "ai_note", "month", "done", "seq", "no", "created_at"],
        [[Condition("is_ai_gen", 1)]],
    )],
    "diary":       [(
        ["id", "content", "tags", "ai_tags", "ai_note", "date", "mood", "weather", "created_at"],
        [[Condition("is_ai_gen", 1)]],
    )],
    "word":        [(
        ["id", "content", "tags", "ai_tags", "ai_note", "word", "part_of_speech", "phonetic",
         "review_count", "performance", "next_review", "last_review", "related_words", "created_at"],
        [[Condition("is_ai_gen", 1)]],
    )],
    "accumulation": [(
        ["id", "content", "tags", "ai_tags", "ai_note", "category", "source", "note", "created_at"],
        [[Condition("is_ai_gen", 1)]],
    )],
    "aimemory":    [(
        ["id", "title", "content", "tags", "ai_tags", "ai_note", "source", "note", "created_at"],
        [[Condition("is_ai_gen", 1)]],
    )],
}

# ========== 行级写权限（View 白名单） ==========
# AI 只能修改自己创建的行（is_ai_gen=1），且只能写入以下列
AI_WRITE_VIEW: View = {
    "plan":        [(
        ["tags", "ai_tags", "ai_note", "done"],
        [[Condition("is_ai_gen", 1)]],
    )],
    "diary":       [(
        ["tags", "ai_tags", "ai_note"],
        [[Condition("is_ai_gen", 1)]],
    )],
    "word":        [(
        ["tags", "ai_tags", "ai_note", "review_count", "performance", "next_review", "last_review"],
        [[Condition("is_ai_gen", 1)]],
    )],
    "accumulation": [(
        ["tags", "ai_tags", "ai_note"],
        [[Condition("is_ai_gen", 1)]],
    )],
    "aimemory":    [(
        ["tags", "ai_tags", "ai_note", "title", "source", "note"],
        [[Condition("is_ai_gen", 1)]],
    )],
}


def writable_columns(table: str) -> List[str]:
    """返回 AI 可写入的列名列表（从 AI_WRITE_VIEW 派生）。"""
    if table not in AI_WRITE_VIEW:
        return []
    return list({c for spec in AI_WRITE_VIEW[table] for c in spec[0]})


def write_filter(table: str) -> Filter:
    """返回 AI 行级写权限 Filter（从 AI_WRITE_VIEW 派生）。"""
    if table not in AI_WRITE_VIEW:
        return [[Condition("is_ai_gen", 1)]]
    # 合并所有 TableSpec 的 filter（OR 关系）
    filters: List = []
    for _, flt in AI_WRITE_VIEW[table]:
        filters.append(flt)
    if len(filters) == 1:
        return filters[0]
    return filters


def system_columns(table: str) -> List[str]:
    """返回 AI 添加条目时不可写入的系统列（不在可写白名单中的列）。"""
    if table not in AI_READ_VIEW:
        return []
    # 所有已知列 = 读视图列 + 系统自动列
    all_cols = set()
    for spec in AI_READ_VIEW[table]:
        all_cols.update(spec[0])
    all_cols.update(["updated_at", "is_ai_gen", "seq", "no"])
    writable = set(writable_columns(table))
    return sorted(all_cols - writable)
