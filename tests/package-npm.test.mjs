import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {execFileSync, spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {SKILL, loadBundle, treeHashes} from '../cli/core.mjs';
const ROOT = fileURLToPath(new URL('../', import.meta.url));
function fixture(t, mergeStatus = "merged") {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'oprun-pack-test-'));
  t.after(() => fs.rmSync(root, {recursive: true, force: true}));
  for (const name of ['package.json','release.json','README.md','INSTALL.md','mcp.json','cli','skills','tools']) fs.cpSync(path.join(ROOT,name),path.join(root,name),{recursive:true});
  // Test a synthetic reviewed release independently from the PR's real source status.
  const metadata=JSON.parse(fs.readFileSync(path.join(root,'release.json')));
  metadata.source_merge_status=mergeStatus;
  fs.writeFileSync(path.join(root,'release.json'),JSON.stringify(metadata,null,2)+'\n');
  const git = (...args) => execFileSync('git', args, {cwd:root, stdio:['ignore','pipe','pipe']}).toString().trim();
  git('init','--quiet');git('add','.');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','-c','commit.gpgsign=false','commit','-qm','Synthetic package');
  git('update-ref','refs/remotes/origin/main','HEAD');
  return {root,git};
}
test('committed npm and ZIP payloads agree; packed npx runs without Python or install hooks', t => {
  const {root,git} = fixture(t);
  const run = (cmd,args,cwd=root) => execFileSync(cmd,args,{cwd,encoding:'utf8',stdio:['ignore','pipe','pipe']});
  run(process.execPath,['tools/package-npm.mjs','--output-dir','npm-package']);
  run('python3',['tools/package.py','--output-dir','zip-package']);
  const bundle=loadBundle(path.join(root,'npm-package'));
  const zip=JSON.parse(fs.readFileSync(path.join(root,'zip-package','manifest.json')));
  assert.deepEqual(bundle.manifest.skill_files,zip.skill_files);
  assert.equal(bundle.manifest.revision,zip.revision);assert.equal(zip.revision,git('rev-parse','HEAD'));
  const packed=JSON.parse(run('npm',['pack','--json','--ignore-scripts','--cache',path.join(root,'cache')],path.join(root,'npm-package')))[0];
  const names=packed.files.map(f=>f.path);
  assert.ok(names.includes('cli/main.mjs'));assert.ok(names.includes('bundle.json'));
  assert.ok(names.every(n=>!n.includes('.npmrc')&&!n.includes('.env')&&!n.startsWith('tests/')&&!n.startsWith('tools/')));
  const tar=path.join(root,'npm-package',packed.filename);
  run('python3',['tools/package.py','--output-dir','combined-release','--npm-tarball',tar]);
  const combined=JSON.parse(fs.readFileSync(path.join(root,'combined-release/manifest.json')));
  assert.ok(combined.files['oprun-skills.tgz']);
  assert.deepEqual(fs.readFileSync(path.join(root,'combined-release/oprun-skills.tgz')),fs.readFileSync(tar));
  const dest=path.join(root,'user-project','.agents','skills',SKILL);
  // Execute the exact packed artifact through npm's npx-compatible exec path.
  const installed=JSON.parse(run('npm',['exec','--offline','--yes','--cache',path.join(root,'exec-cache'),'--package',tar,'--','oprun-skills','install','--host','codex','--target',dest]));
  assert.equal(installed.installation.status,'installed');
  assert.deepEqual(treeHashes(dest),zip.skill_files);
  const checked=JSON.parse(run('npm',['exec','--offline','--yes','--cache',path.join(root,'exec-cache'),'--package',tar,'--','oprun-skills','doctor','--offline','--target',dest]));
  assert.equal(checked.installation.status,'current'); assert.equal(checked.connection.oauth,'not_checked');
  // Rebuilding committed bytes yields the same payload manifest.
  run(process.execPath,['tools/package-npm.mjs','--output-dir','npm-package-again']);
  assert.deepEqual(fs.readFileSync(path.join(root,'npm-package/bundle.json')),fs.readFileSync(path.join(root,'npm-package-again/bundle.json')));
});
test('npm builder rejects dirty inputs, mismatched versions, unpushed commits and tag reuse', t => {
  const {root,git}=fixture(t);
  const run=(out,...extra)=>spawnSync(process.execPath,['tools/package-npm.mjs','--output-dir',out,...extra],{cwd:root,encoding:'utf8'});
  fs.appendFileSync(path.join(root,'cli/main.mjs'),'\n// uncommitted\n');
  assert.notEqual(run('dirty').status,0);assert.equal(fs.existsSync(path.join(root,'dirty')),false);
  git('add','cli/main.mjs');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','-c','commit.gpgsign=false','commit','-qm','Change');
  assert.notEqual(run('unpushed').status,0);assert.equal(run('trial','--allow-unpushed').status,0);
  const release=JSON.parse(fs.readFileSync(path.join(root,'release.json')));git('tag',`v${release.version}`);
  fs.appendFileSync(path.join(root,'cli/main.mjs'),'\n// new revision\n');git('add','cli/main.mjs');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','-c','commit.gpgsign=false','commit','-qm','Later');
  assert.notEqual(run('tagged','--allow-unpushed').status,0);
  const pkg=JSON.parse(fs.readFileSync(path.join(root,'package.json')));pkg.version='9.0.0';fs.writeFileSync(path.join(root,'package.json'),JSON.stringify(pkg));git('add','package.json');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','-c','commit.gpgsign=false','commit','-qm','Mismatch');
  assert.notEqual(run('mismatch','--allow-unpushed').status,0);
});

test('pending canonical source cannot create a formal package', t=>{
 const {root}=fixture(t,'pending');
 const run=(extra=[])=>spawnSync(process.execPath,['tools/package-npm.mjs','--output-dir','candidate',...extra],{cwd:root,encoding:'utf8'});
 const formal=run();assert.notEqual(formal.status,0);assert.match(formal.stderr,/source has not merged/);assert.equal(fs.existsSync(path.join(root,'candidate')),false);
 assert.equal(run(['--allow-unpushed']).status,0);
 assert.equal(JSON.parse(fs.readFileSync(path.join(root,'candidate/release.json'))).source_merge_status,'pending');
});
