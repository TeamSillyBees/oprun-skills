#!/usr/bin/env node
// Build only committed bytes, with the same Skill tree and hashes as the ZIP.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {parseArgs} from 'node:util';
import {createHash} from 'node:crypto';

const root = fileURLToPath(new URL('../', import.meta.url));
const git = (...args) => execFileSync('git', args, {cwd: root});
const {values} = parseArgs({options: {'output-dir': {type: 'string'}, 'allow-unpushed': {type: 'boolean', default: false}}});
if (!values['output-dir']) throw new Error('--output-dir is required');
const revision = git('rev-parse', 'HEAD').toString().trim();
const required = ['package.json', 'release.json', 'README.md', 'INSTALL.md', 'cli', 'tools/package-npm.mjs', 'skills/oprun-project-planning'];
if (git('diff', 'HEAD', '--name-only', '--', ...required).length || git('ls-files', '--others', '--exclude-standard', '--', ...required).length) throw new Error('Commit npm package sources before building');
if (!values['allow-unpushed'] && !git('branch', '-r', '--contains', revision).toString().trim()) throw new Error('Push package sources before formal build');
const read = name => git('show', `${revision}:${name}`);
const release = JSON.parse(read('release.json'));
const pkg = JSON.parse(read('package.json'));
if (pkg.version !== release.version || !/^\d+\.\d+\.\d+$/.test(pkg.version)) throw new Error('npm/ZIP version mismatch');
if (release.source_merge_status !== 'merged' && !values['allow-unpushed']) throw new Error('Skill source has not merged');
const tagged = git('tag', '--list', `v${release.version}`).toString().trim();
if (tagged && git('rev-list', '-1', tagged).toString().trim() !== revision) throw new Error('Version tag belongs to a different revision');
if (Object.keys(pkg.scripts || {}).some(key => /^(preinstall|install|postinstall|prepare|prepack|postpack|prepublish|prepublishOnly|publish|postpublish)$/.test(key))) throw new Error('Implicit installation/publishing hooks are not allowed');
const out = path.resolve(values['output-dir']);
if (fs.existsSync(out)) throw new Error('Refusing to overwrite build directory');
const skillPrefix = 'skills/oprun-project-planning/';
const names = git('ls-tree', '-r', '-z', '--name-only', revision, '--', 'cli', skillPrefix).toString().split('\0').filter(Boolean).sort();
const files = [...names, 'release.json', 'README.md', 'INSTALL.md'];
const bytes = new Map(files.map(name => [name, read(name)]));
const hashes = Object.fromEntries(names.filter(name => name.startsWith(skillPrefix)).map(name => [name.slice(skillPrefix.length), createHash('sha256').update(bytes.get(name)).digest('hex')]));
if (!hashes['SKILL.md']) throw new Error('Missing Skill');
const manifest = {...release, revision, skill_files: hashes};
const publishPackage = {...pkg, oprun: {source_revision: revision, mcp_revision: release.mcp_revision}};
if (release.source_merge_status !== 'merged') publishPackage.private = true;
fs.mkdirSync(out, {recursive: true});
for (const [name, contents] of bytes) {
  fs.mkdirSync(path.dirname(path.join(out, name)), {recursive: true});
  fs.writeFileSync(path.join(out, name), contents, {flag: 'wx', mode: name === 'cli/main.mjs' ? 0o755 : 0o644});
}
fs.writeFileSync(path.join(out, 'bundle.json'), JSON.stringify(manifest, null, 2) + '\n');
fs.writeFileSync(path.join(out, 'package.json'), JSON.stringify(publishPackage, null, 2) + '\n');
console.log(JSON.stringify({directory: out, version: pkg.version, revision, skill_files: Object.keys(hashes).length}));
