# OpRun Skills

## 一句话接入

把这句话发给你的 Agent：

> 请按 https://raw.githubusercontent.com/TeamSillyBees/oprun-skills/main/INSTALL.md 接入 OpRun，带我完成登录。

Agent 需要支持安装 Skill 和远程 HTTP MCP OAuth。首次登录由你完成，无需填写项目编号。不同宿主可能需要打开 MCP 设置或重新加载会话；具体步骤见 [Agent 安装指南](INSTALL.md)。

WorkBuddy 安装 Skill 后还需添加 MCP 连接器并授权，具体见随包的 [接入指引](skills/oprun-project-planning/references/workbuddy.md) 和 [连接配置](skills/oprun-project-planning/assets/workbuddy-mcp.json)。已安装 Skill 时，直接说“连接 OpRun，带我完成登录”。

多宿主配置与新旧服务端兼容方式见[多宿主接入指引](skills/oprun-project-planning/references/hosts.md)。Skill 可以先更新；WorkBuddy 原生回调、受管公共客户端和 CIMD 仍取决于目标服务端是否支持并启用。

## 手动安装

支持 `gh skill install` 的 GitHub CLI 可在目标项目目录执行：

```sh
gh skill install TeamSillyBees/oprun-skills oprun-project-planning@main --agent codex --scope project
```

这一步安装当前源码中的 Skill；继续按 [安装指南](INSTALL.md) 配置 MCP 并登录。其他宿主选择其支持的安装方式。需要固定版本时选用 [Releases](https://github.com/TeamSillyBees/oprun-skills/releases) 中已发布的标签，或核实过的完整提交。v1.0.1 包含完整 WorkBuddy 接入资源；旧 v1.0.0 包只含 Skill 正文。

## 连接后能做什么

登录并验证连接后，Agent 会在回复末尾按你的实际权限给出操作引导。选择后再执行，例如：

- “列出我的项目，再读取库存项目的当前版本和工序。”
- “为研发工序补充库存查询网页的交付物和验收条件，先给我确认。”
- “根据这些需求生成项目方案、工时和报价。”

连接覆盖个人和企业身份当前已有的项目权限。修改已有工序需要你在 OpRun 确认；生成和补充方案使用所选身份的模型额度。旧的单项目连接需重新授权才能使用账号级能力。

[连接配置](https://www.agi.yifx.vip/mcp/setup) · [授权管理与撤销](https://www.agi.yifx.vip/mcp/manage) · [问题反馈](https://github.com/TeamSillyBees/oprun-skills/issues)

## 维护发布

本仓库分发 Skill、安装说明和公开连接配置。`release.json` 记录版本及文档参考的 OpRun 源码版本，不代表生产已发布。提交变更后运行：

```sh
python3 tools/package.py --output-dir dist/v1.0.2
```

输出可复现的 ZIP、安装指南、通用及 WorkBuddy MCP 配置、`manifest.json` 与 `SHA256SUMS`。v1.0.2 ZIP 包含 Skill 正文、多宿主及 WorkBuddy 接入指引和配置。清单记录本仓库提交、OpRun 源码参考和各文件校验值；`oprun_revision` 不代表线上当前版本。为新版本使用新的输出目录和版本标签，发布前运行 `python3 -m unittest discover -s tests`。源码更新与 Release 发布分开执行，不覆盖旧资产。
