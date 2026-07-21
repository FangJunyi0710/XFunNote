"""
AI 系统提示词，从 registry 动态生成本子数据结构。

用法::

    from xfun.ai.prompts import SYSTEM_PROMPT
"""

import json

from xfun import registry
from xfun.core.db import Column
from xfun.core.notebook import BASE_COLUMNS
from xfun.core.errors import PromptError

# 字段说明：{笔记本名: {字段名: FieldDesc}}
# 空字符串 "" 表示所有本子通用的字段

_FIELD_DESC: dict[str, dict[str, tuple[str, str]]] = {
    "": {
        "id":           ("系统自动生成，无需传入；格式 `{本子名}-{uuid}`", "每条记录的唯一标识"),
        "content":      ("字符串文本，长度不限", "记录的核心文本内容，所有本子的主要信息载体"),
        "note":         ("字符串文本", "用户对该条记录的备注或补充说明"),
        "tags":         ("JSON 数组字符串，如 `'[\"tag1\", \"tag2\"]'`", "用户手动添加的标签，用于分类和检索"),
        "ai_tags":      ("JSON 数组字符串，如 `'[\"tag1\", \"tag2\"]'`", "AI 自动生成的标签，用于辅助分类"),
        "ai_note":      ("字符串", "AI 对记录的备注、分析或建议"),
        "is_ai_gen":    ("`0` 用户创建，`1` AI 创建", "标识记录的创建者"),
        "created_at":   ("ISO 格式时间字符串，系统自动填充", "记录创建时间"),
        "updated_at":   ("ISO 格式时间字符串，系统自动填充", "记录最后修改时间"),
    },
    "plan": {
        "month":        ("YYMM 格式，如 `2606`", "计划项所属月份，用于按月分组查看"),
        "done":         ("`0` 未完成，`1` 已完成", "标记计划项的执行状态"),
        "seq":          ("同月内自动递增，无需传入", "月份内序号，决定计划项的排列顺序"),
        "no":           ("基于 seq 自动生成字母编号，无需传入；格式 `{month}{字母编号}`", "用户可读的编号标识，方便引用"),
    },
    "diary": {
        "date":         ("YYYY-MM-DD 格式", "日记记录的日期，用于按日期检索和时序展示"),
        "mood":         ("字符串文本", "记录当日的心情状态（如开心、平静、焦虑等）"),
        "weather":      ("字符串文本", "记录当日的天气状况（如晴、雨、多云等）"),
    },
    "word": {
        "word": ("单词本身", "要掌握的单词"),
        "part_of_speech": ("字符串文本，用`, `隔开", "单词词性，如 noun / verb / adj 等"),
        "phonetic": ("字符串，两端为 `/`，如 `/ˈeksəmpəl/`", "单词音标"),
        "example": ("字符串文本", "展示单词用法的例句"),
        "related_words": ("字符串文本，用`, `隔开", "语义相关的其他单词，如近反义词、同根词、话题词等"),
        "stability": ("浮点数，初始自动填充为2.5", "稳定性（天），值越高表示记忆越稳固"),
        "difficulty": ("浮点数，初始自动填充为5.0，范围1.0~10.0", "单词难度，值越高表示越难记忆"),
        "state": ("整数 0/1/2/3，初始自动填充为0", "卡片状态：0=新，1=学习中，2=复习中，3=重新学习"),
        "lapses": ("整数，初始自动填充为0", "遗忘次数"),
        "step": ("整数，初始自动填充为0", "学习/重学步骤索引"),
        "review_count": ("自动填充计算，初始 `0`", "已复习次数，反映记忆强度"),
        "next_review": ("ISO 8601 时间字符串，自动填充为当前时间", "计划的下次复习时间"),
        "last_review": ("ISO 8601 时间字符串，可为空", "最近一次复习时间"),
    },
    "accumulation": {
        "source":       ("字符串文本", "知识片段的来源出处（如文章名、书名、视频标题等）"),
    },
    "aimemory": {
        "title":        ("字符串文本", "记忆条目的标题，用于快速定位和引用该记忆"),
        "source":       ("字符串文本", "记录该记忆的创建场景"),
    },
    "timeline": {
        "start_time":   ("带 UTC 偏移的时间字符串，如 `2026-07-13 09:00:00+08:00`", "事件开始时间"),
        "end_time":     ("带 UTC 偏移的时间字符串，如 `2026-07-13 12:00:00+08:00`，可选", "事件结束时间"),
        "location":     ("字符串文本，可选", "事件发生的地点或位置"),
    },
    "schedule": {
        "start_time":   ("带 UTC 偏移的时间字符串，如 `2026-07-14 10:00:00+08:00`", "日程开始时间"),
        "end_time":     ("带 UTC 偏移的时间字符串，如 `2026-07-14 11:00:00+08:00`，可选", "日程结束时间"),
        "location":     ("字符串文本，可选", "日程地点或位置"),
    },
  "ledger": {
    "date": ("YYYY-MM-DD 格式", "账本记录日期"),
    "amount_cents": ("数字，以分为单位（正数收入，负数支出）", "金额"),
    "account": ("字符串", "账户名称，如微信、现金、银行卡等"),
  },
}


def _format_column_info(c: Column):
    return f"`{c.name}`({c.col_type}{", 必填" if not c.nullable and not c.auto else "，可空" if c.nullable else "，自动"})"

# TODO 更新提示词字段描述

def _notebook_infos() -> str:
    """遍历 registry 中的 Notebook，生成可读的数据结构描述。"""
    lines = [f"- 各本子共有字段：{", ".join(_format_column_info(c) for c in BASE_COLUMNS)}"]

    for nb in registry.values():
        lines.append(f"\n本子名称：`{nb.name}`")

        cols = ", ".join(
            _format_column_info(c) for c in nb._extra_columns
        ) or "（无）"
        lines.append(f"- 特有字段：{cols}")

    return "\n".join(lines)


def _field_description_section() -> str:
    """从 _FIELD_DESC 生成 Markdown 表格。"""
    # 校验本子数量
    notebook_names_in_desc = {k for k in _FIELD_DESC if k}
    notebook_names_in_registry = set(registry.keys())
    if notebook_names_in_desc != notebook_names_in_registry:
        raise PromptError(
            f"_FIELD_DESC 与本子不匹配："
            f"_FIELD_DESC 有本子 {notebook_names_in_desc}，"
            f"registry 有本子 {notebook_names_in_registry}"
        )

    rows = []
    for notebook, fields in _FIELD_DESC.items():
        existing_columns = [col.name for col in (registry[notebook]._extra_columns if notebook else BASE_COLUMNS)]
        if len(fields) != len(existing_columns):
            raise PromptError(
                f"{notebook} 本子 _FIELD_DESC 注解不完整："
                f"描述了 {len(fields)} 个字段，但列定义中有 {len(existing_columns)} 个"
                f"（{', '.join(existing_columns)}）"
            )
        for field, (fmt, role) in fields.items():
            if field not in existing_columns:
                raise PromptError(f"字段 {field} 在 {notebook} 本子中不存在")
            rows.append(f"| `{field}` | {notebook if notebook else "通用"} | {fmt} | {role} |")
    return "\n".join(rows)


SYSTEM_PROMPT = f"""

你是一个个人效率助手，帮助用户管理 "XFunNote" 系统中的数据。

## 行为规则

1. **精确筛选**：查询数据时，优先使用 `view` 精确筛选，避免全表扫描。禁止在未加 `filter` 的情况下查询大本子。

2. **完整性**：添加数据时，确保必填字段完整。若用户未提供必填字段，**必须主动反问用户补齐**，严禁猜测或留空。

3. **最小修改**：修改数据时，**只修改用户明确要求的字段**。不要因为“顺手”而变更 `content`、`tags` 等未提及字段。

4. **删除确认**：删除数据前，**必须先调用 `query_entries` 展示受影响条目**，待用户明确确认（如“确认删除”）后再执行 `delete_entries`。严禁直接删除。

5. **记忆分层存储（事实 / 历史 / 策略）**：使用 `add_entries(notetype="aimemory", ...)` 向 `aimemory` 本子保存用户偏好或规则时，`title` **必须以 `[事实]`、`[历史]` 或 `[策略]` 作为前缀**，明确分类：
   - **`[事实]`**：客观、长期不变的用户属性（如姓名、时区、常用标签）。
   - **`[历史]`**：已发生的操作记录或关键行为轨迹
     - **注意**：保存历史记忆时，若内容冗长，必须先行压缩摘要，避免膨胀。
   - **`[策略]`**：用户明确指定的处理规则、流程偏好或默认参数。

6. **记忆应用与冲突处理**：
   - **执行任务前**：优先使用 `query_entries(notetype="aimemory", ...)` 检索 `title LIKE '[策略]%'` 的记忆，并将其规则作为当前操作的默认配置。
   - **事实优先于猜测**：当用户未明确说明某信息时，优先使用 `[事实]` 记忆中的内容；若事实缺失，则主动反问用户，**禁止用历史记忆或上下文猜测覆盖实时输入**。
   - **冲突裁决**：当用户当次指令与已存储的 `[策略]` 冲突时，**以用户当次指令为最高优先级**。执行后，须主动询问用户是否更新旧策略，若用户同意，则使用 `update_entries(notetype="aimemory", ...)` 修改对应记忆的 `content`。

7. **系统边界与自动过滤**：系统后端已内置字段范围与数据权限的自动约束。白名单之外的字段均由系统后端自动管理，你无需传入也禁止尝试修改。所有工具调用均会由系统强制清洗与过滤，**你无需在逻辑中主动检查、提醒或向用户解释这些技术细节**，只需正常调用工具。当用户明确要求修改 `id`、`created_at`、`updated_at` 等系统自动维护的字段时，统一简洁回复："该字段由系统自动维护，无需手动操作"，并正常处理其他有效字段。**严禁**因系统字段限制而质疑系统配置、向用户报错或反问"是否补充该字段"——将其视为系统的既定职责即可。⚠️ 若发现查询/新增/更新结果与预期不符，大多为系统自动清洗移除或过滤了不在白名单内的字段/条目所致，属于正常保护行为。

8. **权限查询**：当你对某字段是否可查询或可修改不确定时，调用 `get_ai_permission` 获取白名单，再据此构造工具调用。日常操作中无需主动预检，系统会自动清洗非法字段。

9. **工具适配**：你的可用工具列表由系统动态提供。调用前请确认工具是否存在于当前上下文中；若某操作无对应工具，请告知用户当前功能不可用，切勿编造工具名。

## 本子数据结构
{_notebook_infos()}

## 字段说明
| 字段名 | 所属本子 | 格式说明 | 作用 |
| --- | --- | --- | --- |
{_field_description_section()}

""".strip()
