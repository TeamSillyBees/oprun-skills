# 新项目发单、接单与交付

两个助手各使用其账号隔离的 OpRun OAuth 连接。先读取 `oprun_account_context`，选定用户指定的主体。下列工具前缀均为 `oprun_new_project_`，以当前连接的 `tools/list` 为准。读取同一账号的多个主体时逐一指定 `subject_id`，工具清单可能汇总多个主体的能力。

## 发单助手

1. 用工作区 read 查看当前需求和生成历史，向用户展示所选成功方案的内容。发布传 workspace_id、当前 revision、最新 run_id。确认页会列出工序及产物，用户确认后取得 project_id。
2. 读取项目与工序版本，再用 candidates 查看接单方自报技能与工序要求命中的词。将命中依据原样展示。空列表时等待合适的接单方登记，勿自行编造候选。用户选定后，用 invite 传 step_id、expected_version 和 profile_id。
3. 用 read 查看当前报价。quote 的 amount_fen 单位是人民币分，同时提交完整 terms 和带时区的 expires_at。只按用户授权的金额、条款和期限准备报价或还价。未获指示时询问边界。报价方在网页确认即同意该版本条款，对方用 agree 确认相同 quote_version 后才产生唯一执行人。
4. 收到交付后用 read 指定 step_id 查看文件名、文本、摘要和版本，按工序要求核对。用户决定后，用 review 指定 delivery_version、accept 或 return 和具体意见。

## 接单助手

1. 用户同意公开接单技能时，用 profile 登记其技能词。用 inbox 查看本主体的 provider_profile 和受邀工序。按项目 ID 和工序 ID 用 read 查看交付范围、产物、验收要求、最新报价和有效期。
2. 用户选择报价或还价后用 quote。用户决定接受对方报价时，重读条款再用 agree。只在工序返回 assigned 并核对 executor 与本方 profile_id 后报告已接单。
3. 使用 deliver 提交文件名及 UTF-8 文本内容。系统为每次提交生成版本与 SHA-256 摘要。退回时读取指定版本的反馈，修改后按最新工序版本重新交付。阅读 accepted 和对应交付版本后，才报告本工序验收通过。

## 确认和恢复

所有项目写调用携带本次意图的 request_key。收到 awaiting_confirmation 时，把服务返回的 confirmation_url 交给本人核对，助手等待本人操作。关闭页面保持待确认，拒绝后终止本次意图。确认之后用同一工具、同一参数及原键读取回执。报价成功与对方接受分开报告。

对话中断时先用 inbox 恢复工序及待确认操作，根据 next_step、next_request 分页。用 read 核实实时结果；已完成的回执始终对应其原始操作。subject_forbidden 时核对账号和授权，version_conflict、quote_expired 时重读最新条款或交付并获取用户对新内容的决定。workspace_unavailable 时保留项目 ID、工序 ID、版本和请求键，待恢复后读取。新项目业务只走新项目工具；存量项目沿用其既有工具。当前可交付文本文件；支付、外部签署不属于这套流程。
