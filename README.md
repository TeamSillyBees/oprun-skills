# OpRun 新项目 Skill

通过同一条 `oprun-new` MCP 连接准备企业需求、查范围版本、议价、交付、查逐条质检报告、补证与复核。企业在第一方页面确认范围和验收。发单和接单用户分别登录授权，宿主按所选主体和项目关系显示可用工具。

把这句话发给你的 Agent：

> 请按 https://github.com/TeamSillyBees/oprun-skills/blob/main/INSTALL.md 安装或升级 OpRun 新项目 Skill，并用部署方给出的地址配置和检查 oprun-new。

支持写入 Skill 目录且运行 Node.js 22+ 的宿主可使用 npm/npx。Qveris、WorkBuddy 使用原生 ZIP 导入。从 1.5.0 升级后，在新会话选择 `oprun-new` 并重新授权。安装器会校验制品并为受管更新保存备份。新服务地址由部署方提供，仓库的配置使用占位地址。

2.0.0 固定到已合入的 MCP 来源。目标环境完成新连接验证后发布制品。安装与升级步骤见[安装指引](INSTALL.md)。

## 维护发布

Skill 内容的唯一来源是 oprun-mcp 仓库的 `skills/oprun-project-planning`，与服务端协议同仓维护，并由 OpRun MCP 以资源形式提供。**不要直接修改本仓库的 `skills/`**；修改先合入 oprun-mcp `main`，再同步到这里。本仓库只维护安装说明、通用连接示例、安装器、同步和打包工具。

1. 在 oprun-mcp 本地克隆中拉取最新 `main`，然后在本仓库运行（默认 `origin/main`，拒绝未合入 main 的提交）：

   ```sh
   python3 tools/sync.py --oprun-mcp ../oprun-mcp
   ```

   脚本按来源提交完整替换 `skills/oprun-project-planning/`，删除上游已移除的文件，并把来源提交写入 `release.json` 的 `mcp_revision`。核对差异后更新 `version`。

2. 运行 `python3 -m unittest discover -s tests` 和 `python3 tools/sync.py --oprun-mcp ../oprun-mcp --check`，确认 `skills/` 与记录的来源提交完全一致。

3. 提交并推送后打包。独立 INSTALL.md 链接到该提交，未推送时脚本拒绝打包；仅本地试打包可加 `--allow-unpushed`：

   ```sh
   python3 tools/package.py --output-dir dist/v<版本>
   ```

MCP 来源待合入时，用 `tools/sync.py --ref <完整提交> --allow-unmerged` 做本地试验。试验 npm 包包含 `private: true`，上传工具检查来源状态。发布资产时先创建绑定完整提交的空草稿，再运行 `python3 tools/upload_assets.py --directory dist/v<版本> --tag v<版本>`；核对下载后再正式发布。安装说明以 `text/plain` 上传，但 GitHub 下载层仍可能返回二进制类型；一句话接入使用仓库网页说明，下载入口仅供包管理工具使用。不覆盖既有正式资产。

输出可复现的 ZIP、安装指南、安装工具 `install.py`、通用及各宿主 MCP 配置（Skill 中的 `assets/qveris-mcp.json`）、`manifest.json` 与 `SHA256SUMS`。ZIP 即同步来的完整 Skill 目录；清单的 `skill_files` 列出每个成员的校验值，`mcp_revision` 是 Skill 来源提交，不代表线上当前版本。为新版本使用新的输出目录和版本标签；源码更新与 Release 发布分开执行，不覆盖旧资产。

Skill 的唯一维护源在 [oprun-mcp](https://github.com/TeamSillyBees/oprun-mcp)。

## npm 发布

npm 与 ZIP 使用相同的 `release.json` 版本、固定来源和逐文件摘要。先运行 `node --test tests/*.test.mjs`，再提交推送。构建器拒绝未提交内容、版本错配、覆盖旧制品和安装时自动执行的脚本。

```sh
node tools/package-npm.mjs --output-dir dist/npm-v<版本>
cd dist/npm-v<版本>
npm pack --ignore-scripts
```

发布前核对 npm 包名的所有权、包内文件清单，以及 `bundle.json` 和 ZIP `manifest.json` 中的 `skill_files`、`revision` 完全一致。使用已审核的 `.tgz` 执行 `npm publish <包文件> --access public --ignore-scripts`；首次发布和 npm 的双重验证由维护者完成，不记录凭据。正式 ZIP 和 npm 必须来自同一提交。用 `python3 tools/package.py --output-dir dist/v<版本> --npm-tarball dist/npm-v<版本>/oprun-skills-<版本>.tgz` 生成联合 Release，逐文件验证后把 npm 包作为 `oprun-skills.tgz` 纳入清单。分别下载验证后才报告发布完成。npm 发布失败时不要宣称 npm 注册表已可用，原 ZIP 安装保持可用；也可在固定的 GitHub Release 下载同版本 npm 包。

CLI 没有运行时依赖及安装钩子；`install` / `update` 仅在显式调用时写 Skill 目录。`doctor` 不读取 OAuth 凭据，不查询业务项目。npm 包不会在后台拉取新内容：更新使用 `npx oprun-skills@2.0.0 update`，需要固定版本时用 `@<版本>`。原 Python 安装器继续提供；两者兼容同一安装记录。
