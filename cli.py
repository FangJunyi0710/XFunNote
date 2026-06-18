#!/usr/bin/env python3
# cli.py
import sys
import typer
from xfun import db,registry
import json

app = typer.Typer(no_args_is_help=True)

@app.command()
def init():
	db.init(registry)
	# ...
	# 其他初始化操作

@app.command()
def add(notename:str,entry:str):
	# 向指定的某本子添加条目
	nb = registry.notebook(notename)
	with db.transaction() as conn:
		nb.add(conn, json.loads(entry))


if __name__ == "__main__":
	app()

'''
测试语句：

./cli.py
./cli.py init
./cli.py add plan '{"month": "2607", "content": "测试内容"}'



./cli.py listcolumns plan
./cli.py listid plan --filter month=2606,done=0
./cli.py list plan plan-2607-001 plan-2607-005 --column id,month,content

./cli.py delete plan plan-2607-001 plan-2607-005

./cli.py update plan plan-2607-001 plan-2607-005 --set done=1



'''