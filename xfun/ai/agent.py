"""
LangChain Agent — 管理 AI 对话与工具调用。

用法::

    from xfun.ai.agent import chat, chat_stream

    # 非流式
    result = chat("帮我查本月计划")

    # 流式
    for chunk in chat_stream("帮我查本月计划"):
        print(chunk, end="")
"""

from typing import Generator

from langchain.agents import AgentState, create_agent as _create_agent
from langchain_core.messages import AIMessage
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
# 内部构建函数
# ---------------------------------------------------------------------------


def _build_llm():
    """构建 LangChain ChatOpenAI 实例（指向 DeepSeek API）。"""
    return ChatOpenAI(
        model=DEEPSEEK_MODEL or "deepseek-chat",
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL or "https://api.deepseek.com",
    ).bind(extra_body={"thinking": {"type": "disabled"}})


def _get_last_ai_content(messages: list) -> str:
    """从消息列表中提取最后一个 AI 回复的文本内容。"""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            return str(msg.content)
    return ""


def create_agent(system: str = SYSTEM_PROMPT) -> "CompiledStateGraph":
    """
    创建 LangChain Agent（LangGraph 编译图）。

    Parameters
    ----------
    system : str
        System prompt。

    Returns
    -------
    CompiledStateGraph
    """
    llm = _build_llm()
    return _create_agent(
        llm,
        tools=_TOOLS,
        system_prompt=system,
    )


# ---------------------------------------------------------------------------
# 公开对话接口
# ---------------------------------------------------------------------------


def chat(
    message: str,
    system: str = SYSTEM_PROMPT,
    max_rounds: int = 5,
) -> str:
    """
    非流式对话，自动处理工具调用。

    Parameters
    ----------
    message : str
        用户消息。
    system : str
        System prompt。
    max_rounds : int
        最大工具调用轮数（LangGraph 使用 recursion_limit）。

    Returns
    -------
    str
        AI 回复内容。
    """
    agent = create_agent(system)
    result = agent.invoke(
        {"messages": [{"role": "human", "content": message}]},
        {"recursion_limit": max_rounds * 2 + 10},
    )
    return _get_last_ai_content(result["messages"])


def chat_stream(
    message: str,
    system: str = SYSTEM_PROMPT,
    max_rounds: int = 5,
) -> Generator[str, None, None]:
    """
    流式对话生成器，逐段 yield 文本块。

    Parameters
    ----------
    message : str
        用户消息。
    system : str
        System prompt。
    max_rounds : int
        最大工具调用轮数。

    Yields
    ------
    str
        文本块（节点级事件）。
    """
    agent = create_agent(system)
    config = {"recursion_limit": max_rounds * 2 + 10}

    for event in agent.stream(
        {"messages": [{"role": "human", "content": message}]},
        config,
    ):
        # model 节点：AI 回复或工具调用
        if "model" in event:
            msgs = event["model"].get("messages", [])
            for m in msgs:
                if isinstance(m, AIMessage):
                    if m.tool_calls:
                        for tc in m.tool_calls:
                            yield f"\n[执行 {tc['name']}]\n"
                    if m.content:
                        yield str(m.content)

        # tools 节点：工具返回结果
        if "tools" in event:
            pass  # 工具结果不需要额外输出
