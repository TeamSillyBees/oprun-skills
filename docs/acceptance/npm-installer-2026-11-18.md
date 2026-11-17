# npm 安装器验证

日期：2026-11-18。目标版本：1.4.0。范围：oprun-skills 安装与分发，不改 OpRun / MCP 业务服务。

## 已验证

- 11 项 Node 定向用例、33 项现有 Python 用例通过。
- 实际 `npm pack` 制品通过 `npm exec --package <tgz> -- oprun-skills` 安装及离线检查；未安装 Python 依赖，没有运行时 npm 依赖。
- npm 与 ZIP 的 Skill 逐文件摘要、来源提交、版本一致；联合 Release 对 npm 包全部成员和脚本字节进行核验。
- 重复安装不改 Skill 内容；兼容原 Python 安装记录；不同内容更新保留原件，本地修改和降级被阻止。
- 更新切换失败可恢复旧目录；并发锁、软链接、非法文件名、损坏记录、同版本内容冲突均有回归。
- 既有 MCP 配置和 OAuth 授权不被写入；Qveris 配置保留 issuer、OAuth、scope，只读配置只包含读取权限。
- 公开 OAuth 资源发现及 S256 PKCE 检查通过；检查不读取令牌、不查询项目、不执行业务动作。
- Skill 与固定 oprun-mcp 来源 `7a2f5da2b1f96e18e224fa428873a0407dc2589b` 一致。

## 边界

- 本轮运行环境为 macOS、Node.js 26.10.0、npm 11.19.1。声明最低 Node.js 22；Windows、Linux 和 Node.js 22 的系统级实机验收未执行。
- doctor 的“公开发现通过”不等于用户 OAuth 或工具调用通过。实际登录仍由客户端完成。
- 桌面客户端不能执行命令时继续原生 ZIP 导入；不声称 npm 能自动替换 Qveris 技能库。此前 Qveris OAuth、43 项工具加载、重连与 account_context 的记录见同目录 `qveris-2026-11-18.md`，本轮未重新执行这些客户端动作。
- 发布前检查不等于注册表发布成功；注册表与 GitHub Release 均须发布后下载验证。

## 恢复

更新输出 backup 路径，目录位于 Skill 扫描目录之外。恢复前核对旧备份的 `.oprun-install.json` 和逐文件摘要，再保存当前目录并还原；不得覆盖后续本地修改。旧 ZIP Release 和 Python 安装入口保留。

## 发布后核验

- 制品提交：`82c868868f75f99c86b10b5164059de3002348bc`。
- [GitHub v1.4.0](https://github.com/TeamSillyBees/oprun-skills/releases/tag/v1.4.0) 的 10 个资产已全部下载，逐字节及 SHA-256 与本地制品一致。
- [npm oprun-skills 1.4.0](https://www.npmjs.com/package/oprun-skills/v/1.4.0) 正式可下载，latest 指向 1.4.0；下载 tarball 与 GitHub 和本地制品逐字节一致。
- 使用全新缓存、隔离项目分别从 GitHub 和 npm 执行 npx 安装、重复更新和 doctor 均通过。全部 Skill 文件与 ZIP 清单一致，公开发现通过，OAuth 与工具状态仍如实保留为未检查。
- 发布初次受 npm 2FA 限制，维护者完成发布后已核验正式版本；未绕过认证、未修改业务服务。
