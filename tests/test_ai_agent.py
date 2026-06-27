"""测试 Agent — 核心生成器 agent_invoke 及辅助函数（LangGraph 重构版）。"""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk, ToolCall, ToolMessage

from xfun.ai.agent import (
    StreamLevel,
    _build_llm,
    _chunk_to_message,
    accumulate_messages,
    agent_invoke,
)


# ════════════════════════════════════════════════════════════════
#  夹具
# ════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_tool():
    tool = MagicMock()
    tool.name = "test_tool"
    tool.invoke.return_value = {"result": "ok"}
    return tool


@pytest.fixture
def mock_tcc():
    """创建一个 ToolCallChunk 风格的 dict。"""
    return {"name": "test_tool", "args": '{"key": "val"}', "id": "call_1", "index": 0}


# ════════════════════════════════════════════════════════════════
#  StreamLevel 测试
# ════════════════════════════════════════════════════════════════


class TestStreamLevel:
    def test_enum_members(self):
        assert isinstance(StreamLevel.TOKEN, StreamLevel)
        assert isinstance(StreamLevel.MSG, StreamLevel)
        assert isinstance(StreamLevel.SYNC, StreamLevel)

    def test_is_enum(self):
        assert issubclass(StreamLevel, __import__("enum").Enum)


# ════════════════════════════════════════════════════════════════
#  _build_llm 测试
# ════════════════════════════════════════════════════════════════


class TestBuildLLM:
    def test_builds_llm_with_tools(self, monkeypatch, mock_tool):
        class FakeChatOpenAI:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
            def bind_tools(self, tools):
                self.bound_tools = tools
                return self

        monkeypatch.setattr("xfun.ai.agent.ChatOpenAI", FakeChatOpenAI)
        llm = _build_llm([mock_tool], timeout=30, max_retries=3)
        assert llm.bound_tools == [mock_tool]
        assert llm.kwargs.get("timeout") == 30
        assert llm.kwargs.get("max_retries") == 3
        assert "streaming" not in llm.kwargs

    def test_builds_llm_without_tools(self, monkeypatch):
        class FakeChatOpenAI:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
            def bind_tools(self, tools):
                self.bound_tools = tools
                return self

        monkeypatch.setattr("xfun.ai.agent.ChatOpenAI", FakeChatOpenAI)
        llm = _build_llm([])
        assert llm.bound_tools == []


# ════════════════════════════════════════════════════════════════
#  accumulate_messages 测试
# ════════════════════════════════════════════════════════════════


class TestAccumulateMessages:
    def test_merge_consecutive_chunks(self):
        """连续 AIMessageChunk 自动合并为一个。"""
        result: list = []
        accumulate_messages(result, AIMessageChunk(content="He"))
        accumulate_messages(result, AIMessageChunk(content="llo"))
        assert len(result) == 1
        assert isinstance(result[0], AIMessageChunk)
        assert result[0].content == "Hello"

    def test_flush_chunk_via_none(self):
        """None 作为结束信号，将挂起的 AIMessageChunk 转为 AIMessage。"""
        result: list = []
        accumulate_messages(result, AIMessageChunk(content="Hello"))
        accumulate_messages(result, None)
        assert len(result) == 1
        assert isinstance(result[0], AIMessage)
        assert result[0].content == "Hello"

    def test_flush_chunk_via_tool_message(self):
        """ToolMessage 到来时，先 flush 挂起的 chunk 再追加。"""
        result: list = []
        accumulate_messages(result, AIMessageChunk(content="Hello"))
        tm = ToolMessage(content="result", tool_call_id="c1", name="t")
        accumulate_messages(result, tm)
        assert len(result) == 2
        assert isinstance(result[0], AIMessage)
        assert result[0].content == "Hello"
        assert isinstance(result[1], ToolMessage)

    def test_flush_chunk_via_aimessage(self):
        """AIMessage 到来时，先 flush 挂起的 chunk。"""
        result: list = []
        accumulate_messages(result, AIMessageChunk(content="chunk"))
        accumulate_messages(result, AIMessage(content="full"))
        assert len(result) == 2
        assert isinstance(result[0], AIMessage)  # flushed from chunk
        assert isinstance(result[1], AIMessage)

    def test_noop_on_empty_with_none(self):
        """空结果 + None 不产生任何消息。"""
        result: list = []
        accumulate_messages(result, None)
        assert result == []

    def test_append_aimessage_directly(self):
        """无挂起 chunk 时 AIMessage 直接追加。"""
        result: list = []
        accumulate_messages(result, AIMessage(content="ok"))
        assert len(result) == 1
        assert result[0].content == "ok"

    def test_multiple_rounds_merge(self):
        """多轮 chunk 组正确合并和 flush。"""
        result: list = []
        accumulate_messages(result, AIMessageChunk(content="A"))
        accumulate_messages(result, AIMessageChunk(content="B"))
        accumulate_messages(result, ToolMessage(content="t1", tool_call_id="1", name="t"))
        accumulate_messages(result, AIMessageChunk(content="C"))
        accumulate_messages(result, None)
        assert len(result) == 3
        assert isinstance(result[0], AIMessage)
        assert result[0].content == "AB"
        assert isinstance(result[1], ToolMessage)
        assert isinstance(result[2], AIMessage)
        assert result[2].content == "C"


# ════════════════════════════════════════════════════════════════
#  _chunk_to_message 测试
# ════════════════════════════════════════════════════════════════


class TestChunkToMessage:
    def test_basic_conversion(self):
        chunk = AIMessageChunk(content="Hello", additional_kwargs={"reasoning": "think"})
        msg = _chunk_to_message(chunk)
        assert isinstance(msg, AIMessage)
        assert msg.content == "Hello"
        assert msg.additional_kwargs == {"reasoning": "think"}

    def test_with_tool_calls(self):
        tc = ToolCall(name="t", args={}, id="c1")
        chunk = AIMessageChunk(content="", tool_calls=[tc])
        msg = _chunk_to_message(chunk)
        assert msg.tool_calls is not None
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0]["name"] == "t"
        assert msg.tool_calls[0]["id"] == "c1"


# ════════════════════════════════════════════════════════════════
#  Mock Graph（用于 SYNC / MSG 模式测试）
# ════════════════════════════════════════════════════════════════


class MockGraph:
    """模拟编译后的 LangGraph。"""

    def __init__(self, final_state: dict | None = None, events: list[dict] | None = None):
        self.final_state = final_state or {}
        self.events = events or []

    def invoke(self, state: dict, config: dict | None = None) -> dict:
        return self.final_state

    def stream(self, state: dict, stream_mode: str = "updates", config: dict | None = None):
        for event in self.events:
            yield event


def _patch_graph(monkeypatch: pytest.MonkeyPatch, mock_graph: MockGraph) -> None:
    """用 monkeypatch 替换 _build_agent_graph 使其返回 (mock_graph, 999)。"""
    monkeypatch.setattr(
        "xfun.ai.agent._build_agent_graph",
        lambda tools, max_iterations, **kw: (mock_graph, 999),
    )


# ════════════════════════════════════════════════════════════════
#  _drive 辅助
# ════════════════════════════════════════════════════════════════


def _drive(gen):
    """驱动生成器，返回 (yielded, StopIteration.value)。"""
    yielded: list = []
    try:
        while True:
            yielded.append(next(gen))
    except StopIteration as e:
        return yielded, e.value
    return yielded, None  # pragma: no cover


# ════════════════════════════════════════════════════════════════
#  SYNC 模式测试
# ════════════════════════════════════════════════════════════════


class TestAgentInvokeSync:
    def test_no_tools(self, monkeypatch):
        final = {"messages": [AIMessage(content="同步结果", tool_calls=[])]}
        _patch_graph(monkeypatch, MockGraph(final_state=final))

        yielded, _ = _drive(agent_invoke([], tools=[], stream_level=StreamLevel.SYNC))

        assert len(yielded) == 1
        assert yielded[0].content == "同步结果"

    def test_with_tool_calls(self, monkeypatch):
        first = AIMessage(content="查一下", tool_calls=[ToolCall(name="t", args={}, id="c1")])
        tm = ToolMessage(content='{"result":"ok"}', tool_call_id="c1", name="t")
        second = AIMessage(content="完成", tool_calls=[])
        final = {"messages": [first, tm, second]}
        _patch_graph(monkeypatch, MockGraph(final_state=final))

        yielded, _ = _drive(agent_invoke([], tools=[MagicMock()], stream_level=StreamLevel.SYNC))

        assert len(yielded) == 3
        assert yielded[0].content == "查一下"
        assert isinstance(yielded[1], ToolMessage)
        assert yielded[2].content == "完成"

    def test_with_timeout(self, monkeypatch):
        """传递 timeout 等 llm_kwargs，确保参数正常透传（graph 不被 mock 内部干扰）。"""
        final = {"messages": [AIMessage(content="超时测试", tool_calls=[])]}
        _patch_graph(monkeypatch, MockGraph(final_state=final))

        yielded, _ = _drive(
            agent_invoke([], tools=[], stream_level=StreamLevel.SYNC, timeout=30)
        )

        assert yielded[0].content == "超时测试"


# ════════════════════════════════════════════════════════════════
#  MSG 模式测试
# ════════════════════════════════════════════════════════════════


class TestAgentInvokeMsg:
    def test_no_tools(self, monkeypatch):
        events = [
            {"call_model": {"messages": [AIMessage(content="你好世界", tool_calls=[])]}},
        ]
        _patch_graph(monkeypatch, MockGraph(events=events))

        yielded, _ = _drive(agent_invoke([], tools=[], stream_level=StreamLevel.MSG))

        assert len(yielded) == 1
        assert yielded[0].content == "你好世界"

    def test_with_tool_call(self, monkeypatch):
        """MSG 模式含工具调用：yield AIMessage → ToolMessage → AIMessage。"""
        first_aimsg = AIMessage(
            content="让我查查",
            tool_calls=[ToolCall(name="test_tool", args={"key": "val"}, id="c1")],
        )
        tm = ToolMessage(content='{"result":"ok"}', tool_call_id="c1", name="test_tool")
        second_aimsg = AIMessage(content="完成", tool_calls=[])
        events = [
            {"call_model": {"messages": [first_aimsg]}},
            {"tools": {"messages": [tm]}},
            {"call_model": {"messages": [second_aimsg]}},
        ]
        _patch_graph(monkeypatch, MockGraph(events=events))

        yielded, _ = _drive(agent_invoke([], tools=[MagicMock()], stream_level=StreamLevel.MSG))

        assert len(yielded) == 3
        assert yielded[0].content == "让我查查"
        assert isinstance(yielded[1], ToolMessage)
        assert yielded[1].content == '{"result":"ok"}'
        assert yielded[2].content == "完成"


# ════════════════════════════════════════════════════════════════
#  TOKEN 模式测试
# ════════════════════════════════════════════════════════════════


class MockStreamingLLM:
    """模拟 streaming LLM：.stream() 返回预设的 chunk 组。"""

    def __init__(self, chunk_groups: list[list[AIMessageChunk]]):
        self.chunk_groups = chunk_groups
        self.call_count = 0

    def stream(self, messages: list):
        chunks = self.chunk_groups[self.call_count]
        self.call_count += 1
        for c in chunks:
            yield c


class MockToolNode:
    """模拟 ToolNode。"""

    def __init__(self, expected_tools: list | None = None):
        self.expected_tools = expected_tools

    def invoke(self, state: dict) -> dict:
        # 提取最后一个消息的 tool_call，返回对应 ToolMessage
        last_msg = state["messages"][-1]
        tms = []
        for tc in last_msg.tool_calls or []:
            tms.append(
                ToolMessage(
                    content=json.dumps({"result": f"ok_{tc['name']}"}),
                    tool_call_id=tc["id"],
                    name=tc["name"],
                )
            )
        return {"messages": tms}


def _patch_token(monkeypatch: pytest.MonkeyPatch, mock_llm: Any) -> None:
    """为 TOKEN 模式替换 _build_llm 和 ToolNode。"""
    monkeypatch.setattr("xfun.ai.agent._build_llm", lambda tools, **kw: mock_llm)
    monkeypatch.setattr("xfun.ai.agent.ToolNode", MockToolNode)


class TestAgentInvokeToken:
    def test_stream_tokens(self, monkeypatch):
        """TOKEN 模式：逐 chunk yield。"""
        chunks = [
            AIMessageChunk(content="Hel", tool_call_chunks=[]),
            AIMessageChunk(content="lo", tool_call_chunks=[]),
        ]
        _patch_token(monkeypatch, MockStreamingLLM([chunks]))

        yielded, _ = _drive(agent_invoke([], tools=[], stream_level=StreamLevel.TOKEN))

        assert len(yielded) == 2
        assert yielded[0].content == "Hel"
        assert yielded[1].content == "lo"

    def test_with_tool_call(self, monkeypatch, mock_tcc):
        """TOKEN 模式含工具调用：chunks → ToolMessage → 下一轮 chunks。"""
        first_chunks = [
            AIMessageChunk(content="处理", tool_call_chunks=[mock_tcc]),
            AIMessageChunk(content="中", tool_call_chunks=[]),
        ]
        second_chunks = [
            AIMessageChunk(content="完成", tool_call_chunks=[]),
        ]
        _patch_token(monkeypatch, MockStreamingLLM([first_chunks, second_chunks]))

        yielded, _ = _drive(
            agent_invoke([], tools=[MagicMock()], stream_level=StreamLevel.TOKEN)
        )

        # yield: "处理", "中", ToolMessage, "完成"
        assert len(yielded) == 4
        assert yielded[0].content == "处理"
        assert yielded[1].content == "中"
        assert isinstance(yielded[2], ToolMessage)
        assert yielded[3].content == "完成"

    def test_with_reasoning_content(self, monkeypatch):
        """TOKEN 模式含 reasoning_content，覆盖 additional_kwargs 分支。"""
        chunk = AIMessageChunk(
            content="最终答案",
            tool_call_chunks=[],
            additional_kwargs={"reasoning_content": "思考中"},
        )
        _patch_token(monkeypatch, MockStreamingLLM([[chunk]]))

        yielded, _ = _drive(agent_invoke([], tools=[], stream_level=StreamLevel.TOKEN))

        assert yielded[0].content == "最终答案"
        assert yielded[0].additional_kwargs.get("reasoning_content") == "思考中"


# ════════════════════════════════════════════════════════════════
#  边界场景测试
# ════════════════════════════════════════════════════════════════


class TestAgentInvokeEdgeCases:
    def test_max_iterations_sync(self, monkeypatch):
        """SYNC 模式：递归限制防止无限循环。graph 内置 recursion_limit 已在 _build_agent_graph 中计算。"""
        # 构造一个导致循环的最终状态（最后消息含 tool_calls）
        loop_msg = AIMessage(content="继续", tool_calls=[ToolCall(name="t", args={}, id="loop")])
        final = {"messages": [loop_msg]}
        _patch_graph(monkeypatch, MockGraph(final_state=final))

        yielded, _ = _drive(
            agent_invoke([], tools=[MagicMock()], stream_level=StreamLevel.SYNC)
        )
        # 至少 yield 了一条消息（完整的模拟结果，因为 mock graph 不检查 recursion_limit）
        assert len(yielded) == 1

    def test_max_iterations_token(self, monkeypatch):
        """TOKEN 模式：超过 max_iterations 限制时强制终止。"""
        tcc = {"name": "test_tool", "args": '{}', "id": "loop", "index": 0}
        chunks = [AIMessageChunk(content="x", tool_call_chunks=[tcc])]
        # 始终返回含 tool_call 的 chunk，触发循环
        _patch_token(monkeypatch, MockStreamingLLM([chunks] * 20))

        yielded, _ = _drive(
            agent_invoke([], tools=[MagicMock()], stream_level=StreamLevel.TOKEN, max_iterations=3)
        )

        # 3 轮 = 3 chunks + 3 ToolMessages = 6
        assert len(yielded) == 6
        chunks_count = sum(1 for y in yielded if isinstance(y, AIMessageChunk))
        tm_count = sum(1 for y in yielded if isinstance(y, ToolMessage))
        assert chunks_count == 3
        assert tm_count == 3

    def test_default_stream_level(self, monkeypatch):
        """默认 stream_level=SYNC。"""
        final = {"messages": [AIMessage(content="默认同步", tool_calls=[])]}
        _patch_graph(monkeypatch, MockGraph(final_state=final))

        yielded, _ = _drive(agent_invoke([], tools=[]))

        assert yielded[0].content == "默认同步"

    def test_tools_none_treated_as_empty(self, monkeypatch):
        """tools=None 等价于 tools=[]。"""
        final = {"messages": [AIMessage(content="无工具", tool_calls=[])]}
        _patch_graph(monkeypatch, MockGraph(final_state=final))

        yielded, _ = _drive(agent_invoke([], tools=None, stream_level=StreamLevel.SYNC))

        assert yielded[0].content == "无工具"


# ════════════════════════════════════════════════════════════════
#  消息序列化测试
# ════════════════════════════════════════════════════════════════


class TestMessageSerialization:
    def test_parse_messages_json_roundtrip(self):
        """序列化-反序列化往返。"""
        from xfun.ai.agent import messages_to_json, parse_messages_json

        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

        original = [
            SystemMessage(content="sys"),
            HumanMessage(content="hello"),
            AIMessage(content="hi"),
            ToolMessage(content="done", tool_call_id="c1", name="t"),
        ]
        serialized = messages_to_json(original)
        parsed = parse_messages_json(serialized)

        assert len(parsed) == 4
        assert isinstance(parsed[0], SystemMessage)
        assert isinstance(parsed[1], HumanMessage)
        assert isinstance(parsed[2], AIMessage)
        assert isinstance(parsed[3], ToolMessage)
        for o, p in zip(original, parsed):
            assert o.content == p.content

    def test_ensure_system_message_inserts(self):
        from xfun.ai.agent import ensure_system_message
        from langchain_core.messages import HumanMessage, SystemMessage

        msgs = [HumanMessage(content="hi")]
        result = ensure_system_message(msgs, "you are a bot")
        assert len(msgs) == 2
        assert isinstance(msgs[0], SystemMessage)
        assert msgs[0].content == "you are a bot"

    def test_ensure_system_message_no_duplicate(self):
        from xfun.ai.agent import ensure_system_message
        from langchain_core.messages import HumanMessage, SystemMessage

        msgs = [SystemMessage(content="existing"), HumanMessage(content="hi")]
        result = ensure_system_message(msgs, "new-prompt")
        assert len(msgs) == 2
        assert msgs[0].content == "existing"
