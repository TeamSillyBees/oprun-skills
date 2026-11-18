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
import urllib.request
from urllib.parse import urlsplit
import zipfile

REPO = 'TeamSillyBees/oprun-skills'
SKILL = 'oprun-project-planning'
SERVER = 'oprun-new'
LIMIT = 16 * 1024 * 1024
STATE = '.oprun-install.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url, opener=urllib.request.urlopen):
    request = urllib.request.Request(url, headers={'User-Agent': 'oprun-skill-installer'})
    with opener(request, timeout=25) as response:
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


def deployment_url(value, path):
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        parsed.port
    except ValueError:
        host = None
    if (host is None or host.endswith('.invalid')
            or (parsed.scheme != 'https' and (parsed.scheme != 'http' or host not in {'localhost', '127.0.0.1', '::1'}))
            or parsed.username is not None or parsed.path != path
            or value != f'{parsed.scheme}://{parsed.netloc}{path}' or any(char.isspace() for char in value)):
        raise ValueError('新 MCP 资源须为 HTTPS /mcp，issuer 须为 HTTPS /mcp-oauth；本地回环可使用 HTTP')
    return parsed


def profile(host, readonly, files, endpoint=None, issuer=None):
    config = json.loads(files['assets/qveris-mcp.json'])
    if set(config['mcpServers']) != {SERVER}:
        raise ValueError('安装包缺少新版 MCP 配置')
    server = config['mcpServers'][SERVER]
    scopes = [scope for scope in server['scope'].split() if not readonly or scope.endswith(':read')]
    result = {'server': SERVER, 'requested_scopes': scopes, 'config_written': False, 'oauth': 'not_checked', 'tools': 'not_checked'}
    if endpoint is None or (host == 'qveris' and issuer is None):
        return {**result, 'status': 'awaiting_endpoint', 'next': '请使用部署方提供的新 MCP 地址和所需 OAuth issuer。'}
    server['url'] = endpoint.geturl()
    if host == 'qveris':
        server['issuer'] = issuer.geturl()
        server['scope'] = ' '.join(scopes)
    else:
        server.pop('scope')
        server.pop('authMode')
        server.pop('issuer', None)
        if host == 'workbuddy':
            server['type'] = 'streamableHttp'
    return {**result, 'config': config, 'status': 'awaiting_oauth', 'next': '在宿主选择此新连接并完成 OAuth，然后核对工具和当前主体。'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check_connection(endpoint, issuer):
    opener = urllib.request.build_opener(NoRedirect()).open
    resource_url = f'{endpoint.scheme}://{endpoint.netloc}/.well-known/oauth-protected-resource/mcp'
    resource = json.loads(fetch(resource_url, opener))
    def includes(values, value):
        return isinstance(values, list) and value in values

    if not isinstance(resource, dict) or resource.get('resource') != endpoint.geturl() or not includes(resource.get('authorization_servers'), issuer.geturl()):
        raise ValueError('OAuth 资源归属不符')
    auth_url = f'{issuer.scheme}://{issuer.netloc}/.well-known/oauth-authorization-server/mcp-oauth'
    auth = json.loads(fetch(auth_url, opener))
    if (not isinstance(auth, dict) or auth.get('issuer') != issuer.geturl()
            or not includes(auth.get('code_challenge_methods_supported'), 'S256')
            or not includes(auth.get('scopes_supported'), 'quality:read')):
        raise ValueError('OAuth 发现或 PKCE 不可用')
    return {'discovery': 'passed', 'oauth': 'not_checked', 'tools': 'not_checked',
            'next': '由宿主完成登录，再通过新连接调用 tools/list 和 oprun_new_account_context。'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'update', 'check'])
    parser.add_argument('--host', choices=['auto', 'codex', 'claude', 'qveris', 'workbuddy', 'generic'], default='auto')
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--target', type=Path, help='完整 Skill 目标目录；桌面客户端由宿主确认此路径')
    parser.add_argument('--version', default='latest')
    parser.add_argument('--readonly', action='store_true')
    parser.add_argument('--mcp-url', help='部署方提供的新 MCP 地址')
    parser.add_argument('--oauth-issuer', help='部署方提供的新 OAuth issuer')
    parser.add_argument('--offline', action='store_true', help='check 时仅检查本地文件')
    args = parser.parse_args()
    try:
        endpoint = deployment_url(args.mcp_url, '/mcp') if args.mcp_url is not None else None
        issuer = deployment_url(args.oauth_issuer, '/mcp-oauth') if args.oauth_issuer is not None else None
        if args.action == 'check':
            if args.offline:
                result = {'discovery': 'not_checked', 'oauth': 'not_checked', 'tools': 'not_checked'}
            elif endpoint is not None and issuer is not None:
                result = check_connection(endpoint, issuer)
            else:
                result = {'status': 'awaiting_endpoint', 'oauth': 'not_checked', 'tools': 'not_checked'}
            if args.target:
                receipt = json.loads((args.target / STATE).read_text())
                result['skill'] = 'verified' if tree_hashes(args.target) == receipt['skill_files'] else 'modified'
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        if args.offline:
            raise ValueError('--offline 仅适用于 check')
        manifest, files = release_bundle(args.version)
        host = choose_host(args.host, args.project)
        connection = profile(host, args.readonly, files, endpoint, issuer)
        target = args.target
        if target is None and host in ('codex', 'claude'):
            target = args.project / ('.agents' if host == 'codex' else '.claude') / 'skills' / SKILL
        result = install(target, manifest, files, args.action == 'update') if target else {'skill': 'awaiting_host_import', 'version': manifest['version']}
        result.update({'host': host, 'connection': connection})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as error:
        # Never print response bodies, authenticated URLs or credentials.
        print(json.dumps({'status': 'blocked', 'reason': str(error) if isinstance(error, ValueError) else type(error).__name__}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
