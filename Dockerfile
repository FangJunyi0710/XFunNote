# syntax=docker/dockerfile:1

# ============================================================
# Stage 1: 构建前端（Vite + React）
# ============================================================
FROM node:20-slim AS frontend-builder

WORKDIR /build/frontend

# 先装依赖（利用层缓存）
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# 拷贝源码并构建（vite.config 对缺失 .env 宽容）
COPY frontend/ ./
RUN npm run build


# ============================================================
# Stage 2: 运行时（Python 3.12 + nginx + uvicorn）
# ============================================================
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    XFUN_DATA_DIR=/data

# nginx + 基础工具（head/base64 来自 coreutils，slim 已含）
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

WORKDIR /app

# 安装 Python 依赖（仅运行时依赖，无 pytest）
COPY requirements-build.txt ./
RUN pip install -r requirements-build.txt

# 拷贝后端与核心引擎源码
COPY backend/ ./backend/
COPY xfun/ ./xfun/

# 拷贝前端构建产物
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

# 拷贝 nginx 配置与入口脚本
COPY deploy/docker/nginx.conf /etc/nginx/conf.d/xfunnote.conf
COPY deploy/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 数据卷（SQLite 数据库 / .env / 备份）
VOLUME ["/data"]
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import socket; s=socket.create_connection(('127.0.0.1',8000),3); s.close()" || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
