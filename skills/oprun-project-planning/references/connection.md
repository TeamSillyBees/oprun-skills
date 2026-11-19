# 共用新项目连接

在宿主中把 `oprun-new` 的地址设为 `https://v2.agi.yifx.vip/mcp`。正式环境的 OAuth issuer 为 `https://v2.agi.yifx.vip/mcp-oauth`。使用其他部署时，将模板中的地址和 issuer 一起换成该部署的资源地址及其元数据公布的授权服务地址。发单与接单助手可以使用同一份配置。每位用户在各自宿主会话授权并选择本人的主体。

优先让宿主通过受保护资源元数据发现授权服务。若宿主另需填 issuer，使用该元数据返回的授权服务地址。授权使用 S256 PKCE。允许的能力由发单或接单主体及授权范围共同确定，超出代理权限的动作继续交给第一方确认页。

- 规划和确认：`plan:read`、`plan:propose`、`plan:generate`、`plan:publish`。
- 候选与议价：`match:read`、`match:propose`。
- 交付、质检和验收：`delivery:read`、`delivery:submit`、`quality:read`、`quality:review`、`acceptance:propose`。

升级时显式新增或选择 `oprun-new`，重新 OAuth 授权。保留宿主中其他连接和用户配置。切换主体时重新授权并读取 `oprun_new_account_context`。遇到令牌过期或被撤销时重连，遇到权限不足时确认当前主体和授权。凭证由宿主处理，写入聊天的内容只包含业务定位和脱敏回执。
