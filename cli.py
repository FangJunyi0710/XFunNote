#!/usr/bin/env python3
# cli.py
import shutil
import typer
from xfun import db,registry
import json
from dataclasses import asdict
from pathlib import Path

app = typer.Typer(no_args_is_help=True)


def _parse_json_to_list(s: str):
	"""解析 JSON 字符串，返回列表。若为单个 JSON 值则包装成单元素列表。"""
	data = json.loads(s)
	return data if isinstance(data, list) else [data]

@app.command()
def init():
	db.init(registry)
	# ...
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
		ids = nb.add(conn, _parse_json_to_list(entry))
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
		results = nb.get_by_id(conn, _parse_json_to_list(entry_ids))
	typer.echo(json.dumps(results, ensure_ascii=False, indent=4))

@app.command()
def delete(notename: str, entry_ids: str):
	"""批量删除条目。entry_ids 为 JSON 字符串，如 '["id1", "id2"]'。"""
	nb = registry.notebook(notename)
	ids = _parse_json_to_list(entry_ids)
	with db.transaction() as conn:
		nb.delete(conn, ids)


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

./cli.py listid plan --filter month=2606,done=0

./cli.py delete plan '["plan-2607-001", "plan-2607-002"]'

./cli.py update plan plan-2607-001 plan-2607-005 --set done=1

'''
