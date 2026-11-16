# 在 QVeris Studio 中连接 OpRun

适用于 QVeris Studio 的“自定义 MCP”。配置字段已核对桌面版 1.0.22；其他版本先检查导入后的表单，不把配置检查当成授权成功。

## 按任务选择配置

[方案](../assets/qveris-mcp.json)、[接单](../assets/qveris-worker-mcp.json)、[发单](../assets/qveris-publisher-mcp.json) 三选一。下面表格展示方案配置；接单和发单的 Scope 以所选文件为准。需要保留已有能力时按[匹配指引](matching.md)比较并合并范围，重新授权。方案配置不含接单权限。

## 配置并登录

1. 打开“自定义 MCP”。已有同站点 OpRun 连接时编辑这一条；没有时新增，保留其他连接和工具选择。
2. 在“从 JSON 配置导入”中粘贴上面选定的配置 JSON，点击“填入表单”。
3. 核对下表，再点击“保存并授权”，由用户在浏览器登录 OpRun 并确认授权。不要手填 Client ID、密钥或回调地址；客户端自动注册，使用 S256 PKCE 和本机随机端口回调。

| 表单字段 | 标准配置 |
| --- | --- |
| 连接器名称 | `oprun` |
| 连接方式 | 远程 Streamable HTTP |
| Server URL | `https://www.agi.yifx.vip/mcp` |
| 认证方式 | OAuth 登录授权 |
| OAuth 授权服务地址 | `https://www.agi.yifx.vip/mcp` |
| Scopes | `plan:read plan:propose plan:generate` |

用户只要求只读或已有只读连接时，保留对应只读 Scope；方案用 `plan:read`，邀请用 `match:read`，不要因导入配置扩大授权。用户指定其他 OpRun 站点时，同步替换 URL 和 issuer，并通过该站点的 [MCP 资源元数据](https://www.agi.yifx.vip/.well-known/oauth-protected-resource/mcp) 核对实际授权服务器；不要混用不同环境。

这里的授权服务地址是 **issuer**，不是 `/authorize` 授权页面，也不是 `.well-known` 元数据地址。OpRun MCP 的 issuer 带 `/mcp`；不要使用域名根路径的网页登录认证。以目标站点返回的 [授权元数据](https://www.agi.yifx.vip/.well-known/oauth-authorization-server/mcp) 为准，不照表单占位提示填写 `openid offline_access`。

**不要直接导入通用 MCP 配置。** 1.0.22 的 JSON 导入会将没有 `authMode: "oauth"`、也没有请求头的配置设为“无需认证”；授权服务地址留空时则默认使用服务域名根路径。专用配置显式保留 `authMode`、`issuer`、`scope` 三项。安装新版 Skill 不会更新已保存的连接，已有连接也须核对这三项。

令牌由 Qveris 保存。不要索取或复制网页 Cookie、OpRun 网页登录令牌、Qveris API Key，也不要把这些值填入连接或排错记录。

## 验证授权、工具和重连

- 授权回到客户端后，确认 OpRun 的工具列表已加载。只有“配置已保存”不足以判定成功。
- 在只启用 OpRun 连接器的对话中要求：“仅调用 `oprun_account_context` 检查连接，不列出项目、不生成或修改方案。”确认真实工具调用成功；文本回复本身不构成证据。
- 使用该连接的“验证并刷新”重新获取工具列表。需要确认重新建立连接时，可仅停用再启用这一条 OpRun 连接，恢复其原有工具选择，再执行同一只读检查。
- 如需验证应用重启后的恢复，由用户正常退出并重新打开 Qveris，再执行只读检查；不要为验收强制关闭用户应用。一次重连成功不等于已验证令牌到期后的自动刷新。

记录客户端版本、验证日期、授权是否回跳、工具是否加载、只读检查及重连结果。记录中不包含账号资料、项目内容、授权链接、回调参数或令牌。撤销授权、拒绝授权和到期刷新仅在实际测试后标记通过。

## 按症状排查

| 状态或错误 | 处理方式 |
| --- | --- |
| `POST /mcp` 返回 `401 invalid_token`，尚未出现授权页 | 检查认证方式是否为 OAuth，再核对 issuer 和 Scope；使用“保存并授权”或“重新授权”，不要反复点击刷新工具 |
| 授权地址留空，出现发现失败或客户端注册失败 | 填写站点的 `/mcp` issuer；1.0.22 默认找域名根路径，可能进入网页登录认证。不要修改 OpRun 的根 OIDC 配置 |
| `invalid_scope` | 使用所选场景的业务 Scope；方案只读用 `plan:read`，邀请只读用 `match:read`，不要添加 `openid offline_access` |
| 浏览器已授权，`/mcp` 仍返回 `401 invalid_token` | 未授权、令牌失效、错误站点或撤销均可能导致此错误；核对站点并在这一条连接上重新授权，不把所有 401 都归因于 Scope |
| `403` 且响应声明 `insufficient_scope` | 核对当前请求所需权限；仅在用户确实需要该操作时重新授权，不为加载工具默认申请发布或匹配权限 |
| `invalid_client` | 通过此连接的“重新授权”重新动态注册；保留其他连接，不手填另一个宿主的客户端 ID |
| `invalid_grant` | 使用新授权流程，不重复提交旧回调或授权码；业务任务沿用原编号，避免重复创建 |
| `invalid_redirect_uri` 或回跳未完成 | 核对客户端实际登记的回环地址和服务端策略；不要换成通配符或手改主机、端口、路径 |
| 方案工具正常，匹配工具缺失，匹配能力为 false | 对照[匹配指引](matching.md)申请 `match:read`／`match:propose` 并重新授权；不把此状态当作没有邀请 |
| 工具已加载，对话中仍不可用 | 检查该连接和所需工具是否启用，按宿主要求重载会话；无需重装 Skill 或扩大授权 |
| 错误的 `stage` 为空 | 当前服务端 MCP 传输入口可能不填此字段；记录客户端版本、无参数的请求路径、HTTP 状态和错误码，不推断为成功或模型问题 |

显式配置后仍失败时，区分发现、注册、授权、回跳、换码、MCP 调用六个阶段，提供不含秘密的错误信息。只返回 401 的情况不能证明已经完成授权。不要通过关闭服务端鉴权或共享静态令牌解决连接问题。

本页维护接入配置与排错步骤，不改变 OpRun 服务端或 Qveris 客户端代码。其他宿主见[多宿主指引](hosts.md)。
