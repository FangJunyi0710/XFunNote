"""
AI Agent — 核心对话引擎（Tool Calling Loop）。

核心函数 :func:`agent_invoke` 负责接收对话消息列表，
自动调用 LLM（DeepSeek）并循环执行工具，最终返回所有新消息供调用方 extend。

用法::

    from langchain_core.messages import HumanMessage
    from xfun.ai.agent import agent_invoke

    messages = [HumanMessage(content="帮我查一下今天的计划")]
    new_messages = agent_invoke(messages)
    messages.extend(new_messages)
    print(new_messages[-1].content)
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from xfun.ai.prompts import SYSTEM_PROMPT
from xfun.ai.tools import add_entries, delete_entries, query_entries, update_entries
from xfun.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from xfun.core.errors import AIError, ToolError

_MAX_ITERATIONS = 10
"""单次 ``agent_invoke`` 内最大工具调用轮数，防止无限循环。"""

_TOOLS: list[BaseTool] = [
    query_entries,
    add_entries,
    update_entries,
    delete_entries,
]

_DEFAULT_LLM_KWARGS: dict[str, Any] = {
    "temperature": 0.1,
    "extra_body": {"thinking": {"type": "disabled"}},
}


def agent_invoke(
    messages: list[BaseMessage],
    system_prompt: str | None = None,
    **llm_kwargs: Any,
) -> list[BaseMessage]:
    """核心函数：传入消息列表，返回需要 extend 的新消息列表。

    Parameters
    ----------
    messages : list[BaseMessage]
        现有对话消息列表。每次调用独立执行，
        如需保留上下文需调用方自行 ``messages.extend(返回值)``。
    system_prompt : str, optional
        覆盖默认的 :data:`~xfun.ai.prompts.SYSTEM_PROMPT`。
        设为 ``None`` 使用默认提示词。
    **llm_kwargs
        传递给 ``ChatOpenAI`` 的额外参数，如 ``temperature=0.7``，
        ``max_tokens=2000``。默认 ``temperature=0.1``，
        ``extra_body={"thinking": {"type": "disabled"}}``。
        可在此处覆盖。

    Returns
    -------
    list[BaseMessage]
        本次调用产生的所有新消息（AIMessage / ToolMessage），
        调用方可用 ``messages.extend(返回值)`` 延续对话。

    Raises
    ------
    AIError
        模型未配置或出现内部错误。
    """
    if not LLM_API_KEY:
        raise AIError("未配置 LLM_API_KEY，请检查 .env 文件")

    # 合并默认参数与用户覆盖参数（用户参数优先）
    merged_kwargs = {**_DEFAULT_LLM_KWARGS, **llm_kwargs}

    llm = ChatOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        **merged_kwargs,
    )
    llm_with_tools = llm.bind_tools(_TOOLS)

    working_messages = _prepare_messages(messages, system_prompt)

    new_messages: list[BaseMessage] = []

    for _ in range(_MAX_ITERATIONS):
        response = llm_with_tools.invoke(working_messages)
        new_messages.append(response)
        working_messages.append(response)

        if not response.tool_calls:
            # LLM 最终回复，无工具调用 → 本轮结束
            break

        # 执行本轮所有工具调用
        for tc in response.tool_calls:
            tm = _execute_tool_call(tc)
            new_messages.append(tm)
            working_messages.append(tm)

    return new_messages


# ════════════════════════════════════════════════════════════
#  内部辅助
# ════════════════════════════════════════════════════════════


def _prepare_messages(
    messages: list[BaseMessage],
    system_prompt: str | None,
) -> list[BaseMessage]:
    """准备工作消息列表：自动注入系统提示词。"""
    sp_content = system_prompt or SYSTEM_PROMPT

    if messages and isinstance(messages[0], SystemMessage):
        if messages[0].content == sp_content:
            return list(messages)
        result = list(messages)
        result[0] = SystemMessage(content=sp_content)
        return result

    return [SystemMessage(content=sp_content)] + list(messages)


def _execute_tool_call(tc: dict[str, Any]) -> ToolMessage:
    """执行单次工具调用并返回 ToolMessage。"""
    tool_name = tc["name"]
    tool_args = tc["args"]
    tool_id: str = tc["id"]

    tool = _find_tool(tool_name)
    if tool is None:
        raise ToolError(f"未知工具: {tool_name}")

    try:
        content = tool.invoke(tool_args)
    except Exception as e:
        content = json.dumps({"error": str(e)}, ensure_ascii=False)

    return ToolMessage(content=content, tool_call_id=tool_id)


def _find_tool(name: str) -> BaseTool | None:
    """根据名称查找已注册的工具。"""
    return next((t for t in _TOOLS if t.name == name), None)


__all__ = ["agent_invoke", "_TOOLS"]
