# 按同版履约

## 读状态与恢复

企业和接单者用 `oprun_new_project_inbox` 查本人项目，再用 `oprun_new_project_read` 读取项目、范围版本和工序。视图只读。刷新与深链恢复时保留当前范围版本。使用网页回退时让用户完成登录，并核对网页显示的主体和版本。

执行外部写入前检查工具清单、主体、业务关系及版本。需用户确认时交给返回的第一方页面。关闭页面、断线或未知结果时先查 `oprun_new_project_request_status` 和业务状态，找不到回执再用原输入与原 `request_key` 继续。需要修改提交内容时使用新键。版本冲突时重新读并按新的版本确认。

## 保存接单技能

用户明确要保存自报技能时，使用当前接单主体调用 `oprun_new_project_profile`。收到 `completed` 后用 `oprun_new_project_profile_read` 读取 `profile.matching_skills`，通过同一会话继续导入。管理员代导入库后，直接调用读工具获取该字段，无需再提交技能。遇到旧请求的 `awaiting_confirmation`，以原参数和 `request_key` 重试同一个工具。`requires_refresh` 时读取当前画像，再按用户需要提交。匹配证据授权可在画像页随时管理。

## 候选和议价

- `oprun_new_project_candidates` 查看冻结工序的候选证据、覆盖和仍缺的条件。
- 固定价工序查询成功且候选列表为空时，只展示回执的 `message`「等待 OPC 接单，接单后可确认签署。」发邀、接单、选定及签署权限仍以相应回执为准。
- 企业通过 `oprun_new_project_invite` 准备正式邀请。受邀主体通过 `oprun_new_project_invitation_decide` 准备答复。发单主体可按服务端允许的动作撤回未成交邀请。
- `oprun_new_project_quote` 提交本邀请内的价格与有效期，`oprun_new_project_agree` 由对方确认确切有效版本。按已确认回执判断实际执行人。

## 交付、质检与验收

- `oprun_new_project_deliver` 按本人有效分配提交实际成果或获准制品引用。每个必交资产使用对应 `asset_id`。重交保留旧交付历史。
- `oprun_new_project_quality_read` 查看特定交付版的逐条报告。展示条款、状态和可复核证据。缺原件、缺执行结果、超时或无法判断时标待核。查看报告保留检查运行状态、结果及企业决定。
- 使用 `oprun_new_project_quality_review` 申请复核。确认对应条款、交付版、争议理由与证据位置。需更新制品时提交新版，按原条款重新查看报告。
- 企业用 `oprun_new_project_review` 准备人工验收或退回，在第一方页面确认。验收时需要同一范围、同一交付版及条款证据。退回时明确成果和条款。下游仅领取获权且已达到条件的具体制品版本。
