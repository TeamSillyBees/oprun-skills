import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {execFileSync, spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {SKILL, STATE, SERVER, deploymentUrl, digest, safeName, treeHashes, loadBundle, install, inspect, profile, chooseHost, checkConnection} from '../cli/core.mjs';
const ROOT = fileURLToPath(new URL('../', import.meta.url));
const RESOURCE = deploymentUrl('https://mcp.oprun.test/mcp', '/mcp');
const ISSUER = deploymentUrl('https://api.oprun.test/mcp-oauth', '/mcp-oauth');
function fixture(t, version = '1.4.0') {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'oprun-node-test-'));
  t.after(() => fs.rmSync(root, {recursive: true, force: true}));
  const skillRoot = path.join(root, 'skills', SKILL);
  fs.cpSync(path.join(ROOT, 'skills', SKILL), skillRoot, {recursive: true});
  fs.cpSync(path.join(ROOT, 'cli'), path.join(root, 'cli'), {recursive: true});
  const manifest = {repository: 'TeamSillyBees/oprun-skills', skill: SKILL, version, revision: 'a'.repeat(40), mcp_revision: 'b'.repeat(40), source_merge_status: 'merged', skill_files: treeHashes(skillRoot, false)};
  fs.writeFileSync(path.join(root, 'bundle.json'), JSON.stringify(manifest));
  fs.writeFileSync(path.join(root, 'release.json'), JSON.stringify(manifest));
  const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json')));
  fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({...pkg, version}));
  return {root, skillRoot, manifest};
}
function target(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'oprun-user-test-'));
  t.after(() => fs.rmSync(dir, {recursive: true, force: true}));
  return path.join(dir, '.agents', 'skills', SKILL);
}
function newContent(bundle) {
  fs.appendFileSync(path.join(bundle.skillRoot, 'SKILL.md'), '\nSynthetic updated instructions.\n');
  bundle.manifest.skill_files = treeHashes(bundle.skillRoot, false);
}
test('bundled Skill validates every file and rejects tamper, extras and identity drift', t => {
  const b = fixture(t); assert.deepEqual(loadBundle(b.root).manifest, b.manifest);
  fs.writeFileSync(path.join(b.skillRoot, 'extra.txt'), 'extra');
  assert.throws(() => loadBundle(b.root), /checksum/);
  fs.unlinkSync(path.join(b.skillRoot, 'extra.txt'));
  fs.appendFileSync(path.join(b.skillRoot, 'SKILL.md'), 'tamper');
  assert.throws(() => loadBundle(b.root), /checksum/);
  b.manifest.version = '9.0.0'; fs.writeFileSync(path.join(b.root, 'bundle.json'), JSON.stringify(b.manifest));
  assert.throws(() => loadBundle(b.root), /identity/);
});
test('install is idempotent, update backs up prior bytes outside active Skill directory', t => {
  const b = fixture(t), dest = target(t);
  const config = path.join(path.dirname(path.dirname(dest)), 'config.json');
  fs.mkdirSync(path.dirname(config), {recursive: true}); fs.writeFileSync(config, '{"existing":"keep"}');
  assert.equal(install(b, dest).status, 'installed');
  assert.equal(install(b, dest).status, 'current');
  assert.equal(inspect(b, dest).status, 'current');
  const newer = fixture(t, '1.5.0'); newContent(newer);
  assert.equal(inspect(newer, dest).status, 'update_available');
  const result = install(newer, dest, true);
  assert.equal(result.status, 'updated');
  assert.ok(!result.backup.startsWith(path.dirname(dest) + path.sep));
  assert.deepEqual(treeHashes(result.backup), b.manifest.skill_files);
  assert.deepEqual(treeHashes(dest), newer.manifest.skill_files);
  assert.equal(fs.readFileSync(config, 'utf8'), '{"existing":"keep"}');
  assert.throws(() => install(b, dest, true), /Downgrade/);
});
test('modified, unmanaged and same-version different content cannot be overwritten', t => {
  const b = fixture(t), dest = target(t); install(b, dest);
  const newer = fixture(t, '1.5.0'); newContent(newer);
  fs.appendFileSync(path.join(dest, 'SKILL.md'), '\nUser notes');
  const before = fs.readFileSync(path.join(dest, 'SKILL.md'));
  assert.equal(inspect(b, dest).status, 'modified');
  assert.throws(() => install(newer, dest, true), /Local Skill/);
  assert.deepEqual(fs.readFileSync(path.join(dest, 'SKILL.md')), before);
  fs.unlinkSync(path.join(dest, STATE));
  assert.throws(() => install(newer, dest, true), /Existing Skill/);
  const other = target(t); install(b, other); newContent(b);
  assert.throws(() => install(b, other, true), /Same version/);
});
test('same-content Python receipt upgrades without replacing Skill or connection', t => {
  const b = fixture(t), dest = target(t); install(b, dest);
  const prior = {...b.manifest, version: '1.3.2'};
  fs.writeFileSync(path.join(dest, STATE), JSON.stringify(prior));
  assert.equal(install(b, dest, true).status, 'current');
  assert.equal(JSON.parse(fs.readFileSync(path.join(dest, STATE))).version, '1.4.0');
  fs.unlinkSync(path.join(dest, STATE));
  assert.equal(install(b, dest).status, 'current');
});
test('failed atomic update restores old Skill and releases lock', t => {
  const b = fixture(t), newer = fixture(t, '1.5.0'), dest = target(t);
  install(b, dest); newContent(newer); let calls = 0;
  assert.throws(() => install(newer, dest, true, {renameSync(from, to) {
    calls++; if (calls === 2) throw new Error('Synthetic rename failure'); fs.renameSync(from, to);
  }}), /Synthetic/);
  assert.deepEqual(treeHashes(dest), b.manifest.skill_files);
  assert.equal(inspect(b, dest).status, 'current');
  assert.equal(fs.existsSync(path.join(path.dirname(dest), `.${SKILL}.lock`)), false);
});
test('active lock, symlinks, unsafe names and corrupt receipts fail closed', t => {
  const b = fixture(t), dest = target(t); install(b, dest);
  const lock = path.join(path.dirname(dest), `.${SKILL}.lock`); fs.mkdirSync(lock);
  assert.throws(() => install(b, dest), /active/); fs.rmdirSync(lock);
  fs.symlinkSync(path.join(dest, 'SKILL.md'), path.join(dest, 'linked'));
  assert.throws(() => install(b, dest), /Symbolic/); fs.unlinkSync(path.join(dest, 'linked'));
  fs.writeFileSync(path.join(dest, STATE), '{'); assert.throws(() => install(b, dest), SyntaxError);
  for (const name of ['../escape', '/escape', 'a\\b', 'con.txt', 'a:stream', 'b/..', 'file.', STATE]) assert.throws(() => safeName(name));
  assert.throws(() => install(b, path.join(path.dirname(dest), 'other')), /Target/);
});
test('host profiles preserve OAuth scope and existing configuration stays user-managed', t => {
  const b = fixture(t);
  const q = profile(b, 'qveris', false, RESOURCE, ISSUER), ro = profile(b, 'qveris', true, RESOURCE, ISSUER);
  assert.equal(q.config.mcpServers[SERVER].issuer, ISSUER.href);
  assert.equal(q.config.mcpServers[SERVER].authMode, 'oauth');
  assert.ok(ro.requested_scopes.every(s => s.endsWith(':read')));
  assert.equal(profile(b, 'workbuddy', false, RESOURCE).config.mcpServers[SERVER].type, 'streamableHttp');
  assert.equal(profile(b, 'codex', false, RESOURCE).config.mcpServers[SERVER].authMode, undefined);
  assert.equal(q.config.mcpServers[SERVER].url, RESOURCE.href);
  assert.deepEqual(Object.keys(q.config.mcpServers), [SERVER]);
  assert.equal(profile(b, 'qveris', false, RESOURCE).config, undefined);
  assert.equal(profile(b, 'codex', false).status, 'awaiting_endpoint');
  assert.equal(q.config_written, false); assert.equal(q.oauth, 'not_checked');
  assert.equal(chooseHost('auto', b.root), 'generic');
  fs.mkdirSync(path.join(b.root, '.agents')); assert.equal(chooseHost('auto', b.root), 'codex');
  fs.mkdirSync(path.join(b.root, '.claude')); assert.equal(chooseHost('auto', b.root), 'generic');
});
test('public discovery verifies resource and PKCE without authenticated requests', async () => {
  const calls = [];
  const mock = async (url, options) => {
    calls.push(url); assert.equal(options.headers.authorization, undefined);
    assert.equal(options.redirect, 'error');
    return new Response(JSON.stringify(url.includes('protected-resource') ?
      {resource: RESOURCE.href, authorization_servers: [ISSUER.href]} :
      {issuer: ISSUER.href, code_challenge_methods_supported: ['S256'], scopes_supported: ['quality:read']}));

  };
  const result = await checkConnection(RESOURCE, ISSUER, mock);
  assert.equal(result.discovery, 'passed'); assert.equal(result.oauth, 'not_checked'); assert.equal(result.tools, 'not_checked'); assert.deepEqual(calls, [
    RESOURCE.origin + '/.well-known/oauth-protected-resource/mcp',
    ISSUER.origin + '/.well-known/oauth-authorization-server/mcp-oauth',
  ]);
  await assert.rejects(checkConnection(RESOURCE, ISSUER, async url => {
    if (url.includes('authorization-server')) throw new Error('Mismatched metadata must stop issuer discovery');
    return new Response(JSON.stringify({resource: RESOURCE.href, authorization_servers: ['https://other.test/mcp-oauth']}));
  }), /metadata/);
  await assert.rejects(checkConnection(RESOURCE, ISSUER, async url => url.includes('protected-resource')
    ? mock(url, {headers: {}, redirect: 'error'})
    : new Response(JSON.stringify({issuer: ISSUER.href, code_challenge_methods_supported: ['S256'], scopes_supported: ['plan:read']}))), /metadata/);
  await assert.rejects(checkConnection(RESOURCE, ISSUER, async () => new Response('{}')), /metadata/);
  await assert.rejects(checkConnection(RESOURCE, ISSUER, async () => new Response('denied', {status: 401})), /failed/);
  await assert.rejects(checkConnection(RESOURCE, ISSUER, async () => new Response('x'.repeat(256*1024+1))), /size/);
});
test('CLI installs, checks, blocks modified files and handles desktop native import', t => {
  const b = fixture(t), dest = target(t);
  const run = (...args) => spawnSync(process.execPath, [path.join(b.root, 'cli/main.mjs'), ...args], {encoding: 'utf8'});
  let result = run('install', '--target', dest, '--host', 'codex'); assert.equal(result.status, 0, result.stderr);
  result = run('doctor', '--target', dest, '--offline'); assert.equal(result.status, 0);
  assert.equal(JSON.parse(result.stdout).connection.discovery, 'not_checked');
  fs.appendFileSync(path.join(dest, 'SKILL.md'), 'local'); result = run('doctor', '--target', dest, '--offline'); assert.equal(result.status, 1);
  result = run('install', '--host', 'qveris', '--readonly'); assert.equal(result.status, 0);
  const q = JSON.parse(result.stdout); assert.equal(q.installation.status, 'awaiting_host_import');
  assert.equal(q.connection.status, 'awaiting_endpoint'); assert.equal(q.connection.config, undefined);
  result = run('install', '--host', 'qveris', '--mcp-url', RESOURCE.href, '--oauth-issuer', ISSUER.href); assert.equal(result.status, 0);
  assert.equal(JSON.parse(result.stdout).connection.config.mcpServers[SERVER].issuer, ISSUER.href);
  assert.notEqual(run('doctor', '--mcp-url', 'https://user:secret@mcp.oprun.test/mcp').status, 0);
  assert.ok(q.installation.zip.includes('/v1.4.0/')); assert.ok(q.connection.requested_scopes.every(s => s.endsWith(':read')));
  assert.equal(run('update', '--target', target(t)).status, 1);
  assert.equal(run('install', '--host', 'unknown').status, 1);
});
