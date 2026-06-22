#!/usr/bin/env python3
# cli.py
import shutil
import typer
from typing import Optional
from xfun import db,registry
from xfun.core.filter import parse_filter_json
import json
from dataclasses import asdict
from pathlib import Path

app = typer.Typer(no_args_is_help=True)


def parse_list_json(s: str):
    """解析 JSON 字符串，返回列表。若为单个 JSON 值则包装成单元素列表。"""
    data = json.loads(s)
    return data if isinstance(data, list) else [data]

@app.command()
def init():
    pass
    # 其他初始化操作

@app.command()
def reset():
    """删除 data 目录并重新创建，然后初始化数据库。"""
    data_dir = Path("data")
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir()
    init()

@app.command()
def add(notename: str, entry: str):
    nb = registry.notebook(notename)
    with db.transaction() as conn:
        ids = nb.add(conn, parse_list_json(entry))
    typer.echo(json.dumps(ids, ensure_ascii=False, indent=4))

@app.command()
def listcolumns(notename: str):
    """列出指定本子的所有列定义，以 JSON 格式输出。"""
    nb = registry.notebook(notename)
    typer.echo(json.dumps(
        [asdict(c) for c in nb.columns],
        ensure_ascii=False, indent=4))

@app.command("list")
def cmd_list(notename: str, entry_ids: str):
    nb = registry.notebook(notename)
    with db.transaction() as conn:
        results = nb.get_by_id(conn, parse_list_json(entry_ids))
    typer.echo(json.dumps(results, ensure_ascii=False, indent=4))

@app.command()
def listid(notename: str,
           filter: Optional[str] = typer.Option(None, "--filter", "-f"),
           order_by: Optional[str] = typer.Option(None, "--order-by", "-O", help="排序列名，支持逗号分隔多列及 ASC/DESC，如 'month ASC, seq'"),
           limit: int = typer.Option(-1, "--limit", "-l", help="最大返回条数，默认展示全部"),
           offset: int = typer.Option(0, "--offset", "-o", help="偏移量")):
    """按条件列出条目 ID。"""
    nb = registry.notebook(notename)
    parsed_filter = parse_filter_json(filter) if filter else []
    with db.read_transaction() as conn:
        ids = nb.list(conn, parsed_filter, order_by=order_by, limit=limit, offset=offset)
    typer.echo(json.dumps(ids, ensure_ascii=False, indent=4))

@app.command()
def delete(notename: str, entry_ids: str):
    """批量删除条目。entry_ids 为 JSON 字符串，如 '["id1", "id2"]'。"""
    nb = registry.notebook(notename)
    ids = parse_list_json(entry_ids)
    with db.transaction() as conn:
        nb.delete(conn, ids)

@app.command()
def update(notename: str, entry_ids: str, entry: str):
    """批量更新条目。entry_ids 为 ID 列表 JSON，entry 为更新字段 JSON。"""
    nb = registry.notebook(notename)
    ids = parse_list_json(entry_ids)
    entry_dict = json.loads(entry)
    with db.transaction() as conn:
        nb.update(conn, ids, entry_dict)

if __name__ == "__main__":
    app()

'''
测试语句：

./cli.py
./cli.py init
./cli.py reset

./cli.py add plan '{"month": "2607", "content": "测试内容"}'
./cli.py add plan '[{"month": "2607", "content": "条目A"}, {"month": "2607", "content": "条目B"}]'

./cli.py listcolumns plan

./cli.py list plan '"plan-2607-001"'
./cli.py list plan '["plan-2607-001", "plan-2607-002"]'

./cli.py listid plan
./cli.py listid plan --filter '{"column": "month", "value": "2607"}'
./cli.py listid plan --filter '[{"column": "month", "value": "2607"}]'
./cli.py listid plan --filter '[[{"column": "month", "value": "2607"}]]'
./cli.py listid plan --filter '[[{"column": "content", "value": "%test%", "op": "LIKE"}]]'
./cli.py listid plan --filter '[[{"column": "month", "value": "2607"}, {"column": "done", "value": 0}]]'
./cli.py listid plan --filter '[[{"column": "month", "value": "2607"}], [{"column": "month", "value": "2608"}]]'
./cli.py listid plan --filter '[[{"column": "month", "value": ["2607", "2608"], "op": "IN"}]]'
./cli.py listid plan --filter '[[{"column": "no", "value": [1, 10], "op": "BETWEEN"}]]'
./cli.py listid plan --order-by 'month ASC, seq DESC'
./cli.py listid plan --filter '{"column": "month", "value": "2607"}' --order-by 'no' --limit 5

./cli.py delete plan '["plan-2607-001", "plan-2607-002"]'

./cli.py update plan '["plan-2607-001","plan-2607-005"]' '{"done": 1}'

'''
