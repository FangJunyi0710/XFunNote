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
# Stage 2: 构建后端（Kotlin + Ktor → fat jar）
# ============================================================
FROM gradle:8.7-jdk21 AS server-builder

WORKDIR /build/server

# 先拷贝构建脚本，利用 Gradle 依赖缓存层
COPY server/build.gradle.kts server/settings.gradle.kts server/gradle.properties ./
RUN gradle dependencies --no-daemon || true

# 拷贝源码并打包 fat jar
COPY server/src ./src
RUN gradle shadowJar --no-daemon


# ============================================================
# Stage 3: 运行时（JRE 21，单进程同时托管 API + 前端静态）
# ============================================================
FROM eclipse-temurin:21-jre AS runtime

ENV XFUN_DATA_DIR=/data \
    BACKEND_PORT=80 \
    JAVA_OPTS="-Xmx512m"

WORKDIR /app

# 后端 fat jar
COPY --from=server-builder /build/server/build/libs/*-all.jar /app/xfunnote-server.jar

# 前端构建产物（Kotlin 服务器从 CWD/frontend/dist 提供静态文件）
COPY --from=frontend-builder /build/frontend/dist /app/frontend/dist

# 入口脚本
COPY deploy/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 数据卷（SQLite 数据库 / .env / 备份）
VOLUME ["/data"]
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD bash -c "</dev/tcp/127.0.0.1/${BACKEND_PORT}" || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
