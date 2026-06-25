#!/usr/bin/env python3

from __future__ import annotations

import ast
import subprocess
from collections.abc import Generator
from pathlib import Path


# ════════════════════════════════════════════════════════════
#  项目路径
# ════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent.parent
XFUN_DIR = PROJECT_ROOT / "xfun"
CLI_FILE = PROJECT_ROOT / "cli.py"

# 颜色调色板（按拓扑排序后层序号循环分配）
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
#  目录树自动发现（替代手工 LAYER_CONFIG / SUBPACKAGE_DIRS）
# ════════════════════════════════════════════════════════════


def _discover_dirs() -> list[tuple[str, Path]]:
    """扫描项目目录树，自动发现层名与扫描目录。

    返回 ``[(层名, 目录路径), ...]``，按发现顺序排列。

    发现规则::

        xfun/<subdir>/    → 层名 = 子目录名（如 core, ai, notebooks, utils）
        xfun/             → 层名 = "xfun"（存放顶层 *.py）
        <root>/<dir>/     → 层名 = 目录名（如 backend, frontend）
        <root>/cli.py     → 层名 = "root"
    """
    layers: list[tuple[str, Path]] = []

    # ── xfun 下的直接子目录 ──
    for item in sorted(XFUN_DIR.iterdir()):
        if item.is_dir() and not item.name.startswith("_") and not item.name.startswith("."):
            layers.append((item.name, item))

    # ── xfun 顶层包 ──
    layers.append(("xfun", XFUN_DIR))

    # ── 项目根的额外子目录（过滤系统/数据目录） ──
    _EXCLUDED_DIRS = {"xfun", "data", "input", "output", "tests", "scripts", "__pycache__"}
    for item in sorted(PROJECT_ROOT.iterdir()):
        if item.is_dir() and item.name not in _EXCLUDED_DIRS and not item.name.startswith("."):
            layers.append((item.name, item))

    # ── cli.py ──
    if CLI_FILE.exists():
        layers.append(("root", PROJECT_ROOT))

    return layers


# ════════════════════════════════════════════════════════════
#  模块映射（完全从目录树推导）
# ════════════════════════════════════════════════════════════


def _module_file_map() -> dict[str, str]:
    """自动扫描目录树，构建 ``{ 短模块名: 绝对文件路径 }`` 映射。

    映射规则::

        xfun/core/db.py           → "db"
        xfun/__init__.py          → "__init__"
        xfun/config.py            → "config"
        cli.py                   → "cli"
        backend/main.py           → "main"

    注意: 子包的 ``__init__.py`` (如 ``core/__init__.py``) 不纳入映射，
    因为其名称与 Mermaid subgraph 名冲突，且内容为空无实际依赖。
    """
    mapping: dict[str, str] = {}

    for layer_name, layer_dir in _discover_dirs():
        if layer_name == "root":
            # 根层：扫描该项目根下的 .py（通常只有 cli.py）
            for f in sorted(layer_dir.glob("*.py")):
                mapping[f.stem] = str(f.resolve())
        elif layer_name == "xfun":
            # xfun 顶层 *.py（含 __init__.py）
            for f in sorted(layer_dir.glob("*.py")):
                mapping[f.stem] = str(f.resolve())
        else:
            # 子包目录：跳过 __init__.py（避免与 subgraph 名冲突），
            # 只映射具体的模块文件
            for f in sorted(layer_dir.glob("*.py")):
                if f.stem != "__init__":
                    mapping[f.stem] = str(f.resolve())

    return mapping


# ════════════════════════════════════════════════════════════
#  Import 解析
# ════════════════════════════════════════════════════════════


def _resolve_absolute(modname: str, mod_file_map: dict[str, str]) -> str | None:
    """解析绝对模块路径（``xfun.xxx.yyy``）→ 短模块名。

    只解析具体的 ``.py`` 文件（不含子包 ``__init__.py``，
    因其名称与 Mermaid subgraph 冲突且内容为空）。

    返回 ``None`` 表示非 xfun 内部模块（第三方库 / 标准库）。
    """
    parts = modname.split(".")
    if parts[0] != "xfun":
        return None

    # ``xfun`` 本身就是 ``__init__``
    if len(parts) == 1:
        return "__init__"

    # 尝试普通文件：xfun/core/db.py
    rel_parts = parts[1:]  # ["core", "db"]
    candidate = XFUN_DIR.joinpath(*rel_parts).with_suffix(".py")
    name = candidate.resolve().stem if candidate.exists() else None
    if name and name in mod_file_map:
        return name

    return None


def _resolve_relative(
    file_path: str,
    level: int,
    module: str | None,
    names: list[str],
    mod_file_map: dict[str, str],
) -> Generator[str, None, None]:
    """解析相对导入 → 模块名列表。

    ``from . import X, Y`` 和 ``from ..A.B import Z`` 都会正确处理。
    """
    fpath = Path(file_path).resolve()
    base = fpath.parent

    # 向上跳 (level - 1) 层
    for _ in range(level - 1):
        base = base.parent

    # 确定需要查找的候选模块名
    if module is not None:
        # from .db import ...  → module="db"
        # from ..utils.time_utils import ... → module="utils.time_utils"
        # from ..core.db import ...      → module="core.db"
        parts = module.split(".")
        # 遍历路径段（最后一段除外），进入子目录
        current = base
        for seg in parts[:-1]:
            current = current / seg
        # 在最终目录中查找最后一段
        yield from _try_resolve_in_dir(parts[-1], current, mod_file_map)
    else:
        # from . import extras  → names=["extras"]
        # from .. import config → names=["config"]
        for name in names:
            found = list(_try_resolve_in_dir(name, base, mod_file_map))
            if found:
                yield from found
            else:
                # 名称不是文件也不是包 → 它来自 base 的 __init__.py
                init = base / "__init__.py"
                if init.exists():
                    mname = _lookup_module_name(str(init.resolve()), mod_file_map)
                    if mname:
                        yield mname


def _try_resolve_in_dir(
    name: str, directory: Path, mod_file_map: dict[str, str]
) -> list[str]:
    """在指定目录中查找 ``name.py`` 或 ``name/__init__.py``。"""
    result: list[str] = []
    # name.py
    candidate = (directory / f"{name}.py").resolve()
    if candidate.exists():
        mname = _lookup_module_name(str(candidate), mod_file_map)
        if mname:
            result.append(mname)
            return result
    # name/__init__.py
    pkg = (directory / name / "__init__.py").resolve()
    if pkg.exists():
        mname = _lookup_module_name(str(pkg), mod_file_map)
        if mname:
            result.append(mname)
    return result


def _lookup_module_name(file_path: str, mod_file_map: dict[str, str]) -> str | None:
    """反向查找：文件路径 → 模块名。"""
    fp = str(Path(file_path).resolve())
    for mname, fpath in mod_file_map.items():
        if fpath == fp:
            return mname
    return None


# ════════════════════════════════════════════════════════════
#  核心：扫描依赖
# ════════════════════════════════════════════════════════════


def scan_deps() -> dict[str, list[str]]:
    """扫描 xfun 包及 cli.py / backend 的所有内部 import，构建依赖图。

    返回::

        {
            "db":      ["config", "errors", "time_utils"],
            "ops":     ["__init__", "db", "filter", "view"],
            ...
        }
    """
    mod_file_map = _module_file_map()
    graph: dict[str, list[str]] = {mod: [] for mod in mod_file_map}

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
#  层构建（全自动：目录发现 + 拓扑排序 + 颜色分配）
# ════════════════════════════════════════════════════════════


def _infer_layer(mod_name: str, mod_file_map: dict[str, str]) -> str | None:
    """根据文件路径推断层名。"""
    fpath = mod_file_map.get(mod_name)
    if not fpath:
        return None
    fpath_p = Path(fpath).resolve()

    for layer_name, layer_dir in _discover_dirs():
        try:
            fpath_p.relative_to(layer_dir.resolve())
            return layer_name
        except ValueError:
            continue

    return None


def _layer_dep_graph(
    layer_members: dict[str, list[str]],
    module_graph: dict[str, list[str]],
) -> dict[str, list[str]]:
    """将模块级依赖聚合为层间依赖图。"""
    mod_to_layer: dict[str, str] = {}
    for layer, mods in layer_members.items():
        for m in mods:
            mod_to_layer[m] = layer

    layer_deps: dict[str, set[str]] = {name: set() for name in layer_members}
    for mod, deps in module_graph.items():
        src = mod_to_layer.get(mod)
        if not src:
            continue
        for dep in deps:
            dst = mod_to_layer.get(dep)
            if dst and dst != src:
                layer_deps[src].add(dst)

    return {k: sorted(v) for k, v in layer_deps.items()}


def _topo_sort_layers(
    layer_names: list[str],
    layer_members: dict[str, list[str]],
    module_graph: dict[str, list[str]],
) -> list[str]:
    """对层进行拓扑排序（从底向上），确保依赖方向一致。

    底层（无依赖或被依赖最多）排在前面，顶层（依赖最多）排在后面。
    """
    layer_deps = _layer_dep_graph(layer_members, module_graph)
    # layer_deps[A] = [B, C]  →  A 依赖 B 和 C，B 和 C 应排在 A 之前

    in_degree = {name: len(deps) for name, deps in layer_deps.items()}
    queue = [name for name in layer_names if in_degree.get(name, 0) == 0]
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

    # 补充未在拓扑排序中的层
    for name in layer_names:
        if name not in sorted_names:
            sorted_names.append(name)

    return sorted_names


def build_layers(
    graph: dict[str, list[str]],
) -> list[tuple[str, list[str], str]]:
    """从依赖图自动构建层定义。

    返回::

        [("utils", ["time_utils"], "#d4f0c0"),
         ("core",  ["config", "db", ...], "#e8f4fd"),
         ...]

    层顺序由拓扑排序自动决定，颜色从调色板循环分配。
    """
    mod_file_map = _module_file_map()

    # 按层分组
    layer_members: dict[str, list[str]] = {}
    for mod in graph:
        layer = _infer_layer(mod, mod_file_map)
        if layer:
            layer_members.setdefault(layer, []).append(mod)

    # 使用目录发现顺序作为拓扑排序的输入
    discovered = [name for name, _ in _discover_dirs() if name in layer_members]

    # 拓扑排序
    sorted_names = _topo_sort_layers(discovered, layer_members, graph)

    # 按排序顺序分配颜色
    result: list[tuple[str, list[str], str]] = []
    for i, name in enumerate(sorted_names):
        members = sorted(layer_members[name])
        color = _COLOR_PALETTE[i % len(_COLOR_PALETTE)]
        result.append((name, members, color))

    return result


# ════════════════════════════════════════════════════════════
#  循环依赖检测
# ════════════════════════════════════════════════════════════


def find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
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


def to_mermaid(
    graph: dict[str, list[str]] | None = None,
    layers: list[tuple[str, list[str], str]] | None = None,
    direction: str = "LR",
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
    """
    if graph is None:
        graph = scan_deps()
    if layers is None:
        layers = build_layers(graph)

    lines = [f"graph {direction}"]

    # subgraph 分组
    for name, members, color in layers:
        lines.append(f"    subgraph {name}[{name}]")
        for mod in members:
            if mod in graph:
                lines.append(f"        {mod}({mod})")
        lines.append("    end")
        lines.append(
            f"    style {name} fill:{color},stroke:#333,stroke-width:1px,color:#333"
        )

    # 边
    for mod, deps in graph.items():
        for dep in deps:
            lines.append(f"    {mod} --> {dep}")

    return "```mermaid\n" + "\n".join(lines) + "\n```"


# ════════════════════════════════════════════════════════════
#  Graphviz DOT 格式（分层）
# ════════════════════════════════════════════════════════════


def to_dot(
    graph: dict[str, list[str]] | None = None,
    layers: list[tuple[str, list[str], str]] | None = None,
) -> str:
    """渲染为带子图的 Graphviz DOT 格式。

    需安装 graphviz::

        pip install graphviz
        sudo apt install graphviz       # Linux
        brew install graphviz           # macOS
    """
    if graph is None:
        graph = scan_deps()
    if layers is None:
        layers = build_layers(graph)

    lines = [
        "digraph xfun_deps {",
        "    rankdir=LR;",
        '    node [shape=box, style="rounded,filled", fillcolor="#f0f0f0"];',
        "",
    ]

    for name, members, color in layers:
        escaped_name = name.replace("-", "_")
        lines.append(f"    subgraph cluster_{escaped_name} {{")
        lines.append(f'        label="{name}";')
        lines.append('        style="rounded,dashed";')
        lines.append(f'        fillcolor="{color}";')
        lines.append('        color="#666";')
        lines.append('        fontcolor="#333";')
        for mod in members:
            if mod in graph:
                lines.append(f'        "{mod}";')
        lines.append("    }")
        lines.append("")

    lines.append("    // 边")
    for mod, deps in graph.items():
        for dep in deps:
            lines.append(f'    "{mod}" -> "{dep}";')

    lines.append("}")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
#  纯文本报告
# ════════════════════════════════════════════════════════════


def to_text(
    graph: dict[str, list[str]] | None = None,
    layers: list[tuple[str, list[str], str]] | None = None,
) -> str:
    """以纯文本格式输出依赖关系与分层。"""
    if graph is None:
        graph = scan_deps()
    if layers is None:
        layers = build_layers(graph)

    lines: list[str] = []
    for name, members, _ in layers:
        lines.append(f"[[ {name} ]]")
        for mod in members:
            deps = graph.get(mod, [])
            if deps:
                lines.append(f"  {mod}  →  {', '.join(deps)}")
            else:
                lines.append(f"  {mod}  (无依赖)")
        lines.append("")

    # 循环检测
    cycles = find_cycles(graph)
    if cycles:
        lines.append("⚠️  循环依赖检测:")
        for c in cycles:
            lines.append(f"  {' → '.join(c)}")
    else:
        lines.append("✅  无循环依赖")

    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
#  项目目录树（根据 .gitignore 过滤）
# ════════════════════════════════════════════════════════════

def _is_ignored(p: Path) -> bool:
    # .git 是 Git 内部目录，不在 .gitignore 中，需显式排除
    if ".git" in p.parts:
        return True
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(p)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def to_tree() -> str:
    """输出项目目录树，依据 ``.gitignore`` 规则过滤被忽略的文件/目录。"""
    lines: list[str] = [f"{PROJECT_ROOT.name}/"]

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

    _walk(PROJECT_ROOT)
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
#  Typer CLI 入口
# ════════════════════════════════════════════════════════════

import typer

app = typer.Typer(no_args_is_help=True)


@app.command()
def mermaid(
    direction: str = typer.Option(
        "LR", "--direction", "-d",
        help="图方向: LR (Left→Right) 或 TD (Top→Down)",
    ),
):
    """输出带层分组的 Mermaid 流程图"""
    graph = scan_deps()
    layers = build_layers(graph)
    print(to_mermaid(graph, layers, direction=direction))


@app.command()
def dot():
    """输出 Graphviz DOT 格式（需安装 graphviz）"""
    graph = scan_deps()
    layers = build_layers(graph)
    print(to_dot(graph, layers))


@app.command()
def text():
    """输出纯文本格式的依赖关系与分层"""
    graph = scan_deps()
    layers = build_layers(graph)
    print(to_text(graph, layers))


@app.command()
def validate():
    """校验有无循环依赖"""
    graph = scan_deps()
    cycles = find_cycles(graph)
    if cycles:
        print("⚠️  发现循环依赖:")
        for c in cycles:
            print(f"  {' → '.join(c)}")
        raise typer.Exit(code=1)
    else:
        print("✅  无循环依赖")


@app.command()
def tree():
    """输出项目目录树（依据 .gitignore 过滤）"""
    print(to_tree())


if __name__ == "__main__":
    app()
