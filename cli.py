#!/usr/bin/env python3
# cli.py
import sys
import typer
from xfun import db,registry

app = typer.Typer()

@app.command()
def init():
	db.init()
	# ...
	# 其他初始化操作

@app.command()
def add(notename:str,entry:object):
	# 向指定的某本子添加条目
	registry.notebook(notename).add(entry)


if __name__ == "__main__":
	app()