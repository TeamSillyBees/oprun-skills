import fs from 'node:fs';
import path from 'node:path';
import {createHash, randomUUID} from 'node:crypto';

export const SKILL = 'oprun-project-planning';
export const STATE = '.oprun-install.json';
export const SERVER = 'oprun-new';
const REPO = 'TeamSillyBees/oprun-skills';
export const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const fail = message => { throw new Error(message); };
const json = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const equal = (a, b) => JSON.stringify(Object.entries(a).sort()) === JSON.stringify(Object.entries(b).sort());
export function safeName(name) {
  const parts = name.split('/');
  if (!name || name.includes('\\') || parts.some(p => !p || p === '.' || p === '..' || /[<>:"|?*\x00-\x1f]/.test(p) || /[. ]$/.test(p) || /^(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\.|$)/i.test(p)) || name.toLowerCase() === STATE.toLowerCase()) fail('Unsafe Skill file name');
}
export function treeHashes(root, ignoreReceipt = true) {
  const entries = [];
  const seen = new Set();
  let size = 0;
  function walk(dir, prefix = '') {
    for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
      const name = prefix + entry.name;
      const full = path.join(dir, entry.name);
      const stat = fs.lstatSync(full);
      if (stat.isSymbolicLink()) fail('Symbolic links are not supported inside a Skill');
      if (ignoreReceipt && name === STATE) {
        if (!stat.isFile()) fail('Invalid installation receipt');
        continue;
      }
      safeName(name);
      if (seen.has(name.toLowerCase())) fail('Case-conflicting Skill paths');
      seen.add(name.toLowerCase());
      if (stat.isDirectory()) walk(full, name + '/');
      else if (stat.isFile()) {
        size += stat.size;
        if (size > 16 * 1024 * 1024) fail('Skill exceeds size limit');
        entries.push([name, digest(fs.readFileSync(full))]);
      } else fail('Unsupported Skill entry');
    }
  }
  if (fs.lstatSync(root).isSymbolicLink()) fail('Symbolic link Skill directory');
  walk(root);
  return Object.fromEntries(entries);
}
function version(value) {
  if (!/^\d+\.\d+\.\d+$/.test(value)) fail('Invalid stable version');
  return value.split('.').map(Number);
}
function compare(a, b) {
  const av = version(a), bv = version(b);
  for (let i = 0; i < 3; i++) if (av[i] !== bv[i]) return Math.sign(av[i] - bv[i]);
  return 0;
}
export function loadBundle(root) {
  const manifest = json(path.join(root, 'bundle.json'));
  const release = json(path.join(root, 'release.json'));
  const pkg = json(path.join(root, 'package.json'));
  if (manifest.repository !== REPO || manifest.skill !== SKILL || manifest.version !== release.version || manifest.version !== pkg.version || manifest.mcp_revision !== release.mcp_revision || !/^[a-f0-9]{40}$/.test(manifest.revision) || !/^[a-f0-9]{40}$/.test(manifest.mcp_revision)) fail('Package identity mismatch');
  if (manifest.source_merge_status !== release.source_merge_status ||
      !['merged', 'pending'].includes(manifest.source_merge_status)) fail('MCP source status mismatch');
  version(manifest.version);
  const skillRoot = path.join(root, 'skills', SKILL);
  const hashes = treeHashes(skillRoot, false);
  if (!hashes['SKILL.md'] || !equal(hashes, manifest.skill_files)) fail('Skill content checksum mismatch');
  return {manifest, skillRoot};
}
function writeReceipt(dir, manifest) {
  const temporary = path.join(dir, `.oprun-receipt-${randomUUID()}`);
  try {
    fs.writeFileSync(temporary, JSON.stringify({version: manifest.version, revision: manifest.revision, skill_files: manifest.skill_files}, null, 2) + '\n', {flag: 'wx', mode: 0o600});
    fs.renameSync(temporary, path.join(dir, STATE));
  } finally { fs.rmSync(temporary, {force: true}); }
}
function targetPath(target) {
  const absolute = path.resolve(target);
  // Resolve existing ancestors (e.g. macOS /tmp) without accepting a symlink target.
  try {
    if (fs.lstatSync(absolute).isSymbolicLink()) fail('Symbolic link installation target');
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  if (path.basename(absolute) !== SKILL) fail(`Target must end in ${SKILL}`);
  fs.mkdirSync(path.dirname(absolute), {recursive: true});
  return path.join(fs.realpathSync(path.dirname(absolute)), path.basename(absolute));
}
export function install(bundle, target, update = false, operations = fs) {
  target = targetPath(target);
  const {manifest, skillRoot} = bundle;
  // Revalidate immediately before use; never rely on a stale download/receipt.
  if (!equal(treeHashes(skillRoot, false), manifest.skill_files)) fail('Skill content checksum mismatch');
  const parent = path.dirname(target);
  const lock = path.join(parent, `.${SKILL}.lock`);
  try { fs.mkdirSync(lock); } catch { fail('Another installation is active; inspect the lock before retrying'); }
  let stage;
  let backup;
  try {
    if (fs.existsSync(target)) {
      const actual = treeHashes(target);
      const receiptPath = path.join(target, STATE);
      const receipt = fs.existsSync(receiptPath) ? json(receiptPath) : null;
      if (receipt && compare(manifest.version, receipt.version) < 0) fail('Downgrade refused');
      if (equal(actual, manifest.skill_files)) {
        writeReceipt(target, manifest);
        return {status: 'current', target, version: manifest.version};
      }
      if (!update || !receipt) fail('Existing Skill differs; preserve and review it before updating');
      if (!equal(actual, receipt.skill_files)) fail('Local Skill changes detected; nothing overwritten');
      if (compare(manifest.version, receipt.version) <= 0) fail('Same version has different contents; update refused');
    } else if (update) fail('Skill is not installed; run install first');
    stage = fs.mkdtempSync(path.join(parent, '.oprun-stage-'));
    for (const name of Object.keys(manifest.skill_files)) {
      safeName(name);
      const output = path.join(stage, name);
      fs.mkdirSync(path.dirname(output), {recursive: true});
      fs.copyFileSync(path.join(skillRoot, name), output, fs.constants.COPYFILE_EXCL);
    }
    if (!equal(treeHashes(stage), manifest.skill_files)) fail('Staged Skill verification failed');
    writeReceipt(stage, manifest);
    if (fs.existsSync(target)) {
      // Store backups outside the active Skill discovery directory.
      const backupRoot = path.join(parent, '..', 'oprun-skill-backups');
      fs.mkdirSync(backupRoot, {recursive: true});
      backup = path.join(fs.mkdtempSync(path.join(backupRoot, 'backup-')), SKILL);
      operations.renameSync(target, backup);
    }
    try { operations.renameSync(stage, target); stage = undefined; }
    catch (error) {
      if (backup) operations.renameSync(backup, target);
      throw error;
    }
    return {status: update ? 'updated' : 'installed', target, version: manifest.version, ...(backup ? {backup} : {})};
  } finally {
    if (stage) fs.rmSync(stage, {recursive: true, force: true});
    fs.rmdirSync(lock);
  }
}
export function inspect(bundle, target) {
  if (!fs.existsSync(target)) return {status: 'not_installed'};
  const actual = treeHashes(target);
  const receiptPath = path.join(target, STATE);
  if (!fs.existsSync(receiptPath)) return {status: equal(actual, bundle.manifest.skill_files) ? 'unmanaged_matching' : 'unmanaged'};
  const receipt = json(receiptPath);
  const matches = equal(actual, receipt.skill_files);
  const comparison = compare(receipt.version, bundle.manifest.version);
  return {status: !matches ? 'modified' : comparison < 0 ? 'update_available' : comparison > 0 ? 'newer_than_cli' : equal(actual, bundle.manifest.skill_files) ? 'current' : 'content_mismatch', installed_version: receipt.version, package_version: bundle.manifest.version};
}
export function chooseHost(host, project) {
  if (host !== 'auto') return host;
  const found = [['codex', '.agents'], ['claude', '.claude']].filter(([, marker]) => fs.existsSync(path.join(project, marker)));
  return found.length === 1 ? found[0][0] : 'generic';
}
export function deploymentUrl(value, pathname) {
  let url;
  try { url = new URL(value); } catch { fail('请输入部署方提供的新 MCP 地址或 OAuth issuer'); }
  const loopback = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if (!(url.protocol === 'https:' || (loopback && url.protocol === 'http:')) ||
      url.hostname.endsWith('.invalid') || url.href !== url.origin + pathname) {
    fail('新 MCP 资源须为 HTTPS /mcp，issuer 须为 HTTPS /mcp-oauth；本地回环可使用 HTTP');
  }
  return url;
}
export function profile(bundle, host, readonly, resource, issuer) {
  const config = json(path.join(bundle.skillRoot, 'assets', 'qveris-mcp.json'));
  if (Object.keys(config.mcpServers).length !== 1 || !config.mcpServers[SERVER]) fail('安装包缺少新版 MCP 配置');
  const server = config.mcpServers[SERVER];
  const requested_scopes = server.scope.split(' ').filter(scope => !readonly || scope.endsWith(':read'));
  const connection = {server: SERVER, requested_scopes, config_written: false, oauth: 'not_checked', tools: 'not_checked'};
  if (!resource || (host === 'qveris' && !issuer)) {
    return {...connection, status: 'awaiting_endpoint', next: '请使用部署方提供的新 MCP 地址和所需 OAuth issuer。'};
  }
  server.url = resource.href;
  if (host === 'qveris') {
    server.issuer = issuer.href;
    server.scope = requested_scopes.join(' ');
  }
  else {
    delete server.authMode; delete server.issuer; delete server.scope;
    if (host === 'workbuddy') server.type = 'streamableHttp';
  }
  return {...connection, config, status: 'awaiting_oauth', next: '在宿主选择此新连接并完成 OAuth，然后核对工具和当前主体。'};
}
export async function checkConnection(endpoint, issuer, fetcher = fetch) {
  async function get(url) {
    const response = await fetcher(url, {signal: AbortSignal.timeout(15000), redirect: 'error', headers: {'accept': 'application/json'}});
    if (!response.ok) fail('Public OAuth discovery request failed');
    const reader = response.body.getReader();
    const chunks = []; let size = 0;
    try {
      for (;;) {
        const {done, value} = await reader.read(); if (done) break;
        size += value.length; if (size > 256 * 1024) fail('Discovery document exceeds size limit');
        chunks.push(Buffer.from(value));
      }
    } finally { await reader.cancel(); }
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  }
  const resource = await get(endpoint.origin + '/.well-known/oauth-protected-resource/mcp');
  const includes = (values, expected) => Array.isArray(values) && values.includes(expected);
  if (resource.resource !== endpoint.href || !includes(resource.authorization_servers, issuer.href)) fail('Unexpected OAuth discovery metadata');
  const auth = await get(issuer.origin + '/.well-known/oauth-authorization-server/mcp-oauth');
  if (auth.issuer !== issuer.href || !includes(auth.code_challenge_methods_supported, 'S256') ||
      !includes(auth.scopes_supported, 'quality:read')) fail('Unexpected OAuth discovery metadata');
  return {discovery: 'passed', oauth: 'not_checked', tools: 'not_checked', next: '在宿主完成 OAuth，再通过新连接调用 tools/list 和 oprun_new_account_context。'};
}
