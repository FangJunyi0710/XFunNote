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
    xfun ai        [TEXT]...               → AI 对话
    xfun config    show / set KEY VALUE     → 配置管理
    xfun init                               → 初始化数据库
"""

from __future__ import annotations

from dataclasses import asdict
import json
import os
from typing import Optional

import typer
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typer import Argument, Option

from xfun import db, registry
from xfun.ai.agent import agent_invoke
from xfun.config import DB_PATH, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from xfun.core.errors import XFunError
from xfun.core.filter import parse_filter_json
from xfun.core.ops import add as ops_add
from xfun.core.ops import delete as ops_delete
from xfun.core.ops import query as ops_query
from xfun.core.ops import update as ops_update
from xfun.core.view import parse_view_json, root_permission

app = typer.Typer(no_args_is_help=True)


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


def _msg_role(msg) -> str:
    """返回消息的 role 字符串（user / assistant / system / tool）。"""
    name = type(msg).__name__
    if "Human" in name:
        return "user"
    if "AI" in name or "AIMessage" in name:
        return "assistant"
    if "System" in name:
        return "system"
    if "Tool" in name:
        return "tool"
    return "unknown"


# ════════════════════════════════════════════════════════════
#  命令：list — 列出笔记本名称
# ════════════════════════════════════════════════════════════


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
    try:
        view = parse_view_json(view_json)
        perm = root_permission(db)
        with db.read_transaction() as conn:
            results = ops_query(
                conn, perm, notetype, view,
                order_by=order_by, limit=limit, offset=offset,
            )
        typer.echo(json.dumps(results, ensure_ascii=False, default=str))
    except Exception as e:
        typer.echo(_error(str(e)))
        raise typer.Exit(code=1)


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
    try:
        entries = json.loads(entries_json)
        perm = root_permission(db)
        with db.transaction() as conn:
            results = ops_add(conn, perm, notetype, entries)
        typer.echo(json.dumps(results, ensure_ascii=False, default=str))
    except Exception as e:
        typer.echo(_error(str(e)))
        raise typer.Exit(code=1)


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
    try:
        flt = parse_filter_json(filter_json)
        values = json.loads(values_json)
        perm = root_permission(db)
        with db.transaction() as conn:
            results = ops_update(conn, perm, notetype, flt, values)
        typer.echo(json.dumps(results, ensure_ascii=False, default=str))
    except Exception as e:
        typer.echo(_error(str(e)))
        raise typer.Exit(code=1)


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
    try:
        flt = parse_filter_json(filter_json)
        perm = root_permission(db)
        with db.transaction() as conn:
            results = ops_delete(conn, perm, notetype, flt)
        typer.echo(json.dumps(results, ensure_ascii=False, default=str))
    except Exception as e:
        typer.echo(_error(str(e)))
        raise typer.Exit(code=1)


# ════════════════════════════════════════════════════════════
#  命令：ai — AI 对话
# ════════════════════════════════════════════════════════════


@app.command()
def ai(
    text: Optional[list[str]] = Argument(
        None, help="对话文本（可多个，自动拼接为一条 HumanMessage）"
    ),
    messages_json: Optional[str] = Option(
        None,
        "--messages",
        help="消息历史 JSON 数组，格式: [{\"role\": \"user\", \"content\": \"...\"}, ...]",
    ),
    json_output: bool = Option(
        False,
        "--json",
        help="以 JSON 格式输出完整消息列表",
    ),
):
    """AI 对话。

    支持单轮 / 多轮对话。通过 [TEXT]... 传入当前提问，
    通过 --messages 传入历史消息实现持续对话。
    """
    # 解析 --messages 参数
    messages: list = []
    if messages_json:
        try:
            raw_messages = json.loads(messages_json)
        except json.JSONDecodeError:
            typer.echo(_error("messages 参数不是有效的 JSON"))
            raise typer.Exit(code=1)

        for msg in raw_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                messages.append(SystemMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))

    # 将 [TEXT]... 参数拼接为一条 HumanMessage
    if text:
        messages.append(HumanMessage(content=" ".join(text)))

    if not messages:
        typer.echo(_error("请提供文本或 --messages 参数"))
        raise typer.Exit(code=1)

    try:
        new_msgs = agent_invoke(messages)
        if json_output:
            msg_list = [
                {"role": _msg_role(m), "content": m.content}
                for m in new_msgs
            ]
            typer.echo(json.dumps(msg_list, ensure_ascii=False))
        else:
            # 输出 AI 最终回复（从后往前找第一个有 content 的消息）
            output = None
            for m in reversed(new_msgs):
                if hasattr(m, "content") and m.content:
                    output = m.content
                    break
            if output:
                typer.echo(output)
    except XFunError as e:
        typer.echo(_error(str(e)))
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(_error(str(e)))
        raise typer.Exit(code=1)


# ════════════════════════════════════════════════════════════
#  命令：config — 配置管理
# ════════════════════════════════════════════════════════════


@app.command()
def config(
    action: str = Argument(help="操作: show / set"),
    key: Optional[str] = Argument(None, help="配置键（set 时必填）"),
    value: Optional[str] = Argument(None, help="配置值（set 时必填）"),
):
    """配置管理。show：查看当前配置；set：设置配置项并写入 .env。"""
    if action == "show":
        typer.echo(
            json.dumps(
                {
                    "DB_PATH": DB_PATH,
                    "LLM_MODEL": LLM_MODEL,
                    "LLM_BASE_URL": LLM_BASE_URL,
                    "LLM_API_KEY": "***" if LLM_API_KEY else "",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif action == "set":
        if not key or value is None:
            typer.echo(_error("set 操作需要 KEY 和 VALUE"))
            raise typer.Exit(code=1)
        # 写入 .env 文件
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        with open(env_path, "a") as f:
            f.write(f"\n{key}={value}")
        # 立即生效
        os.environ[key] = value
        typer.echo(json.dumps({"message": f"{key}={value} 已设置"}, ensure_ascii=False))
    else:
        typer.echo(_error(f"未知操作: {action}, 可用: show, set"))
        raise typer.Exit(code=1)


# ════════════════════════════════════════════════════════════
#  命令：init — 初始化数据库
# ════════════════════════════════════════════════════════════


@app.command()
def init():
    """初始化数据库（建表 / 同步列 / 建索引）。"""
    try:
        # xfun/__init__.py 在 import 时已调用 db.init()，
        # 此处提供显式调用的入口
        db.init({name: nb.columns for name, nb in registry.items()})
        typer.echo(json.dumps({"message": "数据库初始化完成"}, ensure_ascii=False))
    except Exception as e:
        typer.echo(_error(str(e)))
        raise typer.Exit(code=1)


# ════════════════════════════════════════════════════════════
#  入口
# ════════════════════════════════════════════════════════════


def main():
    app()


if __name__ == "__main__":
    main()
