# 提交交付与跟踪质检

接单人承接的工序进入“进行中”后，可以通过 OpRun 提交实际成果。交付走和网页相同的提交命令：准备 → 用户在 OpRun 网页确认 → 查询确认状态 → 执行 → 回查。提交只启动质检；发单方验收和结算是另外的操作，Agent 不能代为完成。

## 先读交付上下文

调用 `oprun_delivery_context(subject_id, project_id, node_pk)`。`node_pk` 来自 `oprun_match_project` 或接单收件箱，不是方案工具的字符串 `node_id`。返回内容：

- `node`：工序状态、版本、交付要求和验收标准。提交必须携带这里的 `version`。
- `deliveries`：历史交付版本，新版本在前；每版附 `quality_check`（执行状态、进度、判定、分数、问题和说明）。
- `files`：已上传到这道工序的项目文件，只有它们可以作为附件。
- `submit`：`allowed` 和 `reason`。原因：`not_assignee`（不是执行人）、`node_not_in_progress`（工序不在进行中）、`dependencies_not_ready`（前置工序未就绪）。方案验收、承诺书和前置依赖在提交时由 OpRun 再次核对。
- `stage`：`not_submitted`、`partial_submitted`、`quality_check_in_progress`、`rework_required`、`awaiting_acceptance`、`accepted`、`settled`。

发单方也可以读取自己项目工序的交付和质检进度（`role` 为 `publisher`），但不能提交。

## 附件

Agent 不上传文件，也拿不到存储凭据。成果文件由用户在 OpRun 的工序页面上传到该工序，再重新读取交付上下文，在 `files` 中取得 `file_id`。Agent 生成的文字成果可以写进交付说明（最多 5000 字）；较长的文档、代码包和二进制文件请用户上传后作为附件。

## 准备、确认和提交

1. 与用户确认交付说明、实际工时和附件，以及这是阶段交付（`partial`）还是最终交付（`final`）。不要替用户决定最终交付。
2. 调用 `oprun_prepare_delivery`，传入 `subject_id`、`project_id`、`node_pk`、当前 `version`、`submission_mode`、`summary`、`actual_hours`、`file_ids` 和本次意图唯一的 `request_key`。
3. 把原样返回的 `confirmation_url` 交给用户，由用户在 OpRun 核对内容后确认。打开页面不等于确认；关闭页面保持未确认。确认 5 分钟内有效。
4. 用 `oprun_action_status(action_id)` 查证状态为 `approved` 后，调用 `oprun_execute_action(action_id)`。
5. 执行成功表示“已提交”，工序进入质检。之后用 `oprun_delivery_context` 或 `oprun_action_status` 的 `current` 查看质检进度。

## 结果的含义

已上传、已提交、质检通过、发单方已验收是四个不同状态：

- 文件出现在 `files` 只表示已上传，还没有交付。
- 执行成功只表示已提交，质检可能仍在排队。
- 质检通过后工序进入 `awaiting_acceptance`，仍需发单方验收。
- 只有 `stage` 为 `accepted` 或 `settled` 时才能说发单方已验收；结算金额以 OpRun 为准。

质检判定为不通过、工序回到进行中时，`stage` 为 `rework_required`：按 `quality_check.issues` 修改后，重新读取上下文、以新版本准备一次新的提交。

## 冲突与恢复

- `version_conflict` 或 `node_not_in_progress`：重新读取交付上下文，必要时请用户重新确认，不要用旧版本重试。
- `file_unavailable`：附件不在该工序的项目文件中，请用户上传到这道工序后重新读取。
- 网络超时或结果未知：用原 `action_id` 查询或重试执行，不要用新的 `request_key` 再准备一次，以免重复提交。会话中断、没有原编号时，用 `oprun_recent_operations` 找回。
- `insufficient_scope`：连接缺少 `delivery:submit`（或只读连接），请用户重新授权。
