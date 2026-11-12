# 多宿主连接 OpRun

MCP 地址为 `https://www.agi.yifx.vip/mcp`。安装 Skill 后仍需在宿主添加 MCP 连接，再由宿主启动 OAuth；浏览器直接打开网站不会替宿主完成连接。本包可以先于服务端更新安装。下列新增能力对应 OpRun 源码 `1659eef336b37024f28e32976aa36598c2204d1a`；这个提交标识不代表目标站点已发布。接入时读取目标站点的 `/mcp/setup` 和授权元数据，并核对服务端发布说明。

## 先核对服务端能力

- 元数据提供 `registration_endpoint` 时，默认沿用宿主动态注册（DCR）和 S256 PKCE。
- `/mcp/setup` 尚无 `profiles` 时，使用宿主原生配置、下文示例或随包的 [WorkBuddy 配置](../assets/workbuddy-mcp.json)；缺少 `profiles` 不表示现有 DCR 接入不可用。
- WorkBuddy 原生回调、受管公共客户端 ID、回环端口变化和授权响应 `iss` 需要相应服务端修复上线。Skill 安装不能启用这些服务端能力；未上线时保留可用的原连接，将不受支持的回调报为待服务端升级，不反复重装或修改回调绕过校验。
- 只有授权元数据明确返回 `client_id_metadata_document_supported: true` 才选择 CIMD；缺失或为 `false` 时使用 DCR。只支持 CIMD 的宿主需等待服务端出站网络就绪并启用该能力。

## 选择宿主配置

服务端提供 `/mcp/setup` 的 `profiles` 时，按宿主选择独立配置。将所需条目合并到该宿主配置中，保留其他连接。

| 宿主 | 入口和格式 | 回调特征与注意事项 |
| --- | --- | --- |
| WorkBuddy 桌面 | `profiles.workbuddy`；完整 `mcpServers` JSON，传输 `streamableHttp` | 已确认的私有回调为 `workbuddy://workbuddy/mcp/oauth/callback`；自动打开受阻时点击返回应用链接 |
| Cursor | `profiles.cursor`；`mcpServers` 下配置 `url` | 同一注册可含 HTTPS 云回调和 localhost 桌面回调；必须分别完整登记 |
| VS Code | `profiles.vscode`；`.vscode/mcp.json` 顶层为 `servers`，传输 `http` | 支持宿主自己的 HTTPS 元数据文档 ID；桌面回环与 `https://vscode.dev/redirect` 是不同回调；`vscode:mcp/install` 是安装链接，不是授权回调 |
| Claude Code | `profiles.claude_code.command` 的命令参数 | CLI 使用回环随机端口；localhost 与 127.0.0.1 不互换，由客户端实际登记决定 |
| Claude 云连接器 | 在设置的连接器入口填写 `profiles.claude_cloud.url` | 即使从桌面应用操作也可能是云端 HTTPS 回调；不能套用 Claude Code 的回环配置 |
| Codex | `profiles.codex.command` 的命令参数 | 自动注册或 CIMD 由宿主版本决定；资源 URL 与 MCP URL 一致，回环端口可变化，路径仍须登记一致 |
| ChatGPT | 在对应工作区的自定义 MCP／开发者连接器入口填写 `profiles.chatgpt.url`，认证 OAuth | 使用宿主生成的动态或稳定 HTTPS 回调；仅在元数据声明支持时要求授权响应 `iss`；不要假定所有产品入口使用同一个回调 |

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
codex mcp login oprun
```

只读连接可在宿主支持时指定 `plan:read`。添加命令成功仅说明配置已保存，继续完成浏览器授权，并调用 `oprun_account_context` 才能确认连接。

## 客户端注册选择

默认使用宿主动态注册（DCR）。CIMD 需服务端验证宿主元数据的公共 HTTPS 出站访问后，显式设置 `OPRUN_MCP_OAUTH_CIMD_ENABLED=true` 才启用；运营端能力状态与发现元数据同步。关闭时宿主应选择 DCR，或服务端已部署支持的受管公共客户端，仅支持 CIMD 的宿主需要先完成出站网络配置。支持 CIMD 的授权元数据包含 `client_id_metadata_document_supported: true`，文档必须公开通过 HTTPS 返回 JSON，文档 `client_id` 与 URL 完全一致，且登记本次实际回调。文档不要包含 Cookie、密钥或用户凭据。若同时公布 `none` 与其他认证方式，OpRun 选择 `none + PKCE`；只有 `private_key_jwt` 的客户端不在本版本支持范围。

只有宿主明确提供手动公共客户端字段且自动模式不可用，且目标服务端已部署对应登记时，才使用以下公共 ID；不要仅按 Skill 版本填写：

| 公共客户端 ID | 登记回调 |
| --- | --- |
| `oprun-workbuddy-v1` | `workbuddy://workbuddy/mcp/oauth/callback` |
| `oprun-claude-code-v1` | `http://localhost/callback`、`http://127.0.0.1/callback` |
| `oprun-codex-v1` | `http://localhost/callback`、`http://127.0.0.1/callback` |

上述 ID 无密钥，使用 `none` 和 S256 PKCE；回环端口可变化，路径和 query 不可变化。使用不同路径的宿主版本应保留自动注册/CIMD，不能强行套用已有 ID。其他手填 ID 不会自动注册。共享公共 ID 每次都需要用户确认。

服务端规则与受管列表由 OpRun 服务仓库的 ADR 0056 及回调策略维护；本仓库分发安装说明，不能改变目标站点策略。WorkBuddy 开放平台云连接器涉及不同的服务端凭据托管，本版本未发布或迁移到该形态。

## 定位失败与验收

按发现、注册、授权、回跳、换码、工具调用六个阶段排查。记录宿主名称及版本、失败路径、HTTP 状态、`error` 和 `stage`；不复制带参数的授权 URL、授权码、Cookie、Token 或完整回调响应。

- `invalid_redirect_uri`：核对登记回调和实际回调，不能用通配符、任意 scheme 或修改主机绕过。
- `invalid_client_metadata`：核对公共客户端认证方式、授权类型和回调字段。
- `invalid_client`：DCR 过期时重建该连接；CIMD 检查公网 HTTPS 可达、JSON、字段和响应大小；预注册核对登记 ID。
- `invalid_grant`：重新授权；业务任务沿用原编号，不重复生成或保存。
- 浏览器已授权但宿主未继续：点击返回应用链接；仍失败时从宿主重新连接，勿反复提交旧授权页。

发布后的每个宿主版本至少完成：未登录连接、已登录允许与拒绝、回到宿主、`oprun_account_context`、`oprun_list_projects`、刷新、撤销后调用被拒绝。用无项目的账号也可验证连接，项目列表为空不表示授权失败。

OpRun 服务仓库的协议矩阵覆盖上述宿主的代表回调形态，并验证错误边界；它不等同于各桌面应用或云产品的实际验收。服务监控的进程计数同样不构成宿主验收结果。

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
