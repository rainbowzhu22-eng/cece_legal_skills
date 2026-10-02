#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同脱敏助手 · Windows 安装器
=============================================================================
把 macOS 版 install_macos.sh 适配为 Windows 原生安装流程：
  1. 定位 Python >= 3.9（优先 WorkBuddy 受管 Python，回退系统 py / python）
  2. 把技能部署到 WorkBuddy skills 区（含版本守卫，逻辑与 Mac 版一致）
  3. 在技能目录内建独立 venv 并安装 requirements.txt（仅首次需联网）
  4. 运行识别 / 改写引擎自检
  5. 在桌面生成「合同脱敏（WorkBuddy）.bat」双击入口
仅依赖标准库；运行时只监听 127.0.0.1，不上传任何文书到云端。
"""
from __future__ import annotations

import os
import sys
import shutil
import subprocess

# ---- 与 install_macos.sh 保持一致的版本标记 ----
BUILD_ID = "contract-desensitizer-v1.2.3-20261002"
PREV_BUILD_IDS = [
    "github-cd4d86a-pdf-text-check-20260929",
    "github-cd4d86a-litigation-review-ux-20260927",
    "github-cd4d86a-litigation-review-20260926",
    "github-cd4d86a-english-org-no-embedded-20260926",
    "github-cd4d86a-english-org-20260926",
]
MIN_PY = (3, 9)
DESKTOP_APP_NAME = "合同脱敏（WorkBuddy）.bat"
REQUIRED = ("docx", "pdfplumber", "pypdf", "reportlab", "pypdfium2", "PIL")


def bundle_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def package_dir() -> str:
    return os.path.join(bundle_dir(), "contract-desensitizer-offline")


def env_or(default: str, *env_keys: str) -> str:
    for k in env_keys:
        v = os.environ.get(k)
        if v:
            return v
    return os.path.expandvars(default)


def skills_dir() -> str:
    return env_or(r"%USERPROFILE%\.workbuddy\skills",
                  "CONTRACT_DESENSITIZER_SKILLS_DIR")


def desktop_dir() -> str:
    return env_or(r"%USERPROFILE%\Desktop",
                  "CONTRACT_DESENSITIZER_DESKTOP_DIR")


def find_python() -> str | None:
    """优先受管 Python，其次 PATH 上的 py / python。"""
    managed_base = os.path.expandvars(
        r"%USERPROFILE%\.workbuddy\binaries\python\versions")
    candidates: list[str] = []
    if os.path.isdir(managed_base):
        # 版本目录按名排序，取最新
        for d in sorted(os.listdir(managed_base), reverse=True):
            p = os.path.join(managed_base, d, "python.exe")
            if os.path.isfile(p):
                candidates.append(p)
    for name in ("py", "python"):
        from shutil import which
        p = which(name)
        if p:
            candidates.append(p)
    for c in candidates:
        try:
            rc = subprocess.run(
                [c, "-c", "import sys;assert sys.version_info>=%r" % (MIN_PY,)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
            if rc == 0:
                return c
        except OSError:
            pass
    return None


def has_deps(python: str) -> bool:
    code = "import " + ", ".join(REQUIRED)
    return subprocess.run(
        [python, "-c", code],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def deploy(package: str, target: str) -> str:
    """返回状态信息。"""
    if not os.path.isfile(os.path.join(package, "SKILL.md")):
        sys.exit("✗ 安装包不完整：缺少 contract-desensitizer-offline/SKILL.md")
    if os.path.exists(target):
        installed = ""
        bp = os.path.join(target, ".workbuddy-package-build")
        if os.path.isfile(bp):
            with open(bp, encoding="utf-8") as f:
                installed = f.read().strip()
        if installed == BUILD_ID:
            return "同版本技能已存在，跳过复制。"
        if installed in PREV_BUILD_IDS:
            shutil.copytree(package, target, dirs_exist_ok=True)
            with open(bp, "w", encoding="utf-8") as f:
                f.write(BUILD_ID + "\n")
            return "已用本安装包更新上一份本地包；旧版生成的脱敏文件仍需从原件重新生成。"
        sys.exit(f"✗ 目标目录已有另一份技能，未覆盖：{target}")
    shutil.copytree(package, target)
    with open(os.path.join(target, ".workbuddy-package-build"),
              "w", encoding="utf-8") as f:
        f.write(BUILD_ID + "\n")
    return f"WorkBuddy 技能已部署：{target}"


def bootstrap(python: str, target: str) -> None:
    venv = os.path.join(target, "scripts", ".venv")
    vpy = os.path.join(venv, "Scripts", "python.exe")
    req = os.path.join(target, "scripts", "requirements.txt")
    if os.path.isfile(vpy) and has_deps(vpy):
        print("· 依赖环境已就绪，跳过安装。")
        return
    print("· 正在建立独立 Python 环境并安装依赖（首次需联网）…")
    subprocess.run([python, "-m", "venv", venv], check=True)
    subprocess.run([vpy, "-m", "pip", "install", "--quiet", "--upgrade", "pip"],
                  check=False)
    subprocess.run([vpy, "-m", "pip", "install", "--quiet", "-r", req],
                  check=True)


def run_selftests(python: str, target: str) -> None:
    scripts = os.path.join(target, "scripts")
    print("· 正在检查识别与脱敏引擎…")
    subprocess.run([python, os.path.join(scripts, "contract_sensitive_detector.py"),
                    "--selftest", "--quiet"], cwd=scripts, check=True)
    subprocess.run([python, os.path.join(scripts, "contract_redactor.py"),
                    "--selftest"], cwd=scripts, check=True)


DESKTOP_LAUNCHER = r"""@echo off
chcp 65001 >nul
setlocal
set "SKILL=__SKILL_PATH__"
if not exist "%SKILL%\SKILL.md" (
  echo [合同脱敏] 未找到技能，请先运行安装脚本 install_windows.bat
  pause
  exit /b 1
)
set "VENV=%SKILL%\scripts\.venv\Scripts\python.exe"
if exist "%VENV%" (
  "%VENV%" "%SKILL%\scripts\launcher\start.py"
) else (
  where py >nul 2>nul && py "%SKILL%\scripts\launcher\start.py"
  if errorlevel 1 python "%SKILL%\scripts\launcher\start.py"
)
"""


def make_desktop_launcher(desktop: str, target: str) -> str:
    os.makedirs(desktop, exist_ok=True)
    dest = os.path.join(desktop, DESKTOP_APP_NAME)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(DESKTOP_LAUNCHER.replace("__SKILL_PATH__", target.replace("%", "%%").replace("^", "^^")))
    return dest


# 停止脚本只请求本工具服务退出，不按端口结束其他进程。
STOP_BAT_NAME = "停止合同脱敏服务.bat"
STOP_BAT = r"""@echo off
chcp 65001 >nul
setlocal
set "SKILL=__SKILL_PATH__"
set "VENV=%SKILL%\scripts\.venv\Scripts\python.exe"
if not exist "%VENV%" (
  echo 未找到合同脱敏的 Python 环境，请重新安装。
  pause
  exit /b 1
)
"%VENV%" "%SKILL%\scripts\launcher\start.py" --stop
pause
"""


def make_desktop_stop(desktop: str, target: str) -> str:
    os.makedirs(desktop, exist_ok=True)
    dest = os.path.join(desktop, STOP_BAT_NAME)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(STOP_BAT.replace("__SKILL_PATH__", target.replace("%", "%%").replace("^", "^^")))
    return dest


def main() -> int:
    pkg = package_dir()
    tgt = os.path.join(skills_dir(), "contract-desensitizer-offline")
    print("=== 合同脱敏助手 · Windows 安装 ===")
    print(f"· 安装包目录：{pkg}")
    print(f"· 技能部署区：{tgt}")
    print(f"· 桌面目录  ：{desktop_dir()}")

    py = find_python()
    if not py:
        sys.exit("✗ 需要 Python 3.9+。请先安装 Python，或让 WorkBuddy 安装受管 Python 后重试。")
    print(f"· 使用 Python ：{py}")

    msg = deploy(pkg, tgt)
    print("· " + msg)

    bootstrap(py, tgt)

    # 自检用 venv 内的 python
    vpy = os.path.join(tgt, "scripts", ".venv", "Scripts", "python.exe")
    try:
        run_selftests(vpy if os.path.isfile(vpy) else py, tgt)
    except subprocess.CalledProcessError as exc:
        raise SystemExit("✗ 引擎自检未通过，安装未完成。请保留窗口中的错误信息并联系提供安装包的人。") from exc

    dest = make_desktop_launcher(desktop_dir(), tgt)
    print(f"· 桌面入口已创建：{dest}")
    stop = make_desktop_stop(desktop_dir(), tgt)
    print(f"· 桌面停止脚本已创建：{stop}")
    print()
    print("安装完成。双击桌面「合同脱敏（WorkBuddy）.bat」即可启动；")
    print("浏览器会自动打开 http://127.0.0.1:18800/ 。")
    print("文书仅在本机处理，不会上传云端。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
