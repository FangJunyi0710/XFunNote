from __future__ import annotations

import json
from collections.abc import Generator
from enum import Enum, auto
from typing import Any

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolCall,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from xfun.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from xfun.core.errors import ToolError


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
    merged_kwargs = dict(llm_kwargs)
    merged_kwargs.pop("streaming", None)  # 防止与 stream()/invoke() 冲突
    llm = ChatOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        **merged_kwargs,
    )
    return llm.bind_tools(tools)

def _chunk_to_message(chunk: AIMessageChunk) -> AIMessage:
    """将累积的 AIMessageChunk 转换为完整的 AIMessage。"""
    return AIMessage(
        content=chunk.content,
        additional_kwargs=chunk.additional_kwargs,
        response_metadata=chunk.response_metadata,
        usage_metadata=chunk.usage_metadata,
        tool_calls=chunk.tool_calls,
    )

def agent_invoke(
    messages: list[BaseMessage],
    tools: list[BaseTool] | None = None,
    stream_level: StreamLevel = StreamLevel.SYNC,
    max_iterations: int = 10,
    timeout: int | float | None = None,
    max_retries: int = 2,
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
    tools = tools or []
    merged_kwargs = dict(llm_kwargs)
    if timeout is not None:
        merged_kwargs["timeout"] = timeout
    merged_kwargs["max_retries"] = max_retries
    llm_with_tools = _build_llm(tools, **merged_kwargs)
    working_messages = list(messages)
    new_messages: list[BaseMessage] = []
    for _ in range(max_iterations):
        if stream_level == StreamLevel.TOKEN:
            accumulated = AIMessageChunk(content="")
            for chunk in llm_with_tools.stream(working_messages):
                accumulated += chunk
                yield chunk  # AIMessageChunk — 逐 token 流式

            response = _chunk_to_message(accumulated)
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

def _execute_tool_call(
    tc: dict[str, Any],
    tools: list[BaseTool],
) -> ToolMessage:
    """执行单次工具调用并返回 ToolMessage。

    工具返回值保存为 ``artifact``，``content`` 统一由 ``json.dumps`` 生成。
    """
    tool_name = tc["name"]
    tool_args = tc["args"]
    tool_id: str = tc["id"]
    tool = _find_tool(tool_name, tools)

    try:
        if tool is None:
            raise ToolError(f"未知工具: {tool_name}")
        artifact = tool.invoke(tool_args)
        status = "success"
    except Exception as e:
        artifact = {"error": str(e)}
        status = "error"

    return ToolMessage(
        content=json.dumps(artifact, ensure_ascii=False, default=str),
        artifact=artifact,
        tool_call_id=tool_id,
        name=tool_name,
        status=status,
    )

def _find_tool(name: str, tools: list[BaseTool]) -> BaseTool | None:
    """根据名称在工具列表中查找工具。"""
    return next((t for t in tools if t.name == name), None)


# ════════════════════════════════════════════════════════════
#  消息序列化 / 反序列化
# ════════════════════════════════════════════════════════════

_ROLE_MAP: list[tuple[type[BaseMessage], str]] = [
    (HumanMessage, "user"),
    (AIMessage, "assistant"),
    (SystemMessage, "system"),
    (ToolMessage, "tool"),
]
_ROLE_CLASS_MAP: dict[str, type[BaseMessage]] = {r: c for c, r in _ROLE_MAP}


def _role(msg: BaseMessage) -> str:
    """返回 BaseMessage 对应的 role 字符串（循环判断，扩展友好）。"""
    for cls, role in _ROLE_MAP:
        if isinstance(msg, cls):
            return role
    return "unknown"


def parse_messages_json(obj: list[dict]) -> list[BaseMessage]:
    """将 Python 列表对象（来自 json.loads）解析为 BaseMessage 列表。

    使用 ``model_validate`` 保留所有扩展字段（如 ``additional_kwargs``），
    避免了手动选取字段导致的信息丢失。

    Args:
        obj: 格式 ``[{"role": "user|assistant|system|tool", "content": "..."}, ...]``

    Returns:
        解析后的 BaseMessage 列表。
    """
    messages: list[BaseMessage] = []
    for msg in obj:
        role = msg.get("role", "user")
        cls = _ROLE_CLASS_MAP.get(role, HumanMessage)
        data = {k: v for k, v in msg.items() if k != "role"}
        messages.append(cls.model_validate(data))
    return messages


def messages_to_json(messages: list[BaseMessage]) -> list[dict]:
    """将 BaseMessage 列表序列化为可 JSON 序列化的 Python 对象。

    使用 ``model_dump`` 保留所有扩展字段，再补上 ``role`` 字段。

    Args:
        messages: BaseMessage 列表。

    Returns:
        可直接用于 ``json.dumps`` 的列表，格式同 ``parse_messages_json`` 输入。
    """
    result: list[dict] = []
    for m in messages:
        d = m.model_dump()
        d["role"] = _role(m)
        result.append(d)
    return result


def ensure_system_message(
    messages: list[BaseMessage],
    system_prompt: str,
) -> list[BaseMessage]:
    """若消息列表中无 SystemMessage，在开头插入给定系统提示词。

    Args:
        messages: 现有的消息列表（会被原地修改）。
        system_prompt: 要插入的系统提示词内容。

    Returns:
        修改后的消息列表（与入参为同一对象）。
    """
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages.insert(0, SystemMessage(content=system_prompt))
    return messages
