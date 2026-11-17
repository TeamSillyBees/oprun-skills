# 中断和连接恢复

只认可对应 OpRun 工具的业务回执。宿主 `discover` / 搜索结果、其他连接器返回、截断文本不是方案生成结果；不据此宣布成功、失败或重新生成。先核对连接来源、工具名、主体和 task_id / workspace_id / revision。request_id 用于排查一次请求，不是业务任务编号。

| 原操作 | 只读恢复 |
|---|---|
| generate_plan / supplement_plan | plan_result(subject_id, task_id, version?)；省略 version 查询最新版本，明确区分原稿和当前稿 |
| evaluate_plan | planning_result(workspace_id, task_id)；不能用 plan_result 替代 |
| open_planning | planning_context(workspace_id) |
| 变更 / 准备操作 / 文件上传 | change_status(change_id) / action_status(action_id) / upload_status(upload_id) |

有 recent_operations 的 check_arguments 时原样用于其 check_with。索引只辅助找编号，不证明业务状态；has_more 仅说明此次返回有截断，不保证更早记录仍存在。旧索引无法确定任务来源时，使用已有确认链接、用户保留的引用或原回执补齐上下文，不猜编号、不挪用其他主体或连接器的记录。恢复查询不授权再次保存、签署或执行。

连接检查用 account_context。若宿主报告连接不存在/工具停用，或服务返回 invalid_token，说明当前无法核实，提示启用连接或重新授权；insufficient_scope 只补所需授权。恢复后先查原状态，不换 request_key 自动重试写入。若宿主未提供连接删除事件，只能在下一次检查/调用时发现，不宣称可即时监听。

已知任务仍排队/执行时遵循 poll_after_ms；终态不轮询。progress 的 observed_at 是服务器查询时刻，stage_updated_at 是阶段最近变化时刻，不是心跳或预计完成时间。完成、失败或取消后的经过时长应固定；缺失时间显示未知，不用客户端计时冒充服务端执行时长。
