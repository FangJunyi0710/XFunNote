from __future__ import annotations

import json
from collections.abc import Generator
from enum import Enum, auto
from typing import Any

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    ToolCall,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from xfun.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from xfun.core.errors import AIError, ToolError

_MAX_ITERATIONS = 10
"""单次 ``agent_invoke`` 内最大工具调用轮数，防止无限循环。"""

_DEFAULT_LLM_KWARGS: dict[str, Any] = {
    "temperature": 0.1,
    "extra_body": {"thinking": {"type": "disabled"}},
}


class StreamLevel(Enum):
    """AI Agent 流式输出的详细程度。
    - ``TOKEN``: 逐个 token 流式输出 LLM 回复（默认），yield ``AIMessageChunk``。
    - ``MSG``: 逐条完整消息输出，yield ``AIMessage`` / ``ToolMessage``。
    - ``SYNC``: 阻塞等待 LLM 完整响应，全程静默，仅在结束循环后 yield 最终 ``AIMessage`` 一次。
    """
    TOKEN = auto()
    MSG = auto()
    SYNC = auto()


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
    tools: list[BaseTool],
    stream_level: StreamLevel = StreamLevel.SYNC,
    **llm_kwargs: Any,
) -> Generator[BaseMessage, None, list[BaseMessage]]:
    """
    核心函数：生成器，yield 中间消息，StopIteration.value 返回完整新消息列表。

    用法::

        messages = [
            SystemMessage(content="你是一个助手..."),
            HumanMessage(content="今天有什么计划？"),
        ]
        try:
            for msg in agent_invoke(messages, tools=...):
                print(msg.content, end="", flush=True)
        except StopIteration as e:
            messages.extend(e.value)
    """
    llm_with_tools = _build_llm(tools, **llm_kwargs)
    working_messages = list(messages)
    new_messages: list[BaseMessage] = []

    for _ in range(_MAX_ITERATIONS):
        if stream_level == StreamLevel.TOKEN:
            full_content = ""
            full_reasoning = ""
            tool_call_buffers: dict[int, dict[str, str]] = {}

            for chunk in llm_with_tools.stream(working_messages):
                reasoning = chunk.additional_kwargs.get("reasoning_content", "")
                if reasoning:
                    full_reasoning += reasoning
                    chunk.additional_kwargs["is_reasoning"] = True
                    yield chunk

                if isinstance(chunk.content, str) and chunk.content:
                    full_content += chunk.content
                    yield chunk  # AIMessageChunk — 逐 token 流式

                for tcc in chunk.tool_call_chunks or []:
                    idx = tcc.get("index", 0) or 0
                    if idx not in tool_call_buffers:
                        tool_call_buffers[idx] = {"name": "", "args": "", "id": ""}
                    buf = tool_call_buffers[idx]
                    buf["name"] += tcc.get("name", "") or ""
                    buf["args"] += tcc.get("args", "") or ""
                    buf["id"] += tcc.get("id", "") or ""

            tool_calls = _accumulate_tool_calls(tool_call_buffers)
            additional_kwargs = {"reasoning_content": full_reasoning} if full_reasoning else {}
            response = AIMessage(content=full_content, tool_calls=tool_calls, additional_kwargs=additional_kwargs)
        else:
            response = llm_with_tools.invoke(working_messages)

        if stream_level == StreamLevel.MSG:
            yield response  # 完整消息模式：yield 组装好的 AIMessage
        new_messages.append(response)
        working_messages.append(response)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            tm = _execute_tool_call(tc, tools)
            if stream_level != StreamLevel.SYNC:
                yield tm
            new_messages.append(tm)
            working_messages.append(tm)

    if stream_level == StreamLevel.SYNC:
        for msg in new_messages:
            yield msg

    return new_messages


def _accumulate_tool_calls(tool_call_buffers: dict[int, dict[str, str]]) -> list[ToolCall]:
    """将流式累积的工具调用片段组装为 ``ToolCall`` 列表。"""
    tool_calls: list[ToolCall] = []
    for idx in sorted(tool_call_buffers):
        buf = tool_call_buffers[idx]
        try:
            parsed_args = json.loads(buf["args"]) if buf["args"] else {}
        except json.JSONDecodeError:
            parsed_args = {}
        tool_calls.append(ToolCall(
                name=buf["name"],
                args=parsed_args,
                id=buf["id"] or f"stream_{idx}",
            )
        )
    return tool_calls


def _execute_tool_call(
    tc: dict[str, Any],
    tools: list[BaseTool],
) -> ToolMessage:
    """执行单次工具调用并返回 ToolMessage。"""
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

def _find_tool(name: str, tools: list[BaseTool]) -> BaseTool | None:
    """根据名称在工具列表中查找工具。"""
    return next((t for t in tools if t.name == name), None)
