---
name: oprun-project-planning
description: Use OpRun to discover accessible projects and read their plans, propose a deliverable and acceptance criteria for one work step, or ask Xiaojun to generate and revise a project graph and quote.
---

# OpRun 项目方案

通过宿主的远程 MCP 连接使用 OpRun。连接地址为用户所在 OpRun 站点的 `/mcp`；让用户在该站点授权所需功能。使用 `tools/list` 获取本次可用工具。凭据由宿主保存。新连接按账号授权，涵盖账号各身份已有的项目权限，无需用户填写项目编号。

## 发现项目与权限

先调用 `oprun_account_context` 获取可用身份与能力，再调用 `oprun_list_projects`。需要查找的项目不在当前页时沿 `next_cursor` 继续读取；结果中的 `project_id`、`subject_id` 是后续调用的依据，不让用户猜编号。

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
