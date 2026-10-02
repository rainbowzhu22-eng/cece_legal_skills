# WorkBuddy Mac / Windows v1.2.3 候选版发布准备

**状态：仅供审阅的候选分支；未创建 GitHub Release，未发布 SkillHub，现有 ZIP 不可公开上传。** 建议候选标签 `v1.2.3-rc.1`，待文档脱敏重建、Windows 实机与最终质量门槛通过后再决定正式版本。

## 来源与范围

- 上游：[whatcccup/cece_legal_skills](https://github.com/whatcccup/cece_legal_skills)，基线提交 `cd4d86a46adc0b4f676e8ee356fd26651cebff48`；本 fork 保留原仓 Git 历史与 MIT 许可。
- fork：[`rainbowzhu22-eng/cece_legal_skills`](https://github.com/rainbowzhu22-eng/cece_legal_skills)。上游当前目录是 `001-contract-desensitizer/`；历史链接中的 `contract_desensitizer/` 已迁移。
- `01-source/` 是 v1.2.3 核心代码；`04-workbuddy/` 提供两平台安装材料。`03-skillhub/` 仍是原有发布版本，不能标称已同步。
- v1.2.3 处理可可靠提取文字的 DOCX、PDF、TXT、MD；外发顾问或 AI 的干净副本目前仅支持 DOCX。扫描或混合 PDF 缺可靠文字层时明确阻断。OCR、页面框选和黑条 PDF 在 v1.3.0 规划中，**不包含在本候选版**。

## 本次变化

- Mac / Windows 采用相同的识别、复核、改写、历史记录和启动器代码。加强机构全称与简称、地址、金额表格、分段号码及 DOCX 位置映射。
- 复核页默认勾选候选，支持取消整类或单处、补录原文与别名、选择仅本文或同案后续文书沿用。
- 历史记录在本机服务重启后仍可查看、下载和删除；服务只监听本机地址，并拒绝不可信来源的写请求。
- 启动器只优雅停止确认属于本工具的旧服务；Windows 后台进程脱离启动控制台。安装自检失败会中止安装。
- 修复同会话还原误用上传时旧映射的问题；还原以本次导出的映射为准，手工补录字段能够回填。

## 候选资产与公开前处理

| 文件 | SHA-256 | 状态 |
| --- | --- | --- |
| 新 `合同脱敏-WorkBuddy-Mac-v1.2.3-候选.zip` | `44c4ffded3eebad3587b2fa637bcbef82c09383a526fb32ec6c549345dd6b9dd` | 已从修正后的源码重建；不含旧截图 PDF、真实文书、会话及缓存。可供 Mac 候选验收，尚非正式 Release |
| 旧 `合同脱敏-WorkBuddy-Mac-v1.2.3-候选.zip` | `87ef1b90185a055516d2266da6b49a51c2fee589032182fa86a85dc8456cc77a` | 旧说明含用户截图中的主体示例；仅作内部历史校验，不可公开上传 |
| `合同脱敏-WorkBuddy-Windows-v1.2.3-候选.zip` | `b77b1955431bedd608ba2e70493a547265c07f08cb76210a46dcc50c71f1ad8d` | 同上，且 Windows 实机尚未验收；不可公开上传 |
| 新 Windows ZIP | 待重建后填写 | 仅在内容检查和相应验收完成后附加到 Release |

ZIP 不进入 Git 历史。公开 fork 的文字说明已把来自用户截图的主体名称换为虚构示例，并纠正“映射内嵌”的过期说法。新 Mac ZIP 由 [`build_macos_bundle.py`](../04-workbuddy/mac/build_macos_bundle.py) 固定清单构建，仅含 16 个安装必需文件。7 个运行脚本与先前实测的 Mac 候选包逐字节一致；安装脚本语法、Python 语法、ZIP 完整性及敏感示例关键字均已检查。旧 Windows ZIP 仍含旧文档，尚不可公开上传。Windows ZIP 内含逐步[实机验收指引](../04-workbuddy/windows/Windows-v1.2.3-实机验收指引.md)及三份虚构样本；旧 Mac ZIP 的图文 PDF 截图未更新且未完成公开内容检查，因此新包未收入该 PDF。

## 已有证据与待完成门槛

- 已完成：两个 ZIP 的完整性、共用脚本逐字节一致、版本号与安装构建号、排除虚拟环境/会话/缓存检查；Mac 正式 WorkBuddy 技能目录安装、技能列表启用、桌面入口启动；真实 6 页盖章扫描协议与混合 PDF 均安全阻断；虚构 DOCX 补录、导出、还原及重启后历史；相关定向回归。
- 待完成：重建 Windows ZIP 并完成内容检查；真实 Windows WorkBuddy 安装和全链路验收；真实文字型法律文书的逐处识别准确性核对；浏览器全矩阵及最终全量回归。完成前不得称“正式发布”或承诺扫描 PDF 脱敏。

## 发布动作（当前均未执行）

1. 完成公开内容检查与上述待验收项并记录结论；从已核定的材料重新构建、重算 SHA-256。
2. 从本候选分支的已验证提交创建标签；GitHub Release 附加 Mac ZIP、Windows ZIP、SHA-256 清单，说明平台差异与已知限制。
3. 只有确认 SkillHub 发布范围、版本和打包规则后，才单独更新 `03-skillhub/` 并发布；本次 GitHub fork 准备不代表 SkillHub 更新。
