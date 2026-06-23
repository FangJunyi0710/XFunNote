"""
AI 系统提示词，从 registry 动态生成本子数据结构。

用法::

    from xfun.ai.prompts import SYSTEM_PROMPT
"""

from xfun import registry
from xfun.core.db import Column
from xfun.core.notebook import BASE_COLUMNS
from xfun.ai.schema import filter_schema_text, view_schema_text
from xfun.utils.time_utils import now_str

# 字段说明：{笔记本名: {字段名: FieldDesc}}
# 空字符串 "" 表示所有本子通用的字段

_FIELD_DESC: dict[str, dict[str, tuple[str, str]]] = {
    "": {
        "id":           ("系统自动生成，无需传入；格式 `{本子名}-{唯一标识}`", "每条记录的唯一标识"),
        "content":      ("字符串文本，长度不限", "记录的核心文本内容，所有本子的主要信息载体"),
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
        "word":         ("单词本身，同时作为 id 字段的唯一标识", "要掌握的单词"),
        "part_of_speech": ("字符串文本，用`, `隔开", "单词词性，如 noun / verb / adj 等"),
        "phonetic":     ("字符串，两端为 `/`，如 `/ˈeksəmpəl/`", "单词音标"),
        "example":      ("字符串文本", "展示单词用法的例句"),
        "related_words": ("字符串文本，用`, `隔开", "语义相关的其他单词，如近反义词、同根词、话题词等"),
        "performance":  ("浮点数 `0.0` — `1.0`", "单词熟练度评分，值越高表示掌握越好"),
        "review_count": ("自动填充计算，初始 `0`", "已复习次数，反映记忆强度"),
        "next_review":  ("日期字符串，YYYY-MM-DD 格式", "计划的下次复习日期，用于间隔复习安排"),
        "last_review":  ("日期字符串，YYYY-MM-DD 格式", "最近一次复习的日期，用于衡量遗忘"),
    },
    "accumulation": {
        "category":     ("字符串文本，用`, `隔开", "知识片段所属的分类，便于归类整理和检索"),
        "source":       ("字符串文本", "知识片段的来源出处（如文章名、书名、视频标题等）"),
        "note":         ("字符串文本", "对知识片段的补充说明或个人思考"),
    },
    "aimemory": {
        "title":        ("字符串文本", "记忆条目的标题，用于快速定位和引用该记忆"),
        "source":       ("字符串文本", "记录该记忆的创建场景"),
    },
}


def _format_column_info(c: Column):
    return f"`{c.name}`({c.col_type}{", 必填" if not c.nullable and not c.auto else "，可空" if c.nullable else "，自动"})"

def _notebook_infos() -> str:
    """遍历 registry 中的 Notebook，生成可读的数据结构描述。"""
    lines = [f"- 各本子共有字段：{", ".join(_format_column_info(c) for c in BASE_COLUMNS)}"]

    for nb in registry:
        lines.append(f"\n本子名称：`{nb.name}`")

        cols = ", ".join(
            _format_column_info(c) for c in nb._extra_columns
        ) or "（无）"
        lines.append(f"- 特有字段：{cols}")

    return "\n".join(lines)


def _field_description_section() -> str:
    """从 _FIELD_DESC 生成 Markdown 表格。"""
    rows = []
    for notebook, fields in _FIELD_DESC.items():
        existing_columns = [col.name for col in (registry.notebook(notebook)._extra_columns if notebook else BASE_COLUMNS)]
        for field, (fmt, role) in fields.items():
            if field not in existing_columns:
                raise ValueError(f"字段 {field} 在 {notebook} 本子中不存在")
            rows.append(f"| `{field}` | {notebook if notebook else "通用"} | {fmt} | {role} |")
    return "\n".join(rows)


SYSTEM_PROMPT = f"""

你是一个个人效率助手，帮助用户管理 "XFunNote" 系统中的数据。

当前系统时间：{now_str()}

## 行为规则
1. **精确筛选**：查询数据时，优先使用 view 精确筛选，避免全表扫描
2. **完整性**：添加数据时，确保必填字段完整
3. **最小修改**：修改数据时，只修改用户要求的字段，不要变更无关数据
4. **删除确认**：删除数据前，必须先查询受影响条目让用户确认
5. **记忆持久**：用户的偏好和规则请使用 `save_memory` 保存到 `aimemory` 本子，确保有清晰的 `title`

## 关键数据结构 JSON Schema 参考

### Filter 格式

Filter 按以下 JSON Schema 严格匹配：

```json
{filter_schema_text()}
```

### View 格式（查询视图）

View 按以下 JSON Schema 严格匹配：

```json
{view_schema_text()}
```

## 本子数据结构
{_notebook_infos()}

## 字段说明
| 字段名 | 所属本子 | 格式说明 | 作用 |
| --- | --- | --- | --- |
{_field_description_section()}

""".strip()
