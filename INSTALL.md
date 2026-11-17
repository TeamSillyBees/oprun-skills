# 安装或更新 OpRun

用户说“安装 OpRun”或“更新 OpRun”时，执行以下简短流程。阅读入口为 https://github.com/TeamSillyBees/oprun-skills/blob/main/INSTALL.md，使用网页读取工具时不要访问 Release 附件下载地址，GitHub 可能将其强制作为二进制附件返回。默认使用最新正式 Release，不用移动的 main 作为安装版本。

1. 先核对当前会话能用的工具和已有连接。Qveris 中连接已保存不等于在本会话启用：在输入框“本对话已启用”中勾选 oprun；工具缺失时只检查一次，不反复用全局研究工具搜索代替。没有下载、文件写入或命令执行能力时，不尝试用研究工具安装软件，直接使用原生 Skill 导入。不要因为界面显示“任务工具离线”就推断 MCP 不可用，独立验证连接。识别当前宿主，不向用户追问已能确定的信息。下载同一正式版本的 `install.py`、`manifest.json`、`SHA256SUMS`；从官方仓库 HTTPS 获取并核对脚本摘要后执行，不使用 curl 管道直接运行。
2. 使用 Python 3.9+：`python3 install.py install --host <宿主>`；更新用 `update`。支持 codex、claude、qveris、workbuddy；无法确定时用 generic。项目目录只在已有明确标记时自动识别；多个标记不猜测。桌面宿主先用其原生安装器导入完整 ZIP；若宿主公开了 Skill 目录，可用 `--target <完整目录>`。不猜测桌面应用内部数据库位置。
3. 工具校验正式包并保护本地修改，更新保留原目录备份。读取工具输出的客户端配置，使用宿主原生能力导入；同站点连接直接复用。导入受限时只让用户完成一次配置导入。用户要求只读时加 `--readonly` 并在 OAuth 中申请输出的只读 scopes；既有授权不自动扩大。
4. 用户完成登录授权。运行 `python3 install.py check` 检查公开发现；再由宿主调用 `tools/list`、`oprun_account_context`。发现通过不代表授权成功，不读取项目，不生成方案。`check --target <目录>` 可同时校验已安装文件。
5. 简短报告“已安装／已更新、已连接”，仅在相应步骤实际成功时使用。等待用户操作时说明具体一步。Qveris 真实客户端验收仍由人工完成，不以脚本测试替代。

再次更新沿用同一流程，不重建连接、不删除用户配置。工具输出 backup 是恢复目录；需要恢复时先核对现有内容再还原，不能覆盖新的本地修改。早期非托管安装只读比较；内容有差异时先保存、核对，不强行覆盖。

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

正式下载入口为 `https://github.com/TeamSillyBees/oprun-skills/releases/latest`。先解析实际标签，所有文件从同一标签下载。`install.py`、ZIP 必须分别通过该版本清单和 SHA256SUMS 校验；摘要证明完整性，可信来源仍是官方仓库 HTTPS。没有 Python 时使用宿主原生 ZIP 安装，并核对完整成员与摘要；不要让用户安装开发环境才能连接。

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
