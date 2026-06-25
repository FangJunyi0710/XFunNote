"""
AI Agent — 核心对话引擎（Tool Calling Loop）。

核心函数 :func:`agent_invoke` 负责接收对话消息列表，
自动调用 LLM（DeepSeek）并循环执行工具，最终返回所有新消息供调用方 extend。

支持流式输出：通过 :class:`StreamLevel` 枚举控制流式粒度，
通过 ``on_chunk`` 回调将中间消息实时送达调用方。

用法::

    from langchain_core.messages import HumanMessage
    from xfun.ai.agent import StreamLevel, agent_invoke

    messages = [HumanMessage(content="帮我查一下今天的计划")]
    new_messages = agent_invoke(messages)
    messages.extend(new_messages)
    print(new_messages[-1].content)
"""

from __future__ import annotations

import json
from collections.abc import Callable
from enum import Enum, auto
from typing import Any

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    SystemMessage,
    ToolCall,
    ToolMessage,
)
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


class StreamLevel(Enum):
    """AI Agent 流式输出的详细程度。

    - ``OFF``: 不流式，使用 ``.invoke()`` 一次获取完整响应（默认）。
    - ``TOOL``: 流式工具执行结果（仅通过 ``on_chunk`` 送达 ``ToolMessage``）。
    - ``FULL``: 完整流式，逐 token 送达 ``AIMessageChunk``，
      而后依次送达 ``AIMessage``（含 ``.tool_calls``）和 ``ToolMessage``。
    """

    OFF = auto()
    TOOL = auto()
    FULL = auto()


def _build_llm(
    tools: list[BaseTool],
    **llm_kwargs: Any,
):
    """构建绑定了工具的 ``ChatOpenAI`` 实例。"""
    merged_kwargs = {**_DEFAULT_LLM_KWARGS, **llm_kwargs}
    llm = ChatOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        **merged_kwargs,
    )
    return llm.bind_tools(tools)


def agent_invoke(
    messages: list[BaseMessage],
    tools: list[BaseTool] | None = None,
    system_prompt: str | None = None,
    stream_level: StreamLevel = StreamLevel.OFF,
    on_chunk: Callable[[BaseMessage], None] | None = None,
    **llm_kwargs: Any,
) -> list[BaseMessage]:
    """核心函数：传入消息列表，返回需要 extend 的新消息列表。

    Parameters
    ----------
    messages : list[BaseMessage]
        现有对话消息列表。每次调用独立执行，
        如需保留上下文需调用方自行 ``messages.extend(返回值)``。
    tools : list[BaseTool], optional
        可用工具列表，默认使用模块级 ``_TOOLS``。
    system_prompt : str, optional
        覆盖默认的 :data:`~xfun.ai.prompts.SYSTEM_PROMPT`。
        设为 ``None`` 使用默认提示词。
    stream_level : StreamLevel, optional
        流式粒度，详见 :class:`StreamLevel`。
    on_chunk : Callable[[BaseMessage], None], optional
        ``stream_level != OFF`` 时，每个中间消息都会调用此回调。
        调用方可在此处实时渲染文本或工具结果。
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
        返回值**不会**包含 ``AIMessageChunk``（仅用于流式渲染）。

    Raises
    ------
    AIError
        模型未配置或出现内部错误。
    """
    if not LLM_API_KEY:
        raise AIError("未配置 LLM_API_KEY，请检查 .env 文件")

    if stream_level == StreamLevel.OFF:
        return _nonstreaming_invoke(messages, tools, system_prompt, **llm_kwargs)
    return _streaming_invoke(messages, tools, system_prompt, stream_level, on_chunk, **llm_kwargs)


# ════════════════════════════════════════════════════════════
#  非流式路径（OFF）
# ════════════════════════════════════════════════════════════


def _nonstreaming_invoke(
    messages: list[BaseMessage],
    tools: list[BaseTool] | None,
    system_prompt: str | None,
    **llm_kwargs: Any,
) -> list[BaseMessage]:
    """非流式：使用 ``.invoke()``，与原始行为一致。"""
    active_tools = tools or _TOOLS
    llm_with_tools = _build_llm(active_tools, **llm_kwargs)
    working_messages = _prepare_messages(messages, system_prompt)
    new_messages: list[BaseMessage] = []

    for _ in range(_MAX_ITERATIONS):
        response = llm_with_tools.invoke(working_messages)
        new_messages.append(response)
        working_messages.append(response)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            tm = _execute_tool_call(tc, active_tools)
            new_messages.append(tm)
            working_messages.append(tm)

    return new_messages


# ════════════════════════════════════════════════════════════
#  流式路径（TOOL / FULL）
# ════════════════════════════════════════════════════════════


def _streaming_invoke(
    messages: list[BaseMessage],
    tools: list[BaseTool] | None,
    system_prompt: str | None,
    stream_level: StreamLevel,
    on_chunk: Callable[[BaseMessage], None] | None,
    **llm_kwargs: Any,
) -> list[BaseMessage]:
    """流式路径：使用 ``.stream()``，根据 ``stream_level`` 决定回调投递内容。"""
    active_tools = tools or _TOOLS
    llm_with_tools = _build_llm(active_tools, **llm_kwargs)
    working_messages = _prepare_messages(messages, system_prompt)
    new_messages: list[BaseMessage] = []

    for _ in range(_MAX_ITERATIONS):
        # 流式接收 LLM 回复
        full_content, tool_call_buffers = _stream_llm_round(
            llm_with_tools,
            working_messages,
            stream_level,
            on_chunk,
        )

        tool_calls = _accumulate_tool_calls(tool_call_buffers)
        response = AIMessage(content=full_content, tool_calls=tool_calls)

        if stream_level == StreamLevel.FULL and on_chunk:
            on_chunk(response)

        new_messages.append(response)
        working_messages.append(response)

        if not response.tool_calls:
            break

        # 执行本轮所有工具调用
        for tc in response.tool_calls:
            tm = _execute_tool_call(tc, active_tools)
            if on_chunk:
                on_chunk(tm)
            new_messages.append(tm)
            working_messages.append(tm)

    return new_messages


def _stream_llm_round(
    llm_with_tools,
    messages: list[BaseMessage],
    stream_level: StreamLevel,
    on_chunk: Callable[[BaseMessage], None] | None,
) -> tuple[str, dict[int, dict[str, str]]]:
    """流式接收 LLM 一轮输出。

    Returns
    -------
    (full_content, tool_call_buffers)
        - full_content: 累积的完整文本
        - tool_call_buffers: 按 index 累积的工具调用片段
    """
    full_content = ""
    tool_call_buffers: dict[int, dict[str, str]] = {}

    for chunk in llm_with_tools.stream(messages):
        # 文本增量
        if chunk.content:
            full_content += chunk.content
            if stream_level == StreamLevel.FULL and on_chunk:
                on_chunk(chunk)

        # 工具调用增量（流式累积）
        for tcc in chunk.tool_call_chunks or []:
            idx = _safe_get(tcc, "index", 0)
            if idx not in tool_call_buffers:
                tool_call_buffers[idx] = {"name": "", "args": "", "id": ""}
            buf = tool_call_buffers[idx]
            buf["name"] += _safe_get(tcc, "name", "")
            buf["args"] += _safe_get(tcc, "args", "")
            buf["id"] += _safe_get(tcc, "id", "")

    return full_content, tool_call_buffers


def _accumulate_tool_calls(
    tool_call_buffers: dict[int, dict[str, str]],
) -> list[ToolCall]:
    """将流式累积的工具调用片段组装为 ``ToolCall`` 列表。"""
    tool_calls: list[ToolCall] = []
    for idx in sorted(tool_call_buffers):
        buf = tool_call_buffers[idx]
        try:
            parsed_args = json.loads(buf["args"]) if buf["args"] else {}
        except json.JSONDecodeError:
            parsed_args = {}
        tool_calls.append(
            ToolCall(
                name=buf["name"],
                args=parsed_args,
                id=buf["id"] or f"stream_{idx}",
            )
        )
    return tool_calls


def _safe_get(obj, attr: str, default: str = "") -> str:
    """安全地从 ``ToolCallChunk``（对象或 dict）中获取字符串字段。"""
    if isinstance(obj, dict):
        return obj.get(attr, default) or default
    return getattr(obj, attr, default) or default


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


def _execute_tool_call(
    tc: dict[str, Any],
    tools: list[BaseTool] | None = None,
) -> ToolMessage:
    """执行单次工具调用并返回 ToolMessage。

    Parameters
    ----------
    tc : dict
        工具调用描述，含 ``name`` / ``args`` / ``id``。
    tools : list[BaseTool], optional
        要搜索的工具列表。为 ``None`` 时使用模块级 ``_TOOLS``。
    """
    tool_name = tc["name"]
    tool_args = tc["args"]
    tool_id: str = tc["id"]

    tool = _find_tool(tool_name, tools)
    if tool is None:
        raise ToolError(f"未知工具: {tool_name}")

    try:
        content = tool.invoke(tool_args)
    except Exception as e:
        content = json.dumps({"error": str(e)}, ensure_ascii=False)

    return ToolMessage(content=content, tool_call_id=tool_id)


def _find_tool(
    name: str,
    tools: list[BaseTool] | None = None,
) -> BaseTool | None:
    """根据名称查找已注册的工具。

    Parameters
    ----------
    name : str
        工具名称。
    tools : list[BaseTool], optional
        要搜索的工具列表。为 ``None`` 时使用模块级 ``_TOOLS``。
    """
    pool = tools or _TOOLS
    return next((t for t in pool if t.name == name), None)


__all__ = ["agent_invoke", "StreamLevel", "_TOOLS"]
