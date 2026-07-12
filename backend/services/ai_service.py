"""AI 对话业务逻辑。"""

from __future__ import annotations
from typing import Any

from langchain_core.messages import BaseMessage

from backend.permissions import get_api_permission_from_db
from xfun.ai.agent import (
    StreamLevel,
    accumulate_messages,
    agent_invoke,
    ensure_system_message,
    messages_to_json,
    parse_messages_json,
)
from xfun.ai.prompts import SYSTEM_PROMPT
from xfun.ai.tools import DEFAULT_TOOL_NAMES, make_tools
from xfun.core.view import DB_Permission, view_to_json
from fastapi import HTTPException, status


def chat(
    messages: list[dict],
    permission: DB_Permission,
    tool_names: list[str] | None = None,
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
    permission : DB_Permission
        注入的最终权限（已由调用方取交集）。
    tool_names : list[str] | None
        工具名称列表，默认包含全部工具。

    Returns
    -------
    list[dict]
        完整的对话历史（含新增消息），格式同输入。
    """
    prompt_text = system_prompt or SYSTEM_PROMPT
    msgs = parse_messages_json(messages)
    ensure_system_message(msgs, prompt_text)

    tools = make_tools(tool_names or DEFAULT_TOOL_NAMES, permission)

    gen = agent_invoke(
        msgs,
        tools=tools,
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


def get_permission_info(permission_name: str = "ai") -> dict:
    """返回指定权限的可读/可写字段的白名单。"""
    perm_obj = get_api_permission_from_db(permission_name)
    if perm_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"未知权限名称: {permission_name!r}")
    read_view, write_view = perm_obj.permission
    return {
        "read": view_to_json(read_view),
        "write": view_to_json(write_view),
    }
