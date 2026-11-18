# 安装或更新 OpRun

用户说“安装 OpRun”或“更新 OpRun”时，先按当前客户端能力选择方式，保留已有配置，再检查连接。说明入口是 https://github.com/TeamSillyBees/oprun-skills/blob/main/INSTALL.md；说明可随 main 更新，实际安装必须固定到正式版本。

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

1. 读取[最新正式发布](https://github.com/TeamSillyBees/oprun-skills/releases/latest)，确定具体版本，提供该版本的 `oprun-project-planning.zip` 下载链接。不要提供仓库的 Source code ZIP，也不要把二进制 ZIP 交给正文读取工具。如果无法解析版本，提供[官方 ZIP 下载入口](https://github.com/TeamSillyBees/oprun-skills/releases/latest/download/oprun-project-planning.zip)，标明“版本待核实”，不编造版本号。
2. 根据已知客户端，只给一条具体导入路径。Qveris 已核验路径为“添加技能 → 上传 ZIP”，选择文件后“导入技能”，再在对话中选择 `oprun-project-planning`；已有 oprun 连接需在“本对话已启用”中启用。WorkBuddy 使用其当前页面的 Skill 安装/导入入口；若无法看到该入口或没有可靠文档，只询问入口位置，不编造按钮名称。能安全下载到获准目录时可代为下载；不能下载时让用户点击链接。不擅自打开或操作用户窗口。
3. 更新使用客户端的原生更新或替换方式。保留既有 MCP 连接、配置、授权、会话及用户自定义内容，不先卸载旧 Skill，不反复导入同名副本。若客户端只能重复新增，先说明这一限制；有本地改动时先导出或备份并核对，不能直接覆盖。可靠核对到 Skill 文件完全一致时，无需重复导入。
4. 宿主不能自动导入时，简短提示“请下载并导入 ZIP，完成后告知结果”，状态为“等待导入确认”。客户端显示导入成功或用户确认后，再检查 Skill 是否在当前会话启用；仅下载完成不能报告已安装。不能读取已安装版本时明确“已导入，版本待客户端核实”。

对无命令能力的客户端，首次引导只需要：下载链接、当前宿主的导入步骤，以及“已有连接会保留”。不要再展示 npm 命令、要求用户配置开发环境或索取凭据。能够读取二进制文件的工具应按同版本 `manifest.json` 和 `SHA256SUMS` 核对 ZIP；做不到时使用官方链接并标明“文件摘要未核验”，不声称已校验。

## 命令安装与更新

```sh
npx oprun-skills@latest install --host <宿主>
npx oprun-skills@latest update --host <宿主>
npx oprun-skills@latest doctor --host <宿主>
```

支持 codex、claude、qveris、workbuddy、generic。只有项目标记唯一时可省略 `--host` 自动识别；多个标记不猜测。默认项目范围：Codex 为 `.agents/skills/oprun-project-planning`，Claude Code 为 `.claude/skills/oprun-project-planning`。全局安装仅在用户要求时使用已公开的目录。

工具输出 `awaiting_host_import` 表示还没有完成安装，转入上面的 ZIP 流程。桌面宿主只在已公开支持目录时使用 `--target <完整Skill目录>`，目录名须为 `oprun-project-planning`。`npx` 首次可能要求确认下载包，遵循宿主提示。

更新使用当前正式版；一旦解析出版本，本次安装、更新、检查和下载均使用同一版本（例如 `oprun-skills@<版本>`），不混用变动的 latest。npm 和 GitHub 发布不同步时，分别说明可用版本，不把旧包称为新版。

npm 注册表不可用时，可使用同版本 GitHub 包：`npx https://github.com/TeamSillyBees/oprun-skills/releases/download/v<版本>/oprun-skills.tgz install --host <宿主>`；更新改用 `update`。没有命令能力时不展示这个备用命令，直接走 ZIP。

已有 Python 安装方式继续保留：从同一固定 Release 下载并校验 `install.py`、`manifest.json`、`SHA256SUMS`，用 Python 3.9+ 执行 `python3 install.py install|update|check`。不要使用 curl 管道直接运行下载脚本。

## 复用连接，再检查

Skill 安装与 MCP 连接分开判断。同站点连接已经可用时直接复用，不因更新 Skill 删除、重建连接或要求重新授权。Qveris 中“已保存”不等于当前会话已启用；只检查一次是否启用并刷新，不反复用全局研究工具搜索。界面显示“任务工具离线”不能单独证明 OpRun MCP 不可用。

没有连接时，使用宿主原生方式导入对应配置；仅查看时使用只读配置。需要增加权限时再由用户重新授权，不悄悄扩大已有授权。用户本人完成首次 OAuth；密码、Cookie、Token、授权回调参数都不应索取、导出或保存到日志。

| 客户端 | 新建连接时使用 |
| --- | --- |
| Codex / Claude Code | 宿主支持的 MCP OAuth 方式，命令以本机帮助为准 |
| Qveris | [统一配置](skills/oprun-project-planning/assets/qveris-mcp.json)或[只读配置](skills/oprun-project-planning/assets/qveris-readonly-mcp.json)，点击“保存并授权” |
| WorkBuddy | [专用配置](skills/oprun-project-planning/assets/workbuddy-mcp.json)，点击“连接” |
| 其他 | 核实支持 Streamable HTTP 和 OAuth S256 PKCE，使用原生连接入口 |

服务地址和 OAuth issuer 均为 `https://www.agi.yifx.vip/mcp`。Qveris 显式使用 `authMode: oauth`、该 issuer 及配置中的 Scope，不填写 `openid offline_access`。详细差异按需阅读 [Qveris 指引](skills/oprun-project-planning/references/qveris.md)、[WorkBuddy 指引](skills/oprun-project-planning/references/workbuddy.md)及[多宿主指引](skills/oprun-project-planning/references/hosts.md)。一个连接覆盖当前身份获准的方案、发单、接单、交付等能力，无需分别配置。

有命令工具时可运行 `doctor` 检查本地记录和公开 OAuth 发现；`--offline` 只核对文件。没有命令工具时跳过 doctor，直接用当前宿主检查连接和工具加载，再调用 `oprun_account_context`；支持直接 `tools/list` 时一并检查。不得为了验证安装而读取项目、生成方案或执行业务操作。

公开发现通过不等于 OAuth 成功。无法调用 MCP 时报告“连接待验证”，不因导入 Skill 或用户已登录就宣称工具可用。`update_available` 只表示本地版本早于 CLI 所携版本；`host_managed` 只表示安装由客户端管理，不是已安装证明。

## 完成状态与恢复

分别报告 Skill 和连接状态，保持简短：例如“Skill 已导入；连接已验证”，或“等待 ZIP 导入；已有连接保留”。只有客户端证据或用户确认支持时才报告已导入，只有实际工具调用成功时才报告连接已验证；版本、摘要未核实的部分单独说明。

| 情况 | 下一步 |
| --- | --- |
| Skill 已导入，当前会话未启用 | 选择 Skill，或按宿主要求重新加载会话 |
| 401 / 授权已失效 | 使用现有连接的登录授权入口 |
| 工具未加载 | 检查连接启用状态并刷新一次 |
| 权限不足 | 根据 account_context 的 required_scopes，在使用该功能时重新授权 |
| 本地内容有改动 | 保留并核对差异，不强制覆盖 |
| 无法核实版本或调用工具 | 如实标为待核实，不重复安装来代替验证 |

npm 更新输出 backup 路径，备份位于 Skill 扫描目录外的 `oprun-skill-backups`。恢复前核对两边安装记录和摘要，先保存当前内容，再将 backup 中完整 Skill 目录放回原 target，不能覆盖后续本地修改。ZIP 导入前保存的原包和自定义内容也应保留。撤销授权使用[授权管理](https://www.agi.yifx.vip/mcp/manage)，安装更新不会自动撤销。

说明页面读取失败时改用 GitHub Contents API 的 INSTALL.md（content 为 Base64）；不要重复读取被当作 `application/octet-stream` 的 Release 说明附件。只提供官方链接时如实标记未读取版本。

新项目履约使用当前连接中的 `oprun_workspace_assess`、`oprun_new_project_profile_read`、`oprun_new_project_invitation_decide` 和 `oprun_new_project_request_status`。宿主工具目录和已登录主体决定实际能力。候选 Skill 的 `release.json` 标记 `pending` 时只能本地试装；MCP 来源合入后，用 `tools/sync.py` 同步实际合入的提交并核对摘要，再发布 ZIP 和 npm 包。

Skill 正文唯一来源仍是 oprun-mcp 的固定提交。安装指引更新不改变服务端能力，不代替客户端真实验收。
