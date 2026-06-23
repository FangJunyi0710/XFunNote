"""
DeepSeek API 客户端封装，自动管理 Function Calling 工具。

用法::

    client = AIClient()
    result = client.chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "帮我查询本月计划"},
    ])
"""

import json
import os
import sys
from typing import Any, Callable, Dict, Generator, List

from openai import OpenAI, Stream
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from xfun.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

from . import tools

# ---------------------------------------------------------------------------
# Function Calling 工具定义（JSON Schema 格式）
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "query_entries",
            "description": "查询本子中的条目（只读）。通过View指定要查询的表、列和筛选条件，系统自动限制为AI可读范围。",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "enum": ["plan", "diary", "word", "accumulation"],
                        "description": "本子名称",
                    },
                    "view_json": {
                        "type": "string",
                        "description": "View JSON，格式如 '{\"plan\":[[[\"id\",\"content\",\"month\"],[{\"column\":\"month\",\"value\":\"2606\"}]]]}'，外层key为表名，值为[[列名列表,筛选条件],...]",
                    },
                    "order_by": {
                        "type": "string",
                        "description": "排序列名，如 'created_at DESC'",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "最多返回条数",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "偏移量",
                    },
                },
                "required": ["table", "view_json"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_entries",
            "description": "添加条目到本子。自动标记为 AI 生成（is_ai_gen=1）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "enum": ["plan", "diary", "word", "accumulation"],
                        "description": "本子名称",
                    },
                    "entries_json": {
                        "type": "string",
                        "description": "JSON数组，如 '[{\"content\":\"学习Python\",\"month\":\"2606\"}]'",
                    },
                },
                "required": ["table", "entries_json"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_entries",
            "description": "更新条目。只允许修改白名单列：tags, ai_tags, ai_note, done, review_count, performance, next_review, last_review。",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "enum": ["plan", "diary", "word", "accumulation"],
                        "description": "本子名称",
                    },
                    "entry_ids_json": {
                        "type": "string",
                        "description": "JSON数组，要更新的条目ID，如 '[\"plan-2606-xxx\"]'",
                    },
                    "entry_json": {
                        "type": "string",
                        "description": "JSON对象，要更新的字段，如 '{\"done\":1}'",
                    },
                },
                "required": ["table", "entry_ids_json", "entry_json"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_entries",
            "description": "删除条目（仅限AI创建的）。需要用户确认。",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "enum": ["plan", "diary", "word", "accumulation"],
                        "description": "本子名称",
                    },
                    "entry_ids_json": {
                        "type": "string",
                        "description": "JSON数组，要删除的条目ID",
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "确认删除，必须为true",
                    },
                },
                "required": ["table", "entry_ids_json", "confirm"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "manage_tags",
            "description": "管理条目标签：添加(add)、移除(remove)或替换(set)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "enum": ["plan", "diary", "word", "accumulation"],
                        "description": "本子名称",
                    },
                    "entry_ids_json": {
                        "type": "string",
                        "description": "JSON数组，条目ID列表",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["add", "remove", "set"],
                        "description": "操作模式: add/remove/set",
                    },
                    "tags_json": {
                        "type": "string",
                        "description": "JSON数组，标签列表",
                    },
                },
                "required": ["table", "entry_ids_json", "mode", "tags_json"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_ai_note",
            "description": "追加 AI 备注到条目，保留原有内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "enum": ["plan", "diary", "word", "accumulation"],
                        "description": "本子名称",
                    },
                    "entry_id": {
                        "type": "string",
                        "description": "条目ID",
                    },
                    "note": {
                        "type": "string",
                        "description": "要追加的备注内容",
                    },
                },
                "required": ["table", "entry_id", "note"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_memories",
            "description": "跨本子搜索AI相关内容。在所有本子中检索匹配的内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词",
                    },
                    "category": {
                        "type": "string",
                        "description": "积累本分类筛选",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "保存内容到积累本，自动分类为「AI记忆」。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "记忆内容",
                    },
                    "source": {
                        "type": "string",
                        "description": "来源",
                    },
                    "note": {
                        "type": "string",
                        "description": "备注",
                    },
                },
                "required": ["content"],
            },
        },
    },
]


class AIClient:
    """DeepSeek API 客户端封装，自动管理 Function Calling 工具。"""

    def __init__(self):
        if not DEEPSEEK_API_KEY:
            raise ValueError(
                "DEEPSEEK_API_KEY 未设置，请在 .env 文件中配置"
            )
        base_url = DEEPSEEK_BASE_URL or "https://api.deepseek.com"
        print(f"[debug] base_url={base_url}", file=sys.stderr)
        print(f"[debug] http_proxy={os.environ.get('http_proxy', '')} https_proxy={os.environ.get('https_proxy', '')}", file=sys.stderr)
        print(f"[debug] SSL_CERT_FILE={os.environ.get('SSL_CERT_FILE', '')} REQUESTS_CA_BUNDLE={os.environ.get('REQUESTS_CA_BUNDLE', '')}", file=sys.stderr)
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )
        self.model = DEEPSEEK_MODEL
        self._tools = TOOL_DEFINITIONS
        self._tool_map = self._build_tool_map()

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _build_tool_map(self) -> Dict[str, Callable]:
        """工具名 → 实际 Python 函数 的映射。"""
        return {
            "query_entries": tools.query_entries,
            "add_entries": tools.add_entries,
            "update_entries": tools.update_entries,
            "delete_entries": tools.delete_entries,
            "manage_tags": tools.manage_tags,
            "add_ai_note": tools.add_ai_note,
            "search_memories": tools.search_memories,
            "save_memory": tools.save_memory,
        }

    def _execute_tool_call(self, tool_call) -> str:
        """执行单个 tool call，返回 JSON 结果字符串。"""
        func_name = tool_call.function.name
        func = self._tool_map.get(func_name)
        if not func:
            return json.dumps({"error": f"未知工具: {func_name}"}, ensure_ascii=False)
        try:
            args = json.loads(tool_call.function.arguments)
            return func(**args)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def _non_streaming_tool_round(self, messages: list) -> ChatCompletion:
        """一轮非流式的 API 调用（用于检测是否需要工具调用）。"""
        print(f"[debug] _non_streaming_tool_round: model={self.model}, msgs={len(messages)}", file=sys.stderr)
        try:
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self._tools,
                tool_choice="auto",
                extra_body={"thinking": {"type": "disabled"}},
            )
        except Exception as e:
            print(f"[debug] _non_streaming_tool_round error: {type(e).__name__}: {e}", file=sys.stderr)
            raise

    def _streaming_round(self, messages: list) -> Stream[ChatCompletionChunk]:
        """纯流式输出，不携带 tools（避免流式工具调用的复杂性）。"""
        print(f"[debug] _streaming_round: model={self.model}, msgs={len(messages)}", file=sys.stderr)
        try:
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                extra_body={"thinking": {"type": "disabled"}},
            )
        except Exception as e:
            print(f"[debug] _streaming_round error: {type(e).__name__}: {e}", file=sys.stderr)
            raise

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tool_rounds: int = 5,
    ) -> str:
        """
        带 Function Calling 的对话。

        Parameters
        ----------
        messages : list[dict]
            消息列表，格式同 OpenAI API。
        max_tool_rounds : int
            最大工具调用轮数，防止无限循环。

        Returns
        -------
        str
            AI 回复内容。
        """
        for _ in range(max_tool_rounds):
            response = self._non_streaming_tool_round(messages)
            message = response.choices[0].message

            # 没有工具调用 → 直接返回回复
            if not message.tool_calls:
                return message.content or ""

            # 有工具调用 → 追加 assistant 消息
            messages.append(message)

            # 按序执行所有工具调用
            for tool_call in message.tool_calls:
                result = self._execute_tool_call(tool_call)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

        # 达到最大轮数后获取最终回复
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            extra_body={"thinking": {"type": "disabled"}},
        )
        return response.choices[0].message.content or ""

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        max_tool_rounds: int = 5,
    ) -> Generator[str, None, None]:
        """
        流式对话，逐 chunk yield 文本。

        Function Calling 在后台处理（非流式判断工具调用），
        仅在无工具调用时输出流式文本。

        Parameters
        ----------
        messages : list[dict]
            消息列表。
        max_tool_rounds : int
            最大工具调用轮数。

        Yields
        ------
        str
            文本 chunk。
        """
        for _ in range(max_tool_rounds):
            # 先做一次非流式调用判断是否有工具调用
            response = self._non_streaming_tool_round(messages)
            message = response.choices[0].message

            if not message.tool_calls:
                # 无工具调用 → 流式输出最终回答
                stream = self._streaming_round(messages)
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return

            # 有工具调用 → 执行并通知用户
            messages.append(message)
            for tool_call in message.tool_calls:
                result = self._execute_tool_call(tool_call)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
                yield f"\n[执行 {tool_call.function.name}]\n"

        # 达到最大轮数后输出最终回答
        stream = self._streaming_round(messages)
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
