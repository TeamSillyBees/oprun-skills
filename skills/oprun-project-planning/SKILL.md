---
name: oprun-project-planning
description: Connect or reconnect OpRun in WorkBuddy or another remote MCP host, discover accessible projects and read their plans, propose deliverables, or ask Xiaojun to generate and revise a project graph and quote.
---

# OpRun 项目方案

通过宿主的远程 MCP 连接使用 OpRun。默认地址为 `https://www.agi.yifx.vip/mcp`；用户明确提供其他 OpRun 站点时使用该站点的 `/mcp`。连接按账号授权，涵盖账号各身份已有的项目权限，无需填写项目编号。

先按[多宿主接入指引](references/hosts.md)核对目标站点已启用的能力，再选择宿主配置格式；Skill 更新不代表服务端已经升级。不要把 WorkBuddy 的配置字段直接套用到 VS Code、Codex 或 Claude Code。

## 连接、登录与恢复

用户要求“连接 OpRun”“登录”或“列出项目”时，先确定 MCP 是否可用。安装此 Skill 只提供操作指引，不会自动创建宿主的 MCP 连接。

接入提示只表达安装、连接和登录。登录或连接验证尚未完成时，只说明当前状态与需要用户完成的下一步；可用操作放在连接成功后的回复末尾。

1. 检查宿主已加载的 OpRun 工具或原生 MCP 配置。已有同站点连接则复用；同名连接指向其他站点时说明冲突，不覆盖。
2. 缺少连接时，使用当前宿主支持的配置工具添加名为 `oprun` 的远程 Streamable HTTP MCP，并启动宿主原生 OAuth。WorkBuddy 的配置和具体操作见随包提供的 [WorkBuddy 接入指引](references/workbuddy.md) 与 [连接配置](assets/workbuddy-mcp.json)。不要在 WorkBuddy 中运行 Codex 专用命令。
3. 宿主没有配置工具时，向用户提供上述地址和可导入的配置，明确当前为“已安装 Skill，待添加连接器”，引导其添加并点击“连接”。不要仅让用户重复说“连接”或重装 Skill。
4. 由用户在宿主打开的页面登录并确认范围。标准范围为 `plan:read`、`plan:propose`、`plan:generate`；用户只要求只读授权时，使用宿主支持的范围设置仅申请 `plan:read`，不默认扩大权限。若宿主不能指定范围，先说明限制。没有弹窗时，检查是否已创建连接及其状态；只有宿主已生成授权链接时才展示该链接，不能猜测授权地址。
5. 通过 MCP `tools/list` 确认可用工具，再调用 `oprun_account_context` 做只读连接验证。工具调用成功才报告“已连接”；配置存在或 Skill 已加载不能证明授权成功。用户只要求接入时，到此完成验证，按文末规则给出下一步引导；用户已经要求查看项目或处理方案时，继续原任务。

凭据交给宿主保存，不索取密码、Token 或 Cookie，不将授权链接写入文件和日志，不自行实现另一个 OAuth 客户端。连接支持续期时由宿主刷新；返回 `invalid_grant` 时重新授权，返回 `invalid_client` 时使用宿主的重建注册功能；没有该功能则仅重新添加 OpRun 连接，不清除其他连接。安装和连接验收不生成方案、不保存草稿、不消耗模型额度。

## 发现项目与权限

用户要求查看项目，或需要为其业务任务定位项目时，先调用 `oprun_account_context` 获取可用身份与能力，再调用 `oprun_list_projects`。需要查找的项目不在当前页时沿 `next_cursor` 继续读取；结果中的 `project_id`、`subject_id` 是后续调用的依据，不让用户猜编号。

列表的 `unavailable_subjects` 会说明因 AI 服务授权未确认而暂不可用的身份；向用户说明原因，其余可用身份仍可正常读取。

按项目名称和所属身份定位。存在同名项目或多个可执行身份时，让用户按名称选择。只读请求调用 `oprun_read_plan` 并展示当前版本和工序；权限不足时依据返回原因处理，不切换到其他账号绕过。若旧连接只提供无参数的 `oprun_read_plan`，沿用其单项目范围；需要其他项目时重新连接。

## 修改已有项目

1. 调用 `oprun_read_plan`，传入选定项目的 `project_id`、`subject_id`，使用返回的实际工序标识和版本。用户说“把库存查询网页加到研发工序里”时，若有两道研发工序，请用户选定一道。
2. 把要求写成可以检查的交付物和验收条件。对用户尚未决定、会改变交付范围的条件，先询问。
3. 调用 `oprun_preview_deliverable`，沿用同一项目与身份。展示修改前后内容及返回的确认链接，让用户亲自在 OpRun 核对。为每次不同的修改生成独立的 `request_key`，网络重试沿用原值。
4. 用 `oprun_change_status` 查询结果。用户同意后调用 `oprun_save_change`。连接中断时用原 `change_id` 查证或重试。只有收到保存回执后才报告“已保存草稿”，附上新版本号。若用户拒绝就结束；版本冲突时重新读取、生成差异并取得新的确认。

## 从需求生成方案

1. 确定本次任务归属的 `subject_id`；有多个身份且用户尚未确定时，先按名称询问。用自然语言描述目标、交付物及已知约束，调用 `oprun_generate_plan`。保存返回的 `task_id` 和版本。请求超时时用同一个 `request_key` 重试。
2. 用 `oprun_plan_result` 按相同身份和任务编号查进度。排队或执行中时逐步延长查询间隔。完成后展示工序、依赖、工时和报价；费用以返回的方案为准。
3. 用户补充需求时用 `oprun_supplement_plan` 传入原身份、任务编号、原版本和新要求。用相同任务编号查最新结果，或指定版本对照。已撤销或过期的连接由用户重新授权。

## 连接成功后的回复

用户只要求接入时，简短确认“已连接 OpRun”，在回复末尾给出可用的下一步，等待用户选择。根据实际可用工具，以及 `oprun_account_context` 返回的 `scopes` 和各身份能力筛选引导：

- `can_read_plans`：查看项目和当前方案。
- `can_propose_changes`：提出交付要求的修改，确认后保存草稿。
- `can_generate_plans`：根据需求生成方案和报价，使用所选身份的模型额度。

只读连接只展示查看选项；没有可用身份时，依据 `unavailable_reason` 说明需要完成的操作。这里只提供引导，不自动列出项目、读取方案或执行修改。用户原请求已经包含业务任务时，继续该任务并报告结果，无需让用户重新选择。
