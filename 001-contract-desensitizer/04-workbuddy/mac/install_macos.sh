#!/bin/bash
# 在当前 Mac 安装合同脱敏 WorkBuddy 技能，并生成桌面双击入口。
set -euo pipefail

if [ "$(uname -s)" != "Darwin" ]; then
  echo "仅支持 macOS。" >&2
  exit 1
fi

bundle_dir="$(cd "$(dirname "$0")" && pwd)"
package_dir="$bundle_dir/contract-desensitizer-offline"
skills_dir="${CONTRACT_DESENSITIZER_SKILLS_DIR:-$HOME/.workbuddy/skills}"
target_dir="$skills_dir/contract-desensitizer-offline"
desktop_dir="${CONTRACT_DESENSITIZER_DESKTOP_DIR:-$HOME/Desktop}"
desktop_app="$desktop_dir/合同脱敏（WorkBuddy）.app"
build_id="contract-desensitizer-v1.2.3-20261002"
previous_build_id="github-cd4d86a-pdf-text-check-20260929"
older_build_id="github-cd4d86a-litigation-review-ux-20260927"
oldest_build_id="github-cd4d86a-litigation-review-20260926"
legacy_build_id="github-cd4d86a-english-org-no-embedded-20260926"
first_build_id="github-cd4d86a-english-org-20260926"

if [ ! -f "$package_dir/SKILL.md" ]; then
  echo "安装包不完整：缺少 contract-desensitizer-offline/SKILL.md。" >&2
  exit 1
fi

python_bin=""
for name in python3.13 python3.12 python3.11 python3.10 python3; do
  candidate="$(command -v "$name" 2>/dev/null || true)"
  if [ -n "$candidate" ] && "$candidate" -c 'import sys; assert sys.version_info >= (3, 9)' 2>/dev/null; then
    python_bin="$candidate"
    break
  fi
done
if [ -z "$python_bin" ]; then
  echo "需要 Python 3.9 或更新版本。请让 WorkBuddy 先安装 Python，然后重新运行此脚本。" >&2
  exit 1
fi

mkdir -p "$skills_dir" "$desktop_dir"
if [ -e "$target_dir" ]; then
  installed_build="$(cat "$target_dir/.workbuddy-package-build" 2>/dev/null || true)"
  if [ "$installed_build" = "$previous_build_id" ] || [ "$installed_build" = "$older_build_id" ] || [ "$installed_build" = "$oldest_build_id" ] || [ "$installed_build" = "$legacy_build_id" ] || [ "$installed_build" = "$first_build_id" ]; then
    /usr/bin/ditto "$package_dir" "$target_dir"
    printf '%s\n' "$build_id" > "$target_dir/.workbuddy-package-build"
    echo "已更新上一份 WorkBuddy 本地包；旧版生成的脱敏文件仍需从原件重新生成。"
  elif [ "$installed_build" != "$build_id" ]; then
    echo "目标目录已有另一份技能，未覆盖：$target_dir" >&2
    exit 1
  else
    echo "同版本技能已安装。"
  fi
else
  staging_dir="$(mktemp -d "$skills_dir/.contract-desensitizer-offline.XXXXXX")"
  /usr/bin/ditto "$package_dir" "$staging_dir"
  printf '%s\n' "$build_id" > "$staging_dir/.workbuddy-package-build"
  mv "$staging_dir" "$target_dir"
  echo "WorkBuddy 技能已安装：$target_dir"
fi

venv_python="$target_dir/scripts/.venv/bin/python"
if [ ! -x "$venv_python" ] ||
   ! "$venv_python" -c 'import docx, pdfplumber, pypdf, reportlab, pypdfium2, PIL' 2>/dev/null; then
  echo "正在建立独立 Python 环境并安装依赖（首次需要联网）…"
  "$python_bin" -m venv "$target_dir/scripts/.venv"
  "$venv_python" -m pip install \
    --disable-pip-version-check --quiet -r "$target_dir/scripts/requirements.txt"
fi

echo "正在检查识别和脱敏引擎…"
"$venv_python" "$target_dir/scripts/contract_sensitive_detector.py" --selftest --quiet
"$venv_python" "$target_dir/scripts/contract_redactor.py" --selftest >/dev/null

if [ -e "$desktop_app" ]; then
  echo "桌面入口已存在，未覆盖：$desktop_app"
else
  temp_script="$(mktemp "${TMPDIR:-/tmp}/contract-launcher.XXXXXX")"
  "$python_bin" - "$bundle_dir/launcher.applescript" "$target_dir/scripts/" "$temp_script" <<'PY'
import sys
from pathlib import Path
template = Path(sys.argv[1]).read_text(encoding="utf-8")
path = sys.argv[2].replace("\\", "\\\\").replace('"', '\\"')
Path(sys.argv[3]).write_text(template.replace("__SCRIPTS_PATH__", path), encoding="utf-8")
PY
  /usr/bin/osacompile -o "$desktop_app" "$temp_script" >/dev/null
  rm -f "$temp_script"
  echo "桌面入口已创建：$desktop_app"
fi
echo "安装完成。双击桌面应用，或对 WorkBuddy 说：帮我把合同脱敏。"
