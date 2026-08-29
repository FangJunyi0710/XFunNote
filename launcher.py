#!/usr/bin/env python3
"""
XFunNote 生产启动器 — 服务管理 CLI（与开发用 cli.py 无关）。

职责：管理前后端一体的服务进程（启动 / 停止 / 重启 / 状态 / 打开浏览器 /
配置 / 注册守护进程 / 查看日志）。用户通过浏览器（PC）或 WebView（安卓）访问。

架构（复刻 Vite 开发模式）：
- 后端 API 进程：127.0.0.1:BACKEND_PORT（默认 8000），仅处理 /api，内部端口。
- 浏览器侧前端服务器：0.0.0.0:VITE_HTTP_PORT/VITE_HTTPS_PORT（默认 80/443），
  托管 frontend/dist 静态 SPA，并把 /api/* 反向代理到后端；HTTPS 时 80→443 跳转。
"""

from __future__ import annotations

import mimetypes
import os
import secrets
import signal
import ssl
import subprocess
import sys
import threading
import webbrowser
import http.server
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional

import typer
import uvicorn
from xfun.config import (
    BACKEND_PORT, DATA_DIR, LOG_FILE, PID_FILE, PROJECT_ROOT,
    VITE_HTTP_PORT, VITE_HTTPS_PORT, SSL_PARAMS,
)

app = typer.Typer(help="XFunNote 服务管理", no_args_is_help=True)


def _is_running(pid: int) -> bool:
    if sys.platform == "win32":
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True, text=True,
        )
        return str(pid) in out.stdout
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _guess_content_type(path: Path) -> str:
    t, _ = mimetypes.guess_type(str(path))
    return t or "application/octet-stream"


def _frontend_handler_factory(dist_dir: Path, backend_api: str):
    class _Handler(http.server.BaseHTTPRequestHandler):
        def _proxy(self):
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
            self.send_response(resp.status)
            for k, v in resp.getheaders():
                if k.lower() in ("transfer-encoding", "connection"):
                    continue
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.read())

        def _static(self):
            index = dist_dir / "index.html"
            if not index.exists():
                self.send_error(404, "前端未构建，请先执行 vite build")
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

        def log_message(self, *args):
            pass

    return _Handler


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

        def log_message(self, *args):
            pass

    http.server.HTTPServer((host, from_port), _R).serve_forever()


def run_server(host: str = "0.0.0.0", port: int = BACKEND_PORT) -> None:
    """启动组合服务（安卓端子线程 / PC 端子进程调用）。

    后端 API 运行在 127.0.0.1:BACKEND_PORT（内部），浏览器侧前端服务器运行在
    VITE_HTTP_PORT / VITE_HTTPS_PORT（默认 80/443）。
    """
    threading.Thread(
        target=lambda: uvicorn.run(
            "backend.main:app", host="127.0.0.1", port=BACKEND_PORT, reload=False
        ),
        daemon=True,
    ).start()

    dist_dir = PROJECT_ROOT / "frontend" / "dist"
    handler = _frontend_handler_factory(dist_dir, f"http://127.0.0.1:{BACKEND_PORT}")
    key, cert = SSL_PARAMS
    if key and cert:
        # 有证书：443 承载内容(HTTPS)，80 跳转至 443
        httpd = http.server.HTTPServer((host, VITE_HTTPS_PORT), handler)
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
        # 无证书：80 承载内容(HTTP)，443 反向跳转至 80（明文 HTTP 重定向）
        threading.Thread(
            target=_redirect_server,
            args=(host, VITE_HTTPS_PORT, "http", VITE_HTTP_PORT),
            daemon=True,
        ).start()
        http.server.HTTPServer((host, VITE_HTTP_PORT), handler).serve_forever()


def _open_url(scheme: str, frontend_port: int) -> str:
    return f"{scheme}://127.0.0.1:{frontend_port}"


def _do_start(host: str, do_open: bool) -> None:
    pf = PID_FILE
    if pf.exists():
        try:
            old = int(pf.read_text().strip())
        except ValueError:
            old = None
        if old and _is_running(old):
            typer.echo(f"服务已在运行 (PID {old})")
            return
        pf.unlink(missing_ok=True)

    key, _ = SSL_PARAMS
    scheme = "https" if key else "http"
    frontend_port = VITE_HTTPS_PORT if key else VITE_HTTP_PORT

    env = dict(os.environ)
    env.setdefault("XFUN_DATA_DIR", str(DATA_DIR))

    bootstrap = (
        "from launcher import run_server\n"
        f"run_server(host={host!r})\n"
    )
    log = LOG_FILE.open("ab")
    proc = subprocess.Popen(
        [sys.executable, "-c", bootstrap],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    pf.write_text(str(proc.pid))
    url = _open_url(scheme, frontend_port)
    typer.echo(f"服务已启动 (PID {proc.pid})，访问: {url}")
    if key:
        typer.echo(f"HTTP :{VITE_HTTP_PORT} 将自动跳转至 HTTPS :{VITE_HTTPS_PORT}")
    else:
        typer.echo(f"HTTPS :{VITE_HTTPS_PORT} 将自动跳转至 HTTP :{VITE_HTTP_PORT}")
    typer.echo(f"日志: {LOG_FILE}")
    if do_open:
        webbrowser.open(url)


def _do_stop() -> None:
    pf = PID_FILE
    if not pf.exists():
        typer.echo("服务未运行")
        return
    try:
        pid = int(pf.read_text().strip())
    except ValueError:
        pf.unlink(missing_ok=True)
        typer.echo("服务未运行（pid 文件损坏）")
        return
    if not _is_running(pid):
        pf.unlink(missing_ok=True)
        typer.echo("服务未运行")
        return
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    pf.unlink(missing_ok=True)
    typer.echo("服务已停止")


def _do_status() -> None:
    pf = PID_FILE
    if pf.exists():
        try:
            pid = int(pf.read_text().strip())
        except ValueError:
            pid = None
        if pid and _is_running(pid):
            key, _ = SSL_PARAMS
            scheme = "https" if key else "http"
            fp = VITE_HTTPS_PORT if key else VITE_HTTP_PORT
            typer.echo(f"运行中 (PID {pid})，URL: {_open_url(scheme, fp)}")
            return
    typer.echo("未运行")


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


def _do_config(action: str, pairs: List[str]) -> None:
    kv = _read_env_file()
    if action == "get":
        if pairs:
            for key in pairs:
                typer.echo(f"{key}={kv.get(key, '')}")
        else:
            for k, v in kv.items():
                typer.echo(f"{k}={v}")
    elif action == "set":
        changed = False
        for pair in pairs:
            if "=" not in pair:
                typer.echo(f"跳过非法参数（需 KEY=VALUE）: {pair}", err=True)
                continue
            k, v = pair.split("=", 1)
            kv[k.strip()] = v.strip()
            changed = True
        if changed:
            _write_env_file(kv)
            typer.echo("已更新配置（需 restart 生效）")
    elif action == "init":
        if "ROOT_TOKEN" not in kv or not kv["ROOT_TOKEN"]:
            kv["ROOT_TOKEN"] = "sk-" + secrets.token_urlsafe(24)
            _write_env_file(kv)
            typer.echo("已生成 ROOT_TOKEN")
        else:
            typer.echo("ROOT_TOKEN 已存在")


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
        f"WorkingDirectory={PROJECT_ROOT}\n"
        f"Environment=XFUN_DATA_DIR={DATA_DIR}\n"
        "ExecStart=" + exe + " start --host 0.0.0.0\n"
        "Restart=on-failure\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )


def _do_install_service() -> None:
    if sys.platform == "win32":
        typer.echo("Windows 暂不支持守护进程注册（直接运行 exe 即可）", err=True)
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
def start(
    host: str = typer.Option("0.0.0.0", "--host", help="监听地址（默认 0.0.0.0 局域网）"),
    open: bool = typer.Option(False, "--open", help="启动后打开浏览器"),
):
    """启动服务"""
    _do_start(host, open)


@app.command()
def stop():
    """停止服务"""
    _do_stop()


@app.command()
def restart(
    host: str = typer.Option("0.0.0.0", "--host"),
    open: bool = typer.Option(False, "--open"),
):
    """重启服务"""
    _do_stop()
    _do_start(host, open)


@app.command()
def status():
    """查看状态"""
    _do_status()


@app.command()
def open():
    """打开浏览器"""
    key, _ = SSL_PARAMS
    scheme = "https" if key else "http"
    fp = VITE_HTTPS_PORT if key else VITE_HTTP_PORT
    webbrowser.open(_open_url(scheme, fp))


@app.command()
def config(
    action: str = typer.Argument(..., help="get | set | init"),
    pairs: Optional[List[str]] = typer.Argument(None, help="get: KEY...；set: KEY=VALUE..."),
):
    """读写配置 (.env)"""
    _do_config(action, pairs or [])


@app.command("install-service")
def install_service():
    """注册用户守护进程 (Linux systemd --user)"""
    _do_install_service()


@app.command("uninstall-service")
def uninstall_service():
    """卸载用户守护进程"""
    _do_uninstall_service()


if __name__ == "__main__":
    app()
