"""测试 agent_invoke 核心逻辑。

- 无 API Key → AIError
- 无工具调用 → 直接返回 AI 回答
- 工具调用 → 工具执行 → AI 最终回答
- 工具执行异常 → 错误 JSON
- 系统提示词注入/去重
- 最大迭代保护
"""

import json
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from xfun.ai.agent import _find_tool, _prepare_messages, agent_invoke
from xfun.core.errors import AIError


# ══════════════════════════════════════════════════════════════════════
#  无 API Key
# ══════════════════════════════════════════════════════════════════════


class TestNoAPIKey:
    def test_raises(self, monkeypatch):
        monkeypatch.setattr("xfun.ai.agent.LLM_API_KEY", "")
        with pytest.raises(AIError, match="LLM_API_KEY"):
            agent_invoke([HumanMessage(content="hi")])


# ══════════════════════════════════════════════════════════════════════
#  直接回复（无工具调用）
# ══════════════════════════════════════════════════════════════════════


class TestDirectReply:
    @pytest.fixture(autouse=True)
    def _mock_llm(self, monkeypatch):
        mock = MagicMock()
        mock.bind_tools.return_value = mock
        mock.invoke.return_value = AIMessage(content="你好，我是 AI 助手！")
        monkeypatch.setattr("xfun.ai.agent.ChatOpenAI", lambda **kw: mock)

    def test_returns_single_ai_message(self):
        new = agent_invoke([HumanMessage(content="你好")])
        assert len(new) == 1
        assert isinstance(new[0], AIMessage)

    def test_content_contains_reply(self):
        new = agent_invoke([HumanMessage(content="你好")])
        assert "你好" in new[0].content

    def test_caller_can_extend(self):
        msgs = [HumanMessage(content="你好")]
        new = agent_invoke(msgs)
        msgs.extend(new)
        assert len(msgs) == 2


# ══════════════════════════════════════════════════════════════════════
#  工具调用循环
# ══════════════════════════════════════════════════════════════════════


class TestToolCallLoop:
    @pytest.fixture(autouse=True)
    def _mock_tool(self, monkeypatch):
        tool = MagicMock()
        tool.name = "query_entries"
        tool.invoke.return_value = json.dumps({"results": [{"content": "任务1"}]})
        monkeypatch.setattr("xfun.ai.agent._find_tool", lambda name: tool)

    @pytest.fixture(autouse=True)
    def _mock_llm(self, monkeypatch):
        calls = [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "query_entries",
                        "args": {"view": {"plan": []}, "notetype": "plan"},
                        "id": "call_1",
                    }
                ],
            ),
            AIMessage(content="查到了，本月有 3 个任务。"),
        ]
        mock = MagicMock()
        mock.bind_tools.return_value = mock
        mock.invoke.side_effect = calls
        monkeypatch.setattr("xfun.ai.agent.ChatOpenAI", lambda **kw: mock)

    def test_returns_three_messages(self):
        new = agent_invoke([HumanMessage(content="这个月有什么计划？")])
        assert len(new) == 3

    def test_message_types(self):
        new = agent_invoke([HumanMessage(content="这个月有什么计划？")])
        assert isinstance(new[0], AIMessage)  # 请求工具
        assert isinstance(new[1], ToolMessage)  # 工具结果
        assert isinstance(new[2], AIMessage)  # 最终回复

    def test_tool_message_content(self):
        new = agent_invoke([HumanMessage(content="这个月有什么计划？")])
        data = json.loads(new[1].content)
        assert "results" in data
        assert data["results"][0]["content"] == "任务1"

    def test_final_reply(self):
        new = agent_invoke([HumanMessage(content="这个月有什么计划？")])
        assert "查到了" in new[2].content


# ══════════════════════════════════════════════════════════════════════
#  工具执行异常
# ══════════════════════════════════════════════════════════════════════


class TestToolCallError:
    @pytest.fixture(autouse=True)
    def _mock_llm(self, monkeypatch):
        mock = MagicMock()
        mock.bind_tools.return_value = mock
        # 第一轮返回工具请求，第二轮返回最终回复（循环终止）
        mock.invoke.side_effect = [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "query_entries",
                        "args": {},
                        "id": "call_err",
                    }
                ],
            ),
            AIMessage(content="处理完毕"),
        ]
        monkeypatch.setattr("xfun.ai.agent.ChatOpenAI", lambda **kw: mock)

    def test_error_wrapped_in_json(self, monkeypatch):
        tool = MagicMock()
        tool.name = "query_entries"
        tool.invoke.side_effect = ValueError("突然错误")
        monkeypatch.setattr("xfun.ai.agent._find_tool", lambda name: tool)

        new = agent_invoke([HumanMessage(content="查")])
        assert len(new) == 3  # AIMessage(tool) + ToolMessage(error) + AIMessage(final)
        err = json.loads(new[1].content)
        assert "error" in err
        assert new[2].content == "处理完毕"


# ══════════════════════════════════════════════════════════════════════
#  最大迭代保护
# ══════════════════════════════════════════════════════════════════════


class TestMaxIterations:
    @pytest.fixture(autouse=True)
    def _mock_tool(self, monkeypatch):
        tool = MagicMock()
        tool.name = "query_entries"
        tool.invoke.return_value = "{}"
        monkeypatch.setattr("xfun.ai.agent._find_tool", lambda name: tool)

    @pytest.fixture(autouse=True)
    def _mock_llm(self, monkeypatch):
        response = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "query_entries",
                    "args": {},
                    "id": "call_loop",
                }
            ],
        )
        mock = MagicMock()
        mock.bind_tools.return_value = mock
        mock.invoke.return_value = response
        monkeypatch.setattr("xfun.ai.agent.ChatOpenAI", lambda **kw: mock)
        monkeypatch.setattr("xfun.ai.agent._MAX_ITERATIONS", 3)

    def test_stops_at_max_iterations(self):
        new = agent_invoke([HumanMessage(content="循环")])
        # 3 轮 × [AIMessage + ToolMessage] = 6
        assert len(new) == 6

    def test_last_message_is_tool_call(self):
        new = agent_invoke([HumanMessage(content="循环")])
        # 倒数第二条是第 3 轮发出的工具请求（未收到最终回复）
        assert isinstance(new[-2], AIMessage)
        assert new[-2].tool_calls
        # 最后一条是第 3 轮的工具执行结果
        assert isinstance(new[-1], ToolMessage)


# ══════════════════════════════════════════════════════════════════════
#  未知工具 → AIError
# ══════════════════════════════════════════════════════════════════════


class TestUnknownTool:
    @pytest.fixture(autouse=True)
    def _mock_llm(self, monkeypatch):
        mock = MagicMock()
        mock.bind_tools.return_value = mock
        mock.invoke.return_value = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "nonexistent_tool",
                    "args": {},
                    "id": "call_bad",
                }
            ],
        )
        monkeypatch.setattr("xfun.ai.agent.ChatOpenAI", lambda **kw: mock)

    def test_unknown_tool_raises(self):
        with pytest.raises(AIError, match="未知工具"):
            agent_invoke([HumanMessage(content="查")])


# ══════════════════════════════════════════════════════════════════════
#  系统提示词注入 / 去重
# ══════════════════════════════════════════════════════════════════════


class TestPrepareMessages:
    def test_empty_messages(self):
        result = _prepare_messages([], None)
        assert len(result) == 1
        assert isinstance(result[0], SystemMessage)

    def test_dedup_same_content(self):
        from xfun.ai.prompts import SYSTEM_PROMPT

        msgs = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content="hi")]
        result = _prepare_messages(msgs, None)
        assert len(result) == 2
        assert result[0].content == SYSTEM_PROMPT

    def test_replace_different_system(self):
        msgs = [SystemMessage(content="旧的提示词"), HumanMessage(content="hi")]
        result = _prepare_messages(msgs, "新的提示词")
        assert len(result) == 2
        assert result[0].content == "新的提示词"
        assert isinstance(result[1], HumanMessage)

    def test_custom_system_prompt_no_existing(self):
        msgs = [HumanMessage(content="hi")]
        result = _prepare_messages(msgs, "自定义提示词")
        assert len(result) == 2
        assert isinstance(result[0], SystemMessage)
        assert result[0].content == "自定义提示词"


# ══════════════════════════════════════════════════════════════════════
#  _find_tool
# ══════════════════════════════════════════════════════════════════════


class TestFindTool:
    def test_finds_existing(self):
        tool = _find_tool("query_entries")
        assert tool is not None
        assert tool.name == "query_entries"

    def test_nonexistent_returns_none(self):
        assert _find_tool("nonexistent_tool") is None
