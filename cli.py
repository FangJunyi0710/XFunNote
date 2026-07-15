#!/usr/bin/env python3
"""
XFunNote CLI — 命令行接口

所有 CRUD 命令参数均为 JSON 格式，输出统一为 JSON。
设计目的：为后续 FastAPI 后端接口预演，而非日常使用。

命令列表::

    xfun list                    [--all]    → 列出笔记本名称（--all 含系统表）
    xfun schema    TABLE                    → 查看字段结构（系统表亦可）
    xfun query     TABLE VIEW_JSON          → 通用查询（系统表亦可）
    xfun add       TABLE ENTRIES_JSON       → 通用添加（系统表亦可）
    xfun update    TABLE FILTER_JSON V_JSON → 通用更新（系统表亦可）
    xfun delete    TABLE FILTER_JSON        → 通用删除（系统表亦可）
    xfun ai sync   --messages JSON [--tool-names] [--permission-name]
    xfun ai chat                          [--tool-names] [--permission-name]
    xfun init                               → 初始化数据库
    xfun backup                             → 在线热备份数据库
    xfun restore  BACKUP_PATH [--list] [--no-backup]  → 从备份恢复数据库
    xfun reset               [--no-backup]  → 重置数据库

系统表 (可通过 list --all 查看): _token, _permission, _view, _filter
Token/Permission/View/Filter 管理直接复用 query / add / update / delete 命令
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import json
from pathlib import Path
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
from langchain_core.messages import AIMessageChunk, BaseMessage, HumanMessage, ToolMessage
from xfun.ai.tools import DEFAULT_TOOL_NAMES, make_tools
from xfun.core.filter import Condition, parse_filter_json
from xfun.core.ops import add as ops_add
from xfun.core.ops import delete as ops_delete
from xfun.core.ops import query as ops_query
from xfun.core.ops import update as ops_update
from xfun.core.view import full_view, no_view, parse_view_json, root_permission, view_to_json

app = typer.Typer(no_args_is_help=True)
ai_app = typer.Typer(no_args_is_help=True)


@app.callback()
def main_callback():
    """
    XFunNote 命令行接口 — 轻量级无模式笔记系统。

    所有 CRUD 命令参数均为 JSON 格式，输出统一为 JSON。
    系统表 (_token, _permission, _view, _filter) 可直接通过 query/add/update/delete 操作。
    """
    pass


# ════════════════════════════════════════════════════════════
#  内部辅助
# ════════════════════════════════════════════════════════════


_SYSTEM_TABLES = {"_token", "_permission", "_view", "_filter"}


def _error(msg: str) -> str:
    return json.dumps({"error": msg}, ensure_ascii=False)


def _validate_table(table: str) -> None:
    """校验表名是否存在。"""
    if table in registry or table in _SYSTEM_TABLES:
        return
    names = list(registry.keys()) + sorted(_SYSTEM_TABLES)
    typer.echo(_error(f"未知表: {table}, 可用: {names}"))
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


@app.command("list")
def list_(
    show_all: bool = Option(False, "--all", "-a", help="包含系统表"),
):
    """列出所有笔记本名称（list[str]），--all 包含系统表。"""
    names = list(registry.keys())
    if show_all:
        names += sorted(_SYSTEM_TABLES)
    typer.echo(json.dumps(names, ensure_ascii=False))


# ════════════════════════════════════════════════════════════
#  命令：schema — 查看字段结构
# ════════════════════════════════════════════════════════════


@app.command()
def schema(table: str = Argument(help="表名")):
    """查看表字段结构。"""
    _validate_table(table)
    if table in registry:
        cols = [asdict(c) for c in registry[table].columns]
    else:
        cols = [asdict(c) for c in db.table_infos[table]]
    typer.echo(json.dumps(cols, ensure_ascii=False))


# ════════════════════════════════════════════════════════════
#  命令：query — 通用查询
# ════════════════════════════════════════════════════════════


@app.command()
def query(
    table: str = Argument(help="表名"),
    view_json: str = Argument(help="查询视图 JSON"),
    order_by: str = Option("", "--order-by", help="排序字段（如 created_at DESC）"),
    limit: int = Option(-1, "--limit", "-l", help="最大返回条数"),
    offset: int = Option(0, "--offset", "-o", help="偏移量"),
):
    """通用查询。返回匹配的条目列表。"""
    _validate_table(table)
    with _cli_handle():
        view = parse_view_json(json.loads(view_json))
        perm = root_permission(db)
        with db.read_transaction() as conn:
            results = ops_query(
                conn, perm, table, view,
                order_by=order_by, limit=limit, offset=offset,
            )
        typer.echo(json.dumps(results, ensure_ascii=False, default=str))


# ════════════════════════════════════════════════════════════
#  命令：add — 通用添加
# ════════════════════════════════════════════════════════════


@app.command()
def add(
    table: str = Argument(help="表名"),
    entries_json: str = Argument(help="条目列表 JSON"),
):
    """通用添加。返回新增条目的完整信息。"""
    _validate_table(table)
    with _cli_handle():
        entries = json.loads(entries_json)
        perm = root_permission(db)
        with db.transaction() as conn:
            results = ops_add(conn, perm, table, entries)
        typer.echo(json.dumps(results, ensure_ascii=False, default=str))


# ════════════════════════════════════════════════════════════
#  命令：update — 通用更新
# ════════════════════════════════════════════════════════════


@app.command()
def update(
    table: str = Argument(help="表名"),
    filter_json: str = Argument(help="筛选条件 JSON"),
    values_json: str = Argument(help="更新值 JSON"),
):
    """通用更新。返回更新后条目的完整信息。"""
    _validate_table(table)
    with _cli_handle():
        flt = parse_filter_json(json.loads(filter_json))
        values = json.loads(values_json)
        perm = root_permission(db)
        with db.transaction() as conn:
            results = ops_update(conn, perm, table, flt, values)
        typer.echo(json.dumps(results, ensure_ascii=False, default=str))


# ════════════════════════════════════════════════════════════
#  命令：delete — 通用删除
# ════════════════════════════════════════════════════════════


@app.command()
def delete(
    table: str = Argument(help="表名"),
    filter_json: str = Argument(help="筛选条件 JSON"),
):
    """通用删除。返回被删除条目的完整信息。"""
    _validate_table(table)
    with _cli_handle():
        flt = parse_filter_json(json.loads(filter_json))
        perm = root_permission(db)
        with db.transaction() as conn:
            results = ops_delete(conn, perm, table, flt)
        typer.echo(json.dumps(results, ensure_ascii=False, default=str))


# ════════════════════════════════════════════════════════════
#  内部辅助：_lookup_permission — 查询权限定义
# ════════════════════════════════════════════════════════════


def _lookup_permission(permission_name: str):
    """从 _permission 表查询权限定义，返回 DB_Permission。"""
    with db.read_transaction() as conn:
        results = ops_query(conn, root_permission(db), "_permission", full_view(db),
                            Condition("id", permission_name, "="), limit=1)
    if not results:
        typer.echo(_error(f"未知权限: {permission_name!r}"))
        raise typer.Exit(code=1)
    row = results[0]
    read_view = parse_view_json(json.loads(row["read_view"]))
    write_view = parse_view_json(json.loads(row["write_view"]))
    return (read_view, write_view)


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
    tool_names_json: str | None = None
    permission_name: str = "ai"

    def make_tools(self):
        """根据 tool_names_json 和 permission_name 动态构建工具列表。"""
        return make_tools(
            json.loads(self.tool_names_json) if self.tool_names_json else DEFAULT_TOOL_NAMES,
            _lookup_permission(self.permission_name),
        )


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
    流式输出单个 AIMessageChunk，将 thinking 及其他非 text 字段以灰色输出到 stderr。
    """
    parts = extract_content_parts(chunk)
    if "thinking" in parts:
        typer.echo(f"\033[2m{parts['thinking']}\033[0m", err=True, nl=False)
    if "text" in parts:
        typer.echo(parts["text"], nl=False, err=True)
    # 其余字段统一在末尾用灰色输出
    other = {k: v for k, v in parts.items() if k not in ("thinking", "text")}
    if other:
        typer.echo(f"\033[2m{json.dumps(other, ensure_ascii=False)}\033[0m", err=True, nl=False)
    

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
    tool_names_json: str | None = Option(None, "--tool-names", "-t", help="工具名称列表 JSON 数组，如 '[\"query_entries\",\"add_entries\"]'，默认全部"),
    permission_name: str = Option("ai", "--permission-name", "-p", help="权限名称，对应 _permission 表记录"),
):
    """AI 对话系列命令。所有子命令最终 stdout 输出完整消息列表 JSON。"""
    ctx.obj = AIConfig(
        messages_json=messages_json,
        max_iterations=max_iterations,
        system_prompt=system_prompt,
        llm_kwargs_json=llm_kwargs_json,
        tool_names_json=tool_names_json,
        permission_name=permission_name,
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
        tools = cfg.make_tools()
        gen = agent_invoke(
            messages, tools=tools,
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
        tools = cfg.make_tools()

        try:
            while True:
                try:
                    messages.append(HumanMessage(content=_read_multiline_input()))
                except (EOFError, KeyboardInterrupt, Abort):
                    break
                gen = agent_invoke(
                    messages, tools=tools,
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
#  命令：view — 输出视图定义
# ════════════════════════════════════════════════════════════

view_app = typer.Typer(no_args_is_help=True, help="查看/导出视图定义")


@view_app.command("full")
def view_full():
    """输出 full_view 定义（所有表全部列 + TRUE_CONDITION）"""
    with _cli_handle():
        result = view_to_json(full_view(db))
        typer.echo(json.dumps(result, ensure_ascii=False))


@view_app.command("no")
def view_no():
    """输出 no_view 定义（所有表空列 + FALSE_CONDITION）"""
    with _cli_handle():
        result = view_to_json(no_view(db))
        typer.echo(json.dumps(result, ensure_ascii=False))


app.add_typer(view_app, name="view")

# ════════════════════════════════════════════════════════════
#  命令：init — 初始化数据库
# ════════════════════════════════════════════════════════════


@app.command()
def init():
    """初始化数据库（建表 / 同步列 / 建索引）。"""
    with _cli_handle():
        init_db()
        typer.echo(json.dumps({"message": "数据库初始化完成"}, ensure_ascii=False))


# ════════════════════════════════════════════════════════════
#  命令：backup — 备份数据库
# ════════════════════════════════════════════════════════════


@app.command()
def backup():
    """在线热备份数据库。"""
    with _cli_handle():
        path = db.backup()
        typer.echo(json.dumps({"message": f"备份完成: {path}"}, ensure_ascii=False))


# ════════════════════════════════════════════════════════════
#  命令：restore — 恢复数据库
# ════════════════════════════════════════════════════════════


@app.command()
def restore(
    backup_path: str = Argument(None, help="备份文件路径（省略时结合 --list 使用）"),
    list_backups: bool = Option(False, "--list", "-l", help="列出所有可用备份"),
    no_backup: bool = Option(False, "--no-backup", help="恢复前不备份当前数据库"),
):
    """从备份文件恢复数据库。恢复前默认先备份当前数据库。"""
    with _cli_handle():
        if list_backups:
            backup_dir = Path(db.db_path).parent / "backups"
            if not backup_dir.exists():
                typer.echo(json.dumps([], ensure_ascii=False))
                return
            files = sorted([str(f) for f in backup_dir.iterdir() if f.is_file()])
            typer.echo(json.dumps(files, ensure_ascii=False))
            return

        if not backup_path:
            typer.echo(_error("请提供备份文件路径，或使用 --list 查看可用备份"))
            raise typer.Exit(code=1)

        # 恢复前先备份当前数据库（安全网）
        if not no_backup:
            pre_path = db.backup()
            typer.echo(json.dumps({"pre_restore_backup": pre_path}, ensure_ascii=False))

        path = db.restore(backup_path)
        typer.echo(json.dumps({"message": f"已从备份恢复: {path}"}, ensure_ascii=False))


# ════════════════════════════════════════════════════════════
#  命令：reset — 重置数据库
# ════════════════════════════════════════════════════════════


@app.command()
def reset(
    no_backup: bool = Option(False, "--no-backup", help="重置前不备份"),
):
    """重置数据库（清空所有表并重新初始化）。"""
    with _cli_handle():
        if not no_backup:
            path = db.backup()
            typer.echo(json.dumps({"backup": path}, ensure_ascii=False))
        db.reset()
        typer.echo(json.dumps({"message": "数据库已重置"}, ensure_ascii=False))


# ════════════════════════════════════════════════════════════
#  入口
# ════════════════════════════════════════════════════════════


def main():
    app()


if __name__ == "__main__":
    main()
