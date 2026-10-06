#!/usr/bin/env python3
"""
XFunNote CLI — 命令行接口

所有 CRUD 命令参数均为 JSON 格式，输出统一为 JSON。
设计目的：为后续 FastAPI 后端接口预演，而非日常使用。

"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
import json
from pathlib import Path
import traceback

import typer
from typer import Argument, Option

from xfun import init_db, registry
from xfun.core.db import DB
from xfun.core.filter import parse_filter_json
from xfun.core.ops import add as ops_add
from xfun.core.ops import delete as ops_delete
from xfun.core.ops import query as ops_query
from xfun.core.ops import update as ops_update
from xfun.core.view import full_view, no_view, parse_view_json, root_permission, view_to_json
from xfun.system_tables import SYSTEM_TABLES
from xfun.utils.file_utils import get_db_path

app = typer.Typer(no_args_is_help=True)

db: DB

@app.callback()
def main_callback(
    user: str = Option("--user", "-u", help="用户名")
):
    """
    XFunNote 命令行接口 — 轻量级无模式笔记系统。

    所有 CRUD 命令参数均为 JSON 格式，输出统一为 JSON。
    系统表可直接通过 query/add/update/delete 操作。
    """
    if not user:
        typer.echo("必须指定用户名", err = True)
        typer.Exit(code=1)

    global db
    db = DB(get_db_path(user))
    init_db(db)


# ════════════════════════════════════════════════════════════
#  内部辅助
# ════════════════════════════════════════════════════════════


_SYSTEM_TABLES = SYSTEM_TABLES.keys()


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
        db.init()
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
