# WorkBuddy v1.2.3 候选版安装材料源文件

本目录存放 Mac / Windows 安装器、共用 Skill 配置、启动器、说明和**虚构**验收样本。核心检测、脱敏、Web 服务、界面及测试的唯一维护位置是 [`../01-source/`](../01-source/)；制作平台 ZIP 时，将这些核心脚本与测试复制进 `contract-desensitizer-offline/`，再加入本目录对应的 `shared/` 与 `mac/` 或 `windows/` 文件。

本目录本身不是可直接双击安装的包。Mac 安装包可用 [`mac/build_macos_bundle.py`](mac/build_macos_bundle.py) 从固定清单构建；Mac 正式发布范围见 [Mac 发布说明](../02-github/WORKBUDDY-MAC-v1.2.3-RELEASE.md)，Windows 候选状态见 [候选版记录](../02-github/WORKBUDDY-v1.2.3-RC.md)。Mac 旧包另含图文 PDF 说明，其截图尚未更新；新包已排除该 PDF。

`03-skillhub/` 保留原仓发布形态，本 fork 没有把 v1.2.3 发布到 SkillHub。所有真实合同、扫描协议、会话、映射文件、虚拟环境和脱敏结果均不得进入 Git。
