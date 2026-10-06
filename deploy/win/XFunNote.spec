# -*- mode: python ; coding: utf-8 -*-
"""XFunNote Windows 打包规格（PyInstaller）。

用法：
    pyinstaller XFunNote.spec
生成 dist/XFunNote.exe（单文件控制台程序）。

入口：backend/embedded_server.py（内嵌前端静态 + /api 代理 + uvicorn 后端）。
版本号：从 frontend/package.json 读取。
"""
import os
import subprocess
import sys
from PyInstaller.utils.hooks import collect_submodules

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPEC), "..", ".."))

# 读取版本号
version_output = subprocess.run(
    [sys.executable, os.path.join(PROJECT_ROOT, "scripts", "read_version.py")],
    capture_output=True, text=True, check=True
)
VERSION = version_output.stdout.strip()

# 生成 Windows 版本资源文件
version_parts = VERSION.split(".")
file_version = tuple(int(p) for p in version_parts) + (0,) * (4 - len(version_parts))

version_info_path = os.path.join(PROJECT_ROOT, "version_info.txt")
with open(version_info_path, "w", encoding="utf-8") as f:
    f.write(f'''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={file_version},
    prodvers={file_version},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'XFunNote'),
         StringStruct(u'FileDescription', u'XFunNote Local-First Note Taking with AI'),
         StringStruct(u'FileVersion', u'{VERSION}.0'),
         StringStruct(u'InternalName', u'XFunNote'),
         StringStruct(u'LegalCopyright', u'Copyright (C) 2026 FangJunyi0710'),
         StringStruct(u'OriginalFilename', u'XFunNote.exe'),
         StringStruct(u'ProductName', u'XFunNote'),
         StringStruct(u'ProductVersion', u'{VERSION}.0')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)''')

hiddenimports = (
    ["backend", "xfun"]
    + collect_submodules("backend")
    + collect_submodules("xfun")
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
    version_file=version_info_path,
)