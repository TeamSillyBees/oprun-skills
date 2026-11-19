# 安装或更新 OpRun 新项目 Skill

新版 Skill 使用独立的 OpRun 新项目 MCP。正式环境的连接名为 `oprun-new`，MCP 地址为 `https://v2.agi.yifx.vip/mcp`，OAuth issuer 为 `https://v2.agi.yifx.vip/mcp-oauth`。已导入旧占位地址的用户可直接编辑这条连接并重新授权，无需重装 Skill。

## 先选择安装方式

先查看当前会话已有的工具、宿主和 OpRun 连接，不让用户选择 npm 或 ZIP 等技术方案，不根据客户端名称猜测执行能力。

| 当前能力 | 直接采用的方式 |
| --- | --- |
| 能执行命令、写入获准 Skill 目录，且已有 Node.js 22+ | npm/npx 安装或更新 |
| 没有命令工具、没有文件写入能力、Node.js 不可用，或命令被宿主限制 | 原生 ZIP 导入，不要求用户安装 Node.js、Python 或打开终端 |
| 能运行命令，但桌面宿主未公开 Skill 安装目录 | 原生 ZIP 导入，不修改应用私有目录或数据库 |
| 客户端不支持 Skill 导入 | 明确说明不能安装 Skill；若支持 MCP，可继续复用或配置连接，不能称为 Skill 已安装 |

工具列表已能确定能力时不做无效尝试。命令安装因能力不足失败一次后转 ZIP，不反复尝试命令，也不用联网搜索工具代替文件写入。网络故障或文件校验失败需如实说明，不能通过改用 ZIP 绕过校验。

## ZIP 安装与更新

1. 从[最新稳定发行页](https://github.com/TeamSillyBees/oprun-skills/releases/latest)取得 `oprun-project-planning.zip` 和同版校验清单。命令宿主可使用该页的 `oprun-skills.tgz`。
2. 根据已知客户端，只给一条具体导入路径。Qveris 已核验路径为“添加技能 → 上传 ZIP”，选择文件后“导入技能”，再在对话中选择 `oprun-project-planning`；在“本对话已启用”中启用 `oprun-new`。WorkBuddy 使用其当前页面的 Skill 安装/导入入口；若无法看到该入口或没有可靠文档，只询问入口位置，不编造按钮名称。能安全下载到获准目录时可代为下载；不能下载时让用户点击链接。不擅自打开或操作用户窗口。
3. 更新使用客户端的原生更新或替换方式。保留既有 MCP 连接、配置、授权、会话及用户自定义内容，不先卸载旧 Skill，不反复导入同名副本。若客户端只能重复新增，先说明这一限制；有本地改动时先导出或备份并核对，不能直接覆盖。可靠核对到 Skill 文件完全一致时，无需重复导入。
4. 宿主不能自动导入时，简短提示“请下载并导入 ZIP，完成后告知结果”，状态为“等待导入确认”。客户端显示导入成功或用户确认后，再检查 Skill 是否在当前会话启用；仅下载完成不能报告已安装。不能读取已安装版本时明确“已导入，版本待客户端核实”。

对无命令能力的客户端，首次引导只需要：下载链接、当前宿主的导入步骤，以及“升级后需配置并授权 `oprun-new`”。不要再展示 npm 命令、要求用户配置开发环境或索取凭据。能够读取二进制文件的工具应按同版本 `manifest.json` 和 `SHA256SUMS` 核对 ZIP；做不到时使用官方链接并标明“文件摘要未核验”，不声称已校验。

## 命令安装与更新

```sh
OPRUN_NEW_MCP_URL=https://v2.agi.yifx.vip/mcp
OPRUN_NEW_OAUTH_ISSUER=https://v2.agi.yifx.vip/mcp-oauth
npx https://github.com/TeamSillyBees/oprun-skills/releases/download/v2.5.1/oprun-skills.tgz install --host "$OPRUN_HOST" --mcp-url "$OPRUN_NEW_MCP_URL" --oauth-issuer "$OPRUN_NEW_OAUTH_ISSUER"
npx https://github.com/TeamSillyBees/oprun-skills/releases/download/v2.5.1/oprun-skills.tgz update --host "$OPRUN_HOST" --mcp-url "$OPRUN_NEW_MCP_URL" --oauth-issuer "$OPRUN_NEW_OAUTH_ISSUER"
npx https://github.com/TeamSillyBees/oprun-skills/releases/download/v2.5.1/oprun-skills.tgz doctor --host "$OPRUN_HOST" --mcp-url "$OPRUN_NEW_MCP_URL" --oauth-issuer "$OPRUN_NEW_OAUTH_ISSUER"
```

按当前宿主填写 `OPRUN_HOST`，可用值为 codex、claude、qveris、workbuddy、generic。如果使用自建环境，将两个地址变量一起改为目标部署公布的值。只有项目标记唯一时可省略 `--host` 自动识别；多个标记不猜测。默认项目范围：Codex 为 `.agents/skills/oprun-project-planning`，Claude Code 为 `.claude/skills/oprun-project-planning`。全局安装仅在用户要求时使用已公开的目录。

工具输出 `awaiting_host_import` 表示还没有完成安装，转入上面的 ZIP 流程。桌面宿主只在已公开支持目录时使用 `--target <完整Skill目录>`，目录名须为 `oprun-project-planning`。`npx` 首次可能要求确认下载包，遵循宿主提示。

本次安装、更新、检查和下载使用同一个已发布的新版本。npm 和 GitHub 发布不同步时，分别说明可用版本。

npm 注册表不可用时，可使用同版本 GitHub 包：`npx https://github.com/TeamSillyBees/oprun-skills/releases/download/v<版本>/oprun-skills.tgz install --host <宿主>`；更新改用 `update`。没有命令能力时不展示这个备用命令，直接走 ZIP。

已有 Python 安装方式继续保留：从同一固定 Release 下载并校验 `install.py`、`manifest.json`、`SHA256SUMS`，用 Python 3.9+ 执行 `python3 install.py install|update|check`。不要使用 curl 管道直接运行下载脚本。

## 配置新连接并检查

1. 在宿主中新建或选择 `oprun-new`。发单和接单使用同一份连接配置，两位用户分别登录，用自己的账号选择主体并授权。
2. Qveris 使用[连接模板](skills/oprun-project-planning/assets/qveris-mcp.json)。正式环境可直接导入。使用其他部署时，将模板中的 `url` 和 `issuer` 一起换成该部署的资源地址及其元数据公布的授权服务地址。使用只读授权时，仅申请 `plan:read match:read delivery:read quality:read`。其他宿主使用 Streamable HTTP、OAuth S256 PKCE 和受保护资源发现。更多配置见[共用新项目连接](skills/oprun-project-planning/references/connection.md)。
3. 从 1.5.0 升级时在新会话显式选择 `oprun-new` 并重新授权。把原宿主连接留给使用原协议的会话。更换主体后重新授权并调用 `oprun_new_account_context` 核对。
4. 在宿主刷新工具目录，检查连接中的 `oprun_new_account_context` 与 `oprun_new_project_read`。后者只用于用户指定且有权限的新项目。仅检查安装时调用账号上下文即可。密码、Cookie、Token 和授权回调参数由宿主管理。

`doctor` 带两项公开地址时，验证资源、issuer、S256 和质检权限是否出现在 OAuth 发现元数据。公开发现、Skill 导入、OAuth 授权和工具调用各有独立状态。缺地址时输出 `awaiting_endpoint`；`--offline` 仅核对安装。完成授权并验证当前主体后，才报告连接可用。

## 完成状态与恢复

分别报告 Skill 和连接状态，保持简短：例如“Skill 已导入；连接已验证”，或“等待 ZIP 导入；新连接待授权”。只有客户端证据或用户确认支持时才报告已导入，只有实际工具调用成功时才报告连接已验证；版本、摘要未核实的部分单独说明。

| 情况 | 下一步 |
| --- | --- |
| Skill 已导入，当前会话未启用 | 选择 Skill，或按宿主要求重新加载会话 |
| 401 / 授权已失效 | 使用 `oprun-new` 的登录授权入口 |
| 工具未加载 | 检查连接启用状态并刷新一次 |
| 权限不足 | 根据 `oprun_new_account_context` 和所需权限，在新连接中重新授权 |
| 本地内容有改动 | 保留并核对差异，不强制覆盖 |
| 无法核实版本或调用工具 | 如实标为待核实，不重复安装来代替验证 |

npm 更新输出 backup 路径，备份位于 Skill 扫描目录外的 `oprun-skill-backups`。恢复前核对两边安装记录和摘要，先保存当前内容，再将 backup 中完整 Skill 目录放回原 target，不能覆盖后续本地修改。ZIP 导入前保存的原包和自定义内容也应保留。撤销新连接授权使用宿主和新部署提供的授权管理入口。

说明页面读取失败时改用 GitHub Contents API 的 INSTALL.md（content 为 Base64）；不要重复读取被当作 `application/octet-stream` 的 Release 说明附件。只提供官方链接时如实标记未读取版本。

新项目的交付、补证、质检报告、复核与验收见[按同版履约](skills/oprun-project-planning/references/fulfillment.md)。连接暂不可用时保留当前项目、版本及请求键，恢复后查原回执。候选 Skill 的 `release.json` 标记 `pending` 时仅供本地试装；MCP 来源合入后同步实际合入的提交并核对摘要。

Skill 正文唯一来源仍是 oprun-mcp 的固定提交。安装指引更新不改变服务端能力，不代替客户端真实验收。
