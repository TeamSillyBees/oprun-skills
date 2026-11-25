---
name: oprun-project-planning
description: Use the independent OpRun project workspace for requirement briefs, confirmed scopes, fixed-price invitations, OPC acceptance, enterprise signing, historical negotiation, versioned delivery, and evidence-based quality and acceptance.
---

# OpRun 新项目

发单助手与接单助手共用同一个 `oprun-new` MCP 配置。用户通过宿主的 OAuth 登录并选择本人主体。需要核对主体、切换授权或排查权限时，用 `oprun_new_account_context` 查看当前连接；它同时返回按用途分组的工具索引，不确定该用哪个工具时先看它。一个连接只代表一个主体，所有工具的 subject_id 都可省略。首次生成方案可直接创建工作区。需求、报价、交付和验收由这个连接对应的新工作台办理。

## 从需求到同版约定

发单助手自动维护草案、版本和生成任务，在对话里交付说明书、工序、报价状态和承诺书草案。用户可以在对话里继续修改，按需打开 OpRun 网页查看、改名或确认发布。

1. 每轮只问决定范围、工期或价格的关键项，最多四问。未答最多追问一次，用户跳过就采用合理约定，并在回复里说明。用户说“先出一版”、等待生成或查询受限时，当轮交付六章初稿全文。优先用本次创建或修订回执的 saved_draft.chapters，保留用户原话。仅有会话原稿时据此整理六章。缺依据的价格、工时与工期标为待核实。预算是规划约束。已有系统核价时才判断是否超出预算上限，再说明缩范围、分期或调整预算的选项。
2. 说明书按“需求背景与目标、做什么、不做什么、协作约定、工序总览、各工序明细”六章编写。每道列输入及来源、工作范围、交付物、验收标准、报价、工时与工期、前置工序。区分累计工作量和依赖路径上的工期。咨询仅给建议，修改时保留无关段落，只重算受影响的输入、输出、依赖、价格和工期。
3. 用户明确要求“生成完整版”时，有本会话明确关联的工作区就沿用该版本，草案已修改时先用 `oprun_workspace_revise` 保存全文。首次生成用 `oprun_workspace_create` 保存最新完整草案，保留范围和预算上限。独立 MCP 可省略 subject_id，由当前 OAuth 授权补齐。草案明确指定了其他发单主体时先切换授权。取得 workspace_id 和 revision 后调用 `oprun_workspace_generate`，保留 workspace_id、revision、run_id 及建档和生成各自的原 request_key。按 poll_after_seconds 用 `oprun_workspace_run_status` 查询原任务。429 等满 Retry-After 再查，持续限流时延长间隔。401 交宿主刷新授权，403 核对主体和权限，503 暂停查询并保留上次已知状态。遇到 generation_in_progress，用 `oprun_workspace_read` 找到该修订已有的任务，继续查原 run_id。
   - failed 或 outcome_unknown 均停止轮询，用 `oprun_workspace_read` 带原 workspace_id、run_id 取回六章初稿和链接。按 failure.message 说明原因，截断时说明可用更简洁的输出重算，校验未通过时指明需核对的条目。结果待核实时提示上次调用可能已计费。只有用户确认可能再次计费并要求重算，才在原修订用新请求键，把 confirmed_retry_of 设为该终态 run_id。
   - 用用户明确给出的项目名作 title。没有名称时从核心交付目标拟名，遇到 workspace_title_needs_confirmation 时请用户核对。发布前需要纠正名称时，打开工作区网页的「修改项目名称」，保存后重新读取承诺书和发布预览。
   - 已有 specification 时交付六章、工序和 pricing。已确认价按 currency 和整数分展示，例如 CNY 的 12345 分写为「人民币 123.45 元」。待锁价时显示「承接价待企业确认」。固定价方案拆解完成后，展示 commitment_draft 的项目范围、交付验收要求和承诺书条款，供企业在锁价前预览。企业在发布页逐道核对明确承接价，缺价保留草案。
   - 首次成图或修订后成功生成新版图时，在解释工序依赖的句中使用 Markdown 行内链接，方括号内固定写「工序图」，紧接的圆括号内填入本次 `oprun_workspace_read` 回执的实际 `web_url`，核对 `workspace_id` 和 `focused_run_id` 与正在交付的运行一致。修订后用新版地址；即使省略 `auto_open`，也照常给出具名链接。尚无工序图时，只说明当前进度。
   - 引用资料时，在引用处使用 Markdown 行内链接，方括号内写资料实际标题，紧接的圆括号内填该条检索结果的真实网址。同一段里的每篇资料分别使用自己的标题和地址。缺少可核实的标题或网页地址时，用普通文本说明依据；内部 `source_ref`（如 `redacted:…`）只作标识。正文直接输出 Markdown 链接，不用代码块包裹，也不在段尾重复列出裸网址。
4. 用户明确要发布时，调用 `oprun_new_project_publish` 准备确认。请企业在返回的第一方网页确认准确预览，再用 `oprun_new_project_request_status` 查原回执。
5. 用 `oprun_new_project_read` 查看已确认项目。同版的 `brief` 和 `graph` 共用成果、条款与交接标识。优先使用宿主支持的方案面板，或打开回执中的同版网页。按照服务返回的权限展示，保留范围版本和工序定位。

## 履约

- 企业锁价发邀后，OPC 每次查看推荐首位的一道工序，本人按固定价接单后进入企业待选名单。多人可接同一道。企业查看工序中的 applications，指定一名已接单人并用 `oprun_new_project_fixed_select` 准备选定。在第一方页面确认后，该工序其他人未选中。所有工序均有企业选定的执行人后才可签署。企业本人勾选确认定稿后，initial_steps 列出的无前置且输入就绪的工序同时开工。工序验收后等待企业另行确认项目整体验收，按项目锁定总价进入待结算。
- 固定价工序按企业锁价本人承接。历史议价工序按已冻结范围和本人交付证据匹配候选，核对授权、本人贡献、覆盖与缺口，分别展示待报价、待回复、档期冲突和正式报价。用本人主体查邀请，表达意向并在范围内议价。正式邀请、回函和唯一执行人分别以新后端回执为准。报价过期、退出或出现冲突时，留在原卡重新核对当前可用候选。
- 用户要联系 OPC 时，用当前主体的 `oprun_new_project_read` 回执中的 chat_url 打开项目群。要查看所有群时用 `oprun_new_project_chat_rooms` 按 next 翻页。仅发单方和已接单执行人能参加。实际发言由用户在第一方页面完成。
- 工序有 latest_milestone 时标明“阶段交付”，根据正式交付、质检、验收和交接回执说明负责人及下一步。阶段成果只更新进度，群内文字仅作沟通。正式提交走工序入口。
- 执行人提交确切版本的成果，带 `asset_id` 和当前工序版本，收到可查回执后方可报告已交付。按同版条款查看质检、补齐材料并在必要时申请复核。企业在第一方页面确认逐条验收，退回时引用具体成果、条款和理由。
- 说明一道工序的进度时，照抄回执中的 `step_status.label`，并按 `action_owner` 说明在等谁。只有 `self` 是当前用户的待办，其余写成等待对方或等待前置条件。列表、详情、收件箱和结算里，同一道工序的 `step_status` 相同。列表为空时按 `empty.reason` 说明原因。
- 回答里用到的结论来自失败后重试的调用时，说明哪次调用失败过、失败是否影响结论。

工具与恢复方式见 [履约指引](references/fulfillment.md)。配置及升级见 [宿主接入](references/connection.md)。

固定价项目先按[锁价、接单与签署](references/fixed-price.md)读取真实状态。OPC 首页与智能找单用 `oprun_new_project_fixed_work`，企业和执行人查验收及待结算用 `oprun_new_project_fixed_settlement`。
