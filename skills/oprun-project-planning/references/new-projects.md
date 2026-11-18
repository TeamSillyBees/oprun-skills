# 新项目发单、接单与交付

两个助手各使用本人的 OAuth 连接。先用 `oprun_account_context` 选定主体，再读 `tools/list`。下文短名称的前缀是 `oprun_new_project_`。同一账号有多个主体时，权限和数据都按选中的 subject_id 判断。

## 发单助手

1. 用 workspace read 核对需求、最新成功的 run_id 和 revision。可用时调用 `oprun_workspace_assess`。有 plan 阶段缺口，请发单方补齐并生成新版。execution 或 acceptance 缺口留到开工或验收处理。publish 绑定上述版本，由发单方在网页核对成果、交接、验收要求和可协商档期后确认。
2. read 返回 scope_digest 时，工序范围已经冻结。用 candidates 查看 match_snapshot_id、每项成果的证据覆盖和缺口、可用档期。档期未知就标为待核。分页沿用同一快照和 next_offset。若候选人撤回资料，停止展示已撤回的依据。由候选首页取得新快照。网页确认时服务会复核资料授权和版本，过期、撤回或变更都需要重读。技能自报和基于本人经历的依据要分别说明。缺少证据可请接单方补资料；原始简历、联系方式留在本人授权页面。
3. 选定人选后用 invite 传 step_id、expected_version、scope_digest、match_snapshot_id 和 profile_id。尚未成交可以用 invitation_decide 的 withdraw 撤回，重新读取后用新快照邀请替补。即使再次邀请同一人，也要使用新 invitation_id；前次意向、报价及同意都不继承。接单方确认意向才进入议价。发单方可在原定工序和允许的档期内还价。
4. 用 read 核对最新报价、归属和有效期。agree 只接受对方的当前 quote_version。收到交付后按 asset_id、内容、文件摘要和验收条件逐项复核。review 要绑定 delivery_version。退回写明 return_asset_ids 和反馈，验收通过后核对实际状态。

## 接单助手

1. 用 profile 登记技能。profile_read 返回本主体的证据摘要及 profile_url。引导本人在网页补充原句、行动、成果和档期，随时可撤回授权。证据仅代表本人陈述，不能写成平台核验业绩。
2. 用 inbox 找邀请，用 read 查看本人受邀工序。绑定 scope_digest、invitation_id、invitation_version、expected_version，用 invitation_decide 选择 interested 或 decline。遇到“删掉测试、改交付格式再报价”等要求，说明范围已由发单方确认，可按原范围报价或拒绝邀请。接单助手不得更改工序、承诺交付范围外的内容，或把范围修改藏进报价或交付备注。
3. 对带 scope_digest 的工序，quote 携带 subject_id、step_id、expected_version、scope_digest、invitation_id、invitation_version 和本次 request_key；可协商内容仅含人民币分 amount_fen、有效期 expires_at 和可选的窗口内 delivery_at。沿用本次邀请和范围版本，不传自由文本 terms。报价成功后等待对方决定。确认 assigned 且 executor 等于本方 profile_id 后才报告已接单。
4. deliver 的 outputs 必须覆盖确认的每个 asset_id。文本项传 filename、content；已上传的附件项传本工序的 artifact_id。附件使用本人登录的交付上传页或业务 API，保留摘要。不得复用其他工序附件。退回后在原范围重交所有必交项，并读取新版本和验收结果。

## 中断与兼容

每个写操作带本次意图唯一的 request_key。awaiting_confirmation 时仅向用户展示服务返回的 confirmation_url，由对应账号本人确认。用 request_status 查看原 request_id。requires_refresh 表示原请求所依据的范围、资料或邀请已变化，先读工序和新快照，再请用户决定。已拒绝、过期或暂时读不到时，如实报告。重试先核对同一请求，避免重复动作。

inbox 的 next_step、next_request 和事件 next_event 分别推进；more_events 为 true 时继续取事件。事件用于定位，read 用于核对当前版本。scope_mismatch、version_conflict、quote_expired 或 snapshot_expired 时重读并重新确认。subject_forbidden 时核对主体和授权，服务中断保留原请求。历史工序 read 无 scope_digest 时使用既有 v1 文本交付及报价 terms；保持原工序范围。独立新项目工具不可用时，不把新项目写入旧项目系统。
