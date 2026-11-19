# 固定价项目

## 我的工序与智能找单

先从当前连接核对 OPC 主体。用 `oprun_new_project_fixed_work` 的 pending 和 assigned 分别查看待我决定和本人已承接，核对邀请或承接时间及实际回执来源。智能找单用 recommended，按 next_cursor 继续查。只推荐本主体有效、未被占用、排期可容纳且经历证据覆盖交付物的邀请，按最近开工顺序呈现。显示 amount_fen 换算的人民币固定价、工作量、排期、命中的技能与交付物，使用返回的 view_url 看要求、验收与上下游。匹配服务暂不可用时仍可查看原邀请。用户说“找 9,000 元以上的单”仅给本次查询设置 min_amount_fen 为 900000。这里提供本人接单，未提供委托自动接单或百分制评分。

## 验收与待结算

用 `oprun_new_project_fixed_settlement` 按选定主体查，具体项目可传 project_id，明细按 next_step 续查。总额 totals 覆盖全部页，只统计一次。企业可看全项目，执行人仅看分配给自己的工序。分别说明待交付、待企业验收、需修改及反馈、已验收待结算，点击 view_url 回到该工序。project_ready 为真表示项目已全部正式验收。金额为固定承接额，finance_state 为 unverified 时说“财务结果待核实”。已确认收入和实际到账须有财务凭证，目前不能据此计算月收入差额。

## 发邀与本人确认

从当前连接读取主体与权限，固定 subject_id。新工作区 contracting_mode 为 fixed_v1 时，企业准备 publish，传最新 revision、run_id 和 fixed_offer，包括明确的工序承接金额（人民币分）、工作分钟、持续工作日、首个工作日和唯一无前置的首道工序。金额由企业明确或引用已核实的报价。缺价保留草案并说明核算中。确认页核对逐项价格和合计，只有 completed 回执才报告已经锁价、邀请已进入相应收件箱。候选为空时报告具体工序，企业可用 candidates 和 fixed_invite 补邀。

OPC 用 inbox、read 查看本人受邀工序、输出、验收、固定价、工作量与排期。浏览、表示兴趣或跳过保留邀请。本人明确接单后，用最新 step_id、expected_version、scope_digest、invitation_id、price_digest 和 amount_fen 准备 fixed_accept，打开第一方确认页勾选条款。成功后报告“承接成功 · 本人确认”。名额已占、金额变动、排期冲突或资料变更时读取回执并说明。明确拒绝才用 fixed_decline。每次重试复用原 request_key，结果未知时用 request_status 恢复。

企业用 read 检查 signature.missing，列出每道待接工序。ready_to_sign 时展示 contract_url、specification_url 和 first_step，企业明确签署后使用该版 document_digest、scope_version 准备 fixed_sign，由企业本人核对文件、勾选签署。pending、关闭页面或拒绝时继续待签。签署回执 returned receipt_id 后仅首道开工，其余读取各工序 fixed.started；前置验收和交接签收后再交付。多个起点中其余已就绪工序只能另行启动。旧项目继续按议价履约指引办理。
