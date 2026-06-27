#!/usr/bin/env python3
"""
将文件中每对 begin/end 标志之间的内容替换为 stdin 输入的文本。

从左向右扫描，为每个 begin 匹配其后紧邻的 end，执行替换。
未配对的 begin 或 end 保持原样。

用法::

    cat new_content.txt | python scripts/replace.py target.py \\
        -b "### begin" -e "### end"

    echo "NEW" | python scripts/replace.py template.html \\
        -b "<begin>" -e "<end>"
"""

from __future__ import annotations

import json
import sys

import typer

app = typer.Typer(
    name="replace",
    help="将每对 begin/end 之间的内容替换为 stdin 输入的文本",
    no_args_is_help=True,
)


@app.command()
def replace(
    file: str = typer.Argument(..., help="要修改的文件路径"),
    begin: str = typer.Option(
        "### begin", "--begin", "-b",
        help="开头标志（该标志本身保留）",
    ),
    end: str = typer.Option(
        "### end", "--end", "-e",
        help="结尾标志（该标志本身保留）",
    ),
):
    """从左向右扫描，为每个 begin 匹配其后的第一个 end，替换中间内容。

    未配对的 begin 或 end 保持原样。支持行级标志（如 # graph begin）
    和行内标志（如 <begin> / <end>）。
    """
    new_content = sys.stdin.read()

    with open(file, encoding="utf-8") as f:
        original = f.read()

    parts: list[str] = []
    cursor = 0
    replaced = 0

    while True:
        begin_idx = original.find(begin, cursor)
        if begin_idx == -1:
            # 没有更多 begin，追加剩余内容
            parts.append(original[cursor:])
            break

        marker_begin_end = begin_idx + len(begin)
        end_idx = original.find(end, marker_begin_end)

        if end_idx == -1:
            # begin 无配对 end，保持原样，追加剩余全部
            parts.append(original[cursor:])
            break

        # 保留 begin 之前的内容 + begin 标志
        parts.append(original[cursor:marker_begin_end])
        # 插入新内容
        parts.append(new_content)
        # 保留 end 标志
        parts.append(original[end_idx:end_idx + len(end)])
        # 跳过 end 标志
        cursor = end_idx + len(end)
        replaced += 1

    result = "".join(parts)

    with open(file, "w", encoding="utf-8") as f:
        f.write(result)

    typer.echo(json.dumps({
        "file": file,
        "replaced": replaced,
        "begin": begin,
        "end": end,
    }, ensure_ascii=False))


if __name__ == "__main__":
    app()
