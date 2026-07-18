"""
集中管理所有配置，从 .env 和环境变量读取。

其他模块不应直接调用 os.environ.get()，
统一通过此模块获取配置。
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# 更新版本号需改两处：
# frontend/package.json 的 version 字段
# xfun/config.py 的 VERSION 常量
# 需保证主版本号一致，避免 API 路由错误
VERSION = "0.1.0"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 加载 .env 文件
load_dotenv(str(PROJECT_ROOT / ".env"))

XFUN_USER = os.environ.get("XFUN_USER", "default")
DB_PATH = str(PROJECT_ROOT / "data" / f"{XFUN_USER}.db")

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL")
LLM_MODEL = os.environ.get("LLM_MODEL")

SSL_CERT_PATH = os.environ.get("SSL_CERT_PATH", "")
SSL_KEY_PATH = os.environ.get("SSL_KEY_PATH", "")

UVICORN_RELOAD = os.environ.get("UVICORN_RELOAD", "false").lower() == "true"
SHOW_DOCS = os.environ.get("SHOW_DOCS", "false").lower() == "true"
BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8000"))

ROOT_TOKEN = os.environ.get("ROOT_TOKEN", "")
