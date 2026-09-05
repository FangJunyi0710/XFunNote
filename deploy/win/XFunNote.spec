# -*- mode: python ; coding: utf-8 -*-
"""XFunNote Windows 打包规格（PyInstaller）。

用法：
    pyinstaller XFunNote.spec
生成 dist/XFunNote.exe（单文件控制台程序）。

入口：backend/embedded_server.py（内嵌前端静态 + /api 代理 + uvicorn 后端）。
"""
import os
from PyInstaller.utils.hooks import collect_submodules

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPEC), "..", ".."))

hiddenimports = (
    ["backend", "xfun"]
    + collect_submodules("backend")
    + collect_submodules("xfun")
    + collect_submodules("langchain")
    + collect_submodules("langchain_core")
    + collect_submodules("langchain_anthropic")
    + collect_submodules("fastapi")
    + collect_submodules("starlette")
    + collect_submodules("uvicorn")
    + collect_submodules("pydantic")
    + collect_submodules("pydantic_core")
    + ["typer", "future_uuid", "fsrs", "dotenv"]
)

datas = [
    (os.path.join(PROJECT_ROOT, "frontend", "dist"), "frontend/dist"),
]

a = Analysis(
    [os.path.join(PROJECT_ROOT, "backend", "embedded_server.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pytest_cov", "uvloop", "httptools", "watchfiles"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="XFunNote",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
