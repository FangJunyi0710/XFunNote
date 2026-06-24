"""
LangChain Agent — 管理 AI 对话与工具调用。

用法::

    from xfun.ai.agent import chat_state, chat_stream_state

    # 非流式（返回完整对话状态）
    state = chat_state("帮我查本月计划")
    print(state["ai_text"])                # 最终回复
    for msg in state["messages"]:          # 完整历史（含工具调用）
        print(f"[{msg['role']}] {msg['content']}")

    # 持续对话：传入上一轮的 messages
    state2 = chat_state("继续说说", messages=state["messages"])

    # 流式（逐事件输出，最终返回完整状态）
    gen = chat_stream_state("帮我查本月计划")
    for event in gen:
        if event["type"] == "text":
            print(event["content"], end="")
        elif event["type"] == "tool_start":
            print(f"[执行 {event['name']}]")
    full_state = gen.send(None)  # 或等 generator 自动返回
"""

from typing import Any, Dict, Generator, List, Optional

from langchain.agents import AgentState, create_agent as _create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from xfun.ai.prompts import SYSTEM_PROMPT
from xfun.ai.tools import (
    add_ai_note,
    add_entries,
    delete_entries,
    manage_tags,
    query_entries,
    save_memory,
    search_memories,
    update_entries,
)
from xfun.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

# ---------------------------------------------------------------------------
# 工具注册表
# ---------------------------------------------------------------------------

_TOOLS = [
    query_entries,
    add_entries,
    update_entries,
    delete_entries,
    manage_tags,
    add_ai_note,
    search_memories,
    save_memory,
]

# ---------------------------------------------------------------------------
# 内部构建
# ---------------------------------------------------------------------------


def _build_llm():
    """构建 LangChain ChatOpenAI 实例（指向 DeepSeek API）。"""
    return ChatOpenAI(
        model=DEEPSEEK_MODEL,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    ).bind(extra_body={"thinking": {"type": "disabled"}})


def create_agent(system: str = SYSTEM_PROMPT) -> "CompiledStateGraph":
    """
    创建 LangChain Agent（LangGraph 编译图）。
    """
    llm = _build_llm()
    return _create_agent(llm, tools=_TOOLS, system_prompt=system)


# ---------------------------------------------------------------------------
# 消息序列化
# ---------------------------------------------------------------------------


def _message_to_dict(msg: BaseMessage) -> Dict[str, Any]:
    """LangChain BaseMessage → 可序列化 dict。"""
    d: Dict[str, Any] = {"role": _role_of(msg), "content": msg.content or ""}
    if isinstance(msg, AIMessage) and msg.tool_calls:
        d["tool_calls"] = [
            {"id": tc["id"], "name": tc["name"], "args": tc["args"]}
            for tc in msg.tool_calls
        ]
    if isinstance(msg, ToolMessage):
        d["tool_call_id"] = msg.tool_call_id
        d["name"] = msg.name or ""
    return d


def _role_of(msg: BaseMessage) -> str:
    if isinstance(msg, HumanMessage):
        return "human"
    if isinstance(msg, AIMessage):
        return "ai"
    if isinstance(msg, ToolMessage):
        return "tool"
    return "unknown"


def _state_to_dict(state: AgentState) -> Dict[str, Any]:
    """AgentState → 对外可用的对话状态 dict。"""
    raw: List[BaseMessage] = state.get("messages", [])
    messages = [_message_to_dict(m) for m in raw]
    # 提取工具调用摘要
    tool_calls = [
        {
            "name": m.get("tool_calls", [{}])[0].get("name", ""),
            "args": m.get("tool_calls", [{}])[0].get("args", {}),
        }
        for m in messages
        if m.get("tool_calls")
    ]
    return {
        "messages": messages,
        "ai_text": _last_ai_text(raw),
        "tool_calls": tool_calls,
    }


def _last_ai_text(messages: List[BaseMessage]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            return str(msg.content)
    return ""


# ---------------------------------------------------------------------------
# 非流式对话（含完整状态）
# ---------------------------------------------------------------------------


def chat_state(
    message: str,
    messages: Optional[List[Dict[str, Any]]] = None,
    system: str = SYSTEM_PROMPT,
    max_rounds: int = 5,
) -> Dict[str, Any]:
    """
    非流式对话，返回完整对话状态。

    支持持续对话：传入上一轮返回的 ``messages`` 列表即在该历史基础上继续。

    Parameters
    ----------
    message : str
        用户消息。
    messages : list[dict] | None
        已有对话历史（chat_state 返回的 messages）。
        None 表示开启新对话。
    system : str
        System prompt。
    max_rounds : int
        最大工具调用轮数。

    Returns
    -------
    dict
        - ``messages``: 完整消息列表（每条含 role / content / tool_calls 等）
        - ``ai_text``: 最终 AI 文本回复
        - ``tool_calls``: 本轮工具调用摘要
    """
    agent = create_agent(system)
    input_messages: list = list(messages) if messages else []
    input_messages.append({"role": "human", "content": message})

    result = agent.invoke(
        {"messages": input_messages},
        {"recursion_limit": max_rounds * 2 + 10},
    )
    return _state_to_dict(result)


# ---------------------------------------------------------------------------
# 流式对话（逐事件 yield，最后返回完整状态）
# ---------------------------------------------------------------------------


def chat_stream_state(
    message: str,
    messages: Optional[List[Dict[str, Any]]] = None,
    system: str = SYSTEM_PROMPT,
    max_rounds: int = 5,
) -> Generator[Dict[str, Any], None, Dict[str, Any]]:
    """
    流式对话，逐事件 yield，最终 return 完整状态。

    支持持续对话：传入上一轮返回的 ``messages`` 列表。

    Yields
    ------
    dict
        - ``{"type": "text", "content": "..."}`` — 文本块
        - ``{"type": "tool_start", "name": "fn_name", "args": {...}}`` — 工具开始
        - ``{"type": "tool_end",   "name": "fn_name", "result": "..."}`` — 工具结束

    Returns
    -------
    dict
        完整对话状态（同 ``chat_state`` 返回值）。
    """
    agent = create_agent(system)
    config = {"recursion_limit": max_rounds * 2 + 10}

    input_messages: list = list(messages) if messages else []
    input_messages.append({"role": "human", "content": message})

    # 流式过程中累积 AgentState（最终用于返回）
    accumulated: AgentState = {"messages": []}

    for event in agent.stream({"messages": input_messages}, config):
        if "model" in event:
            msgs = event["model"].get("messages", [])
            accumulated["messages"].extend(msgs)
            for m in msgs:
                if isinstance(m, AIMessage):
                    if m.tool_calls:
                        for tc in m.tool_calls:
                            yield {
                                "type": "tool_start",
                                "name": tc["name"],
                                "args": tc["args"],
                            }
                    if m.content:
                        yield {"type": "text", "content": str(m.content)}

        if "tools" in event:
            msgs = event["tools"].get("messages", [])
            accumulated["messages"].extend(msgs)
            for m in msgs:
                if isinstance(m, ToolMessage):
                    yield {
                        "type": "tool_end",
                        "name": m.name or "",
                        "result": m.content,
                    }

    final = _state_to_dict(accumulated)
    # 将外部传入的历史拼回到最终结果（保持完整对话链）
    if messages:
        final["messages"] = messages + final["messages"]
    return final
