#!/usr/bin/env node
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseArgs} from 'node:util';
import {SKILL, loadBundle, chooseHost, profile, install, inspect, checkConnection, deploymentUrl} from './core.mjs';

const HELP = `OpRun Skill 安装工具（Node.js 22+）
  oprun-skills install [--host codex|claude|qveris|workbuddy|generic] [--project 路径]
  oprun-skills update  [--host ...] [--target 完整Skill目录]
  oprun-skills doctor [--host ...] [--target 完整Skill目录] [--offline]
  --mcp-url    部署方提供的新 MCP 地址
  --oauth-issuer   部署方提供的新 OAuth issuer，Qveris 与发现检查使用
  --readonly   仅输出只读权限配置，不修改现有授权
使用 npx oprun-skills@latest 获取最新版；本工具不会后台自动更新。
桌面宿主无公开安装目录时使用同版本 ZIP；在宿主选择 oprun-new 后由用户完成 OAuth。`;
try {
  const {values, positionals} = parseArgs({allowPositionals: true, options: {
    host: {type: 'string', default: 'auto'}, project: {type: 'string', default: process.cwd()},
    target: {type: 'string'}, 'mcp-url': {type: 'string'}, 'oauth-issuer': {type: 'string'}, readonly: {type: 'boolean', default: false},
    offline: {type: 'boolean', default: false}, help: {type: 'boolean', short: 'h'}, version: {type: 'boolean'}
  }});
  if (values.help || (!positionals.length && !values.version)) { console.log(HELP); }
  else {
    const root = fileURLToPath(new URL('../', import.meta.url));
    const bundle = loadBundle(root);
    if (values.version) console.log(bundle.manifest.version);
    else {
      const command = positionals[0];
      if (positionals.length !== 1 || !['install', 'update', 'doctor', 'check'].includes(command)) throw new Error('Use install, update or doctor');
      if (!['auto', 'codex', 'claude', 'qveris', 'workbuddy', 'generic'].includes(values.host)) throw new Error('Unsupported host');
      if (values.offline && !['doctor', 'check'].includes(command)) throw new Error('--offline applies only to doctor');
      const host = chooseHost(values.host, values.project);
      const endpoint = values['mcp-url'] === undefined ? undefined : deploymentUrl(values['mcp-url'], '/mcp');
      const issuer = values['oauth-issuer'] === undefined ? undefined : deploymentUrl(values['oauth-issuer'], '/mcp-oauth');
      const target = values.target || (['codex', 'claude'].includes(host) ? path.resolve(values.project, host === 'codex' ? '.agents' : '.claude', 'skills', SKILL) : null);
      const result = {package_version: bundle.manifest.version, source_revision: bundle.manifest.mcp_revision, source_merge_status: bundle.manifest.source_merge_status, host};
      if (['doctor', 'check'].includes(command)) {
        result.installation = target ? inspect(bundle, target) : {status: 'host_managed'};
        try {
          result.connection = values.offline ? {discovery: 'not_checked', oauth: 'not_checked', tools: 'not_checked'} :
            endpoint && issuer ? await checkConnection(endpoint, issuer) : profile(bundle, 'qveris', values.readonly);
        }
        catch { result.connection = {discovery: 'failed', oauth: 'not_checked', tools: 'not_checked', next: '检查网络及公开 OAuth 发现地址；未读取登录信息。'}; process.exitCode = 1; }
        if (['modified', 'content_mismatch', 'not_installed', 'unmanaged'].includes(result.installation.status)) process.exitCode = 1;
      } else {
        result.connection = profile(bundle, host, values.readonly, endpoint, issuer);
        const zip = bundle.manifest.source_merge_status === 'pending' ? {} :
          {zip: `https://github.com/TeamSillyBees/oprun-skills/releases/download/v${bundle.manifest.version}/${SKILL}.zip`};
        result.installation = target ? install(bundle, target, command === 'update') : {status: 'awaiting_host_import', ...zip, next: '使用同版本 ZIP 导入，或提供宿主公开支持的 --target 目录。'};
      }
      console.log(JSON.stringify(result, null, 2));
    }
  }
} catch (error) {
  // Do not emit environment values, HTTP bodies, credentials or stack traces.
  console.error(JSON.stringify({error: error.code ? `本地文件操作失败（${error.code}），请检查目标目录。` : error instanceof SyntaxError ? '配置或清单不是有效 JSON。' : error.message}));
  process.exitCode = 1;
}
