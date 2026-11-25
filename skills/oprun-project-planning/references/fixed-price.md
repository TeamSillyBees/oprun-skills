# 固定价项目

拆解完成后从 `oprun_workspace_read` 读取当前 revision、run_id 对应的 commitment_draft，展示模板、工序交付物及验收要求。草案中的价格待企业明确，执行人待企业选定。确认发布时带上 fixed_offer.draft_digest 和各工序承接价，无需指定首道工序；需求修订后重新读取草案。锁价后从项目页查看选人和签署进度。

标题以工作区读回的项目名为准。发布前更正名称后，按原任务重新读取承诺书，再准备发布确认。已确认金额使用回执的币种和分值，人民币金额写明「人民币」和「元」。报价待确认时使用状态文字。

## 推荐和接单

用户要智能找单或找适合自己的项目时，直接调用 `oprun_new_project_fixed_work`，只传 `{"view":"recommended"}`，有明确的金额或档期要求时一并传入筛选条件。MCP 使用当前 OAuth 授权的 OPC 主体，无需先读取画像或工作区。查询成功后，按返回值展示至多一道工序的固定价、排期、档期冲突和匹配依据。回执的 coverage 为 top_recommendation 时只含首位推荐的一道，为 all 时是分页的全部记录。空结果按 empty.reason 说明原因，见下表。工具不可用或授权失败时，检查独立 MCP 连接和 OPC 授权。

| empty.reason | 含义 | 可以怎么办 |
| --- | --- | --- |
| no_profile | 当前主体没有接单画像 | 登记技能或导入经历 |
| no_open_invitation | 没有待本人决定的邀请 | 等企业发单并匹配 |
| filtered_out | 有记录，被这次传入的金额或档期筛选挡住 | 放宽回执 filters 中的条件 |
| invitations_unavailable | 有邀请，但资料或授权已变更，或开工时间已过 | 核对画像与授权 |
| no_supported_match | 有邀请，但本人技能和授权经历不足以支持 | 补充经历证据 |
| no_applications | 没有接单记录 | 无 |
| no_assigned_steps | 没有企业选定本人的工序 | 无 |
| end_of_list | 这一页之后没有更多 | 无 |

查看固定价、工期及实际交付要求后，OPC 用 `oprun_new_project_fixed_accept` 发起第一方本人确认。入参全部取自 `oprun_new_project_fixed_work` 回执中的同一道工序：step_id、expected_version、scope_digest、invitation_id、amount_fen、price_digest；拒绝用 `oprun_new_project_fixed_decline`，取前四项。request_key 由调用方生成，同一次意图重试时沿用。范围或价格在提交前变了，会返回 version_conflict、scope_mismatch 或 fixed_price_mismatch，重新读取后请本人按新版确认。成功后说明“已接单，等待企业选定”。每名 OPC 可同时保有多笔接单记录，多名 OPC 可以接同一道工序。用 applied 查询本人的接单记录，用 assigned 查询企业已选定的任务。未选中时给出本人的最新回执。

要查看合作邀请时，用同一工具的 pending 分页读取当前主体收到的待决定邀请。没有待决定的合作邀请时，pending 显示首位自动推荐。

## 企业手动邀请合作 OPC

企业指定接单方时，用 `oprun_new_project_fixed_invite_partners` 读取该工序可邀请的本企业 OPC 合作资源，按返回的 profile_id 核对人选。用 `oprun_new_project_fixed_invite_partner` 携带该工序的 step_id、expected_version、scope_digest、profile_id 和 request_key，准备沿用冻结价的邀请。发单方本人完成确认后回读回执。接单方可以在待决定列表处理邀请，提交意向后由企业选定。

## 企业选人和签署

企业用 `oprun_new_project_read` 读取每道工序的 fixed.applications。用户指定已接单的候选人后，用 `oprun_new_project_fixed_select` 携带该工序的 invitation_id、expected_version、scope_digest 和 price_digest，核对后由企业在第一方页面确认。只有该工序其他接单记录转为未选中。每道工序均已选定执行人后，核对合同与说明书，再由企业本人签署。新签约流程以 signature.initial_steps 显示签署时可以开工的全部工序；早期冻结合同按 first_step 显示。后续工序等前置验收、所需交接及外部输入核验就绪后开工。

## 状态怎么读

每道工序的回执都带 `step_status`，在 `oprun_new_project_fixed_work`、`oprun_new_project_read`、`oprun_new_project_inbox` 和 `oprun_new_project_fixed_settlement` 中取值一致。照抄 label，不另造同义词。state、started、signed、next_action 是原始字段，只用于核对。

| step_status.code | label | 下一步在谁 |
| --- | --- | --- |
| no_candidates | 暂无待选候选 | 企业。核对匹配结果或补邀 |
| awaiting_opc_acceptance | 待 OPC 接单 | OPC |
| awaiting_enterprise_selection | 已接单，待企业选定 | 企业 |
| not_selected | 企业已选定其他 OPC | 无 |
| awaiting_signature | 已选定执行人，待企业签署 | 企业。选齐所有工序的执行人后签署，OPC 无需签署 |
| awaiting_handoff_receipt | 上游交接已就绪，待执行人签收 | OPC。用 `oprun_new_project_handoff_receive` 签收 |
| awaiting_start | 已签署，待开工 | 前置工序验收和外部输入核验 |
| in_progress | 执行中，待交付 | OPC |
| awaiting_review | 已交付，待企业验收 | 企业 |
| needs_revision | 已退回，待重交 | OPC |
| accepted_awaiting_project_acceptance | 本工序已验收，待企业确认项目整体验收 | 企业 |
| accepted_pending_settlement | 项目已整体验收，待结算 | 平台 |

action_owner 从当前主体的角度给出：self 是本人，enterprise 是企业，provider 是执行人，prerequisites 是前置条件，platform 是平台，none 表示无人待办。项目一级的状态在 `oprun_new_project_read` 的 `project_status`，结算一级的在 `oprun_new_project_fixed_settlement` 的 projects 和 totals 的 `status_label`。

## 工序验收与整项目结算

阶段成果、逐道正式交付、退回重交及工序验收都可按实回读。最后一道工序通过后，企业在项目页看到“核对并确认项目整体验收”。也可根据 project_acceptance 的 scope_version 和 document_digest 调用 `oprun_new_project_fixed_project_accept` 准备同一操作。企业本人勾选确认并取得项目验收回执后才进入待结算。此前该项目的 pending_settlement_fen 为零。

用 `oprun_new_project_fixed_settlement` 按主体查看 projects 和全量 totals。每个项目只计一次，企业看到项目总额，OPC 只看到自己在该项目的份额。工序可作为对账明细，跨页勿重复相加。实际到账和已确认收入依据财务回执。
