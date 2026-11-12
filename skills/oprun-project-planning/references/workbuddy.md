# 在 WorkBuddy 中连接 OpRun

从 GitHub 安装 Skill 后，仍需创建 MCP 连接器。只导入 Skill 不会启动 OAuth；直接打开 OpRun 首页或授权管理页，也不能完成 WorkBuddy 的连接授权。

## 添加连接并授权

优先使用 WorkBuddy 当前提供的原生 MCP 配置和连接工具；没有这些工具时，引导用户在 MCP／连接器设置中新增自定义 MCP，或导入随包的 [workbuddy-mcp.json](../assets/workbuddy-mcp.json)。

- 名称：`oprun`。
- 地址：`https://www.agi.yifx.vip/mcp`；用户指定其他站点时替换为该站点的 `/mcp`。
- 传输：Streamable HTTP。随包 JSON 的 `streamableHttp` 用于 WorkBuddy 连接器导入；不同宿主或 CLI 的格式以其帮助为准，不全局替换用户已有配置。
- 认证：标准 MCP OAuth，不填写静态 Token，不选择要求手填凭据的认证方式。

已有同站点连接时直接复用。保存后在 OpRun 连接器上点击“连接”，由 WorkBuddy 发现授权服务器、注册客户端并打开登录页。登录和确认授权由用户完成；如果不能弹窗但宿主提供了授权链接，可让用户直接打开该链接。不要手动拼接 `/authorize` 或自行生成回调参数。

登录后用 `tools/list` 和 `oprun_account_context` 验证连接。真实调用成功后，按 [Skill 的连接收尾规则](../SKILL.md) 在回复末尾给出可用操作；用户只要求接入时，不自动列出项目或读取方案。尚未完成授权或验证时，只说明当前状态和下一步。

## 按失败阶段恢复

| 观察到的状态 | 下一步 |
| --- | --- |
| 只有 Skill，没有 OpRun 连接器 | 添加上述 MCP 连接，再点击连接；无需反复重装 Skill |
| 有连接器，但等待授权 | 使用该连接器的连接／授权操作；检查宿主是否给出登录链接 |
| 配置已保存，但当前会话没有工具 | 按宿主要求重新加载 MCP 或新建会话，再验证实际工具调用 |
| `invalid_grant`／授权过期 | 在同一连接器重新授权；沿用原业务任务或修改编号 |
| `invalid_client`／客户端注册失效 | 优先让宿主清除此 OpRun 连接的旧注册并重新注册；不支持时重新添加这一连接，再由用户授权 |
| 授权接口网络失败 | 记录失败阶段、请求路径和 HTTP 状态，检查网络后重试；不记录授权码、Cookie、Token 或带参数的授权链接 |

无登录弹窗时先确认连接器存在，再检查发现接口。正常流程为 MCP 返回 `401` 和 `resource_metadata`，资源元数据给出授权服务器，宿主读取其元数据后才发起注册与登录。OpRun 的 issuer 为站点的 `/mcp`；使用元数据中的端点，不把网站登录端点当成 MCP 授权端点。

参考：[WorkBuddy 连接器规范](https://open.workbuddy.cn/docs/connector)、[生产发现元数据](https://www.agi.yifx.vip/.well-known/oauth-authorization-server/mcp)。
