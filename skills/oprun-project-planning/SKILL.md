---
name: oprun-project-planning
description: Use the independent OpRun project workspace for requirement briefs, confirmed scopes, fixed-price invitations, OPC acceptance, enterprise signing, historical negotiation, versioned delivery, and evidence-based quality and acceptance.
---

# OpRun 新项目

发单助手与接单助手共用同一个 `oprun-new` MCP 配置。用户通过宿主的 OAuth 登录并选择本人主体。用 `oprun_new_account_context` 核对当前主体及已经授予的权限。需求、报价、交付和验收由这个连接对应的新工作台办理。

## 从需求到同版约定

1. 整理用户明确的业务成果、边界、接收用途、依赖、预算和期限。把原话、建议与待核实事实分开。第一轮只用经授权的脱敏做法辅助拆解。
2. 用 `oprun_workspace_create` 创建，`oprun_workspace_revise` 保存完整修订，`oprun_workspace_generate` 按明确 revision 生成，`oprun_workspace_assess` 查看缺口。生成后用 `oprun_workspace_read` 核对草稿及 run_id。
3. 检查每项必交成果都有来源、唯一产出方、验收方法、通过条件和所需证据。检查依赖正确、无环且确实能提供下游需要的材料。关键范围缺口由企业澄清。
4. 用户明确要发布时，调用 `oprun_new_project_publish` 准备确认。请企业在返回的第一方网页确认准确预览，再用 `oprun_new_project_request_status` 查原回执。
5. 用 `oprun_new_project_read` 查看已确认项目。同版的 `brief` 和 `graph` 共用成果、条款与交接标识。优先使用宿主支持的方案面板，或打开回执中的同版网页。按照服务返回的权限展示，保留范围版本和工序定位。

## 履约

- 企业确认后，按已冻结工序依据本人交付证据匹配候选。检查授权、本人贡献、覆盖、缺口和真人回函。待报价、待回复和档期冲突分别展示，测算与正式报价分别展示。
- 受邀人用本人主体查邀请，表达意向并在范围内议价。正式邀请、回函和唯一执行人分别以新后端回执为准。报价过期、退出或出现冲突时，留在原卡重新核对当前可用候选。
- 执行人提交确切版本的成果，带 `asset_id` 和当前工序版本，收到可查回执后方可报告已交付。按同版条款查看质检、补齐材料并在必要时申请复核。企业在第一方页面确认逐条验收，退回时引用具体成果、条款和理由。

工具与恢复方式见 [履约指引](references/fulfillment.md)。配置及升级见 [宿主接入](references/connection.md)。

固定价项目先按[锁价、接单与签署](references/fixed-price.md)读取真实状态。
