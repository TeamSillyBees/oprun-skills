---
name: oprun-project-planning
description: Use the independent OpRun project workspace for requirement briefs, confirmed scopes, fixed-price invitations, OPC acceptance, enterprise signing, historical negotiation, versioned delivery, and evidence-based quality and acceptance.
---

# OpRun 新项目

发单助手与接单助手共用同一个 `oprun-new` MCP 配置。用户通过宿主的 OAuth 登录并选择本人主体。用 `oprun_new_account_context` 核对当前主体及已经授予的权限。需求、报价、交付和验收由这个连接对应的新工作台办理。

## 从需求到同版约定

1. 每轮只问决定范围、工期或价格的关键项，最多四问。未答最多追问一次，用户跳过就采用合理约定，并在回复里说明。用户说“先出一版”或规划等待授权、超时，当轮给出说明书全文。报价、工时、总工期无系统值时写“系统核算中”。授权恢复后读取同一修订的工序与排期并补齐。
2. 说明书按“需求背景与目标、做什么、不做什么、协作约定、工序总览、各工序明细”六章编写。每道列输入及来源、工作范围、交付物、验收标准、报价、工时与工期、前置工序。区分累计工作量和依赖路径上的工期。咨询仅给建议，修改时保留无关段落，只重算受影响的输入、输出、依赖、价格和工期。
3. 用 `oprun_workspace_create` 保存完整说明书，用 `oprun_workspace_revise` 携带当前版本保存局部修改后的全文，再按新 revision 生成并评估。用 `oprun_workspace_read` 读取该版本的 specification、run_id 和实际工序。固定价方案拆解完成后，展示 commitment_draft 的项目范围、交付验收要求和承诺书条款，供企业在确认锁价前预览。发布页由企业逐道核对明确的固定承接价，缺价保留草案。
4. 用户明确要发布时，调用 `oprun_new_project_publish` 准备确认。请企业在返回的第一方网页确认准确预览，再用 `oprun_new_project_request_status` 查原回执。
5. 用 `oprun_new_project_read` 查看已确认项目。同版的 `brief` 和 `graph` 共用成果、条款与交接标识。优先使用宿主支持的方案面板，或打开回执中的同版网页。按照服务返回的权限展示，保留范围版本和工序定位。

## 履约

- 企业锁价发邀后，OPC 每次查看推荐首位的一道工序，本人按固定价接单后进入企业待选名单。多人可接同一道。企业查看工序中的 applications，指定一名已接单人并用 `oprun_new_project_fixed_select` 准备选定。在第一方页面确认后，该工序其他人未选中。所有工序均有企业选定的执行人后才可签署。企业本人勾选确认定稿后，initial_steps 列出的无前置且输入就绪的工序同时开工。工序验收后等待企业另行确认项目整体验收，按项目锁定总价进入待结算。
- 固定价工序按企业锁价本人承接。历史议价工序按已冻结范围和本人交付证据匹配候选，核对授权、本人贡献、覆盖与缺口，分别展示待报价、待回复、档期冲突和正式报价。用本人主体查邀请，表达意向并在范围内议价。正式邀请、回函和唯一执行人分别以新后端回执为准。报价过期、退出或出现冲突时，留在原卡重新核对当前可用候选。
- 用户要联系 OPC 时，用当前主体的 `oprun_new_project_read` 回执中的 chat_url 打开项目群。要查看所有群时用 `oprun_new_project_chat_rooms` 按 next 翻页。仅发单方和已接单执行人能参加。实际发言由用户在第一方页面完成。
- 工序有 latest_milestone 时标明“阶段交付”，根据正式交付、质检、验收和交接回执说明负责人及下一步。阶段成果只更新进度，群内文字仅作沟通。正式提交走工序入口。
- 执行人提交确切版本的成果，带 `asset_id` 和当前工序版本，收到可查回执后方可报告已交付。按同版条款查看质检、补齐材料并在必要时申请复核。企业在第一方页面确认逐条验收，退回时引用具体成果、条款和理由。

工具与恢复方式见 [履约指引](references/fulfillment.md)。配置及升级见 [宿主接入](references/connection.md)。

固定价项目先按[锁价、接单与签署](references/fixed-price.md)读取真实状态。OPC 首页与智能找单用 `oprun_new_project_fixed_work`，企业和执行人查验收及待结算用 `oprun_new_project_fixed_settlement`。
