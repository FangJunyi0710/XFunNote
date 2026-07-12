#!/usr/bin/env python3
"""
XFunNote CLI — 命令行接口

所有 CRUD 命令参数均为 JSON 格式，输出统一为 JSON。
设计目的：为后续 FastAPI 后端接口预演，而非日常使用。

命令列表::

    xfun list                              → 列出笔记本名称
    xfun schema    NOTE_TYPE                → 查看字段结构
    xfun query     NOTE_TYPE VIEW_JSON      → 通用查询
    xfun add       NOTE_TYPE ENTRIES_JSON   → 通用添加
    xfun update    NOTE_TYPE FILTER_JSON VALUES_JSON  → 通用更新
    xfun delete    NOTE_TYPE FILTER_JSON    → 通用删除
    xfun ai        --messages JSON          → AI 对话（同步，输出新消息 JSON）
    xfun init                               → 初始化数据库
    xfun backup                             → 在线热备份数据库
    xfun reset               [--no-backup]  → 重置数据库
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import json
import traceback

import typer
from typer import Abort, Argument, Option

from xfun import db, init_db, registry
from xfun.ai.agent import (
    StreamLevel,
    accumulate_messages,
    agent_invoke,
    ensure_system_message,
    extract_content_parts,
    messages_to_json,
    parse_messages_json,
)
from xfun.ai.prompts import SYSTEM_PROMPT
from langchain_core.messages import AIMessageChunk, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from xfun.ai.tools import make_tools
from xfun.core.view import root_permission as _root_permission
from xfun.core.filter import parse_filter_json
from xfun.core.ops import add as ops_add
from xfun.core.ops import delete as ops_delete
from xfun.core.ops import query as ops_query
from xfun.core.ops import update as ops_update
from xfun.core.view import parse_view_json, root_permission

app = typer.Typer(no_args_is_help=True)
ai_app = typer.Typer(no_args_is_help=True)


# ════════════════════════════════════════════════════════════
#  内部辅助
# ════════════════════════════════════════════════════════════


def _error(msg: str) -> str:
    return json.dumps({"error": msg}, ensure_ascii=False)


def _validate_notetype(notetype: str) -> None:
    """校验笔记本类型是否存在，不存在则输出 JSON 错误并退出。"""
    if notetype not in registry:
        names = list(registry.keys())
        typer.echo(_error(f"未知笔记本类型: {notetype}, 可用: {names}"))
        raise typer.Exit(code=1)


@contextmanager
def _cli_handle():
    """统一捕获异常，输出 JSON 错误并退出。"""
    try:
        yield
    except Exception as e:
        traceback.print_exc()
        typer.echo(_error(str(e)))
        raise typer.Exit(code=1)


# ════════════════════════════════════════════════════════════
#  命令：list — 列出笔记本名称
# ════════════════════════════════════════════════════════════


_AI_TOOLS = make_tools(
    ["query_entries", "add_entries", "update_entries", "delete_entries", "get_ai_permission"],
    _root_permission(db),
)


@app.command("list")
def list_():
    """列出所有笔记本名称（list[str]）。"""
    typer.echo(json.dumps(list(registry.keys()), ensure_ascii=False))


# ════════════════════════════════════════════════════════════
#  命令：schema — 查看字段结构
# ════════════════════════════════════════════════════════════


@app.command()
def schema(notetype: str = Argument(help="笔记本类型")):
    """查看笔记本的字段结构。"""
    _validate_notetype(notetype)
    cols = [asdict(c) for c in registry[notetype].columns]
    typer.echo(json.dumps(cols, ensure_ascii=False, indent=2))


# ════════════════════════════════════════════════════════════
#  命令：query — 通用查询
# ════════════════════════════════════════════════════════════


@app.command()
def query(
    notetype: str = Argument(help="笔记本类型"),
    view_json: str = Argument(help="查询视图 JSON"),
    order_by: str = Option("", "--order-by", help="排序字段（如 created_at DESC）"),
    limit: int = Option(-1, "--limit", "-l", help="最大返回条数"),
    offset: int = Option(0, "--offset", "-o", help="偏移量"),
):
    """通用查询。返回匹配的条目列表。"""
    _validate_notetype(notetype)
    with _cli_handle():
        view = parse_view_json(json.loads(view_json))
        perm = root_permission(db)
        with db.read_transaction() as conn:
            results = ops_query(
                conn, perm, notetype, view,
                order_by=order_by, limit=limit, offset=offset,
            )
        typer.echo(json.dumps(results, ensure_ascii=False, default=str))


# ════════════════════════════════════════════════════════════
#  命令：add — 通用添加
# ════════════════════════════════════════════════════════════


@app.command()
def add(
    notetype: str = Argument(help="笔记本类型"),
    entries_json: str = Argument(help="条目列表 JSON"),
):
    """通用添加。返回新增条目的完整信息。"""
    _validate_notetype(notetype)
    with _cli_handle():
        entries = json.loads(entries_json)
        perm = root_permission(db)
        with db.transaction() as conn:
            results = ops_add(conn, perm, notetype, entries)
        typer.echo(json.dumps(results, ensure_ascii=False, default=str))


# ════════════════════════════════════════════════════════════
#  命令：update — 通用更新
# ════════════════════════════════════════════════════════════


@app.command()
def update(
    notetype: str = Argument(help="笔记本类型"),
    filter_json: str = Argument(help="筛选条件 JSON"),
    values_json: str = Argument(help="更新值 JSON"),
):
    """通用更新。返回更新后条目的完整信息。"""
    _validate_notetype(notetype)
    with _cli_handle():
        flt = parse_filter_json(json.loads(filter_json))
        values = json.loads(values_json)
        perm = root_permission(db)
        with db.transaction() as conn:
            results = ops_update(conn, perm, notetype, flt, values)
        typer.echo(json.dumps(results, ensure_ascii=False, default=str))


# ════════════════════════════════════════════════════════════
#  命令：delete — 通用删除
# ════════════════════════════════════════════════════════════


@app.command()
def delete(
    notetype: str = Argument(help="笔记本类型"),
    filter_json: str = Argument(help="筛选条件 JSON"),
):
    """通用删除。返回被删除条目的完整信息。"""
    _validate_notetype(notetype)
    with _cli_handle():
        flt = parse_filter_json(json.loads(filter_json))
        perm = root_permission(db)
        with db.transaction() as conn:
            results = ops_delete(conn, perm, notetype, flt)
        typer.echo(json.dumps(results, ensure_ascii=False, default=str))


# ════════════════════════════════════════════════════════════
#  命令：ai — AI 对话命令组
# ════════════════════════════════════════════════════════════


@dataclass
class AIConfig:
    """AI 命令组共享参数。"""
    messages_json: str | None = None
    max_iterations: int = 10
    system_prompt: str | None = None
    llm_kwargs_json: str | None = None


def _load_system_prompt(custom: str | None) -> str:
    """返回用户自定义系统提示词或默认提示词。"""
    if custom:
        return custom
    return SYSTEM_PROMPT


def _build_llm_kwargs(cfg: AIConfig) -> dict:
    """从 AIConfig 的 llm_kwargs_json 字段解析 LLM 关键字参数。"""
    extra = json.loads(cfg.llm_kwargs_json)
    if not isinstance(extra, dict):
        raise ValueError("--llm-kwargs 必须是 JSON 对象")
    return extra


def _echo_token(chunk: AIMessageChunk) -> None:
    """
    流式输出单个 AIMessageChunk，将 thinking 内容以灰色输出到 stderr。
    """
    parts = extract_content_parts(chunk)
    if "thinking" in parts.keys():
        typer.echo(f"\033[2m{parts['thinking']}\033[0m", err=True, nl=False)
    if "text" in parts.keys():
        typer.echo(parts["text"], nl=False, err=True)

def _read_multiline_input() -> str:
    """读取用户输入，支持 \\ 续行。如果某行不以 \\ 结尾，表示输入结束。"""
    l = typer.prompt("\n>>> ", prompt_suffix="", err=True)
    lines = [l]
    while l.endswith("\\"):
        lines[-1] = lines[-1][:-1]
        l = typer.prompt("..> ", prompt_suffix="", err=True)
        lines.append(l)
    return "\n".join(lines)

_DEFAULT_LLM_KWARGS = {"thinking": {"type": "disabled"}, "timeout": 30.0, "max_retries": 2}
@ai_app.callback()
def ai(
    ctx: typer.Context,
    messages_json: str | None = Option(None, "--messages", "-m", help="消息历史 JSON 数组"),
    max_iterations: int = Option(10, "--max-iterations", "-n", help="最大迭代轮次"),
    system_prompt: str | None = Option(None, "--system-prompt", "--sp", help="自定义系统提示词，留空使用默认"),
    llm_kwargs_json: str | None = Option(json.dumps(_DEFAULT_LLM_KWARGS, ensure_ascii=False), "--llm-kwargs", help="LLM 参数 JSON 字典。"),
):
    """AI 对话系列命令。所有子命令最终 stdout 输出完整消息列表 JSON。"""
    ctx.obj = AIConfig(
        messages_json=messages_json,
        max_iterations=max_iterations,
        system_prompt=system_prompt,
        llm_kwargs_json=llm_kwargs_json,
    )


@ai_app.command("sync")
def ai_sync(ctx: typer.Context):
    """同步模式：静默调用 LLM，仅 stdout 输出完整消息列表 JSON。"""
    cfg: AIConfig = ctx.obj
    if cfg.messages_json is None:
        typer.echo("sync 模式必须提供 --messages", err=True)
        raise typer.Exit(code=1)
    with _cli_handle():
        system_prompt_text = _load_system_prompt(cfg.system_prompt)
        messages = parse_messages_json(json.loads(cfg.messages_json))
        ensure_system_message(messages, system_prompt_text)
        gen = agent_invoke(
            messages, tools=_AI_TOOLS,
            stream_level=StreamLevel.SYNC,
            max_iterations=cfg.max_iterations,
            **_build_llm_kwargs(cfg),
        )
        new_messages: list[BaseMessage] = []
        for msg in gen:
            accumulate_messages(new_messages, msg)
        typer.echo(json.dumps(messages_to_json(messages + new_messages), ensure_ascii=False))


@ai_app.command("chat")
def ai_chat(ctx: typer.Context):
    """交互模式：stderr 流式输出（含思考内容），退出后 stdout JSON。"""
    cfg: AIConfig = ctx.obj
    with _cli_handle():
        system_prompt_text = _load_system_prompt(cfg.system_prompt)
        messages: list = []
        if cfg.messages_json:
            messages = parse_messages_json(json.loads(cfg.messages_json))
        ensure_system_message(messages, system_prompt_text)

        try:
            while True:
                try:
                    messages.append(HumanMessage(content=_read_multiline_input()))
                except (EOFError, KeyboardInterrupt, Abort):
                    break
                gen = agent_invoke(
                    messages, tools=_AI_TOOLS,
                    stream_level=StreamLevel.TOKEN,
                    max_iterations=cfg.max_iterations,
                    **_build_llm_kwargs(cfg),
                )
                extension: list[BaseMessage] = []
                try:
                    for yielded in gen:
                        accumulate_messages(extension, yielded)
                        if isinstance(yielded, AIMessageChunk):
                            _echo_token(yielded)
                        elif isinstance(yielded, ToolMessage):
                            typer.echo(f"\n{yielded.name}: {json.dumps(yielded.additional_kwargs.get("args",""), ensure_ascii=False, default=str)}\n{yielded.content}\n", err=True)
                except KeyboardInterrupt:
                    gen.close()
                except Exception as e:
                    typer.echo(json.dumps(_error(str(e)), ensure_ascii=False), err=True)

                accumulate_messages(extension, None)
                messages.extend(extension)
                typer.echo(err=True)
        finally:
            # 退出后 stdout JSON
            typer.echo(json.dumps(messages_to_json(messages), ensure_ascii=False))


app.add_typer(ai_app, name="ai")

# ════════════════════════════════════════════════════════════
#  命令：init — 初始化数据库
# ════════════════════════════════════════════════════════════


@app.command()
def init():
    """初始化数据库（建表 / 同步列 / 建索引）。"""
    with _cli_handle():
        with db.transaction() as conn:
            init_db(conn)
            typer.echo(json.dumps({"message": "数据库初始化完成"}, ensure_ascii=False))


# ════════════════════════════════════════════════════════════
#  命令：backup — 备份数据库
# ════════════════════════════════════════════════════════════


@app.command()
def backup():
    """在线热备份数据库。"""
    with _cli_handle():
        with db.read_transaction() as conn:
            path = db.backup(conn)
            typer.echo(json.dumps({"message": f"备份完成: {path}"}, ensure_ascii=False))


# ════════════════════════════════════════════════════════════
#  命令：reset — 重置数据库
# ════════════════════════════════════════════════════════════


@app.command()
def reset(
    no_backup: bool = Option(False, "--no-backup", help="重置前不备份"),
):
    """重置数据库（清空所有表并重新初始化）。"""
    with _cli_handle():
        with db.read_transaction() as conn:
            if not no_backup:
                path = db.backup(conn)
                typer.echo(json.dumps({"backup": path}, ensure_ascii=False))
            db.reset(conn)
            typer.echo(json.dumps({"message": "数据库已重置"}, ensure_ascii=False))


# ════════════════════════════════════════════════════════════
#  入口
# ════════════════════════════════════════════════════════════


def main():
    app()


if __name__ == "__main__":
    main()
