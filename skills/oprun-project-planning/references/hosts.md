# 多宿主连接 OpRun

MCP 地址为 `https://www.agi.yifx.vip/mcp`。安装 Skill 后仍需在宿主添加 MCP 连接，再由宿主启动 OAuth；浏览器直接打开网站不会替宿主完成连接。以下配置针对本版本实现，是否已发布应以目标站点的 `/mcp/setup` 和授权元数据为准。

## 选择宿主配置

`/mcp/setup` 的 `profiles` 按宿主返回独立配置。将所需条目合并到该宿主配置中，保留其他连接。

| 宿主 | 入口和格式 | 回调特征与注意事项 |
| --- | --- | --- |
| QVeris Studio | [完整配置](../assets/qveris-mcp.json)或[只读配置](../assets/qveris-readonly-mcp.json)导入自定义 MCP；显式设置 `authMode`、`issuer`、`scope` | 1.0.22 使用动态注册及本机随机端口 `/callback`；授权地址不能留空，详见 [Qveris 指引](qveris.md) |
| WorkBuddy 桌面 | `profiles.workbuddy`；完整 `mcpServers` JSON，传输 `streamableHttp` | 已确认的私有回调为 `workbuddy://workbuddy/mcp/oauth/callback`；自动打开受阻时点击返回应用链接 |
| Cursor | `profiles.cursor`；`mcpServers` 下配置 `url` | 同一注册可含 HTTPS 云回调和 localhost 桌面回调；必须分别完整登记 |
| VS Code | `profiles.vscode`；`.vscode/mcp.json` 顶层为 `servers`，传输 `http` | 支持宿主自己的 HTTPS 元数据文档 ID；桌面回环与 `https://vscode.dev/redirect` 是不同回调；`vscode:mcp/install` 是安装链接，不是授权回调 |
| Claude Code | `profiles.claude_code.command` 的命令参数 | CLI 使用回环随机端口；localhost 与 127.0.0.1 不互换，由客户端实际登记决定 |
| Claude 云连接器 | 在设置的连接器入口填写 `profiles.claude_cloud.url` | 即使从桌面应用操作也可能是云端 HTTPS 回调；不能套用 Claude Code 的回环配置 |
| Codex | `profiles.codex.command` 的命令参数 | 自动注册或 CIMD 由宿主版本决定；资源 URL 与 MCP URL 一致，回环端口可变化，路径仍须登记一致 |
| ChatGPT | 在对应工作区的自定义 MCP／开发者连接器入口填写 `profiles.chatgpt.url`，认证 OAuth | 使用宿主生成的动态或稳定 HTTPS 回调；服务端已支持授权响应 `iss`，不要假定所有产品入口使用同一个回调 |

例如 VS Code 的完整配置为：

```json
{
  "servers": {
    "oprun": {
      "type": "http",
      "url": "https://www.agi.yifx.vip/mcp"
    }
  }
}
```

Claude Code：

```sh
claude mcp add --transport http oprun https://www.agi.yifx.vip/mcp
```

Codex：

```sh
codex mcp add oprun --url https://www.agi.yifx.vip/mcp --oauth-resource https://www.agi.yifx.vip/mcp
```

Codex 添加时即开始授权。不指定范围时申请全部功能，用户可在 OpRun 授权页选择“只允许查看”。只有该次授权未完成才执行 `codex mcp login oprun`；也可用 `codex mcp login oprun --scopes "plan:read match:read delivery:read"` 直接申请只读。

宿主不能在配置里指定范围时，授权页的“只允许查看项目、匹配和交付进度”会把连接收窄为 `plan:read match:read delivery:read`。添加命令成功仅说明配置已保存，继续完成浏览器授权，并调用 `oprun_account_context` 才能确认连接。

## 接单与发单能力

标准连接一次授权覆盖方案、发单、接单和交付；工具列表对所有授权都相同。早期只申请方案范围的旧连接不会自动扩大，需要发单或接单时重新授权，详见[匹配指引](matching.md)。不要为此更改账号权限。

## 方案展示

只有工具列表实际包含 `oprun_view_plan` 时才启用交互查看。它声明标准 MCP Apps 资源；资源通过宿主桥接读取数据，不获取网页登录 Cookie。

- WorkBuddy：安装版本 5.9.3 的只读代码探测确认支持 `_meta.workbuddy.ui.launchSurface=panel`，请求级展示偏好优先；实际摆放由宿主控制。此证据不是完整产品验收。
- 标准 MCP Apps 宿主：使用宿主允许的内嵌区域。VS Code 官方文档当前标为实验性内嵌能力；不能把所有版本视为支持侧栏。
- 未提供 UI、尚未验证或只支持命令行的宿主：使用工具返回的 `web_url` 登录查看。链接不含凭据，也不能转给其他账号越权查看。

授权连接成功、读取资源成功、实际界面展示成功是不同检查项。不要因为连接已通就报告右侧栏已通过验收；也不要通过安装无关扩展或修改浏览器安全策略强行嵌入页面。

## 客户端注册选择

默认使用宿主动态注册（DCR）。CIMD 由目标站点按部署启用，默认关闭；只有授权元数据返回 `client_id_metadata_document_supported: true` 时才选择 CIMD，缺失或为 `false` 时宿主应选择 DCR 或本文的受管公共客户端，只支持 CIMD 的宿主需等待站点启用。支持 CIMD 的授权元数据包含 `client_id_metadata_document_supported: true`，文档必须公开通过 HTTPS 返回 JSON，文档 `client_id` 与 URL 完全一致，且登记本次实际回调。文档不要包含 Cookie、密钥或用户凭据。若同时公布 `none` 与其他认证方式，OpRun 选择 `none + PKCE`；只有 `private_key_jwt` 的客户端不在本版本支持范围。

只有宿主明确提供手动公共客户端字段且自动模式不可用时，使用本版本已有的登记：

| 公共客户端 ID | 登记回调 |
| --- | --- |
| `oprun-workbuddy-v1` | `workbuddy://workbuddy/mcp/oauth/callback` |
| `oprun-claude-code-v1` | `http://localhost/callback`、`http://127.0.0.1/callback` |
| `oprun-codex-v1` | `http://localhost/callback`、`http://127.0.0.1/callback` |

上述 ID 无密钥，使用 `none` 和 S256 PKCE；回环端口可变化，路径和 query 不可变化。使用不同路径的宿主版本应保留自动注册/CIMD，不能强行套用已有 ID。其他手填 ID 不会自动注册。共享公共 ID 每次都需要用户确认。

这些规则的唯一权威说明是 OpRun 仓库 ADR 0056；Skill 不能改变目标站点的回调策略和受管列表。WorkBuddy 开放平台云连接器涉及不同的服务端凭据托管，本版本未发布或迁移到该形态。

## 定位失败与验收

按发现、注册、授权、回跳、换码、工具调用六个阶段排查。记录宿主名称及版本、失败路径、HTTP 状态、`error` 和 `stage`；不复制带参数的授权 URL、授权码、Cookie、Token 或完整回调响应。

- `401 invalid_token`：先区分尚未授权和已有令牌失效；Qveris 核对专用配置的 OAuth、issuer 与 Scope，重新授权后再刷新工具。错误中的 `stage` 为空不代表请求已完成 OAuth。
- `invalid_redirect_uri`：核对登记回调和实际回调，不能用通配符、任意 scheme 或修改主机绕过。
- `invalid_client_metadata`：核对公共客户端认证方式、授权类型和回调字段。
- `invalid_client`：DCR 过期时重建该连接；CIMD 检查公网 HTTPS 可达、JSON、字段和响应大小；预注册核对登记 ID。
- `invalid_grant`：重新授权；业务任务沿用原编号，不重复生成或保存。
- 浏览器已授权但宿主未继续：点击返回应用链接；仍失败时从宿主重新连接，勿反复提交旧授权页。

发布后的每个宿主版本至少完成：未登录连接、已登录允许与拒绝、回到宿主、`oprun_account_context`、`oprun_list_projects`、刷新、撤销后调用被拒绝。用无项目的账号也可验证连接，项目列表为空不表示授权失败。

仓库的协议矩阵覆盖上述宿主的代表回调形态，并验证错误边界；它不等同于各桌面应用或云产品的实际验收。

## 官方案例

- [MCP 客户端注册与 CIMD](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration)
- [Cursor MCP](https://prod.cursor.com/docs/mcp)
- [VS Code MCP 扩展与授权](https://code.visualstudio.com/api/extension-guides/ai/mcp)
- [Claude Code MCP](https://code.claude.com/docs/en/mcp)
- [Claude 自定义远程连接器](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)
- [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp)
- [ChatGPT 插件认证与 issuer 回传](https://developers.openai.com/plugins/build/auth)
- [WorkBuddy 云连接器规范](https://open.workbuddy.cn/docs/connector)

这些产品入口和选项可能随版本变化，使用宿主当前帮助核对；不把安装 deep link 当作 OAuth 回调。
