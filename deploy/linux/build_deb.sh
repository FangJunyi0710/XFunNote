#!/usr/bin/env bash
# 将 PyInstaller 生成的 Linux 单文件二进制打包为 .deb。
# 前置：先构建二进制  pyinstaller deploy/win/XFunNote.spec --noconfirm --clean
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BIN="${1:-dist/XFunNote}"
if [ ! -x "$BIN" ]; then
  echo "找不到二进制: $BIN，请先构建：" >&2
  echo "  pyinstaller deploy/win/XFunNote.spec --noconfirm --clean" >&2
  exit 1
fi

VERSION="$(grep -oE '^VERSION[[:space:]]*=[[:space:]]*"[^"]+"' xfun/config.py | head -n1 | sed -E 's/.*"([^"]+)".*/\1/')"
ARCH="$(dpkg --print-architecture 2>/dev/null || uname -m)"
PKG="xfunnote_${VERSION}_${ARCH}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/opt/xfunnote" "$STAGE/usr/bin" "$STAGE/usr/share/applications"
cp "$BIN" "$STAGE/opt/xfunnote/xfunnote"
chmod 755 "$STAGE/opt/xfunnote/xfunnote"
ln -s /opt/xfunnote/xfunnote "$STAGE/usr/bin/xfunnote"
cp deploy/linux/xfunnote.desktop "$STAGE/usr/share/applications/xfunnote.desktop"

mkdir -p "$STAGE/DEBIAN"
sed -e "s/__VERSION__/$VERSION/" -e "s/__ARCH__/$ARCH/" deploy/linux/control > "$STAGE/DEBIAN/control"

dpkg-deb --build --root-owner-group "$STAGE" "$PKG.deb"

echo "完成：./$PKG.deb"
