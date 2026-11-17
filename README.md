# OpRun Skills

安装或更新，把这句话发给你的 Agent：

> 请按 https://github.com/TeamSillyBees/oprun-skills/blob/main/INSTALL.md 安装或更新 OpRun，带我完成连接。

[下载安装包](https://github.com/TeamSillyBees/oprun-skills/releases/latest/download/oprun-project-planning.zip) · [安装与排错](INSTALL.md)

支持 Skill 和 MCP OAuth 的客户端可按指引完成安装及连接检查，首次登录授权由你完成。Qveris 1.0.22 的当前研究会话可读取指引和检查连接，但不能执行安装程序；实际安装及更新使用“添加技能 → 上传 ZIP”，随后在对话中选择 Skill 并启用 oprun。Qveris、WorkBuddy 若不能自动添加连接，导入对应配置后点击授权即可。一个连接支持方案、发单、接单和交付，能力随当前身份及授权确定。

安装工具只处理 Skill 和公开配置，不保存密码或 Token，不自动扩大已有授权。更新校验正式版本、保留恢复目录，遇到本地修改停止覆盖。

## 连接后能做什么

登录并验证连接后，Agent 会在回复末尾按你的实际权限给出操作引导。选择后再执行，例如：

- “列出我的项目，再读取库存项目的当前版本和工序。”
- “为研发工序补充库存查询网页的交付物和验收条件，先给我确认。”
- “根据这些需求生成项目方案、工时和报价。”

连接覆盖个人和企业身份当前已有的项目权限。修改已有工序需要你在 OpRun 确认；生成和补充方案使用所选身份的模型额度。旧的单项目连接需重新授权才能使用账号级能力。

[连接配置](https://www.agi.yifx.vip/mcp/setup) · [授权管理与撤销](https://www.agi.yifx.vip/mcp/manage) · [问题反馈](https://github.com/TeamSillyBees/oprun-skills/issues)

## 维护发布

Skill 内容的唯一来源是 oprun-mcp 仓库的 `skills/oprun-project-planning`，与服务端协议同仓维护，并由 OpRun MCP 以资源形式提供。**不要直接修改本仓库的 `skills/`**；修改先合入 oprun-mcp `main`，再同步到这里。本仓库只维护安装说明、通用连接示例、同步和打包工具。

1. 在 oprun-mcp 本地克隆中拉取最新 `main`，然后在本仓库运行（默认 `origin/main`，拒绝未合入 main 的提交）：

   ```sh
   python3 tools/sync.py --oprun-mcp ../oprun-mcp
   ```

   脚本按来源提交完整替换 `skills/oprun-project-planning/`，删除上游已移除的文件，并把来源提交写入 `release.json` 的 `mcp_revision`。核对差异后更新 `version`。

2. 运行 `python3 -m unittest discover -s tests` 和 `python3 tools/sync.py --oprun-mcp ../oprun-mcp --check`，确认 `skills/` 与记录的来源提交完全一致。

3. 提交并推送后打包。独立 INSTALL.md 链接到该提交，未推送时脚本拒绝打包；仅本地试打包可加 `--allow-unpushed`：

   ```sh
   python3 tools/package.py --output-dir dist/v<版本>
   ```

发布资产时先创建绑定完整提交的空草稿，再运行 `python3 tools/upload_assets.py --directory dist/v<版本> --tag v<版本>`；核对下载后再正式发布。安装说明以 `text/plain` 上传，但 GitHub 下载层仍可能返回二进制类型；一句话接入使用仓库网页说明，下载入口仅供包管理工具使用。不覆盖既有正式资产。

输出可复现的 ZIP、安装指南、安装工具 `install.py`、通用及各宿主 MCP 配置（Skill 中的 `assets/*-mcp.json`）、`manifest.json` 与 `SHA256SUMS`。ZIP 即同步来的完整 Skill 目录；清单的 `skill_files` 列出每个成员的校验值，`mcp_revision` 是 Skill 来源提交，不代表线上当前版本。为新版本使用新的输出目录和版本标签；源码更新与 Release 发布分开执行，不覆盖旧资产。

Skill 的唯一维护源迁到 [oprun-mcp](https://github.com/TeamSillyBees/oprun-mcp)。此仓库只分发固定提交；原 PR #17 的工序与文件说明由本次同步一并纳入，不需要分别建立发单和接单连接。
