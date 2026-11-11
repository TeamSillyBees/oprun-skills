# 给 Agent 的 OpRun 安装指南

用户要求接入 OpRun 时，按本指南安装并验证。当前源码版本为 **v1.0.1**，是否已有发布包以 [GitHub Releases](https://github.com/TeamSillyBees/oprun-skills/releases) 为准。Skill 为 `oprun-project-planning`，服务地址为 `https://www.agi.yifx.vip/mcp`。用户明确提供其他 OpRun 站点时，使用该站点的 `/mcp`。

**WorkBuddy：安装 Skill 不会自动创建 MCP 连接器。** 从 GitHub 安装后要求“连接 OpRun”，应继续执行 [Skill 随包的 WorkBuddy 接入指引](skills/oprun-project-planning/references/workbuddy.md)，添加连接并启动 OAuth；不要把“Skill 已安装”报告为“已连接”。

## 1. 检查宿主和现有连接

确认当前宿主支持 Skill、Streamable HTTP MCP、OAuth 动态客户端注册与 S256 PKCE。读取宿主原生安装方式和现有 `oprun` 配置；URL 相同则复用。已有同名连接指向其他站点或 Skill 存在本地修改时，先说明冲突，不覆盖用户配置。

默认安装到当前项目；用户要求全局安装时才选择用户范围。权限受限时准备好可执行配置，并说明所需的最小手动操作。不要把某一种宿主的配置格式套用到所有 Agent。

## 2. 安装 Skill

若本机 `gh skill install --help` 可用，可使用原生安装器。以 Codex 为例，在目标项目的 Git 仓库内执行：

```sh
gh skill install TeamSillyBees/oprun-skills oprun-project-planning@main --agent codex --scope project
```

`main` 安装当前源码；需要固定版本时，将它替换为 Releases 中实际存在的标签或核实过的完整提交。其他宿主先从本机帮助确认 `--agent` 值。不要加 `--force` 覆盖已有内容。安装完成后检查宿主能发现 `oprun-project-planning`。[GitHub CLI 安装说明](https://cli.github.com/manual/gh_skill_install)

无此命令时，从已发布的 Release 下载 `oprun-project-planning.zip`、`manifest.json` 和 `SHA256SUMS`，验证 ZIP 的 SHA-256 与两份清单一致。v1.0.1 的 ZIP 应包含且仅包含 `oprun-project-planning/SKILL.md`、`oprun-project-planning/references/workbuddy.md` 和 `oprun-project-planning/assets/workbuddy-mcp.json`；检查成员路径后完整解压到宿主支持的 Skill 目录。若 v1.0.1 尚未发布，从核实过的仓库提交安装完整 Skill 目录。旧 v1.0.0 包只含 Skill 正文，缺少此次接入指引，不能视作已升级。

Codex 项目目录为 `.agents/skills/`。保持目录结构为 `.agents/skills/oprun-project-planning/SKILL.md`。若已存在则先比较，不混合覆盖；完全相同可直接复用。若宿主尚未发现 Skill，按其要求重新加载或打开新会话。[Codex Skill 说明](https://developers.openai.com/codex/skills/)

## 3. 配置 MCP 并由用户登录

使用宿主的原生 MCP 配置，连接名为 `oprun`，传输方式为远程 HTTP，URL 为 `https://www.agi.yifx.vip/mcp`，认证为 OAuth。[mcp.json](mcp.json) 是常用 HTTP 示例；也可从 [线上配置端点](https://www.agi.yifx.vip/mcp/setup) 获取 `mcp_json`。WorkBuddy 连接器导入使用 [workbuddy-mcp.json](skills/oprun-project-planning/assets/workbuddy-mcp.json)，保存后点击该连接器的“连接”。不同入口的类型字段遵循宿主帮助，不把 Codex 命令用于 WorkBuddy。

Codex CLI 示例：

```sh
codex mcp add oprun --url https://www.agi.yifx.vip/mcp --oauth-resource https://www.agi.yifx.vip/mcp
```

当前 Codex 会在添加连接时开始 OAuth。按终端指引让用户在浏览器中登录并核对授权。如果宿主无法自动打开浏览器，向用户展示宿主生成的登录链接。不要把授权链接、验证码、令牌写入项目文件或公开日志；凭据交给宿主保存。

标准连接申请 `plan:read`、`plan:propose`、`plan:generate`，涵盖账号各身份已有的项目权限，无需填写项目编号。用户明确只读时，只申请和同意 `plan:read`；Codex 对已配置的连接可使用：

```sh
codex mcp login oprun --scopes plan:read
```

如果添加连接时已进入标准授权页但用户只要只读，先取消该次授权，再执行上述只读登录命令。已有授权不会因为安装 Skill 自动扩权。[Codex MCP 说明](https://developers.openai.com/codex/mcp/)

登录需要用户本人操作。不要索取密码或 Token，不从用户其他浏览器提取登录态。用户不在场时可完成安装与配置，明确标记“等待登录授权”。

## 4. 验证连接

1. 检查宿主已加载 Skill 和 MCP 连接，必要时让用户重新加载会话。
2. 使用 MCP `tools/list`，确认实际可用工具；只检查配置文件不能证明连接成功。
3. 调用 `oprun_account_context`，再调用 `oprun_list_projects`，沿 `next_cursor` 读取完整列表。按名称和所属身份展示项目，不要求用户猜项目编号。空列表也是有效结果。
4. 若返回 `unavailable_subjects`，说明哪些身份需要先在 OpRun 确认 AI 服务授权，其余身份可继续使用。若只出现旧版无参数的 `oprun_read_plan`，说明是单项目旧连接，引导重新授权。

安装验收只读取上下文和项目列表；需要检查具体方案时调用 `oprun_read_plan`。不要为了验收新建项目、生成方案、修改工序或消耗模型额度。用户后续请求这些操作时，遵循 Skill 的确认和幂等规则。

## 5. 报告结果

报告 Skill 版本、安装位置、MCP 站点及实际达到的状态：已安装、已配置、等待授权、已连接、项目列表已验证。未完成 OAuth 或工具不可调用时，不报告接入成功。遇到宿主不支持、权限不足或网络失败时，说明具体原因和下一步。

用户可在 [OpRun 授权管理](https://www.agi.yifx.vip/mcp/manage) 撤销连接。服务端支持刷新时由宿主续期；`invalid_grant` 时重新授权，`invalid_client` 时通过宿主重建此 OpRun 客户端注册再授权。不要删除其他连接。权限变化或旧连接仍限单项目时，使用宿主原生登录流程重新授权。
