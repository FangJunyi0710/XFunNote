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

def _resolve_data_dir() -> Path:
    """计算数据目录。优先级：XFUN_DATA_DIR 环境变量 > 项目根/data/。"""
    env = os.environ.get("XFUN_DATA_DIR")
    return Path(env) if env else (PROJECT_ROOT / "data")

DATA_DIR = _resolve_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 加载 .env 文件（项目根，开发用）
load_dotenv(str(PROJECT_ROOT / ".env"))

# 加载数据目录下的 .env（打包后用户可覆盖配置，优先级更高）
load_dotenv(str(DATA_DIR / ".env"))

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL")
LLM_MODEL = os.environ.get("LLM_MODEL")

SSL_CERT_PATH = os.environ.get("SSL_CERT_PATH", "")
SSL_KEY_PATH = os.environ.get("SSL_KEY_PATH", "")

UVICORN_RELOAD = os.environ.get("UVICORN_RELOAD", "false").lower() == "true"
SHOW_DOCS = os.environ.get("SHOW_DOCS", "false").lower() == "true"
BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8000"))

# 浏览器侧前端服务器端口（复刻 Vite：80/443，特权端口可用 VITE_*_PORT 覆盖）
VITE_HTTP_PORT = int(os.environ.get("VITE_HTTP_PORT", "80"))
VITE_HTTPS_PORT = int(os.environ.get("VITE_HTTPS_PORT", "443"))

ROOT_TOKEN = os.environ.get("ROOT_TOKEN", "")


PID_FILE = DATA_DIR / ".xfunnote.pid"
LOG_FILE = DATA_DIR / ".xfunnote.log"


def _resolve_ssl_params() -> tuple:
    """返回 (keyfile, certfile) 绝对路径；未配置或文件缺失则返回 (None, None)。"""
    key, cert = SSL_KEY_PATH, SSL_CERT_PATH
    if key and cert and Path(key).exists() and Path(cert).exists():
        return str(Path(key).resolve()), str(Path(cert).resolve())
    return None, None

SSL_PARAMS = _resolve_ssl_params()
