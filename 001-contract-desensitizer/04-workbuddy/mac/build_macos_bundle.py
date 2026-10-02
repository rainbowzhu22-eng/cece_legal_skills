#!/usr/bin/env python3
"""Build the reviewed WorkBuddy Mac candidate from source files only."""

import argparse
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "01-source"
WORKBUDDY = ROOT / "04-workbuddy"
PREFIX = Path("workbuddy-mac-bundle")

FILES = {
    ROOT.parent / "LICENSE": PREFIX / "LICENSE",
    WORKBUDDY / "mac/WorkBuddy安装说明.md": PREFIX / "WorkBuddy安装说明.md",
    WORKBUDDY / "mac/产品使用说明.md": PREFIX / "产品使用说明.md",
    WORKBUDDY / "mac/install_macos.sh": PREFIX / "install_macos.sh",
    WORKBUDDY / "mac/launcher.applescript": PREFIX / "launcher.applescript",
    WORKBUDDY / "shared/SKILL.md": PREFIX / "contract-desensitizer-offline/SKILL.md",
    WORKBUDDY / "shared/references/使用说明.md": PREFIX / "contract-desensitizer-offline/references/使用说明.md",
    WORKBUDDY / "shared/references/脱敏规则清单.md": PREFIX / "contract-desensitizer-offline/references/脱敏规则清单.md",
    WORKBUDDY / "shared/scripts/launcher/README.md": PREFIX / "contract-desensitizer-offline/scripts/launcher/README.md",
    WORKBUDDY / "shared/scripts/launcher/start.py": PREFIX / "contract-desensitizer-offline/scripts/launcher/start.py",
    SOURCE / "requirements.txt": PREFIX / "contract-desensitizer-offline/scripts/requirements.txt",
}
for name in (
    "contract_app_server.py",
    "contract_app_ui.py",
    "contract_redactor.py",
    "contract_review_ext.py",
    "contract_sensitive_detector.py",
):
    FILES[SOURCE / name] = PREFIX / "contract-desensitizer-offline/scripts" / name


def build(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    for source in FILES:
        if not source.is_file():
            raise FileNotFoundError(source)
    with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for source, destination in sorted(FILES.items(), key=lambda item: str(item[1])):
            archive.write(source, str(destination))
    with ZipFile(output) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP integrity check failed: {bad}")
        if set(archive.namelist()) != {str(path) for path in FILES.values()}:
            raise RuntimeError("ZIP manifest mismatch")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"{output}\nfiles={len(FILES)}\nsha256={digest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    build(parser.parse_args().output)
