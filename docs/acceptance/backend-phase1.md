# 独立需求工作区 Skill 同步

状态：pending，上游 MCP PR 尚未合并；不发布 npm/ZIP、不修改现有连接。

本 PR 通过 tools/sync.py 从 canonical oprun-mcp 的固定提交同步，release.json 明确 source_merge_status=pending。新增 workspaces 指引只在 tools/list 实际提供五项新能力时生效，不让旧服务声称具备新能力，仍保持统一 OAuth 连接。

安装/更新不会重写已有 MCP 配置。上游合并后重新 fetch、核对来源可达 main，用正常 sync（不加 allow-unmerged）更新来源，再提升版本、生成发布制品。本 PR 不把未合并的源码标记为已上线。

测试补齐了待审来源禁止正式打包、仅允许显式本地试包的断言；原包内引用检查正确处理 Markdown 锚点。测试夹具自行声明模拟来源状态，不能把真实 pending 状态改成 merged 来让测试通过。
