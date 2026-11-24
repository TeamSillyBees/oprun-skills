# OpRun 新项目 Skill

通过同一条 `oprun-new` MCP 连接准备企业需求、查范围版本、议价、交付、查逐条质检报告、补证与复核。企业在第一方页面确认范围和验收。发单和接单用户分别登录授权，宿主按所选主体和项目关系显示可用工具。

把这句话发给你的 Agent：

> 请按 https://github.com/TeamSillyBees/oprun-skills/blob/main/INSTALL.md 安装或升级 OpRun 新项目 Skill，并按指引配置和检查 oprun-new。

支持写入 Skill 目录且运行 Node.js 22+ 的宿主可使用 npm/npx。Qveris、WorkBuddy 使用原生 ZIP 导入。从 1.5.0 升级后，在新会话选择 `oprun-new` 并重新授权。安装器会校验制品并为受管更新保存备份。正式环境的 MCP 地址为 `https://v2.agi.yifx.vip/mcp`，OAuth issuer 为 `https://v2.agi.yifx.vip/mcp-oauth`。

2.6.3 在回复正文中用「工序图」链接打开本次生成的版本，并用资料实际标题链接引用来源。安装与升级步骤见[安装指引](INSTALL.md)。

## 维护发布

Skill 内容的唯一来源是 oprun-v2 仓库的 `mcp/skills/oprun-project-planning`，与服务端协议同仓维护，并由 OpRun MCP 以资源形式提供。**不要直接修改本仓库的 `skills/`**；修改先合入 oprun-v2 `main`，再同步到这里。本仓库只维护安装说明、通用连接示例、安装器、同步和打包工具。

1.2.0 到 2.6.3 的版本来自 oprun-mcp。那个仓库已经带着完整历史并入 oprun-v2，不再接收改动，所以不要再从它同步：脚本会拒绝。这些版本在 `release.json` 里记录的来源提交在 oprun-v2 里同样存在，`--check` 照常能核对。

`release.json` 里的 `source_repository` 仍然是 `TeamSillyBees/oprun-mcp`。它是写进已发布清单的标识，MCP 服务器的清单和 INSTALL.md 用的也是这个值。要改的话三处一起改，作为一次专门的发布来做，不要顺手改。

1. 在 oprun-v2 本地克隆中拉取最新 `main`，然后在本仓库运行（默认 `origin/main`，拒绝未合入 main 的提交）：

   ```sh
   python3 tools/sync.py --source ../oprun-v2
   ```

   脚本按来源提交完整替换 `skills/oprun-project-planning/`，删除上游已移除的文件，并把来源提交写入 `release.json` 的 `mcp_revision`。核对差异后更新 `version`。

2. 运行 `python3 -m unittest discover -s tests` 和 `python3 tools/sync.py --source ../oprun-v2 --check`，确认 `skills/` 与记录的来源提交完全一致。

3. 提交并推送后打包。独立 INSTALL.md 链接到该提交，未推送时脚本拒绝打包；仅本地试打包可加 `--allow-unpushed`：

   ```sh
   python3 tools/package.py --output-dir dist/v<版本>
   ```

MCP 来源待合入时，用 `tools/sync.py --source ../oprun-v2 --ref <完整提交> --allow-unmerged` 做本地试验。试验 npm 包包含 `private: true`，上传工具检查来源状态。发布资产时先创建绑定完整提交的空草稿，再运行 `python3 tools/upload_assets.py --directory dist/v<版本> --tag v<版本>`；核对下载后再正式发布。安装说明以 `text/plain` 上传，但 GitHub 下载层仍可能返回二进制类型；一句话接入使用仓库网页说明，下载入口仅供包管理工具使用。不覆盖既有正式资产。

输出可复现的 ZIP、安装指南、安装工具 `install.py`、通用及各宿主 MCP 配置（Skill 中的 `assets/qveris-mcp.json`）、`manifest.json` 与 `SHA256SUMS`。ZIP 即同步来的完整 Skill 目录；清单的 `skill_files` 列出每个成员的校验值，`mcp_revision` 是 Skill 来源提交，不代表线上当前版本。为新版本使用新的输出目录和版本标签；源码更新与 Release 发布分开执行，不覆盖旧资产。

Skill 的唯一维护源在 [oprun-v2](https://github.com/TeamSillyBees/oprun-v2) 的 `mcp/skills/`。

## npm 发布

npm 与 ZIP 使用相同的 `release.json` 版本、固定来源和逐文件摘要。先运行 `node --test tests/*.test.mjs`，再提交推送。构建器拒绝未提交内容、版本错配、覆盖旧制品和安装时自动执行的脚本。

```sh
node tools/package-npm.mjs --output-dir dist/npm-v<版本>
cd dist/npm-v<版本>
npm pack --ignore-scripts
```

正式 ZIP 和 npm 包来自同一提交。用 `python3 tools/package.py --output-dir dist/v<版本> --npm-tarball dist/npm-v<版本>/oprun-skills-<版本>.tgz` 生成联合 Release，把 npm 包作为 `oprun-skills.tgz` 纳入清单。上传到草稿后下载校验，再把已合入 `main` 的提交发布为稳定版 GitHub Release。

正式 Release 发布时，工作流校验标签、来源提交、资产摘要和 ZIP 内容，随后用 [npm Trusted Publishing](https://docs.npmjs.com/trusted-publishers/) 将同一份 `oprun-skills.tgz` 发布到 `latest`。工作流重新从 npm 下载并比较包字节，重复运行会检查已发布版本。发布失败时，修复原因后重跑原工作流。GitHub Release 附件仍可直接安装。

首次启用时，npm 包维护者在 `oprun-skills` 的 Settings → Trusted publishing 选择 GitHub Actions，填写组织 `TeamSillyBees`、仓库 `oprun-skills`、工作流文件名 `publish-npm.yml`。环境名留空，启用直接执行 `npm publish`。在下一版就绪后绑定，npm 要求两天内首次发布成功。

CLI 没有运行时依赖及安装钩子；`install` / `update` 仅在显式调用时写 Skill 目录。`doctor` 不读取 OAuth 凭据，不查询业务项目。手动更新可运行 `npx https://github.com/TeamSillyBees/oprun-skills/releases/download/v2.6.3/oprun-skills.tgz update`。原 Python 安装器继续提供；两者兼容同一安装记录。
