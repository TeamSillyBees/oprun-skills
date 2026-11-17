# 安装或更新 OpRun

用户说“安装 OpRun”或“更新 OpRun”时，执行以下简短流程。阅读入口为 https://github.com/TeamSillyBees/oprun-skills/blob/main/INSTALL.md，使用网页读取工具时不要访问 Release 附件下载地址，GitHub 可能将其强制作为二进制附件返回。默认使用最新正式 Release，不用移动的 main 作为安装版本。

1. 先核对当前会话工具、宿主和已有连接。Qveris 中已保存连接还需在“本对话已启用”中勾选 oprun；不要用反复搜索替代连接检查。没有命令执行或文件写入能力时，直接使用宿主原生 ZIP 导入。
2. 有 Node.js 22+ 时执行 `npx oprun-skills@latest install --host <宿主>`，更新使用 `update`，检查使用 `doctor`。支持 codex、claude、qveris、workbuddy、generic。工具携带固定版本的完整 Skill，校验每个文件；不依赖 Python，不启动本地业务服务。`npx` 首次可能要求确认下载官方 npm 包。
3. 默认只写当前项目。Codex 使用 `.agents/skills/oprun-project-planning`，Claude Code 使用 `.claude/skills/oprun-project-planning`。只有项目标记唯一时自动识别；不确定时输出原生导入说明。桌面宿主导入同版本 ZIP；仅当宿主公开支持目录时使用 `--target <完整Skill目录>`，目录名须为 `oprun-project-planning`。不猜测应用私有数据库位置。
4. 复用已有 MCP 连接。工具只输出公开配置，不改写宿主配置；需要时使用原生导入。只读用途加 `--readonly`，已有授权不自动扩大。用户本人完成首次 OAuth；再在客户端调用 `tools/list`、`oprun_account_context` 检查授权和工具。不得查询项目或执行业务操作来验证安装。
5. `doctor` 检查公开 OAuth 发现及本地安装记录，发现成功不代表登录或工具调用成功。`--offline` 仅核对文件；`update_available` 表示已安装版本早于当前 CLI 所携版本，不表示已完成更新。桌面宿主的导入状态需在其原生界面核对。

npm 注册表不可用时，可执行 `npx https://github.com/TeamSillyBees/oprun-skills/releases/latest/download/oprun-skills.tgz install --host <宿主>`，更新时将 `install` 换成 `update`。使用固定版本可把 URL 中的 `latest/download` 改成 `download/v<版本>`。

没有 Node.js 时仍可导入 ZIP。既有 Python 安装方式保留：从同一固定 Release 下载并校验 `install.py`、`manifest.json` 和 `SHA256SUMS`，用 Python 3.9+ 执行 `python3 install.py install|update|check`。不要使用 curl 管道直接运行下载脚本。

只有实际完成相应步骤才能报告“已安装／已更新、已连接”。等待用户登录或原生导入时说明具体一步；不把脚本测试当作客户端真实验收。

再次更新沿用同一流程，不重建连接、不删除用户配置。工具输出 backup 是恢复目录；npm 更新备份放在 Skill 扫描目录外的 `oprun-skill-backups`。需要恢复时先比较两边安装记录和文件摘要，备份当前目录，再将 backup 下的完整 Skill 目录放回原 target；不能覆盖新的本地修改。早期非托管安装只读比较；内容有差异时先保存、核对，不强行覆盖。

安装说明获取失败时：若网页读取工具拒绝 `application/octet-stream`，改读 https://github.com/TeamSillyBees/oprun-skills/blob/main/INSTALL.md；仍无法读取时使用 GitHub Contents API 的 INSTALL.md（content 为 Base64）。同一错误不重复请求。说明入口可跟随 main，实际安装包始终固定正式 Release 标签。

以下为宿主差异和排错参考，无需逐条展示给用户。

## 客户端适配

| 客户端 | 安装位置与连接方式 |
| --- | --- |
| Codex | 当前项目 `.agents/skills/oprun-project-planning`；连接采用本机 CLI 帮助所支持的 MCP OAuth 方式 |
| Claude Code | 当前项目 `.claude/skills/oprun-project-planning`；使用宿主 MCP OAuth 配置 |
| Qveris | 原生导入完整 ZIP；导入 [专用配置](skills/oprun-project-planning/assets/qveris-mcp.json)，点击“保存并授权” |
| WorkBuddy | 原生安装完整 Skill；导入 [专用配置](skills/oprun-project-planning/assets/workbuddy-mcp.json)，点击“连接” |
| 其他 | 先核实宿主支持 Skill、Streamable HTTP、OAuth S256 PKCE；用原生安装与连接方式 |

默认项目范围。全局安装只在用户明确要求时使用宿主文档中的目录。脚本不编辑宿主私有数据库、Token 存储或其他 MCP 配置。仅有 `.agents` 或 `.claude` 标记时可自动识别；桌面客户端及多个标记时由 Agent 根据当前宿主选 `--host`，无需让用户猜路径。

正式下载入口为 `https://github.com/TeamSillyBees/oprun-skills/releases/latest`。先解析实际标签，所有文件从同一标签下载。`install.py`、ZIP 必须分别通过该版本清单和 SHA256SUMS 校验；摘要证明完整性，可信来源仍是官方仓库 HTTPS。没有 Python 时使用 npm 工具或宿主原生 ZIP 安装；不要让用户安装开发环境才能连接。

## 登录和权限

地址和 OAuth issuer 均为 `https://www.agi.yifx.vip/mcp`。Qveris 必须显式使用 `authMode: oauth`、该 issuer 和配置中的 Scope；不填写 `openid offline_access`。详细差异按需阅读 [Qveris 指引](skills/oprun-project-planning/references/qveris.md)、[WorkBuddy 指引](skills/oprun-project-planning/references/workbuddy.md)及[多宿主指引](skills/oprun-project-planning/references/hosts.md)。

用户明确要连接完整功能时采用统一配置；仅查看时采用只读配置。意图不明时在 OAuth 授权页由用户选择，不悄悄扩权。一次连接覆盖当前身份已有的方案、发单、接单及交付能力，无需分别配置。既有只读连接先复用，需要新权限时另行由用户重新授权。

登录及授权由用户本人完成，凭据交给宿主保存。不要索取密码、Cookie、Token，不读取其他浏览器登录态，不把授权链接、回调参数写入文件或日志。配置文件不含静态凭据。尚未登录时可完成安装与配置，报告“等待登录授权”。

## 检查和恢复

| 检查结果 | 下一步 |
| --- | --- |
| Skill 已安装，宿主未发现 | 按宿主要求重新加载会话 |
| 公开发现失败 | 检查网络和站点；不能报告已连接或已是最新 |
| 尚未授权、401 | 使用已有连接的登录授权入口 |
| 工具未加载 | 检查连接是否启用并刷新；不查询业务数据 |
| 权限不足 | 根据 account_context 的 required_scopes，在需要该功能时重新授权 |
| 本地 Skill 有改动 | 保留并核对差异，不使用强制覆盖 |
| 旧版非托管安装 | 内容与正式包一致时登记版本；不同则先备份、比较，由用户决定保留方式 |

安装与更新验证只需 `tools/list` 和 `oprun_account_context`。不自动列出项目、生成方案或执行业务操作。用户已有具体任务时，连接通过后再继续原任务。撤销入口：[授权管理](https://www.agi.yifx.vip/mcp/manage)。

Skill 正文仍由 oprun-mcp 固定来源同步。本次安装器更新不改变服务器能力，文件内容一致时版本登记可更新，无需反复重新登录。新权限和客户端真实展示验收分别确认，不把脚本校验当成真实客户端验收。
