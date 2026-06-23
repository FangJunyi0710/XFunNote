"""
AI 系统提示词，从 registry 动态生成本子数据结构。

用法::

    from xfun.ai.prompts import SYSTEM_PROMPT
"""

from xfun import registry
from xfun.core.db import Column
from xfun.core.notebook import BASE_COLUMNS

# 本子信息映射：display_name + 描述
_NOTEBOOK_INFO: dict[str, tuple[str, str]] = {
    "plan":         ("plan（计划本）",   "月度计划，管理待办事项与目标条目"),
    "diary":        ("diary（日记本）",  "以日期为分组，记录每日日记与心情"),
    "word":         ("word（单词本）",    "英语单词学习，记录拼写、音标、例句与复习进度"),
    "accumulation": ("accumulation（积累本）", "知识累积，记录摘录、灵感，按分类管理"),
    "aimemory":     ("aimemory（AI 记忆本）",  "AI 记忆沉淀，存储用户偏好与结构化记忆"),
}

def _format_column(c: Column):
    return f"{c.name}({c.col_type}{", 必填" if not c.nullable and not c.auto else ""})"
def _notebook_infos() -> str:
    """遍历 registry 中的 Notebook，生成可读的数据结构描述。"""
    lines = [f"各本子共有字段：{", ".join(_format_column(c) for c in BASE_COLUMNS)}"]

    for nb in registry:
        lines.append(f"\n本子名称：**{nb.name}**")

        cols = ", ".join(
            _format_column(c) for c in nb._extra_columns
        ) or "（无）"
        lines.append(f"  特有字段：{cols}")

    return "\n".join(lines)


SYSTEM_PROMPT = f"""\
你是一个个人效率助手，帮助用户管理 "XFunNote" 系统中的数据。

## 行为规则
1. **精确筛选**：查询数据时，优先使用 filter 精确筛选，避免全表扫描
2. **完整性**：添加数据时，确保必填字段完整
3. **最小修改**：修改数据时，只修改用户要求的字段，不要变更无关数据
4. **删除确认**：删除数据前，必须先查询受影响条目让用户确认
5. **日报生成**：生成日报时，同时查询 plan/diary/word/accumulation 当天的数据
6. **记忆持久**：用户的偏好和规则请使用 `save_memory` 保存到 aimemory 本子，确保有清晰的 title

## 本子数据结构
{_notebook_infos()}

## 字段格式说明

""".strip()
