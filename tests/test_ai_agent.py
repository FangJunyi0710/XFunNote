"""测试 Agent — 核心生成器 agent_invoke 及辅助函数。"""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk, ToolCall, ToolMessage

from xfun.ai.agent import (
    StreamLevel,
    _accumulate_tool_calls,
    _build_llm,
    _execute_tool_call,
    _find_tool,
    agent_invoke,
)


# ════════════════════════════════════════════════════════════════
#  夹具
# ════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_tool():
    tool = MagicMock()
    tool.name = "test_tool"
    tool.invoke.return_value = '{"result": "ok"}'
    return tool


@pytest.fixture
def mock_error_tool():
    tool = MagicMock()
    tool.name = "error_tool"
    tool.invoke.side_effect = ValueError("工具执行失败")
    return tool


@pytest.fixture
def mock_tcc():
    """创建一个 ToolCallChunk 风格的 dict。"""
    return {"name": "test_tool", "args": '{"key": "val"}', "id": "call_1", "index": 0}


# ════════════════════════════════════════════════════════════════
#  纯函数测试
# ════════════════════════════════════════════════════════════════


class TestFindTool:
    def test_found(self, mock_tool):
        result = _find_tool("test_tool", [mock_tool])
        assert result is mock_tool

    def test_not_found(self, mock_tool):
        result = _find_tool("nonexistent", [mock_tool])
        assert result is None


class TestAccumulateToolCalls:
    """_accumulate_tool_calls: dict[int, dict[str, str]] → list[ToolCall]"""

    def test_single_call(self):
        buf = {0: {"name": "tool_a", "args": '{"x": 1}', "id": "call_0"}}
        calls = _accumulate_tool_calls(buf)
        assert len(calls) == 1
        assert calls[0]["name"] == "tool_a"
        assert calls[0]["args"] == {"x": 1}
        assert calls[0]["id"] == "call_0"

    def test_empty_args(self):
        buf = {0: {"name": "tool_a", "args": "", "id": ""}}
        calls = _accumulate_tool_calls(buf)
        assert len(calls) == 1
        assert calls[0]["args"] == {}
        assert calls[0]["id"].startswith("stream_")

    def test_invalid_json_args(self):
        buf = {0: {"name": "tool_a", "args": "not-json{", "id": "call_1"}}
        calls = _accumulate_tool_calls(buf)
        assert len(calls) == 1
        assert calls[0]["args"] == {}

    def test_multiple_indices(self):
        buf = {
            1: {"name": "tool_b", "args": '{"b": 2}', "id": "call_1"},
            0: {"name": "tool_a", "args": '{"a": 1}', "id": "call_0"},
        }
        calls = _accumulate_tool_calls(buf)
        assert len(calls) == 2
        assert calls[0]["name"] == "tool_a"
        assert calls[0]["id"] == "call_0"
        assert calls[1]["name"] == "tool_b"
        assert calls[1]["id"] == "call_1"

    def test_empty_buffers(self):
        assert _accumulate_tool_calls({}) == []


class TestExecuteToolCall:
    def test_success(self, mock_tool):
        tc = ToolCall(name="test_tool", args={"key": "val"}, id="call_1")
        tm = _execute_tool_call(tc, [mock_tool])
        assert tm.content == '{"result": "ok"}'
        assert tm.tool_call_id == "call_1"

    def test_tool_exception_captured(self, mock_error_tool):
        tc = ToolCall(name="error_tool", args={}, id="call_2")
        tm = _execute_tool_call(tc, [mock_error_tool])
        result = json.loads(tm.content)
        assert "error" in result
        assert "工具执行失败" in result["error"]

    def test_tool_not_found(self):
        tc = ToolCall(name="nonexistent", args={}, id="call_3")
        tm = _execute_tool_call(tc, [])
        result = json.loads(tm.content)
        assert "error" in result
        assert "未知工具" in result["error"]
        assert tm.tool_call_id == "call_3"


class TestStreamLevel:
    def test_enum_members(self):
        assert StreamLevel.TOKEN.value == 1
        assert StreamLevel.MSG.value == 2
        assert StreamLevel.SYNC.value == 3

    def test_is_enum(self):
        assert isinstance(StreamLevel.TOKEN, StreamLevel)


# ════════════════════════════════════════════════════════════════
#  _build_llm 测试
# ════════════════════════════════════════════════════════════════


class TestBuildLLM:
    """直接测试 _build_llm，不 mock 它，只 mock ChatOpenAI。"""

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
#  Mock LLM 辅助
# ════════════════════════════════════════════════════════════════


class MockInvokeLLM:
    """模拟 SYNC 模式的 LLM：.invoke() 返回按序预设的 AIMessage。"""

    def __init__(self, responses: list[AIMessage]):
        self.responses = responses
        self.call_count = 0

    def invoke(self, messages: list) -> AIMessage:
        resp = self.responses[self.call_count]
        self.call_count += 1
        return resp


class MockStreamLLM:
    """模拟 MSG/TOKEN 模式的 LLM：.stream() 返回预设的 chunk 组。"""

    def __init__(self, chunk_groups: list[list[AIMessageChunk]], /):
        self.chunk_groups = chunk_groups
        self.call_count = 0

    def stream(self, messages: list):
        chunks = self.chunk_groups[self.call_count]
        self.call_count += 1
        for c in chunks:
            yield c


def _patch_llm(monkeypatch: pytest.MonkeyPatch, mock_llm: Any) -> None:
    """用 monkeypatch 替换 _build_llm 使其返回 mock_llm。"""
    monkeypatch.setattr("xfun.ai.agent._build_llm", lambda tools, **kw: mock_llm)


# ════════════════════════════════════════════════════════════════
#  生成器测试
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



class TestAgentInvokeMsg:
    """StreamLevel.MSG — yield 完整 AIMessage + ToolMessage（走 invoke 分支）。"""

    def test_no_tools(self, monkeypatch):
        responses = [AIMessage(content="你好世界", tool_calls=[])]
        _patch_llm(monkeypatch, MockInvokeLLM(responses))

        yielded, new_msgs = _drive(agent_invoke([], tools=[], stream_level=StreamLevel.MSG))

        assert len(yielded) == 1
        assert yielded[0].content == "你好世界"
        assert len(new_msgs) == 1
        assert new_msgs[0].content == "你好世界"

    def test_with_timeout(self, monkeypatch):
        """传递 timeout 参数，覆盖 line 75 的 timeout 分支。"""
        responses = [AIMessage(content="超时测试", tool_calls=[])]
        _patch_llm(monkeypatch, MockInvokeLLM(responses))

        yielded, new_msgs = _drive(
            agent_invoke([], tools=[], stream_level=StreamLevel.MSG, timeout=30)
        )

        assert yielded[0].content == "超时测试"
        assert len(new_msgs) == 1

    def test_with_tool_call(self, monkeypatch, mock_tool):
        """MSG 模式含工具调用：yield 顺序 AIMessage → ToolMessage → AIMessage。"""
        first = AIMessage(
            content="让我查查",
            tool_calls=[ToolCall(name="test_tool", args={"key": "val"}, id="c1")],
        )
        second = AIMessage(content="完成", tool_calls=[])
        _patch_llm(monkeypatch, MockInvokeLLM([first, second]))

        yielded, new_msgs = _drive(
            agent_invoke([], tools=[mock_tool], stream_level=StreamLevel.MSG)
        )

        # 3 个 yield: 第一个 AIMessage + ToolMessage + 第二个 AIMessage
        assert len(yielded) == 3
        assert yielded[0].content == "让我查查"
        assert isinstance(yielded[1], ToolMessage)
        assert yielded[1].content == '{"result": "ok"}'
        assert yielded[2].content == "完成"
        assert len(new_msgs) == 3


class TestAgentInvokeToken:
    """StreamLevel.TOKEN — 逐 chunk yield + yield ToolMessage。"""

    def test_stream_tokens(self, monkeypatch):
        chunk_a = AIMessageChunk(content="Hel", tool_call_chunks=[])
        chunk_b = AIMessageChunk(content="lo", tool_call_chunks=[])
        _patch_llm(monkeypatch, MockStreamLLM([[chunk_a, chunk_b]]))

        yielded, new_msgs = _drive(
            agent_invoke([], tools=[], stream_level=StreamLevel.TOKEN)
        )

        assert len(yielded) == 2
        assert yielded[0].content == "Hel"
        assert yielded[1].content == "lo"
        # new_messages 是完整组装后的消息
        assert len(new_msgs) == 1
        assert new_msgs[0].content == "Hello"

    def test_stream_tokens_with_reasoning(self, monkeypatch):
        """TOKEN 模式含 reasoning_content，覆盖 line 89 分支。"""
        chunk = AIMessageChunk(
            content="最终答案",
            tool_call_chunks=[],
            additional_kwargs={"reasoning_content": "思考中"},
        )
        _patch_llm(monkeypatch, MockStreamLLM([[chunk]]))

        yielded, new_msgs = _drive(
            agent_invoke([], tools=[], stream_level=StreamLevel.TOKEN)
        )

        assert yielded[0].content == "最终答案"
        assert len(new_msgs) == 1
        assert new_msgs[0].additional_kwargs.get("reasoning_content") == "思考中"

    def test_with_tool_call(self, monkeypatch, mock_tool, mock_tcc):
        """TOKEN 模式含工具调用：yield chunk → ToolMessage → 下一轮 chunk。"""
        first_chunks = [
            AIMessageChunk(
                content="处理",
                tool_call_chunks=[mock_tcc],
            ),
            AIMessageChunk(
                content="中",
                tool_call_chunks=[],
            ),
        ]
        second_chunks = [
            AIMessageChunk(content="完成", tool_call_chunks=[]),
        ]
        _patch_llm(monkeypatch, MockStreamLLM([first_chunks, second_chunks]))

        yielded, new_msgs = _drive(
            agent_invoke([], tools=[mock_tool], stream_level=StreamLevel.TOKEN)
        )

        # yield: "处理", "中", ToolMessage, "完成"
        assert len(yielded) == 4
        assert yielded[0].content == "处理"
        assert yielded[1].content == "中"
        assert isinstance(yielded[2], ToolMessage)
        assert yielded[3].content == "完成"


class TestAgentInvokeEdgeCases:
    def test_max_iterations(self, monkeypatch, mock_tool):
        """超过 max_iterations 限制时强制终止。"""
        tc = ToolCall(name="test_tool", args={}, id="loop")
        resp = AIMessage(content="继续", tool_calls=[tc])

        class InfiniteLLM:
            def __init__(self):
                self.call_count = 0
            def invoke(self, messages):
                self.call_count += 1
                return resp

        infinite = InfiniteLLM()
        _patch_llm(monkeypatch, infinite)

        yielded, new_msgs = _drive(
            agent_invoke([], tools=[mock_tool], stream_level=StreamLevel.SYNC)
        )

        # 应该 10 轮停止
        assert infinite.call_count == 10
        # 10 AIMessages + 10 ToolMessages
        assert len(new_msgs) == 20
        assert all(isinstance(m, (AIMessage, ToolMessage)) for m in new_msgs)

    def test_preserves_working_messages(self, monkeypatch):
        """working_messages 在每轮中累积，调用方传入的消息不被修改。"""
        from langchain_core.messages import HumanMessage

        original = [HumanMessage(content="用户输入")]
        first = AIMessage(content="回复1", tool_calls=[])
        _patch_llm(monkeypatch, MockInvokeLLM([first]))

        _, new_msgs = _drive(agent_invoke(original, tools=[]))

        # 原始消息未被修改
        assert len(original) == 1
        assert original[0].content == "用户输入"
        # 新消息追加
        assert len(new_msgs) == 1
        assert new_msgs[0].content == "回复1"


class TestAgentInvokeSyncMode:
    """StreamLevel.SYNC 通过 `agent_invoke` 生成器驱动。"""

    def test_returns_new_messages(self, monkeypatch):
        responses = [AIMessage(content="同步结果", tool_calls=[])]
        _patch_llm(monkeypatch, MockInvokeLLM(responses))

        yielded, new_msgs = _drive(agent_invoke([], tools=[], stream_level=StreamLevel.SYNC))

        # SYNC 模式：所有消息在最后统一 yield
        assert len(yielded) == 1
        assert yielded[0].content == "同步结果"
        assert len(new_msgs) == 1
        assert new_msgs[0].content == "同步结果"

    def test_with_tool_calls(self, monkeypatch, mock_tool):
        first = AIMessage(
            content="查一下",
            tool_calls=[ToolCall(name="test_tool", args={"x": 1}, id="c1")],
        )
        second = AIMessage(content="完成", tool_calls=[])
        _patch_llm(monkeypatch, MockInvokeLLM([first, second]))

        yielded, new_msgs = _drive(
            agent_invoke([], tools=[mock_tool], stream_level=StreamLevel.SYNC)
        )

        # SYNC 模式 yield 所有消息（3条）
        assert len(yielded) == 3
        assert isinstance(yielded[1], ToolMessage)
        assert len(new_msgs) == 3
        assert isinstance(new_msgs[1], ToolMessage)
