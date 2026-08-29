#!/usr/bin/env bash
# 构建 XFunNote Windows 可执行文件（单文件 exe）。
# 在 Windows 上、已激活的 Python 虚拟环境中运行。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "==> 1/3 构建前端 (vite build)"
cd frontend
npm install
npm run build
cd "$ROOT"

echo "==> 2/3 安装打包依赖"
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
python -m pip install pyinstaller

echo "==> 3/3 PyInstaller 打包"
pyinstaller deploy/win/XFunNote.spec --noconfirm --clean

echo "完成：dist/XFunNote.exe"
