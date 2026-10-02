@echo off
chcp 65001 >nul
setlocal
set "SKILLS=%CONTRACT_DESENSITIZER_SKILLS_DIR%"
if not defined SKILLS set "SKILLS=%USERPROFILE%\.workbuddy\skills"
set "SKILL=%SKILLS%\contract-desensitizer-offline"
set "VENV=%SKILL%\scripts\.venv\Scripts\python.exe"
if not exist "%VENV%" (
  echo 未找到合同脱敏的 Python 环境，请运行安装程序。
  pause
  exit /b 1
)
"%VENV%" "%SKILL%\scripts\launcher\start.py" --stop
pause
