"""测试 Agent — 核心生成器 agent_invoke 及辅助函数。"""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolCall,
    ToolMessage,
)

from xfun.ai.agent import (
    StreamLevel,
    _build_llm,
    _execute_tool_call,
    _find_tool,
    _role,
    accumulate_messages,
    agent_invoke,
    ensure_system_message,
    extract_content_parts,
    messages_to_json,
    parse_messages_json,
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
    """直接测试 _build_llm，不 mock 它，只 mock ChatAnthropic。"""

    def test_builds_llm_with_tools(self, monkeypatch, mock_tool):
        class FakeChatAnthropic:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
            def bind_tools(self, tools):
                self.bound_tools = tools
                return self

        monkeypatch.setattr("xfun.ai.agent.ChatAnthropic", FakeChatAnthropic)
        llm = _build_llm([mock_tool], timeout=30, max_retries=3)
        assert llm.bound_tools == [mock_tool]
        assert llm.kwargs.get("timeout") == 30
        assert llm.kwargs.get("max_retries") == 3
        assert "streaming" not in llm.kwargs

    def test_builds_llm_without_tools(self, monkeypatch):
        class FakeChatAnthropic:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
            def bind_tools(self, tools):
                self.bound_tools = tools
                return self

        monkeypatch.setattr("xfun.ai.agent.ChatAnthropic", FakeChatAnthropic)
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


def _consume(gen):
    """驱动生成器，用 accumulate_messages 累积消息。返回 (yielded, new_msgs)。"""
    yielded: list = []
    new_msgs: list = []
    for item in gen:
        yielded.append(item)
        accumulate_messages(new_msgs, item)
    accumulate_messages(new_msgs, None)
    return yielded, new_msgs


def _consume_catching_interrupt(gen):
    """驱动生成器直到 KeyboardInterrupt，返回中断前累积的 (yielded, new_msgs)。"""
    yielded: list = []
    new_msgs: list = []
    try:
        for item in gen:
            yielded.append(item)
            accumulate_messages(new_msgs, item)
    except KeyboardInterrupt:
        pass
    accumulate_messages(new_msgs, None)
    return yielded, new_msgs



class TestAgentInvokeMsg:
    """StreamLevel.MSG — yield 完整 AIMessage + ToolMessage（走 invoke 分支）。"""

    def test_no_tools(self, monkeypatch):
        responses = [AIMessage(content="你好世界", tool_calls=[])]
        _patch_llm(monkeypatch, MockInvokeLLM(responses))

        yielded, new_msgs = _consume(agent_invoke([], tools=[], stream_level=StreamLevel.MSG))

        assert len(yielded) == 1
        assert yielded[0].content == "你好世界"
        assert len(new_msgs) == 1
        assert new_msgs[0].content == "你好世界"

    def test_with_timeout(self, monkeypatch):
        """传递 timeout 参数，覆盖 line 75 的 timeout 分支。"""
        responses = [AIMessage(content="超时测试", tool_calls=[])]
        _patch_llm(monkeypatch, MockInvokeLLM(responses))

        yielded, new_msgs = _consume(
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

        yielded, new_msgs = _consume(
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

        yielded, new_msgs = _consume(
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

        yielded, new_msgs = _consume(
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

        yielded, new_msgs = _consume(
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

        yielded, new_msgs = _consume(
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

        _, new_msgs = _consume(agent_invoke(original, tools=[]))

        # 原始消息未被修改
        assert len(original) == 1
        assert original[0].content == "用户输入"
        # 新消息追加
        assert len(new_msgs) == 1
        assert new_msgs[0].content == "回复1"

    def test_tool_call_interrupted_msg_mode(self, monkeypatch):
        """MSG 模式：工具被 KeyboardInterrupt 中断，yield 仅收到 AIMessage，
        accumulate_messages(None) 后 new_msgs 自动补上错误 ToolMessage。"""
        interrupt_tool = MagicMock()
        interrupt_tool.name = "interrupt_tool"
        interrupt_tool.invoke.side_effect = KeyboardInterrupt()

        first = AIMessage(
            content="正在执行",
            tool_calls=[ToolCall(name="interrupt_tool", args={}, id="c_interrupt")],
        )
        _patch_llm(monkeypatch, MockInvokeLLM([first]))

        yielded, new_msgs = _consume_catching_interrupt(
            agent_invoke([], tools=[interrupt_tool], stream_level=StreamLevel.MSG)
        )

        # yield: 仅 AIMessage（KeyboardInterrupt 发生在 yield ToolMessage 之前）
        assert len(yielded) == 1
        assert isinstance(yielded[0], AIMessage)
        assert yielded[0].content == "正在执行"
        # new_messages 包含 AIMessage + accumulate_messages(None) 补全的错误 ToolMessage
        assert len(new_msgs) == 2
        assert isinstance(new_msgs[0], AIMessage)
        assert new_msgs[0].content == "正在执行"
        assert isinstance(new_msgs[1], ToolMessage)
        assert new_msgs[1].status == "error"
        assert new_msgs[1].tool_call_id == "c_interrupt"
        assert "被中断" in new_msgs[1].content

    def test_tool_call_interrupted_sync_mode(self, monkeypatch):
        """SYNC 模式：工具被中断时 finally 补发错误 ToolMessage，但不 yield（覆盖 line 146 false 分支）。"""
        interrupt_tool = MagicMock()
        interrupt_tool.name = "interrupt_tool"
        interrupt_tool.invoke.side_effect = KeyboardInterrupt()

        first = AIMessage(
            content="同步中断",
            tool_calls=[ToolCall(name="interrupt_tool", args={}, id="c_sync_interrupt")],
        )
        _patch_llm(monkeypatch, MockInvokeLLM([first]))

        # SYNC 模式下 finally 不 yield、异常后也不进入最后的统一 yield 循环
        yielded, new_msgs = _consume_catching_interrupt(
            agent_invoke([], tools=[interrupt_tool], stream_level=StreamLevel.SYNC)
        )

        # 生成器未 yield 任何消息（AIMessage 在 SYNC 下也不 yield）
        assert len(yielded) == 0
        # new_msgs 也为空（local new_messages 未 yield 出来）
        assert len(new_msgs) == 0

    def test_tool_call_interrupted_token_mode(self, monkeypatch):
        """TOKEN 模式：工具被中断时 yield 仅收到 AIMessageChunk，
        accumulate_messages(None) 后 new_msgs 自动补上错误 ToolMessage。"""
        interrupt_tool = MagicMock()
        interrupt_tool.name = "interrupt_tool"
        interrupt_tool.invoke.side_effect = KeyboardInterrupt()

        first_chunks = [
            AIMessageChunk(
                content="token中断",
                tool_call_chunks=[
                    {"name": "interrupt_tool", "args": '{}', "id": "c_token_interrupt", "index": 0}
                ],
            ),
        ]
        _patch_llm(monkeypatch, MockStreamLLM([first_chunks]))

        yielded, new_msgs = _consume_catching_interrupt(
            agent_invoke([], tools=[interrupt_tool], stream_level=StreamLevel.TOKEN)
        )

        # yield: 仅 AIMessageChunk（KeyboardInterrupt 发生在 yield ToolMessage 之前）
        assert len(yielded) == 1
        assert isinstance(yielded[0], AIMessageChunk)
        assert yielded[0].content == "token中断"
        # new_messages: chunk 被 flush 为 AIMessage，再补上错误 ToolMessage
        assert len(new_msgs) == 2
        assert isinstance(new_msgs[0], AIMessage)
        assert isinstance(new_msgs[1], ToolMessage)
        assert new_msgs[1].status == "error"
        assert new_msgs[1].tool_call_id == "c_token_interrupt"
        assert "被中断" in new_msgs[1].content


# ════════════════════════════════════════════════════════════════
#  extract_content_parts 测试
# ════════════════════════════════════════════════════════════════


class TestExtractContentParts:
    def test_string_content_as_list_text(self):
        """content 为 list[dict] 时 text 块正确提取。"""
        msg = AIMessage(content=[{"type": "text", "text": "你好世界"}])
        parts = extract_content_parts(msg)
        # 只有 text 块，key 'thinking' 不存在
        assert "thinking" not in parts
        assert parts.get("text", "") == "你好世界"

    def test_anthropic_thinking_blocks(self):
        """Anthropic thinking mode：content 为 list[dict]，按 type 分拆。"""
        msg = AIMessage(content=[
            {"type": "thinking", "thinking": "让我想想..."},
            {"type": "text", "text": "答案是42"},
        ])
        parts = extract_content_parts(msg)
        assert parts["thinking"] == "让我想想..."
        assert parts["text"] == "答案是42"

    def test_only_thinking(self):
        """只有 thinking 块，无 text 块 — text key 不存在。"""
        msg = AIMessage(content=[
            {"type": "thinking", "thinking": "思考中"},
        ])
        parts = extract_content_parts(msg)
        assert parts.get("thinking", "") == "思考中"
        assert "text" not in parts

    def test_only_text(self):
        """只有 text 块，无 thinking 块 — thinking key 不存在。"""
        msg = AIMessage(content=[
            {"type": "text", "text": "纯文本回复"},
        ])
        parts = extract_content_parts(msg)
        assert "thinking" not in parts
        assert parts.get("text", "") == "纯文本回复"

    def test_multiple_blocks(self):
        """多段 thinking 和 text 交替出现时正确拼接。"""
        msg = AIMessage(content=[
            {"type": "thinking", "thinking": "第一步..."},
            {"type": "text", "text": "结果A"},
            {"type": "thinking", "thinking": "第二步..."},
            {"type": "text", "text": "结果B"},
        ])
        parts = extract_content_parts(msg)
        assert parts["thinking"] == "第一步...第二步..."
        assert parts["text"] == "结果A结果B"

    def test_chunk_with_list_content(self):
        """AIMessageChunk 的 list[dict] content。"""
        chunk = AIMessageChunk(content=[{"type": "text", "text": "流式文本"}])
        parts = extract_content_parts(chunk)
        assert "thinking" not in parts
        assert parts.get("text", "") == "流式文本"


class TestAgentInvokeSyncMode:
    """StreamLevel.SYNC 通过 `agent_invoke` 生成器驱动。"""

    def test_returns_new_messages(self, monkeypatch):
        responses = [AIMessage(content="同步结果", tool_calls=[])]
        _patch_llm(monkeypatch, MockInvokeLLM(responses))

        yielded, new_msgs = _consume(agent_invoke([], tools=[], stream_level=StreamLevel.SYNC))

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

        yielded, new_msgs = _consume(
            agent_invoke([], tools=[mock_tool], stream_level=StreamLevel.SYNC)
        )

        # SYNC 模式 yield 所有消息（3条）
        assert len(yielded) == 3
        assert isinstance(yielded[1], ToolMessage)
        assert len(new_msgs) == 3
        assert isinstance(new_msgs[1], ToolMessage)


# ════════════════════════════════════════════════════════════════
#  _role 测试
# ════════════════════════════════════════════════════════════════


class TestRole:
    def test_human_message(self):
        assert _role(HumanMessage(content="hi")) == "user"

    def test_ai_message(self):
        assert _role(AIMessage(content="hello")) == "assistant"

    def test_system_message(self):
        assert _role(SystemMessage(content="sys")) == "system"

    def test_tool_message(self):
        assert _role(ToolMessage(content="ok", tool_call_id="c1")) == "tool"

    def test_unknown_type(self):
        """未注册的 BaseMessage 子类返回 'unknown'。"""

        class UnknownMessage(BaseMessage):
            content: str = ""
            type: str = "unknown"

        msg = UnknownMessage(content="??")
        assert _role(msg) == "unknown"


# ════════════════════════════════════════════════════════════════
#  parse_messages_json 测试
# ════════════════════════════════════════════════════════════════


class TestParseMessagesJson:
    def test_parse_user(self):
        obj = [{"role": "user", "content": "你好"}]
        msgs = parse_messages_json(obj)
        assert len(msgs) == 1
        assert isinstance(msgs[0], HumanMessage)
        assert msgs[0].content == "你好"

    def test_parse_assistant(self):
        obj = [{"role": "assistant", "content": "回复"}]
        msgs = parse_messages_json(obj)
        assert isinstance(msgs[0], AIMessage)
        assert msgs[0].content == "回复"

    def test_parse_system(self):
        obj = [{"role": "system", "content": "系统提示"}]
        msgs = parse_messages_json(obj)
        assert isinstance(msgs[0], SystemMessage)
        assert msgs[0].content == "系统提示"

    def test_parse_tool(self):
        obj = [{"role": "tool", "content": "tool result", "tool_call_id": "c1"}]
        msgs = parse_messages_json(obj)
        assert isinstance(msgs[0], ToolMessage)
        assert msgs[0].content == "tool result"

    def test_missing_role_defaults_to_user(self):
        """缺少 role 字段时默认解析为 HumanMessage。"""
        obj = [{"content": "无角色"}]
        msgs = parse_messages_json(obj)
        assert isinstance(msgs[0], HumanMessage)
        assert msgs[0].content == "无角色"

    def test_unknown_role_defaults_to_human(self):
        """未知 role 值默认解析为 HumanMessage。"""
        obj = [{"role": "ghost", "content": "???"}]
        msgs = parse_messages_json(obj)
        assert isinstance(msgs[0], HumanMessage)

    def test_multiple_messages(self):
        obj = [
            {"role": "user", "content": "问"},
            {"role": "assistant", "content": "答"},
        ]
        msgs = parse_messages_json(obj)
        assert len(msgs) == 2
        assert isinstance(msgs[0], HumanMessage)
        assert isinstance(msgs[1], AIMessage)

    def test_preserves_additional_kwargs(self):
        """扩展字段（如 additional_kwargs）在解析后得以保留。"""
        obj = [{"role": "user", "content": "hi", "additional_kwargs": {"key": "val"}}]
        msgs = parse_messages_json(obj)
        assert msgs[0].additional_kwargs == {"key": "val"}


# ════════════════════════════════════════════════════════════════
#  messages_to_json 测试
# ════════════════════════════════════════════════════════════════


class TestMessagesToJson:
    def test_serialize_user(self):
        msgs = [HumanMessage(content="hi")]
        result = messages_to_json(msgs)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "hi"

    def test_serialize_multiple(self):
        msgs = [
            HumanMessage(content="问"),
            AIMessage(content="答"),
        ]
        result = messages_to_json(msgs)
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "问"
        assert result[1]["role"] == "assistant"
        assert result[1]["content"] == "答"

    def test_serialize_includes_role(self):
        """每种消息类型的序列化结果都包含正确的 role。"""
        msgs = [
            HumanMessage(content="u"),
            AIMessage(content="a"),
            SystemMessage(content="s"),
            ToolMessage(content="t", tool_call_id="c1"),
        ]
        result = messages_to_json(msgs)
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
        assert result[2]["role"] == "system"
        assert result[3]["role"] == "tool"

    def test_round_trip(self):
        """序列化后反序列化，消息内容应保持一致。"""
        original = [
            HumanMessage(content="用户输入"),
            AIMessage(content="AI回复"),
        ]
        serialized = messages_to_json(original)
        restored = parse_messages_json(serialized)
        for orig, rest in zip(original, restored):
            assert type(orig) is type(rest)
            assert orig.content == rest.content
            assert _role(orig) == _role(rest)


# ════════════════════════════════════════════════════════════════
#  ensure_system_message 测试
# ════════════════════════════════════════════════════════════════


class TestEnsureSystemMessage:
    def test_inserts_when_missing(self):
        """无 SystemMessage 时在开头插入。"""
        msgs = [HumanMessage(content="hi")]
        result = ensure_system_message(msgs, "sys prompt")
        assert len(result) == 2
        assert isinstance(result[0], SystemMessage)
        assert result[0].content == "sys prompt"
        assert result[1].content == "hi"

    def test_no_insert_when_present(self):
        """已有 SystemMessage 时不做插入。"""
        msgs = [SystemMessage(content="existing"), HumanMessage(content="hi")]
        result = ensure_system_message(msgs, "new prompt")
        assert len(result) == 2
        assert result[0].content == "existing"

    def test_mutates_in_place(self):
        """返回的列表与入参为同一对象。"""
        msgs = [HumanMessage(content="hi")]
        result = ensure_system_message(msgs, "prompt")
        assert result is msgs
