# 接单与发单匹配

一个 OpRun 连接覆盖方案、发单和接单。Scope 只决定连接能发起哪些操作；项目归属、邀请归属、身份认证和业务状态每次调用都由 OpRun 重新校验，每个写操作仍需用户在 OpRun 网页逐次确认。

## 检查能力与恢复连接

标准连接申请全部 17 项：`plan:read plan:propose plan:generate plan:publish match:read match:propose delivery:read delivery:submit files:read files:write execution:read execution:propose acceptance:propose release:propose funding:propose settlement:read settlement:propose`。不在配置里写 Scope 的宿主会得到同样的完整申请；用户可在 OpRun 授权页选择“只允许查看”，此时只授予 `plan:read match:read delivery:read files:read execution:read settlement:read`。QVeris 必须在配置里写明 Scope，使用[完整配置](../assets/qveris-mcp.json)或[只读配置](../assets/qveris-readonly-mcp.json)。

工具列表对所有授权都相同，不要用“工具是否存在”判断能力。开始前调用 `oprun_account_context`：

- `server_features` 含 `stable_tool_list` 和 `capability_reasons` 时，按各身份的 `capabilities` 选择操作；不含时说明目标站点较旧，按实际工具和返回错误处理。
- 每项能力给出 `allowed` 和 `reason`：`scope_missing` 需重新授权；`ai_consent_required` 需在 OpRun 确认该身份的 AI 服务授权；`subject_not_worker` 表示该身份没有接单收件箱，换用 `kind` 为 `worker` 的身份；`not_supported` 表示站点暂不提供。提交交付见[交付指引](delivery.md)。`checked_on_use` 为 true 的能力还要在调用时核对项目权限和业务状态。
- `missing_scopes` 非空表示此连接不是完整授权。用户需要缺少的功能时，引导在宿主中重新授权 OpRun 连接；刷新工具、刷新令牌、重装 Skill 都不会扩大旧授权。
- `default_subject_id` 只在恰好一个可用身份时返回。多个身份时按项目归属和用户意图选择，存在歧义再询问；写操作始终显式传 `subject_id`，换身份后重新读取项目，不沿用另一身份的上下文。

调用返回 `insufficient_scope` 时，结果里的 `required_scopes` 是任一可启用该工具的授权，`next_action` 为 `reauthorize`。告诉用户需要重新授权的功能，不要重试，也不要说成“没有邀请”或“没有项目”。

| 工具 | 授权 |
| --- | --- |
| `oprun_match_inbox`、`oprun_match_project`、`oprun_match_candidates` | `match:read`，并按实际业务身份限制读取 |
| `oprun_prepare_match` | `match:propose` |
| `oprun_prepare_publication` | `plan:publish` |
| `oprun_action_status`、`oprun_execute_action` | `match:propose` 或 `plan:publish`，只能处理本连接有权访问的操作 |

常见拒绝原因：`subject_not_worker`（该身份没有收件箱）、`project_unavailable`（当前身份看不到该项目）、`project_permission_required`（只有发单方或项目管理者能邀请、选定或撤回）、`invitation_not_owned`（邀请不是发给当前身份的）、`invitation_state_changed` 和 `version_conflict`（重新读取后再准备）、`candidate_unavailable`（重新读取候选）。记录无秘密的错误码和 `request_id`，不要把拒绝说成没有数据。

## 接单

1. 调用 `oprun_account_context`，从真实结果选择 worker 身份，固定 `subject_id`。不猜测身份编号。需要接单操作时，确认该身份 `can_read_matching` 和 `can_propose_matching` 均为 true。
2. 调用 `oprun_match_inbox`，必须传 `subject_id`；分页沿用返回的 `next_cursor`，不要重复读取第一页。下面仅适用于账号上下文实际返回 `login` 的情况：

```json
{"subject_id":"login","limit":20}
```

3. 展示邀请的交付描述、预计工时、接单金额与状态。缺失或待核实金额不能自行补算。收件箱是待决定邀请，不是完整历史；需要更多交付条款时，用 `oprun_match_project` 传入同一 `subject_id`、`project_id`，从 `nodes` 中按 `node_pk` 查找。
4. 用户明确要接受或拒绝后，调用 `oprun_prepare_match`。使用真实返回值填写以下参数，不猜测版本：

| 参数 | 来源 |
| --- | --- |
| `subject_id` | 已选择的 worker 身份 |
| `project_id`、`node_pk` | 目标邀请；`node_pk` 不是方案工具的字符串 `node_id` |
| `version` | 收件箱的 `node_version`，或最新匹配节点的 `version` |
| `invitation_id`、`invitation_version` | 同一邀请及其最新版本 |
| `action` | `accept` 或 `decline` |
| `request_key` | 本次意图的唯一幂等键；同一请求重试沿用原键 |

5. 展示结果与原样返回的 `confirmation_url`，由用户在 OpRun 确认；接受时还需核对当前项目承诺书。不要拼接链接、代替用户勾选或把打开页面当作确认。确认页不支持 iframe，宿主内嵌无法登录时使用系统浏览器。
6. 用 `oprun_action_status(action_id)` 查证；仅在已确认且允许执行时调用 `oprun_execute_action(action_id)`。关闭页面保持未确认，拒绝则停止。接受意向成功通常为 `pending_enterprise`，表示等待发单方选定，不是已接单完成。
7. 保留项目、工序和邀请引用，用 `oprun_match_project` 跟踪最终状态。邀请从待决定收件箱消失不代表被撤回或已选定。只有目标工序为 `assigned`、`matched=true`，且执行人和自己的邀请身份相符，才报告“已被选定”；仅 `matched=true` 不足以证明本人被选定。引用不足时明确无法核实，不猜测本人 worker_id。

## 发单

1. 先确定真实发单身份与能力。用户已有项目时直接读取项目，不重新生成或发布。
2. 用户要求新建并发布时，`oprun_prepare_publication` 只接受 OpRun 生成的任务：先告知将委托小君生成并使用所选身份的模型额度，用户同意后再用 `oprun_generate_plan` → `oprun_plan_result` 获取方案。当前 Agent 编写的草稿走 SKILL 的保存流程，不能直接发布。准备发布使用 `oprun_prepare_publication`，传入原 `subject_id`、`task_id`、精确 `version`、结果中的 `direction` 和 `request_key`。不把宿主自编 JSON 或预览任务编号当成正式项目。
3. 用户确认承诺书后，按上述“查询状态 → 执行”流程取得正式 `project_id`。只有收到业务回执并核对原任务对应项目后才报告创建成功。
4. `oprun_match_project` 读取实际工序及版本；`oprun_match_candidates` 使用同一身份、项目和 `node_pk` 分页获取真实候选。空列表明确说明，不虚构人选。
5. 用户选择候选后，用 `oprun_prepare_match(action=invite)`，携带 `worker_id`、当前工序 `version` 和独立 `request_key`；用户网页确认后执行。
6. 对方接受意向后重新读工序和邀请版本，用 `action=select` 准备最终选定；携带邀请及版本，仍需用户确认后执行。撤回使用 `withdraw`，也走同一确认流程。
7. 回查同一项目和工序，核对 `assigned`、`matched=true` 与用户选定的唯一执行人。匹配完成不代表已付款、开工或交付验收。

## 状态与异常

- `awaiting_confirmation`、`approved`、`executing`、`completed` 是操作状态；`pending_opc_confirm`、`pending_enterprise`、`assigned` 是工序状态。一次操作 completed 不等于整个项目匹配完成。
- 网络超时或回包丢失时，先用原 `action_id` 查询，再按允许的下一步恢复；不换新 request_key 重做结果未知的操作，不重复生成项目或邀请。
- 确认过期或工序／邀请版本变化时，重新读取并准备新操作，请用户确认新内容；不要循环提交旧版本。
- 重新授权后旧操作可能无法访问。按项目和邀请的业务状态恢复，不能假定旧确认仍有效；历史回执与实时状态分别说明。
- 安装及连接检查只调用工具列表和账号上下文。真实接受、拒绝、选定、撤回及发布会改变业务数据，须在用户实际任务或明确授权的隔离验收范围内执行。

协议与权限规则以 OpRun 仓库 ADR 0056 为准；本页与服务端同仓维护，所装版本与线上版本的核对方法见[更新与兼容](updates.md)。Skill 不修改服务端、权限或账本；本地验证不等于真实接单闭环已验收。
