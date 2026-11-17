#!/usr/bin/env python3
"""Install/update a verified official OpRun Skill; never store OAuth credentials."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import urllib.error
import urllib.request
import zipfile

REPO = 'TeamSillyBees/oprun-skills'
SKILL = 'oprun-project-planning'
SITE = 'https://www.agi.yifx.vip'
LIMIT = 16 * 1024 * 1024
STATE = '.oprun-install.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'oprun-skill-installer'})
    with urllib.request.urlopen(request, timeout=25) as response:
        data = response.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError('下载超过大小限制')
        return data


def release_bundle(tag='latest'):
    if tag == 'latest':
        meta = json.loads(fetch(f'https://api.github.com/repos/{REPO}/releases/latest'))
        tag = meta['tag_name']
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('仅支持正式版本 vX.Y.Z')
    base = f'https://github.com/{REPO}/releases/download/{tag}/'
    # Resolve latest once: all assets must come from the same immutable release.
    checks = dict(line.split('  ', 1)[::-1] for line in fetch(base + 'SHA256SUMS').decode().splitlines())
    raw = fetch(base + 'manifest.json')
    if digest(raw) != checks.get('manifest.json'):
        raise ValueError('发布清单校验失败')
    manifest = json.loads(raw)
    if manifest['repository'] != REPO or manifest['skill'] != SKILL or manifest['tag'] != tag or tag != 'v' + manifest['version']:
        raise ValueError('发布来源或版本不一致')
    bundle = fetch(base + SKILL + '.zip')
    expected = manifest['files'][SKILL + '.zip']
    if digest(bundle) != expected or checks.get(SKILL + '.zip') != expected:
        raise ValueError('安装包校验失败')
    return manifest, unpack(bundle, manifest)


def unpack(data, manifest):
    result = {}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if sum(i.file_size for i in archive.infolist()) > LIMIT:
            raise ValueError('解压大小超限')
        for info in archive.infolist():
            p = PurePosixPath(info.filename)
            if (p.is_absolute() or '..' in p.parts or '\\' in info.filename
                    or not p.parts or p.parts[0] != SKILL or len(p.parts) < 2
                    or str(p) != info.filename or info.is_dir()
                    or any(':' in part for part in p.parts)
                    or stat.S_ISLNK(info.external_attr >> 16)):
                raise ValueError('安装包包含不安全路径')
            name = '/'.join(p.parts[1:])
            if name.casefold() in {n.casefold() for n in result} or name == STATE:
                raise ValueError('安装包成员重复或保留文件冲突')
            result[name] = archive.read(info)
    if 'SKILL.md' not in result or {n: digest(v) for n, v in result.items()} != manifest['skill_files']:
        raise ValueError('安装包成员与清单不一致')
    return result


def tree_hashes(path):
    result = {}
    for item in path.rglob('*'):
        if item.is_symlink():
            raise ValueError('安装目录存在符号链接，保留现场')
        if item.is_file() and item.relative_to(path).as_posix() != STATE:
            result[item.relative_to(path).as_posix()] = digest(item.read_bytes())
    return result


def install(target, manifest, files, update=False):
    target = Path(target).absolute()
    if any(p.is_symlink() for p in (target, *target.parents)):
        raise ValueError('安装路径不能包含符号链接')
    target.parent.mkdir(parents=True, exist_ok=True)
    lock = target.parent / ('.' + target.name + '.lock')
    lock.mkdir()  # Another installation must finish first; never steal its lock.
    stage = None
    backup = None
    try:
        if target.exists():
            current = tree_hashes(target)
            if current == manifest['skill_files']:
                receipt = target / STATE
                if receipt.exists() and tuple(map(int, json.loads(receipt.read_text())['version'].split('.'))) > tuple(map(int, manifest['version'].split('.'))):
                    raise ValueError('拒绝降级')
                receipt.write_text(json.dumps({k: manifest[k] for k in ('version', 'revision', 'skill_files')}, indent=2) + '\n')
                return {'skill': 'current', 'version': manifest['version'], 'path': str(target)}
            receipt = target / STATE
            if not update or not receipt.is_file():
                raise ValueError('已有安装未经管理或内容不同；先核对，未覆盖')
            prior = json.loads(receipt.read_text())
            if current != prior['skill_files']:
                raise ValueError('检测到本地修改，未覆盖；请先保存并核对差异')
            if tuple(map(int, manifest['version'].split('.'))) <= tuple(map(int, prior['version'].split('.'))):
                raise ValueError('拒绝降级或覆盖同版本不同内容')
        stage = Path(tempfile.mkdtemp(prefix='.' + target.name + '-stage-', dir=target.parent))
        for name, data in files.items():
            dest = stage / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        (stage / STATE).write_text(json.dumps({k: manifest[k] for k in ('version', 'revision', 'skill_files')}, indent=2) + '\n')
        if target.exists():
            backup = Path(tempfile.mkdtemp(prefix='.' + target.name + '-backup-', dir=target.parent)) / target.name
            target.rename(backup)
        try:
            stage.rename(target)
        except BaseException:
            if backup:
                backup.rename(target)
            raise
        return {'skill': 'installed', 'version': manifest['version'], 'path': str(target), 'backup': str(backup) if backup else None}
    finally:
        if stage and stage.exists():
            shutil.rmtree(stage)
        lock.rmdir()


def choose_host(host, project):
    if host != 'auto':
        return host
    matches = [name for name, marker in [('codex', '.agents'), ('claude', '.claude')] if (project / marker).is_dir()]
    return matches[0] if len(matches) == 1 else 'generic'


def profile(host, readonly, files):
    name = 'qveris-readonly-mcp.json' if readonly else 'qveris-mcp.json'
    config = json.loads(files['assets/' + name])
    if host != 'qveris':
        server = config['mcpServers']['oprun']
        scopes = server.pop('scope')
        server.pop('authMode')
        server.pop('issuer')
        if host == 'workbuddy':
            server['type'] = 'streamableHttp'
        return config, scopes
    return config, config['mcpServers']['oprun']['scope']


def check_connection():
    resource = json.loads(fetch(SITE + '/.well-known/oauth-protected-resource/mcp'))
    auth = json.loads(fetch(SITE + '/.well-known/oauth-authorization-server/mcp'))
    if resource.get('resource') != SITE + '/mcp' or SITE + '/mcp' not in resource.get('authorization_servers', []):
        raise ValueError('OAuth 资源归属不符')
    if auth.get('issuer') != SITE + '/mcp' or 'S256' not in auth.get('code_challenge_methods_supported', []):
        raise ValueError('OAuth 发现或 PKCE 不可用')
    return {'discovery': 'passed', 'oauth': 'not_checked', 'tools': 'not_checked',
            'next': '由宿主完成登录，再调用 tools/list 和 oprun_account_context；不查询项目。'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'update', 'check'])
    parser.add_argument('--host', choices=['auto', 'codex', 'claude', 'qveris', 'workbuddy', 'generic'], default='auto')
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--target', type=Path, help='完整 Skill 目标目录；桌面客户端由宿主确认此路径')
    parser.add_argument('--version', default='latest')
    parser.add_argument('--readonly', action='store_true')
    args = parser.parse_args()
    try:
        if args.action == 'check':
            result = check_connection()
            if args.target:
                receipt = json.loads((args.target / STATE).read_text())
                result['skill'] = 'verified' if tree_hashes(args.target) == receipt['skill_files'] else 'modified'
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        manifest, files = release_bundle(args.version)
        host = choose_host(args.host, args.project)
        target = args.target
        if target is None and host in ('codex', 'claude'):
            target = args.project / ('.agents' if host == 'codex' else '.claude') / 'skills' / SKILL
        result = install(target, manifest, files, args.action == 'update') if target else {'skill': 'awaiting_host_import', 'version': manifest['version']}
        config, scopes = profile(host, args.readonly, files)
        result.update({'host': host, 'mcp': 'awaiting_host_configuration_or_reuse', 'oauth': 'not_checked',
                       'config': config, 'requested_scopes': scopes,
                       'next': '复用同站点连接；无连接时用宿主原生导入。由用户登录授权，tools/list 与 oprun_account_context 成功后才报告已连接。'})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as error:
        # Never print response bodies, authenticated URLs or credentials.
        print(json.dumps({'status': 'blocked', 'reason': str(error) if isinstance(error, ValueError) else type(error).__name__}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
