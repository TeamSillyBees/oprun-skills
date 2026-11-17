# 独立需求工作区

仅当当前服务实际列出工具时使用；仍用原有 OpRun MCP 连接和 OAuth。需要 `plan:read` 和 `plan:generate`，并以 `oprun_account_context` 返回的当前主体权限为准。旧项目、匹配及交付仍使用原工具，不把旧项目 ID 当作 workspace_id。

1. 由对话整理完整需求文档，保留目标、交付、验收、限制和未决事项。用户未确定的事项保持待定，不设追问轮次硬上限。
2. 用户要求提交后，调用 `oprun_workspace_create(subject_id,title,body,request_key)`。主体不明确时先让用户选择。相同提交的网络重试保留同一 request_key；内容变化不能复用该键。
3. 调用 `oprun_workspace_generate(workspace_id,revision,request_key)`。它只排队，不表示方案已经完成。超时后先 read，再用同键查询/重试，不新建重复任务。
4. 用 `oprun_workspace_read` 查看状态、需求和方案历史。支持 MCP Apps 的宿主可以内嵌或侧栏显示；侧栏位置由宿主决定。其余用返回的网页链接，登录同一账号和主体后查看，URL 不带 Token。
5. 修改时读取当前完整文档，合并用户确认的差异，`revise(expected_revision,body)` 保存完整新版，再为新 revision 生成。409 先读取最新内容，不覆盖别人修改、不删未被授权删除的要求。
6. `needs_input` 说明有未确定条件，展示具体问题和已有草案，让用户继续补充；`failed` 说明生成/校验未完成，不能称为可执行方案。正常草案也不等于预算承诺或项目验收通过。

新工作区不能发布项目、撮合、议价、签署、支付或写旧项目。不得调用这些旧工具来绕过第一阶段边界。后续业务能力须单独确认。

调用不要传账号主键、密钥或内部身份断言；这些由服务端获取。算法 Prompt、评分参数、模型密钥和数据库连接不会返回客户端。
