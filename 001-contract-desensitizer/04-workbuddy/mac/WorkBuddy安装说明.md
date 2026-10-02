# 法务文书脱敏助手 v1.2.3｜WorkBuddy Mac 候选包

本包与 Windows v1.2.3 候选包使用相同识别、复核与导出核心代码。安装包仍需完成本轮发布验收；扫描 PDF 的自动 OCR、手工框选和黑条导出属于下一功能版。

## 发给 WorkBuddy 的指令

把本 ZIP 发给对方，并请对方将下段话连同 ZIP 一起交给 Mac 版 WorkBuddy：

> 请解压我提供的 `合同脱敏-WorkBuddy-Mac-v1.2.3-候选.zip`，进入解压出的 `workbuddy-mac-bundle` 目录，检查其中的 `WorkBuddy安装说明.md`、`install_macos.sh` 和 `contract-desensitizer-offline/SKILL.md`。在 Mac 上运行一次 `bash install_macos.sh`，按脚本输出处理缺失的 Python 或依赖问题。成功后确认技能位于 `~/.workbuddy/skills/contract-desensitizer-offline`，桌面出现“合同脱敏（WorkBuddy）.app”；双击启动并检查 `http://127.0.0.1:18800/health` 返回 200。请不要把我的合同内容上传到云端，也不要修改包内源码。

## 对方日常使用

具体操作见同目录的《产品使用说明.md》。本候选包未附旧版图文 PDF；界面与步骤以当前应用和这份说明为准。

首次安装需要网络下载 Python 依赖。装好后，双击桌面的 **合同脱敏（WorkBuddy）.app**，浏览器会打开 `http://127.0.0.1:18800/`。也可以在 WorkBuddy 中说“帮我把这份合同脱敏”。若 WorkBuddy 尚未识别新技能，重新打开 WorkBuddy 会话。

上传后可选择“合同等文书的内部复核（DOCX / PDF / 文本）”或“诉讼材料发给外部顾问或 AI（仅 DOCX）”。内部复核可处理合同以外的文字文书，但保留原件结构，不作为外发干净副本。诉讼外发审阅目前仅支持 `.docx`：识别到的类型和位置默认已勾选，无需逐类手动选中；可以取消整类或单处。在左右对比页添加漏识别的原文和别名，可选择只用于当前文书，或保存供以后上传的同案文书沿用。后续上传时必须填写完全相同的案件名称；此前已经导出的文件不会自动更新。逐处核对后再生成干净副本。外发模式默认只下载脱敏 DOCX。需要还原时，再单独下载 `mapping.json` 并按原件保管，绝不能一同外发。旧版生成的 DOCX 曾内嵌映射；若要外发，请从原件重新生成。

外发模式会剥离批注、文档属性和自定义 XML；遇到修订、隐藏文字、图片、文本框、外部链接等无法可靠清理的内容会停止导出，需先在 Word 中处理原件再重试。自动识别仍可能漏项，外发前必须人工核对全文。该模式用于发给外部顾问或 AI 审阅，不是法院公开发布模式；目前只完成了合成数据定向测试，完整安全与全量回归仍待验证。

## 包的内容与来源

- `contract-desensitizer-offline/`：WorkBuddy 技能。包含运行脚本和规则说明；合成数据测试保存在 fork 的源码仓中。包内无真实合同、会话文件或虚拟环境。
- `install_macos.sh`：安装技能、独立 Python 环境与桌面入口。若目标位置已有不同版本，会停止而不覆盖。
- `launcher.applescript`：在目标 Mac 本地生成可双击应用；无本机绝对路径。
- `LICENSE`：原仓库 MIT 许可。

基于 [whatcccup/cece_legal_skills](https://github.com/whatcccup/cece_legal_skills) 的 `cd4d86a` 版本，加入本地修复与外发审阅模式。此包不是 GitHub 仓库的官方新版本；单独从 GitHub 克隆当前 `main` 不包含这些本地修改。

运行时仅绑定本机 `127.0.0.1:18800`；安装依赖时需要联网。需要 Python 3.9 或更新版本。
