# OpRun Skills

## 一句话接入

把这句话发给你的 Agent：

> 请按 https://raw.githubusercontent.com/TeamSillyBees/oprun-skills/main/INSTALL.md 接入 OpRun，带我完成登录。

Agent 需要支持安装 Skill 和远程 HTTP MCP OAuth。首次登录由你完成，无需填写项目编号。不同宿主可能需要打开 MCP 设置或重新加载会话；具体步骤见 [Agent 安装指南](INSTALL.md)。

WorkBuddy 安装 Skill 后还需添加 MCP 连接器并授权，具体见随包的 [接入指引](skills/oprun-project-planning/references/workbuddy.md) 和 [连接配置](skills/oprun-project-planning/assets/workbuddy-mcp.json)。已安装 Skill 时，直接说“连接 OpRun，带我完成登录”。

QVeris Studio 使用 [专用接入指引](skills/oprun-project-planning/references/qveris.md) 和 [连接配置](skills/oprun-project-planning/assets/qveris-mcp.json)，显式指定 OAuth、`/mcp` 授权地址及业务 Scope。提供[方案](skills/oprun-project-planning/assets/qveris-mcp.json)、[接单](skills/oprun-project-planning/assets/qveris-worker-mcp.json)、[发单](skills/oprun-project-planning/assets/qveris-publisher-mcp.json)三套配置。方案授权不含匹配；需要接单或发单时按[匹配指引](skills/oprun-project-planning/references/matching.md)重新授权。已保存的连接不会随 Skill 更新自动改变。

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

Skill 内容的唯一来源是 OpRun 仓库的 `integrations/agent-skills/oprun-project-planning`，与服务端协议同仓维护，并由 OpRun MCP 以资源形式提供。**不要直接修改本仓库的 `skills/`**；修改先合入 OpRun `main`，再同步到这里。本仓库只维护安装说明、通用连接示例、同步和打包工具。

1. 在 OpRun 本地克隆中拉取最新 `main`，然后在本仓库运行（默认 `origin/main`，拒绝未合入 main 的提交）：

   ```sh
   python3 tools/sync.py --oprun ../oprun
   ```

   脚本按来源提交完整替换 `skills/oprun-project-planning/`，删除上游已移除的文件，并把来源提交写入 `release.json` 的 `oprun_revision`。核对差异后更新 `version`。

2. 运行 `python3 -m unittest discover -s tests` 和 `python3 tools/sync.py --oprun ../oprun --check`，确认 `skills/` 与记录的来源提交完全一致。

3. 提交并推送后打包。独立 INSTALL.md 链接到该提交，未推送时脚本拒绝打包；仅本地试打包可加 `--allow-unpushed`：

   ```sh
   python3 tools/package.py --output-dir dist/v<版本>
   ```

输出可复现的 ZIP、安装指南、通用及各宿主 MCP 配置（Skill 中的 `assets/*-mcp.json`）、`manifest.json` 与 `SHA256SUMS`。ZIP 即同步来的完整 Skill 目录；清单的 `skill_files` 列出每个成员的校验值，`oprun_revision` 是 Skill 来源提交，不代表线上当前版本。为新版本使用新的输出目录和版本标签；源码更新与 Release 发布分开执行，不覆盖旧资产。
