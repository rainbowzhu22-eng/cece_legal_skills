@echo off
setlocal
set "BUNDLE=%~dp0"
set "PY="

REM 优先 WorkBuddy 受管 Python（位于 %USERPROFILE%\.workbuddy\binaries\python\versions）
for /d %%d in ("%USERPROFILE%\.workbuddy\binaries\python\versions\*") do (
  if exist "%%d\python.exe" set "PY=%%d\python.exe"
)
if not defined PY (
  where py >nul 2>nul && set "PY=py"
)
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo 需要 Python 3.9+。请先安装 Python，或让 WorkBuddy 安装受管 Python 后重试。
  pause
  exit /b 1
)

"%PY%" "%BUNDLE%install_windows.py"
if errorlevel 1 pause
