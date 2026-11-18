# 固定价项目

从当前连接读取主体与权限，固定 subject_id。新工作区 contracting_mode 为 fixed_v1 时，企业准备 publish，传最新 revision、run_id 和 fixed_offer，包括明确的工序承接金额（人民币分）、工作分钟、持续工作日、首个工作日和唯一无前置的首道工序。金额由企业明确或引用已核实的报价。缺价保留草案并说明核算中。确认页核对逐项价格和合计，只有 completed 回执才报告已经锁价、邀请已进入相应收件箱。候选为空时报告具体工序，企业可用 candidates 和 fixed_invite 补邀。

OPC 用 inbox、read 查看本人受邀工序、输出、验收、固定价、工作量与排期。浏览、表示兴趣或跳过保留邀请。本人明确接单后，用最新 step_id、expected_version、scope_digest、invitation_id、price_digest 和 amount_fen 准备 fixed_accept，打开第一方确认页勾选条款。成功后报告“承接成功 · 本人确认”。名额已占、金额变动、排期冲突或资料变更时读取回执并说明。明确拒绝才用 fixed_decline。每次重试复用原 request_key，结果未知时用 request_status 恢复。

企业用 read 检查 signature.missing，列出每道待接工序。ready_to_sign 时展示 contract_url、specification_url 和 first_step，企业明确签署后使用该版 document_digest、scope_version 准备 fixed_sign，由企业本人核对文件、勾选签署。pending、关闭页面或拒绝时继续待签。签署回执 returned receipt_id 后仅首道开工，其余读取各工序 fixed.started；前置验收和交接签收后再交付。多个起点中其余已就绪工序只能另行启动。旧项目继续按议价履约指引办理。
