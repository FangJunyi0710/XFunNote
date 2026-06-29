"""AI 对话业务逻辑。"""

from __future__ import annotations
from typing import Any

from langchain_core.messages import BaseMessage

from xfun.ai.agent import (
    StreamLevel,
    accumulate_messages,
    agent_invoke,
    ensure_system_message,
    messages_to_json,
    parse_messages_json,
)
from xfun.ai.prompts import SYSTEM_PROMPT
from xfun.ai.tools import (
    add_entries,
    delete_entries,
    get_ai_permission,
    query_entries,
    update_entries,
)
from xfun.ai.security import ai_permission
from xfun.core.view import view_to_json

_AI_TOOLS = [
    query_entries,
    add_entries,
    update_entries,
    delete_entries,
    get_ai_permission,
]


def chat(
    messages: list[dict],
    system_prompt: str | None = None,
    max_iterations: int = 10,
    llm_kwargs: dict[str, Any] | None = None,
) -> list[dict]:
    """AI 对话（同步非流式）。输入输出均为序列化消息列表。

    Parameters
    ----------
    messages : list[dict]
        对话历史，格式 ``[{"role": "user", "content": "..."}, ...]``。
    system_prompt : str | None
        自定义系统提示词，默认使用内置 SYSTEM_PROMPT。
    max_iterations : int
        最大工具调用轮次。
    llm_kwargs : dict | None
        传递给 ChatAnthropic 的额外参数（如 temperature）。

    Returns
    -------
    list[dict]
        完整的对话历史（含新增消息），格式同输入。
    """
    prompt_text = system_prompt or SYSTEM_PROMPT
    msgs = parse_messages_json(messages)
    ensure_system_message(msgs, prompt_text)

    gen = agent_invoke(
        msgs,
        tools=_AI_TOOLS,
        stream_level=StreamLevel.SYNC,
        max_iterations=max_iterations,
        **(llm_kwargs or {}),
    )

    new_messages: list[BaseMessage] = []
    for msg in gen:
        accumulate_messages(new_messages, msg)
    accumulate_messages(new_messages, None)
    msgs.extend(new_messages)

    return messages_to_json(msgs)


def get_permission_info() -> dict:
    """返回当前 AI 可读/可写字段的白名单。"""
    read_view, write_view = ai_permission()
    return {
        "read": view_to_json(read_view),
        "write": view_to_json(write_view),
    }
