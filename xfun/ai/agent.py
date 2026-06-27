from __future__ import annotations

from collections.abc import Generator
from enum import Enum, auto
from typing import Annotated, Any, Literal, Sequence

from typing_extensions import TypedDict

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from xfun.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


class StreamLevel(Enum):
    """AI Agent 流式输出的详细程度。
    - ``TOKEN``: 逐个 token 流式输出 LLM 回复（默认），yield ``AIMessageChunk``。
    - ``MSG``: 逐条完整消息输出，yield ``AIMessage`` / ``ToolMessage``。
    - ``SYNC``: 阻塞等待 LLM 完整响应，全程静默，仅在结束循环后 yield 最终消息。
    """
    TOKEN = auto()
    MSG = auto()
    SYNC = auto()


# ════════════════════════════════════════════════════════════
#  LangGraph State
# ════════════════════════════════════════════════════════════

class State(TypedDict):
    """Agent 状态。``add_messages`` reducer 自动处理消息追加与 AIMessageChunk 合并。"""
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ════════════════════════════════════════════════════════════
#  LLM 构建
# ════════════════════════════════════════════════════════════

def _build_llm(
    tools: list[BaseTool],
    **llm_kwargs: Any,
):
    """构建绑定了工具的 ``ChatOpenAI`` 实例。"""
    llm_kwargs = dict(llm_kwargs)
    llm_kwargs.pop("streaming", None)
    llm = ChatOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        **llm_kwargs,
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


# ════════════════════════════════════════════════════════════
#  消息累积
# ════════════════════════════════════════════════════════════

def accumulate_messages(result: list[BaseMessage], item: BaseMessage | None) -> None:
    """
    将流式输出项累积到 ``result`` 列表中，连续的 AIMessageChunk 自动合并为一个 AIMessage。
    若 item 为 ``None``，则作为结束信号，将最后一个挂起的 AIMessageChunk 转为 AIMessage。
    """
    if isinstance(item, AIMessageChunk):
        if result and isinstance(result[-1], AIMessageChunk):
            result[-1] += item
        else:
            result.append(item)
        return

    if result and isinstance(result[-1], AIMessageChunk):
        chunk = result.pop()
        result.append(_chunk_to_message(chunk))

    if item is not None:
        result.append(item)


# ════════════════════════════════════════════════════════════
#  LangGraph Agent 构建
# ════════════════════════════════════════════════════════════

def _build_agent_graph(
    tools: list[BaseTool],
    max_iterations: int,
    **llm_kwargs: Any,
):
    """构建 LangGraph Agent。
    
    流程：
        call_model → should_continue ──有工具调用──→ tools → call_model
                                    ──无工具调用──→ END
    """
    llm = _build_llm(tools, **llm_kwargs)

    def call_model(state: State) -> dict:
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    def should_continue(state: State) -> Literal["tools", "__end__"]:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "__end__"

    # 每次迭代需要两个节点：call_model + tools，最后至少还要一次 call_model
    recursion_limit = max_iterations * 2 + 1

    graph = StateGraph(State)
    graph.add_node("call_model", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("call_model")
    graph.add_conditional_edges("call_model", should_continue)
    graph.add_edge("tools", "call_model")

    return graph.compile(), recursion_limit


# ════════════════════════════════════════════════════════════
#  agent_invoke — 统一入口
# ════════════════════════════════════════════════════════════

def agent_invoke(
    messages: list[BaseMessage],
    tools: list[BaseTool] | None = None,
    stream_level: StreamLevel = StreamLevel.SYNC,
    max_iterations: int = 10,
    **llm_kwargs: Any,
) -> Generator[BaseMessage, None, None]:
    """
    核心函数：生成器，yield 中间消息（AIMessageChunk / ToolMessage / AIMessage）。

    配合 ``accumulate_messages`` 使用::

        new_messages: list[BaseMessage] = []
        for yielded in agent_invoke(messages, tools=...):
            accumulate_messages(new_messages, yielded)
        accumulate_messages(new_messages, None)  # flush 挂起的 chunk（仅在 StreamLevel.TOKEN 下必要）
        messages.extend(new_messages)
    """
    tools = tools or []

    if stream_level == StreamLevel.TOKEN:
        yield from _token_invoke(messages, tools, max_iterations, **llm_kwargs)
    elif stream_level == StreamLevel.MSG:
        yield from _msg_invoke(messages, tools, max_iterations, **llm_kwargs)
    else:
        yield from _sync_invoke(messages, tools, max_iterations, **llm_kwargs)


# ════════════════════════════════════════════════════════════
#  三种流式策略
# ════════════════════════════════════════════════════════════

def _sync_invoke(
    messages: list[BaseMessage],
    tools: list[BaseTool],
    max_iterations: int,
    **llm_kwargs: Any,
) -> Generator[BaseMessage, None, None]:
    """SYNC 模式：用 LangGraph 完整执行，最后统一 yield 所有新消息。"""
    graph, recursion_limit = _build_agent_graph(tools, max_iterations, **llm_kwargs)
    initial_state = {"messages": list(messages)}
    result = graph.invoke(initial_state, {"recursion_limit": recursion_limit})
    new_msgs = result["messages"][len(messages):]
    for msg in new_msgs:
        yield msg


def _msg_invoke(
    messages: list[BaseMessage],
    tools: list[BaseTool],
    max_iterations: int,
    **llm_kwargs: Any,
) -> Generator[BaseMessage, None, None]:
    """MSG 模式：用 LangGraph stream(updates)，逐个 node 产出完整消息。"""
    graph, recursion_limit = _build_agent_graph(tools, max_iterations, **llm_kwargs)
    initial_state = {"messages": list(messages)}
    for event in graph.stream(
        initial_state,
        stream_mode="updates",
        config={"recursion_limit": recursion_limit},
    ):
        for node_output in event.values():
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    yield msg


def _token_invoke(
    messages: list[BaseMessage],
    tools: list[BaseTool],
    max_iterations: int,
    **llm_kwargs: Any,
) -> Generator[BaseMessage, None, None]:
    """TOKEN 模式：LLM 逐 token 流式输出，ToolNode 执行工具调用。

    TOKEN 模式不使用 LangGraph 编排，因为 graph node 内不支持原生逐 token yield。
    采用手动循环：LLM.stream() yield chunk → ToolNode.invoke() yield ToolMessage。
    """
    llm = _build_llm(tools, **llm_kwargs)
    tool_node = ToolNode(tools)
    working = list(messages)

    for _ in range(max_iterations):
        accumulated = AIMessageChunk(content="")
        for chunk in llm.stream(working):
            accumulated += chunk
            yield chunk  # AIMessageChunk — 逐 token

        response = _chunk_to_message(accumulated)
        working.append(response)

        if not response.tool_calls:
            break

        tool_results = tool_node.invoke({"messages": [response]})
        for tm in tool_results["messages"]:
            yield tm  # ToolMessage
            working.append(tm)


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
