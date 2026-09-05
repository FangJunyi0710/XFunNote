#!/usr/bin/env python3
"""读取 frontend/package.json 版本号，供各平台打包脚本复用。"""
import json
from pathlib import Path

pkg_path = Path(__file__).resolve().parent.parent / "frontend" / "package.json"
version = json.loads(pkg_path.read_text(encoding="utf-8"))["version"]
print(version)