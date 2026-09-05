#!/usr/bin/env bash
# 将 Python 源码 + 前端构建产物 + 配置文件打包为 .deb
# 用法：./build_deb.sh [version]   （version 可选，默认读取 frontend/package.json）

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# 读取版本：优先参数，其次 frontend/package.json
if [ $# -ge 1 ]; then
    VERSION="$1"
else
    VERSION="$(python3 scripts/read_version.py)"
fi

ARCH="all"  # 纯 Python 源码，跨架构
PKG="xfunnote_${VERSION}_${ARCH}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

echo "构建 $PKG ..."
echo "暂存目录: $STAGE"

# 目标目录结构
mkdir -p "$STAGE/opt/xfunnote"
mkdir -p "$STAGE/etc/nginx/sites-available"
mkdir -p "$STAGE/etc/systemd/system"
mkdir -p "$STAGE/DEBIAN"

# 1. 复制 Python 源码与前端产物
echo "复制源码 ..."
cp -r backend "$STAGE/opt/xfunnote/"
cp -r xfun "$STAGE/opt/xfunnote/"
cp -r frontend/dist "$STAGE/opt/xfunnote/frontend/"
cp deploy/linux/gunicorn.conf.py "$STAGE/opt/xfunnote/"

# 2. 复制配置文件
echo "复制配置 ..."
cp deploy/linux/nginx-xfunnote.conf "$STAGE/etc/nginx/sites-available/xfunnote"
cp deploy/linux/xfunnote.service "$STAGE/etc/systemd/system/"

# 3. 复制维护脚本
echo "复制维护脚本 ..."
cp deploy/linux/xfunnote.postinst "$STAGE/DEBIAN/postinst"
cp deploy/linux/xfunnote.prerm "$STAGE/DEBIAN/prerm"
chmod 755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/prerm"

# 4. 生成 control 文件
echo "生成 control ..."
sed -e "s/__VERSION__/$VERSION/" -e "s/__ARCH__/$ARCH/" deploy/linux/control > "$STAGE/DEBIAN/control"

# 5. 打包
echo "打包 ..."
dpkg-deb --build --root-owner-group "$STAGE" "$PKG.deb"

echo "完成：$(pwd)/$PKG.deb"