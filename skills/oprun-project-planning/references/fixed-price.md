# 固定价项目

拆解完成后从 `oprun_workspace_read` 读取当前 revision、run_id 对应的 commitment_draft，展示模板、工序交付物及验收要求。草案中的价格待企业明确，执行人待企业选定。确认发布时带上 fixed_offer.draft_digest 和各工序承接价，无需指定首道工序；需求修订后重新读取草案。锁价后从项目页查看选人和签署进度。

## 推荐和接单

登录后核对当前主体。用 `oprun_new_project_fixed_work` 的 recommended 或 pending 查看当前最合适的一道工序。推荐依据为可用排期、本人授权经历与匹配技能。存在更多邀请时也只展示一条。查看固定价、工期及实际交付要求后，OPC 用 `oprun_new_project_fixed_accept` 发起第一方本人确认。成功后说明“已接单，等待企业选定”。每名 OPC 可同时保有多笔接单记录，多名 OPC 可以接同一道工序。用 applied 查询本人的接单记录，用 assigned 查询企业已选定的任务。未选中时给出本人的最新回执。

## 企业选人和签署

企业用 `oprun_new_project_read` 读取每道工序的 fixed.applications。用户指定已接单的候选人后，用 `oprun_new_project_fixed_select` 携带该工序的 invitation_id、expected_version、scope_digest 和 price_digest，核对后由企业在第一方页面确认。只有该工序其他接单记录转为未选中。每道工序均已选定执行人后，核对合同与说明书，再由企业本人签署。新签约流程以 signature.initial_steps 显示签署时可以开工的全部工序；早期冻结合同按 first_step 显示。后续工序等前置验收、所需交接及外部输入核验就绪后开工。

## 工序验收与整项目结算

阶段成果、逐道正式交付、退回重交及工序验收都可按实回读。最后一道工序通过后，企业在项目页看到“核对并确认项目整体验收”。也可根据 project_acceptance 的 scope_version 和 document_digest 调用 `oprun_new_project_fixed_project_accept` 准备同一操作。企业本人勾选确认并取得项目验收回执后才进入待结算。此前该项目的 pending_settlement_fen 为零。

用 `oprun_new_project_fixed_settlement` 按主体查看 projects 和全量 totals。每个项目只计一次，企业看到项目总额，OPC 只看到自己在该项目的份额。工序可作为对账明细，跨页勿重复相加。实际到账和已确认收入依据财务回执。
