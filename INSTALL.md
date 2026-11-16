# 给 Agent 的 OpRun 安装指南

用户要求接入 OpRun 时，按本指南安装并验证。当前源码版本见仓库根目录的 `release.json`（发布包见 `manifest.json`），是否已有发布包以 [GitHub Releases](https://github.com/TeamSillyBees/oprun-skills/releases) 为准。Skill 为 `oprun-project-planning`，服务地址为 `https://www.agi.yifx.vip/mcp`。用户明确提供其他 OpRun 站点时，使用该站点的 `/mcp`。

**WorkBuddy：安装 Skill 不会自动创建 MCP 连接器。** 从 GitHub 安装后要求“连接 OpRun”，应继续执行 [Skill 随包的 WorkBuddy 接入指引](skills/oprun-project-planning/references/workbuddy.md)，添加连接并启动 OAuth；不要把“Skill 已安装”报告为“已连接”。

**QVeris Studio：** 使用 [专用配置](skills/oprun-project-planning/assets/qveris-mcp.json) 和 [接入指引](skills/oprun-project-planning/references/qveris.md)。不要直接导入通用 `mcp.json`；1.0.22 需要显式指定 OAuth、`/mcp` issuer 和业务 Scope。

**服务端能力核对：** Skill 可先安装，连接仍以目标站点当前能力为准。先读[多宿主接入指引](skills/oprun-project-planning/references/hosts.md)；没有 `profiles` 时保留宿主原生配置，没有 CIMD 能力声明时保留 DCR。原生回调和受管公共客户端需服务端部署对应修复，不能通过更新 Skill 或手填客户端 ID 启用。

## 1. 检查宿主和现有连接

确认当前宿主支持 Skill、Streamable HTTP MCP、OAuth 与 S256 PKCE；客户端注册默认用动态注册（DCR），其他方式仅在目标站点元数据声明支持时使用，见[多宿主接入指引](skills/oprun-project-planning/references/hosts.md)。读取宿主原生安装方式和现有 `oprun` 配置；URL 相同则复用。已有同名连接指向其他站点或 Skill 存在本地修改时，先说明冲突，不覆盖用户配置。

默认安装到当前项目；用户要求全局安装时才选择用户范围。权限受限时准备好可执行配置，并说明所需的最小手动操作。不要把某一种宿主的配置格式套用到所有 Agent。

## 2. 安装 Skill

若本机 `gh skill install --help` 可用，可使用原生安装器。以 Codex 为例，在目标项目的 Git 仓库内执行：

```sh
gh skill install TeamSillyBees/oprun-skills oprun-project-planning@main --agent codex --scope project
```

`main` 安装当前源码；需要固定版本时，将它替换为 Releases 中实际存在的标签或核实过的完整提交。其他宿主先从本机帮助确认 `--agent` 值。不要加 `--force` 覆盖已有内容。安装完成后检查宿主能发现 `oprun-project-planning`。[GitHub CLI 安装说明](https://cli.github.com/manual/gh_skill_install)

无此命令时，从已发布的 Release 下载 `oprun-project-planning.zip`、`manifest.json` 和 `SHA256SUMS`，验证 ZIP 的 SHA-256 与两份清单一致。ZIP 成员必须与 `manifest.json` 的 `skill_files` 完全一致（同名、同 SHA-256，均位于 `oprun-project-planning/` 下，无绝对路径或 `..`）；核对后完整解压到宿主支持的 Skill 目录。当前版本尚未发布时，从核实过的仓库提交安装完整 Skill 目录。旧包不会启用新增的服务端能力；已连接的 OpRun 也可通过 MCP 资源 `oprun://integration/manifest` 核对线上 Skill 版本。

Codex 项目目录为 `.agents/skills/`。保持目录结构为 `.agents/skills/oprun-project-planning/SKILL.md`。若已存在则先比较，不混合覆盖；完全相同可直接复用。若宿主尚未发现 Skill，按其要求重新加载或打开新会话。[Codex Skill 说明](https://developers.openai.com/codex/skills/)

## 3. 配置 MCP 并由用户登录

**添加连接前先确认授权范围。** 方案连接申请 `plan:read`、`plan:propose`、`plan:generate`，涵盖账号各身份已有的项目权限，无需填写项目编号；用户明确只读时只申请 `plan:read`；接单或发单按[匹配指引](skills/oprun-project-planning/references/matching.md)选择范围。部分宿主（如 Codex）在添加连接时就会开始标准授权，所以要在添加前问清楚。

使用宿主的原生 MCP 配置，连接名为 `oprun`，传输方式为远程 HTTP，URL 为 `https://www.agi.yifx.vip/mcp`，认证为 OAuth。[mcp.json](mcp.json) 是常用 HTTP 示例；也可从 [线上配置端点](https://www.agi.yifx.vip/mcp/setup) 获取 `mcp_json`。WorkBuddy 连接器导入使用 [workbuddy-mcp.json](skills/oprun-project-planning/assets/workbuddy-mcp.json)，保存后点击该连接器的“连接”。QVeris Studio 导入 [qveris-mcp.json](skills/oprun-project-planning/assets/qveris-mcp.json)，核对认证方式、授权服务地址和 Scope 后点击“保存并授权”。不同入口的字段遵循宿主帮助，不跨宿主套用命令或配置。

Codex CLI 示例：

```sh
codex mcp add oprun --url https://www.agi.yifx.vip/mcp --oauth-resource https://www.agi.yifx.vip/mcp
```

当前 Codex 会在添加连接时开始 OAuth。按终端指引让用户在浏览器中登录并核对授权。如果宿主无法自动打开浏览器，向用户展示宿主生成的登录链接。不要把授权链接、验证码、令牌写入项目文件或公开日志；凭据交给宿主保存。

Codex 添加命令完成标准授权后，无需再执行 `codex mcp login`。用户只要只读时，添加后在授权页取消标准授权，再以只读范围登录：

```sh
codex mcp login oprun --scopes plan:read
```

只有添加时授权未完成（被取消、超时或浏览器未回跳）才再执行 `codex mcp login oprun`。已有授权不会因为安装 Skill 自动扩权。[Codex MCP 说明](https://developers.openai.com/codex/mcp/)

登录需要用户本人操作。不要索取密码或 Token，不从用户其他浏览器提取登录态。用户不在场时可完成安装与配置，明确标记“等待登录授权”。

## 接单与发单授权

Qveris 按任务选择：[方案配置](skills/oprun-project-planning/assets/qveris-mcp.json)、[接单配置](skills/oprun-project-planning/assets/qveris-worker-mcp.json)、[发单配置](skills/oprun-project-planning/assets/qveris-publisher-mcp.json)。其他宿主采用相同 Scope，配置格式仍以宿主为准。默认方案授权没有匹配工具；按[匹配操作指引](skills/oprun-project-planning/references/matching.md)核对能力并重新授权，不反复重装 Skill。已有且仍需要的能力保留。

## 4. 验证连接

1. 检查宿主已加载 Skill 和 MCP 连接，必要时让用户重新加载会话。
2. 使用 MCP `tools/list`，确认实际可用工具；只检查配置文件不能证明连接成功。
3. 调用 `oprun_account_context` 验证真实只读访问，取得本次授权范围与各身份的可用能力。用户只要求接入时，不继续查询项目或读取方案；用户已经提出业务任务时，验证成功后继续原任务。
4. 依据各身份的 `unavailable_reason` 说明需要完成的操作，其余可用身份仍可使用。若只出现旧版无参数的 `oprun_read_plan`，说明是单项目旧连接，引导重新授权。

安装验收只读取账号上下文。用户随后选择查看项目时再查询列表，需要查看具体方案时再调用 `oprun_read_plan`；修改或生成方案遵循 Skill 的确认和幂等规则。

## 5. 报告结果

登录或验证未完成时，只说明当前状态和下一步。未完成 OAuth 或工具不可调用时，不报告接入成功。需要排查时再补充版本、安装位置和站点。

验证成功后，按 [Skill 的连接收尾规则](skills/oprun-project-planning/SKILL.md) 简短确认连接，并在回复末尾按实际权限给出可用操作，等待用户选择。用户原请求已包含业务任务时，继续原任务并报告结果，不重复询问。接入提示中无需列入这些后续操作。

用户可在 [OpRun 授权管理](https://www.agi.yifx.vip/mcp/manage) 撤销连接。服务端支持刷新时由宿主续期；`invalid_grant` 时重新授权，`invalid_client` 时通过宿主重建此 OpRun 客户端注册再授权。不要删除其他连接。权限变化或旧连接仍限单项目时，使用宿主原生登录流程重新授权。
