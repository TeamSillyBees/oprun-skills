# oprun-skills

公开仓库，分发 OpRun 新项目 Skill：Skill 的校验副本、安装器、同步和打包工具。这里发布的 GitHub Release 和 npm 包 `oprun-skills`，所有用户都能装到。

## 改什么、在哪里改

- `skills/` 是 oprun-v2 里 `mcp/skills/oprun-project-planning` 的校验副本，不在这里改。Skill 正文要改，就在 oprun-v2 里按它的流程改、合入它的 `main`，再由维护者用 `tools/sync.py --source <oprun-v2 的检出>` 同步过来。手改的内容会被下一次同步覆盖，`--check` 也会报错。
- 这里可以改的：安装器和命令行工具（`cli/`、`tools/install.py`），同步、打包和上传工具（`tools/` 下其余脚本），测试（`tests/`），`INSTALL.md`、`README.md`、`mcp.json`。
- 只由维护者改：`.github/workflows/`、`release.json`、`package.json` 的版本号、`.gitattributes`。它们决定发布什么、以谁的身份发到 npm。

## 提交改动

- 从最新的 `main` 开分支，改完开 PR。不直接推送到 `main`，不强制推送，不改写已经推送的历史。
- 推送和开 PR 之前，要使用者明确说过提交。合并要使用者明确说过合并，并由维护者审过之后合并。
- 不替任何人在 PR 上批准，也不撤销别人的审查意见。
- 提交之前跑这两组测试，并在 PR 里写明结果：

  ```sh
  python3 -m unittest discover -s tests
  node --test tests/*.test.mjs
  ```

  Windows 上 Python 测试用 `py -3` 代替 `python3`。Node 测试里有一条会直接调用 `python3`，在 Windows 上会因为找不到它而失败，这组测试放到 WSL 或 Linux、macOS 上跑。改了同步相关的代码，再对着 oprun-v2 的检出跑一次 `python3 tools/sync.py --source <oprun-v2 的检出> --check`。跑不通的如实写出来，不要说成通过。
- 真实的令牌、密码不进仓库，写在测试里的也不行。

## 发布

- 只有维护者发布。维护者是 `psyistj` 和 `y08063806159-web`，和 oprun-v2 的负责人相同。
- 其他人和他们的 Agent 不创建 `v*` 标签，不创建或发布 GitHub Release，不运行 `npm publish`。Release 一旦发布，`.github/workflows/publish-npm.yml` 就会把包发到公开的 npm 上。
- 发布步骤见 `README.md` 的“维护发布”和“npm 发布”两节。
