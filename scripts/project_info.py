#!/usr/bin/env python3

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

# 类型别名
DEP_Graph = dict[str, list[str]]


# ════════════════════════════════════════════════════════════
#  颜色调色板（按拓扑排序后层序号循环分配）
# ════════════════════════════════════════════════════════════

_COLOR_PALETTE = [
    "#d4f0c0",  # light green
    "#e8f4fd",  # light blue
    "#ffe0f0",  # light pink
    "#f0e6ff",  # light purple
    "#fff3cd",  # light yellow
    "#ffe0e0",  # light red
    "#d5f5e3",  # mint
    "#fdebd0",  # peach
    "#d6eaf8",  # sky blue
    "#e8daef",  # lavender
]


# ════════════════════════════════════════════════════════════
#  项目根目录（通过 CLI --root 设置）
# ════════════════════════════════════════════════════════════

ROOT_DIR: Path | None = None

def _get_root() -> Path:
    """返回项目根目录，未设置时回退为当前工作目录。"""
    return ROOT_DIR.resolve() if ROOT_DIR else Path.cwd().resolve()


# ════════════════════════════════════════════════════════════
#  忽略规则（使用 git check-ignore 判断）
# ════════════════════════════════════════════════════════════


def _is_ignored(p: Path) -> bool:
    """判断路径是否被 .gitignore 忽略。"""
    # .git 是 Git 内部目录，不在 .gitignore 中，需显式排除
    if ".git" in p.parts:
        return True
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(p)],
            cwd=str(_get_root()),
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


# ════════════════════════════════════════════════════════════
#  模块映射（全自动：扫描所有 .py 文件，过滤 .gitignore）
# ════════════════════════════════════════════════════════════


def _module_file_map() -> dict[str, str]:
    """递归扫描项目根下所有 ``.py`` 文件，构建 ``{ 相对路径(不含.py): 绝对路径 }`` 映射。

    键为相对于项目根的路径（如 ``core/db``、``xfun/__init__``），
    不含 ``.py`` 后缀。被 ``.gitignore`` 忽略的文件/目录自动跳过。
    """
    mapping: dict[str, str] = {}
    root = _get_root()

    for p in sorted(root.rglob("*.py")):
        if _is_ignored(p):
            continue
        rel = str(p.relative_to(root).with_suffix(""))
        mapping[rel] = str(p.resolve())

    return mapping


# ════════════════════════════════════════════════════════════
#  Import 解析（通用版本，不依赖特定包名）
# ════════════════════════════════════════════════════════════


def _resolve_absolute(
    modname: str, mod_file_map: dict[str, str]
) -> str | None:
    """解析绝对模块路径（如 ``xfun.core.db``）→ 相对路径（如 ``xfun/core/db``）。

    返回 ``None`` 表示非项目内部模块（第三方库 / 标准库）。
    从最长路径片段开始尝试匹配（优先精确匹配文件，再匹配 ``__init__.py``）。
    """
    parts = modname.split(".")

    # 从最长路径开始尝试（越具体越优先）
    for i in range(len(parts), 0, -1):
        rel = "/".join(parts[:i])

        # 尝试匹配为普通文件：rel.py
        if rel in mod_file_map:
            return rel

        # 尝试匹配为包：rel/__init__.py
        init_rel = f"{rel}/__init__"
        if init_rel in mod_file_map:
            return init_rel

    return None


def _resolve_relative(
    file_path: str,
    level: int,
    module: str | None,
    names: list[str],
    mod_file_map: dict[str, str],
) -> list[str]:
    """解析相对导入 → 相对路径列表。

    ``from . import X, Y`` 和 ``from ..A.B import Z`` 都会正确处理。
    返回 ``list[str]``（兼容 Generator 场景）。
    """
    fpath = Path(file_path).resolve()
    base = fpath.parent

    # 向上跳 (level - 1) 层
    for _ in range(level - 1):
        base = base.parent

    # 确定需要查找的候选模块名
    if module is not None:
        # from .db import ...        → module="db"
        # from ..utils.time_utils import ...  → module="utils.time_utils"
        # from ..core.db import ...   → module="core.db"
        parts = module.split(".")
        # 遍历路径段（最后一段除外），进入子目录
        current = base
        for seg in parts[:-1]:
            current = current / seg
        # 在最终目录中查找最后一段
        return _try_resolve_in_dir(parts[-1], current, mod_file_map)

    # from . import extras   → names=["extras"]
    # from .. import config  → names=["config"]
    result: list[str] = []
    for name in names:
        found = _try_resolve_in_dir(name, base, mod_file_map)
        if found:
            result.extend(found)
        else:
            # 名称不是文件也不是包 → 它来自 base 的 __init__.py
            init = base / "__init__.py"
            if init.exists():
                mname = _lookup_module_name(str(init.resolve()), mod_file_map)
                if mname:
                    result.append(mname)
    return result


def _try_resolve_in_dir(
    name: str, directory: Path, mod_file_map: dict[str, str]
) -> list[str]:
    """在指定目录中查找 ``name.py`` 或 ``name/__init__.py``，返回匹配的相对路径。"""
    result: list[str] = []
    # name.py
    candidate = (directory / f"{name}.py").resolve()
    if candidate.exists():
        mname = _lookup_module_name(str(candidate), mod_file_map)
        if mname:
            result.append(mname)
            return result
    # name/__init__.py（子包）
    pkg = (directory / name / "__init__.py").resolve()
    if pkg.exists():
        mname = _lookup_module_name(str(pkg), mod_file_map)
        if mname:
            result.append(mname)
    return result


def _lookup_module_name(file_path: str, mod_file_map: dict[str, str]) -> str | None:
    """反向查找：绝对文件路径 → 相对路径键。"""
    fp = str(Path(file_path).resolve())
    for mname, fpath in mod_file_map.items():
        if fpath == fp:
            return mname
    return None


# ════════════════════════════════════════════════════════════
#  核心：扫描依赖
# ════════════════════════════════════════════════════════════


def scan_deps() -> DEP_Graph:
    """扫描项目内所有 ``.py`` 文件的所有内部 import，构建依赖图。

    返回::

        {
            "core/db":      ["config", "core/errors"],
            "core/ops":     ["core/__init__", "core/db", "core/filter", "core/view"],
            "cli":          ["core/notebook"],
            ...
        }

    键值为相对于项目根的路径（不含 ``.py``）。仅包含项目内部模块依赖。
    """
    mod_file_map = _module_file_map()
    graph: DEP_Graph = {mod: [] for mod in mod_file_map}

    for mod_name, file_path in mod_file_map.items():
        deps: set[str] = set()

        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=file_path)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = _resolve_absolute(alias.name, mod_file_map)
                    if mod:
                        deps.add(mod)

            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    # 相对导入
                    module_str = node.module
                    names = [a.name for a in node.names]
                    resolved = _resolve_relative(
                        file_path, node.level, module_str, names, mod_file_map
                    )
                    deps.update(resolved)
                else:
                    # 绝对导入：from xfun.xxx import YYY
                    if node.module:
                        mod = _resolve_absolute(node.module, mod_file_map)
                        if mod:
                            deps.add(mod)
                        # 尝试将每个 name 作为子模块解析
                        for alias in node.names:
                            full = f"{node.module}.{alias.name}"
                            sub_mod = _resolve_absolute(full, mod_file_map)
                            if sub_mod:
                                deps.add(sub_mod)

        graph[mod_name] = sorted(deps)

    return graph


# ════════════════════════════════════════════════════════════
#  层构建（全自动：按第一级目录分组 + 拓扑排序 + 颜色分配）
# ════════════════════════════════════════════════════════════


def _topo_sort_layers(layer_deps: DEP_Graph) -> list[str]:
    """对层进行拓扑排序（从底向上）。"""
    in_degree = {name: len(deps) for name, deps in layer_deps.items()}
    queue = [name for name in layer_deps if in_degree.get(name, 0) == 0]
    sorted_names: list[str] = []

    while queue:
        queue.sort()
        node = queue.pop(0)
        sorted_names.append(node)
        for name, deps in layer_deps.items():
            if node in deps:
                in_degree[name] -= 1
                if in_degree[name] == 0 and name not in sorted_names:
                    queue.append(name)

    # 补充未在拓扑排序中的层（如孤立层）
    for name in layer_deps:
        if name not in sorted_names:
            sorted_names.append(name)

    return sorted_names


def build_layers(
    graph: DEP_Graph,
) -> list[tuple[str, list[str], str]]:
    """从依赖图自动构建层定义。

    返回::

        [("core",     ["core/db", ...], "#d4f0c0"),
         ("xfun/ai",  ["xfun/ai/tools", ...], "#e8f4fd"),
         ...]

    层按模块所在目录的相对路径自动分组（顶层文件归入 ``"."``），
    顺序由拓扑排序决定，颜色从调色板循环分配。
    """
    # 按层分组（直接用所在目录的相对路径作为层名，顶层文件归入 "."）
    layer_members: DEP_Graph = {}
    for mod in graph:
        parts = mod.split("/")
        layer = "/".join(parts[:-1]) if len(parts) > 1 else "."
        layer_members.setdefault(layer, []).append(mod)

    # 构建层间依赖图
    mod_to_layer = {mod: ("/".join(mod.split("/")[:-1]) if len(mod.split("/")) > 1 else ".") for mod in graph}
    layer_deps: DEP_Graph = {name: [] for name in layer_members}
    for mod, deps in graph.items():
        src = mod_to_layer.get(mod)
        if not src:
            continue
        for dep in deps:
            dst = mod_to_layer.get(dep)
            if dst and dst != src and dst not in layer_deps[src]:
                layer_deps[src].append(dst)

    # 拓扑排序
    sorted_layers = _topo_sort_layers(layer_deps)

    # 按排序顺序分配颜色
    result: list[tuple[str, list[str], str]] = []
    for i, name in enumerate(sorted_layers):
        members = sorted(layer_members[name])
        color = _COLOR_PALETTE[i % len(_COLOR_PALETTE)]
        result.append((name, members, color))

    return result


# ════════════════════════════════════════════════════════════
#  循环依赖检测
# ════════════════════════════════════════════════════════════


def find_cycles(graph: DEP_Graph) -> list[list[str]]:
    """检测所有循环依赖，返回所有环 (Tarjan-like DFS)。"""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {m: WHITE for m in graph}
    cycles: list[list[str]] = []
    stack: list[str] = []

    def dfs(node: str):
        color[node] = GRAY
        stack.append(node)
        for dep in graph.get(node, []):
            if dep not in color:
                continue
            if color[dep] == GRAY:
                idx = stack.index(dep)
                cycles.append(stack[idx:] + [dep])
            elif color[dep] == WHITE:
                dfs(dep)
        stack.pop()
        color[node] = BLACK

    for node in graph:
        if color[node] == WHITE:
            dfs(node)

    return cycles


# ════════════════════════════════════════════════════════════
#  Mermaid 流程图（分层）
# ════════════════════════════════════════════════════════════


def _safe_id(name: str) -> str:
    """将路径转安全的 Mermaid/DOT 节点 ID（替换 ``/``、``.`` 为 ``_``）。"""
    return name.replace("/", "_").replace(".", "_")


def to_mermaid(
    graph: DEP_Graph | None = None,
    layers: list[tuple[str, list[str], str]] | None = None,
    direction: str = "LR",
    show_full_path: bool = False,
) -> str:
    """渲染为带层分组的 Mermaid 流程图。

    参数
    ----
    graph : dict | None
        依赖图。为 ``None`` 时自动调用 ``scan_deps()``。
    layers : list | None
        层定义。为 ``None`` 时自动从 ``graph`` 构建。
    direction : str
        图方向，默认 ``"LR"`` (Left→Right)。
        可选 ``"TD"`` (Top→Down) 适合垂直展示。
    show_full_path : bool
        若为 ``True``，层名显示为 ``{根目录}/core`` 等完整路径；
        否则仅显示相对路径（如 ``core``）。
    """
    if graph is None:
        graph = scan_deps()
    if layers is None:
        layers = build_layers(graph)

    root = _get_root()
    lines = [f"graph {direction}"]

    # subgraph 分组
    for name, members, color in layers:
        display_name = str(root / name) if show_full_path else name
        safe_name = _safe_id(name)
        lines.append(f"    subgraph {safe_name}[{display_name}]")
        for mod in members:
            if mod in graph:
                label = Path(mod).name  # basename
                lines.append(f"        {_safe_id(mod)}({label})")
        lines.append("    end")
        lines.append(
            f"    style {safe_name} fill:{color},stroke:#333,stroke-width:1px,color:#333"
        )

    # 边
    for mod, deps in graph.items():
        for dep in deps:
            lines.append(f"    {_safe_id(mod)} --> {_safe_id(dep)}")

    return "```mermaid\n" + "\n".join(lines) + "\n```"


# ════════════════════════════════════════════════════════════
#  项目目录树（根据 .gitignore 过滤）
# ════════════════════════════════════════════════════════════


def to_tree() -> str:
    """输出项目目录树，依据 ``.gitignore`` 规则过滤被忽略的文件/目录。"""
    root = _get_root()
    lines: list[str] = [f"{root.name}/"]

    def _walk(dir_path: Path, prefix: str = "") -> None:
        items = sorted(
            [p for p in dir_path.iterdir() if not _is_ignored(p)],
            key=lambda p: (not p.is_dir(), p.name.lower()),
        )
        for i, item in enumerate(items):
            connector = "└── " if i == len(items) - 1 else "├── "
            display = f"{item.name}/" if item.is_dir() else item.name
            lines.append(f"{prefix}{connector}{display}")
            if item.is_dir():
                sub_prefix = "    " if i == len(items) - 1 else "│   "
                _walk(item, prefix + sub_prefix)

    _walk(root)
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
#  Typer CLI 入口
# ════════════════════════════════════════════════════════════

import typer

app = typer.Typer(no_args_is_help=True)


@app.callback()
def set_root(
    root: Path = typer.Option(
        Path.cwd(),
        "--root",
        "-r",
        help="项目根目录（默认当前目录），所有 .py 文件将基于此路径扫描",
    ),
):
    """通用 Python 项目依赖分析工具

    自动扫描项目根下所有 .py 文件（按 .gitignore 过滤），
    使用 AST 静态分析构建模块间依赖图，支持多格式输出、循环检测和目录树展示。
    """
    global ROOT_DIR
    ROOT_DIR = root.resolve()


@app.command()
def mermaid(
    direction: str = typer.Option(
        "LR",
        "--direction",
        "-d",
        help="图方向: LR (Left→Right) 或 TD (Top→Down)",
    ),
    show_full_path: bool = typer.Option(
        False,
        "--show-full-path",
        help="层名显示完整路径而非相对路径",
    ),
):
    """输出带层分组的 Mermaid 流程图"""
    graph = scan_deps()
    layers = build_layers(graph)
    print(to_mermaid(graph, layers, direction=direction, show_full_path=show_full_path))


@app.command()
def validate():
    """校验有无循环依赖"""
    graph = scan_deps()
    cycles = find_cycles(graph)
    if cycles:
        print("⚠️  发现循环依赖:")
        for c in cycles:
            print(f"  {' → '.join(Path(m).name for m in c)}")
        raise typer.Exit(code=1)
    print("✅  无循环依赖")


@app.command()
def tree():
    """输出项目目录树（依据 .gitignore 过滤）"""
    print(to_tree())


if __name__ == "__main__":
    app()
