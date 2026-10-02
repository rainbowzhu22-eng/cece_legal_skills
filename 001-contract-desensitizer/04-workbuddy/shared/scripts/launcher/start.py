#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合同脱敏助手 · 跨平台启动器（Windows / macOS / Linux 通用）

用法：
    python start.py                 启动本地服务并自动打开浏览器
    python start.py --foreground    前台运行，日志留在当前终端，Ctrl-C 结束

行为：
    1. 找到带依赖的 Python；没有就自动建 .venv 并安装 requirements.txt（仅首次）
    2. 检查 18800 端口；仅对确认属于本工具的旧服务请求优雅退出
    3. 启动 contract_app_server.py（完全离线，只监听 127.0.0.1）
    4. 健康检查通过后打开 http://127.0.0.1:18800/

只依赖标准库，不需要 bash / bat / vbs。
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

PORT = int(os.environ.get("REDACTOR_PORT", "18800"))
APP_URL = f"http://127.0.0.1:{PORT}/"
APP_VERSION = "1.2.3"
REQUIRED = ("docx", "pdfplumber", "pypdf", "reportlab", "pypdfium2", "PIL")
MIN_PY = (3, 9)


def here() -> Path:
    return Path(__file__).resolve().parent


def project_dir() -> Path:
    return here().parent


def has_deps(python: Path) -> bool:
    code = "import " + ", ".join(REQUIRED)
    try:
        return subprocess.run([str(python), "-c", code],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0
    except OSError:
        return False


def pick_python(proj: Path) -> Path | None:
    venv_py = proj / ".venv" / ("Scripts" if os.name == "nt" else "bin") / \
        ("python.exe" if os.name == "nt" else "python")
    candidates = [venv_py, Path(sys.executable)]
    found = os.environ.get("PYTHON")
    if found:
        candidates.append(Path(found))
    for c in candidates:
        if c.exists() and has_deps(c):
            return c
    return None


def bootstrap(proj: Path) -> Path:
    """建虚拟环境并装依赖，返回可用的 python 路径。"""
    if sys.version_info < MIN_PY:
        raise SystemExit(f"✗ 需要 Python {MIN_PY[0]}.{MIN_PY[1]}+，当前是 "
                         f"{sys.version_info.major}.{sys.version_info.minor}")
    venv = proj / ".venv"
    print("· 首次运行：创建虚拟环境…")
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    py = venv / ("Scripts" if os.name == "nt" else "bin") / \
        ("python.exe" if os.name == "nt" else "python")
    print("· 安装依赖（约 1~2 分钟，仅此一次）…")
    subprocess.run([str(py), "-m", "pip", "install", "--quiet", "--upgrade", "pip"],
                   check=False)
    subprocess.run([str(py), "-m", "pip", "install", "--quiet",
                    "-r", str(proj / "requirements.txt")], check=True)
    return py


def port_open() -> bool:
    with socket.socket() as s:
        s.settimeout(0.6)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def service_health() -> dict | None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(APP_URL + "health", timeout=1) as response:
            data = json.loads(response.read(4096))
        if isinstance(data, dict) and data.get("service") == "contract_app_server":
            return data
    except (OSError, ValueError, TypeError):
        pass
    return None


def request_shutdown() -> None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(APP_URL + "api/shutdown", data=b"", method="POST")
    opener.open(request, timeout=2).close()


def prepare_port() -> bool:
    """返回 True 表示同版本服务已运行；不按端口盲杀其他进程。"""
    current = service_health()
    if current and current.get("version") == APP_VERSION:
        return True
    if current:
        try:
            request_shutdown()
        except OSError as exc:
            raise SystemExit(f"旧版服务未能正常退出：{exc}") from exc
        for _ in range(30):
            if not port_open():
                return False
            time.sleep(0.2)
        raise SystemExit("旧版服务未释放端口 18800，请在网页中退出后重试。")
    if port_open():
        raise SystemExit("端口 18800 已被其他程序占用，未结束该程序。请先释放端口或联系管理员。")
    return False


def wait_ready(timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        health = service_health()
        if health and health.get("version") == APP_VERSION:
            return True
        time.sleep(0.3)
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="合同脱敏助手启动器")
    ap.add_argument("--foreground", action="store_true", help="前台运行，Ctrl-C 结束")
    ap.add_argument("--stop", action="store_true", help="只停止本工具服务，不结束占用端口的其他程序")
    args = ap.parse_args()

    if args.stop:
        if service_health():
            request_shutdown()
            print("已请求停止合同脱敏服务。")
        elif port_open():
            raise SystemExit("端口由其他程序占用，未结束该程序。")
        else:
            print("合同脱敏服务未运行。")
        return 0

    proj = project_dir()
    py = pick_python(proj)
    if py is None:
        py = bootstrap(proj)

    if prepare_port():
        print(f"✓ 已有 v{APP_VERSION} 服务运行：{APP_URL}")
        webbrowser.open(APP_URL)
        return 0
    workdir = proj / "sessions"
    workdir.mkdir(exist_ok=True)

    print(f"· 项目目录：{proj}")
    print(f"· Python   ：{py}")
    print(f"· 启动服务（完全离线，仅监听 127.0.0.1:{PORT}）…")

    cmd = [str(py), str(proj / "contract_app_server.py"),
           "--host", "127.0.0.1", "--port", str(PORT),
           "--workdir", str(workdir)]
    if args.foreground:
        proc = subprocess.Popen(cmd, cwd=str(proj))
    else:
        log = workdir / "server.log"
        log_f = open(log, "wb")
        popen_kwargs = dict(cwd=str(proj), stdout=log_f,
                            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        if os.name == "nt":
            # Windows .bat 退出后服务仍需独立运行。
            popen_kwargs["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
        else:
            popen_kwargs["start_new_session"] = True
        try:
            proc = subprocess.Popen(cmd, **popen_kwargs)
        finally:
            log_f.close()

    if not wait_ready():
        proc.terminate()
        print(f"✗ 服务启动失败，日志：{workdir / 'server.log'}", file=sys.stderr)
        return 1

    print(f"✓ 服务已就绪：{APP_URL}")
    webbrowser.open(APP_URL)
    print("  停止服务：网页右上角「退出」，或重新运行本启动器。")

    if args.foreground:
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
