#!/usr/bin/env python3

from __future__ import annotations

import mimetypes
import os
import secrets
import ssl
import subprocess
import sys
import threading
import http.server
import socketserver
import traceback
import urllib.error
import urllib.request
from pathlib import Path
from backend.main import app as backend

import typer
import uvicorn
from xfun.config import (
    BACKEND_PORT, DATA_DIR, PROJECT_ROOT,
    VITE_HTTP_PORT, VITE_HTTPS_PORT, SSL_PARAMS,
)

app = typer.Typer(
    help="XFunNote 服务管理",
    no_args_is_help=True,
)


def _guess_content_type(path: Path) -> str:
    t, _ = mimetypes.guess_type(str(path))
    return t or "application/octet-stream"


def _frontend_handler_factory(dist_dir: Path, backend_api: str):
    class _Handler(http.server.BaseHTTPRequestHandler):
        def _proxy(self):
            client = self.address_string()
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(length) if length else None
            req = urllib.request.Request(backend_api + self.path, data=body, method=self.command)
            for k in self.headers.keys():
                if k.lower() in ("host", "content-length", "connection"):
                    continue
                req.add_header(k, self.headers[k])
            try:
                resp = urllib.request.urlopen(req)
            except urllib.error.HTTPError as e:
                resp = e
            except urllib.error.URLError as e:
                self.send_error(502, f"上游不可达: {e.reason}")
                self.log_message(
                    "[PROXY] %s %s %s -> 502 (%s)", client, self.command, self.path, e.reason
                )
                return
            self.send_response(resp.status)
            for k, v in resp.getheaders():
                if k.lower() in ("transfer-encoding", "connection"):
                    continue
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.read())
            self.log_message(
                "[PROXY] %s %s %s -> %s", client, self.command, self.path, resp.status
            )

        def _static(self):
            client = self.address_string()
            index = dist_dir / "index.html"
            if not index.exists():
                self.send_error(404, "前端未构建，请先执行 vite build")
                self.log_message("[STATIC] %s %s -> 404 (未构建)", client, self.path)
                return
            rel = self.path.split("?", 1)[0].lstrip("/")
            candidate = (dist_dir / rel).resolve()
            root = dist_dir.resolve()
            if rel and candidate.is_file() and root in candidate.parents:
                data = candidate.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", _guess_content_type(candidate))
            else:
                data = index.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            self.log_message("[STATIC] %s %s -> 200", client, self.path)

        def do_GET(self):
            if self.path.startswith("/api"):
                self._proxy()
            else:
                self._static()

        def do_POST(self):
            self._proxy() if self.path.startswith("/api") else self.send_error(405)

        def do_PUT(self):
            self._proxy() if self.path.startswith("/api") else self.send_error(405)

        def do_DELETE(self):
            self._proxy() if self.path.startswith("/api") else self.send_error(405)

        def log_message(self, fmt, *args):
            sys.stderr.write((fmt % args) + "\n")

    return _Handler


class _NoFQDNHTTPServer(http.server.HTTPServer):
    """与标准 HTTPServer 相同，但 server_bind 不做反向 DNS (socket.getfqdn)，
    避免 DNS 解析阻塞导致监听端口迟迟不就绪（开发/部署机 DNS 不可达时尤为明显）。"""

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = str(host)
        self.server_port = port


def _redirect_server(host: str, from_port: int, to_scheme: str, to_port: int) -> None:
    class _R(http.server.BaseHTTPRequestHandler):
        def _redirect(self):
            host_header = self.headers.get("Host", f"127.0.0.1:{from_port}")
            # 提取主机名：处理 IPv6 [::1]:80 与 host:port
            if host_header.startswith("["):
                name = host_header[: host_header.find("]") + 1]
            elif ":" in host_header:
                name = host_header.rsplit(":", 1)[0]
            else:
                name = host_header
            location = f"{to_scheme}://{name}:{to_port}{self.path}"
            self.send_response(301)
            self.send_header("Location", location)
            self.end_headers()

        do_GET = _redirect
        do_HEAD = _redirect

        def log_message(self, fmt, *args):
            sys.stderr.write((fmt % args) + "\n")

    _NoFQDNHTTPServer((host, from_port), _R).serve_forever()


def _serve_backend() -> None:
    uvicorn.run(backend, host="127.0.0.1", port=BACKEND_PORT, reload=False)


def run_server(host: str = "0.0.0.0", port: int = BACKEND_PORT) -> None:
    """启动组合服务（安卓端子线程 / PC 端子进程调用）。

    后端 API 运行在 127.0.0.1:BACKEND_PORT（内部），浏览器侧前端服务器运行在
    VITE_HTTP_PORT / VITE_HTTPS_PORT（默认 80/443）。
    """
    threading.Thread(target=_serve_backend, daemon=True).start()

    dist_dir = PROJECT_ROOT / "frontend" / "dist"
    handler = _frontend_handler_factory(dist_dir, f"http://127.0.0.1:{BACKEND_PORT}")
    key, cert = SSL_PARAMS
    if key and cert:
        # 有证书：443 承载内容(HTTPS)，80 跳转至 443
        httpd = _NoFQDNHTTPServer((host, VITE_HTTPS_PORT), handler)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert, key)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        threading.Thread(
            target=_redirect_server,
            args=(host, VITE_HTTP_PORT, "https", VITE_HTTPS_PORT),
            daemon=True,
        ).start()
        httpd.serve_forever()
    else:
        # 无证书：仅 80 承载内容(HTTP)；不监听 443，避免对 https 客户端
        # 返回明文 400 引发 SSL_ERROR_RX_RECORD_TOO_LONG
        _NoFQDNHTTPServer((host, VITE_HTTP_PORT), handler).serve_forever()


def _read_env_file() -> dict[str, str]:
    path = DATA_DIR / ".env"
    kv: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            kv[k.strip()] = v.strip()
    return kv


def _write_env_file(kv: dict[str, str]) -> None:
    path = DATA_DIR / ".env"
    path.write_text(
        "\n".join(f"{k}={v}" for k, v in kv.items()) + "\n", encoding="utf-8"
    )


def _ensure_root_token() -> None:
    kv = _read_env_file()
    if not kv.get("ROOT_TOKEN"):
        kv["ROOT_TOKEN"] = "sk-" + secrets.token_urlsafe(24)
        _write_env_file(kv)
        typer.echo("已生成 ROOT_TOKEN（数据目录 .env）")


def _systemd_unit_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    cfg = Path(base) if base else (Path.home() / ".config")
    return cfg / "systemd" / "user" / "xfunnote.service"


def _unit_content() -> str:
    exe = os.path.realpath(sys.argv[0])
    return (
        "[Unit]\n"
        "Description=XFunNote 本地服务\n"
        "After=network.target\n\n"
        "[Service]\n"
        "Type=simple\n"
        "WorkingDirectory=%h/.local/share/xfunnote\n"
        "Environment=XFUN_DATA_DIR=%h/.local/share/xfunnote\n"
        "ExecStart=" + exe + " serve --host 0.0.0.0\n"
        "Restart=on-failure\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )


def _do_install_service() -> None:
    if sys.platform == "win32":
        typer.echo("Windows 暂不支持守护进程注册", err=True)
        raise typer.Exit(code=1)
    unit = _systemd_unit_path()
    unit.parent.mkdir(parents=True, exist_ok=True)
    unit.write_text(_unit_content(), encoding="utf-8")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    r = subprocess.run(
        ["systemctl", "--user", "enable", "--now", "xfunnote.service"],
        capture_output=True, text=True,
    )
    typer.echo(r.stdout or r.stderr or "已注册并启动用户守护进程")


def _do_uninstall_service() -> None:
    if sys.platform == "win32":
        typer.echo("Windows 暂不支持守护进程注册", err=True)
        raise typer.Exit(code=1)
    subprocess.run(
        ["systemctl", "--user", "disable", "--now", "xfunnote.service"],
        capture_output=True, text=True,
    )
    _systemd_unit_path().unlink(missing_ok=True)
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    typer.echo("已卸载用户守护进程")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="监听地址（默认 0.0.0.0 局域网）"),
):
    """前台启动服务（供 systemd / 直接运行）"""
    _ensure_root_token()
    run_server(host=host)


@app.command()
def install():
    """注册并启用 systemd 用户守护进程（Linux）"""
    _do_install_service()


@app.command()
def uninstall():
    """卸载 systemd 用户守护进程"""
    _do_uninstall_service()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("serve")
    app()
