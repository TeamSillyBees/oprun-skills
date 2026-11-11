# OpRun Skills

让 Agent 连接 OpRun，发现账号已有权限下的项目、读取方案、提出工序修改，或按需求生成方案。

## 一句话接入

把这句话发给你的 Agent：

> 请按照 https://raw.githubusercontent.com/TeamSillyBees/oprun-skills/main/INSTALL.md 安装 OpRun Skill 并配置 MCP 连接，引导我完成登录授权，然后列出我的项目。

Agent 需要支持安装 Skill 和远程 HTTP MCP OAuth。首次登录由你完成，无需填写项目编号。不同宿主可能需要打开 MCP 设置或重新加载会话；具体步骤见 [Agent 安装指南](INSTALL.md)。

## 手动安装

支持 `gh skill install` 的 GitHub CLI 可在目标项目目录执行：

```sh
gh skill install TeamSillyBees/oprun-skills oprun-project-planning@v1.0.0 --agent codex --scope project
```

这一步安装 Skill；继续按 [安装指南](INSTALL.md) 配置 MCP 并登录。其他宿主选择其支持的安装方式。也可下载 [v1.0.0 安装包与校验清单](https://github.com/TeamSillyBees/oprun-skills/releases/tag/v1.0.0)。

## 连接后能做什么

- “列出我的项目，再读取库存项目的当前版本和工序。”
- “为研发工序补充库存查询网页的交付物和验收条件，先给我确认。”
- “根据这些需求生成项目方案、工时和报价。”

连接覆盖个人和企业身份当前已有的项目权限。修改已有工序需要你在 OpRun 确认；生成和补充方案使用所选身份的模型额度。旧的单项目连接需重新授权才能使用账号级能力。

[连接配置](https://www.agi.yifx.vip/mcp/setup) · [授权管理与撤销](https://www.agi.yifx.vip/mcp/manage) · [问题反馈](https://github.com/TeamSillyBees/oprun-skills/issues)

## 维护发布

本仓库分发 Skill、安装说明和公开连接配置。`release.json` 记录版本及对应的 OpRun 源码版本。提交变更后运行：

```sh
python3 tools/package.py --output-dir dist/v1.0.0
```

输出可复现的 ZIP、安装指南、MCP 配置、`manifest.json` 与 `SHA256SUMS`。清单记录本仓库提交、OpRun 源码版本和各文件校验值。为新版本使用新的输出目录和版本标签。
