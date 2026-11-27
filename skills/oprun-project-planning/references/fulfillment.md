# 按同版履约

## 读状态与恢复

企业和接单者用 `oprun_new_project_inbox` 查本人项目，再用 `oprun_new_project_read` 读取项目、范围版本和工序。视图只读。刷新与深链恢复时保留当前范围版本。使用网页回退时让用户完成登录，并核对网页显示的主体和版本。

先看当前连接的工具清单。只有旧版工具时，`oprun_new_project_list` 用 `next_cursor` 翻页，`oprun_new_project_deliver_validate` 用 `valid` 判断预检，阻塞项是错误码字符串。

工具返回错误时按文本错误信封中的 `hint` 处理。`subject_mismatch` 配 `omit_subject_id`：传入的 subject_id 不是当前授权主体，去掉它重试。`subject_forbidden` 配 `check_target_ids`：连接没有问题，是调用里的项目、工序或回执编号对当前主体不可见，从本人的列表重新取编号。`subject_forbidden` 配 `check_authorization`：当前主体的角色或授权做不了这件事。`unknown_tool`：工具名不在当前主体的清单里，按 did_you_mean 改用列出的名称，或读 `oprun_new_account_context` 的工具索引。

宿主报 `invalid_grant` 等授权错误时，保留原 `request_id` 和未答问题。宿主完成重新授权后核对当前环境、主体和工具清单，同一失败的读取最多重试一次。恢复后继续原查询并补答被中断的问题。失败仍存在时，按回执说明错误及受影响范围。有返回时保留错误码、可重试标记和请求编号。只说观察到的事实，例如「首次失败，重试一次后恢复，原因未查明」。

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
- `oprun_new_project_quality_read` 只在 delivery_version > 0 时调用，查看正式交付版本的逐条报告。版本 0 表示尚无正式交付。展示条款、状态和可复核证据。缺原件、缺执行结果、超时或无法判断时标待核。查看报告保留检查运行状态、结果及企业决定。
- 使用 `oprun_new_project_quality_review` 申请复核。确认对应条款、交付版、争议理由与证据位置。需更新制品时提交新版，按原条款重新查看报告。
- 企业用 `oprun_new_project_review` 准备人工验收或退回，在第一方页面确认。验收时需要同一范围、同一交付版及条款证据。退回时明确成果和条款。下游仅领取获权且已达到条件的具体制品版本。

## OPC 接单查询

1. 用 `oprun_new_account_context` 核对当前角色、主体及授权范围，按已核实的连接说明正式或测试环境。主体编号以 `subject_id` 或 `resolved_subject_id` 回执为准，业务调用默认省略 `subject_id`。`profile_id` 标识画像。连接或环境无法核实的部分标待核实。
2. 用 `oprun_new_project_list_v2` 的 `search` 按编号、可见标题或本人承接的工序名查询。结果有歧义时让用户选定，保持原查询范围。选定后用完整 `project_id` 和对应 `step_id` 读详情。有读取权限的受邀主体可见真实项目标题；project_no 为空时省略业务编号。
3. 工序、项目和结算各用同层级显示状态，例如 `step_status.label`、`project_status.label` 或结算的 `status_label`。宿主提供 `display_status` 或 `status` 时按对应层级引用。核对具体工序进度时，用同一工序、同版详情的 `state`、`started`、`delivery_version` 和 `next_action` 交叉检查，标出缺失或不一致之处。只有显式的 `waiting_on` 或 `action_owner` 能说明当前在等谁。等待企业选定或签署时说明等待主体和本人可做的事。
4. 动作资格取当前工序回执的显式可用动作（若有 `available_actions`）。交付资格先看 `can_deliver`、`deliver_blockers` 和警告，再按正式交付流程核对本次提交。工具清单只说明当前连接有哪些工具。说明时间时分别给出排期窗口、预估工时、实际开工时间。已知时间统一标注北京时间（UTC+08:00）。实际时间取对应事件，预估时长和状态字段只作各自用途。
5. 回答前复核币种和分转元、项目去重口径、已读取范围和失败事实。列表用 `next_project` 续传 `after_project`，全部读完才汇总全量。`fixed_work` 的 `view=assigned` 表示已选定本人，查询进行中的数量时还需按工序显示状态筛选。若本轮仅查询，在回复里注明只读。
6. 给出第一方记录链接时标注是否需要登录、是否已打开核对。收到页面正文或宿主成功渲染回执后，才能报告已打开。仅返回 `view_url`、`chat_url` 或附件链接时，注明入口未验证。卡片失败时如实给出回执诊断和实际返回的同项目回退链接。

## 阶段成果的两个入口

用户问「阶段成果在哪里」「怎么提交阶段成果」或要核验入口时，默认并列展示以下两项和各自的可用状态。指向当前工序中已核实的入口。缺少可用入口时说明查询结果。

| 入口 | 对应工具 | 保存结果 |
| --- | --- | --- |
| 阶段记录 | `oprun_new_project_progress` | 保存阶段进度，可用工序详情的 `latest_milestone` 回读。正式 `delivery_version` 保持原值 |
| 正式交付 | `oprun_new_project_delivery_form` 读交付要求，`oprun_new_project_deliver` 提交 | 按该工序的成果和验收条款提交，确认成功后产生正式交付版本 |

支持扩展表单时，从 `delivery_form.progress` 读取阶段记录字段、4000 字上限、工序版本和最后一次记录。`defaults` 为空。新客户端从 `requirements.outputs` 和 `requirements.acceptance` 读取要求，从 `artifacts` 读取可选制品，从 `submit_url` 和 `attachment_url` 打开提交页和上传页。顶层 `outputs`、`acceptance`、`attachments`、`uploaded_artifacts` 和 `delivery_url` 为兼容字段。附件由用户逐项选定。正式范围的预检和提交须传同一张表单的 `scope_digest`、`expected_version`、`invitation_id`、`invitation_version`。版本冲突时，`expected` 是当前版本，`actual` 是传入值。旧预检的 `blocker_details` 提供字段路径。按交付版本查询表单可从 `delivery_note` 回读已确认的说明；项目详情的当前交付说明在 `steps[].delivery.note`。

读取 `delivery_form` 的结果分为「交付要求」「附件上传入口」「已上传制品」。只有看到实际表单页面或取得成功渲染证据，才描述页面上可填的表单、控件或按钮。接口不可用时，对表单只写「表单不可读」。如已取得附件链接，可单独标为「附件上传页」，沿用链接的登录和验证状态。附件上传页不能替代阶段记录或正式交付入口。

保存阶段记录前展示待保存原文并取得用户明确确认，再调用 `progress` 准备第一方确认。获准保存后回读 `latest_milestone`。群内文字仅作沟通。

## 接单方正式交付

下列步骤必须依次完成。任一步缺失、失败或待核实，说明受阻步骤并停下。

1. 核对当前接单主体和工序，读取 `oprun_new_project_delivery_form`。分别展示交付要求（`outputs`、`acceptance`）、附件上传入口（`attachment_url`）和已上传制品（`attachments`）。记录当前工序的 `expected_version`、`delivery_version`、范围绑定、交付窗口、拦截原因和附件策略。`expected_version` 必须取自本次同一工序的回执。表单不可读、资格受阻或制品查询有警告时停在此步。`can_deliver=true` 只说明当前回执未列出这类资格阻塞，提交仍须完成后续步骤。
2. 列出 `attachments`，逐一核对拟用的项目 `artifact_id`、`asset_id`、文件名、字节数和 SHA-256。核对制品属于同一工序和范围，且内容满足验收条款。能获准读取制品时核对原文，也可用 SHA-256 相同的源文件核对。只有元数据、找不到必交制品或内容无法核对时停下。
   - 对于要求 JSON 含 `item`、`finding` 的 C3 成果，解析 JSON 后逐条检查所需字段。按工具的字符上限核对文本成果。附件核对文件名、编码、格式及 `attachment_policy.max_bytes`。
   - 对话附件只作会话文件来源。候选制品有歧义时请用户指定。测试附件仅限用户明确选定的隔离用例。需补传时先核对文件，获准后走项目上传页，再回读 `attachments`，报告「已上传，未提交」。
3. 用本次拟提交的同一工序、`expected_version`、范围、邀请绑定和完整成果参数调用 `oprun_new_project_deliver_validate_v2`。只有旧版工具时调用 `oprun_new_project_deliver_validate`。按回执逐条原样展示 `blockers` 的 `field` 和 `message`，字段缺失时标明未返回。旧版字符串阻塞项原样展示错误码。预检是只读操作。
4. 新版须明确返回 `ready=true`，旧版须明确返回 `valid=true`。核对预检返回的版本与本次 `expected_version` 相符，并按回执的交付窗口核对当前时刻。回执明确没有窗口时，注明无时段限制。预检未通过、有阻塞、窗口未核实或当前不在已返回的窗口内时，说明具体原因并停止。
5. 向用户列出项目、工序、成果项、将使用的项目附件编号和文件名、当前工序版本、当前正式交付版本及拟生成版本，请用户确认这组内容。纯文本成果展示拟提交的文本。范围、附件、内容或版本变化时，重新读取、预检并确认。
6. 仅在用户明确确认上述内容后调用 `oprun_new_project_deliver`。第一方确认按工具回执办理。同一次写入沿用请求键。在获准的写入流程中，用原 `request_id` 查请求状态，再用 `project_id` 和 `step_id` 回读。确认匹配的正式交付记录和 `delivery_version` 后，报告交付项、项目附件编号、正式版本、当前状态和下一步。`step_version` 是工序版本，`delivery_request_id` 只在回执关联到本人正式交付时引用。

## 交付表单验收

回答交付入口、表单或拦截验证问题时，逐项标出「只读可验证」「需页面操作」「需你授权写入」，说明已取得的证据和待验证项。写入型验收只在获准的隔离环境执行。

- **只读可验证**。读取交付要求、附件入口、已有制品、工序版本和历史交付。用符合输入 schema 的参数执行交付预检，核对版本、阻塞项和窗口。MCP 的正式文本成果 `content` 和阶段记录 `body` 都有 `minLength: 1`。空字符串在 schema 层被拒绝，这只验证输入约束，服务端或页面提示需要单独验证。
- **需页面操作**。打开实际表单，记录当前 `delivery_version`、必填项、控件和按钮初始状态。有页面正文或成功渲染证据才能报告界面所见。页面未打开或只读到了接口字段时，标明界面未验证。
- **需你授权写入**。保存阶段记录、上传附件、手动尝试提交（包括留空必填项）、调用 `deliver` 和本次提交后的回查属于写入验收流程。未经用户明确授权，停在只读检查或页面查看。获准在隔离环境测试后，留空验证应保留初始正式版本且无新提交回执。超限验证用真实上传端点，核对拒绝回执无新附件编号。补齐本次确认的制品并完成正式交付后，回查新版本仅递增一次，留存提示、按钮状态和脱敏回执。

## 交付验收与结算核对

1. 确认完整项目及工序编号，读详情并锁定正式 `delivery_version`，再用 `oprun_new_project_quality_read` 查同版质检，用 `oprun_new_project_fixed_settlement` 查该项目的验收和结算。需要互证所选工序时可加查 `fixed_work` 的 `view=assigned`。
2. 逐项核对成果项、交付物、附件名称、字节数及 SHA-256、质检条款、验收结果及平台返回的时间。核对是否按期交付时，用该版正式交付时间与同版窗口比较。缺少任一项就列为待核实。结果有分页时沿游标读完，未读完时明确已核对哪几页。项目金额按项目去重。
3. 整体验收的 `receipt_id` 用于核对验收。到账以同笔结算的权威财务回执为准，只有明确的 `payment_status=paid` 或有效的 `paid_at` 才能报告已到账。`finance_state=unverified` 或缺少到账证据时，按项目回执报告待结算等当前状态，并说明财务待核实。空的 `confirmed_income_fen` 保持待核实。
4. 按项目与工序、正式交付版本、质检、验收、待结算金额、财务状态、记录链接及未验证项汇报。记录链接标注登录要求和核验情况，涉及推断时附依据。
