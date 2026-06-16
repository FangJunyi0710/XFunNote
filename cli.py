#!/usr/bin/env python3
# cli.py
import sys
import typer
from xfun import db,registry
import json

app = typer.Typer()

@app.command()
def init():
	db.init()
	# ...
	# 其他初始化操作

@app.command()
def add(notename:str,entry:str):
	# 向指定的某本子添加条目
	registry.notebook(notename).add(json.loads(entry))


if __name__ == "__main__":
	app()