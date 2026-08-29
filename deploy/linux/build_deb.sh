#!/usr/bin/env bash
# 将 PyInstaller 生成的 Linux 单文件二进制打包为 .deb。
# 前置：在本机 Linux 上先构建二进制：
#   pyinstaller deploy/win/XFunNote.spec --noconfirm --clean
#   （同一份 spec 在 Linux 上即可产出 Linux 二进制，输出为 dist/XFunNote）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BIN="${1:-dist/XFunNote}"
if [ ! -x "$BIN" ]; then
  echo "找不到二进制: $BIN （请先用 pyinstaller 构建）" >&2
  exit 1
fi

PKG="xfunnote_0.1.0_amd64"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

echo "==> 组装包目录: $STAGE"
mkdir -p "$STAGE/opt/xfunnote" "$STAGE/usr/bin" "$STAGE/usr/share/applications"
cp "$BIN" "$STAGE/opt/xfunnote/xfunnote"
chmod 755 "$STAGE/opt/xfunnote/xfunnote"
ln -s /opt/xfunnote/xfunnote "$STAGE/usr/bin/xfunnote"
cp deploy/linux/xfunnote.desktop "$STAGE/usr/share/applications/xfunnote.desktop"

mkdir -p "$STAGE/DEBIAN"
cp deploy/linux/control "$STAGE/DEBIAN/control"

echo "==> 构建 .deb"
dpkg-deb --build --root-owner-group "$STAGE" "$PKG.deb"

echo "完成：./$PKG.deb"
echo "用户安装后运行：xfunnote install-service   # 注册用户守护进程"
