import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] / 'tools/install.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.target = Path(self.tmp.name).resolve() / m.SKILL
        self.files = {'SKILL.md': b'first', 'references/a.md': b'ref'}
        self.manifest = self.manifest_for(self.files)

    def manifest_for(self, files, version='1.3.0'):
        return {'version': version, 'revision': 'a'*40, 'skill_files': {n: m.digest(v) for n,v in files.items()}}

    def test_install_idempotency_and_upgrade_backup(self):
        m.install(self.target, self.manifest, self.files)
        self.assertEqual(m.install(self.target, self.manifest, self.files)['skill'], 'current')
        files = {'SKILL.md': b'second'}
        result = m.install(self.target, self.manifest_for(files, '1.4.0'), files, True)
        self.assertEqual((Path(result['backup']) / 'SKILL.md').read_bytes(), b'first')
        self.assertFalse((self.target / 'references/a.md').exists())

    def test_modified_unmanaged_and_downgrade_blocked(self):
        m.install(self.target, self.manifest, self.files)
        with self.assertRaises(ValueError):
            m.install(self.target, self.manifest_for({'SKILL.md': b'x'}, '1.2.0'), {'SKILL.md': b'x'}, True)
        (self.target / 'SKILL.md').write_text('local edit')
        with self.assertRaises(ValueError):
            m.install(self.target, self.manifest, self.files, True)
        self.assertEqual((self.target / 'SKILL.md').read_text(), 'local edit')
        (self.target / m.STATE).unlink()
        with self.assertRaises(ValueError):
            m.install(self.target, self.manifest, self.files, True)

    def test_failed_swap_restores_previous(self):
        m.install(self.target, self.manifest, self.files)
        original = Path.rename
        def fail_stage(path, dest):
            if '-stage-' in path.name:
                raise OSError('synthetic failure')
            return original(path, dest)
        with patch.object(Path, 'rename', fail_stage), self.assertRaises(OSError):
            m.install(self.target, self.manifest_for({'SKILL.md': b'new'}, '1.4.0'), {'SKILL.md': b'new'}, True)
        self.assertEqual((self.target / 'SKILL.md').read_bytes(), b'first')

    def test_symlink_and_concurrent_lock_preserved(self):
        self.target.symlink_to(Path(self.tmp.name).resolve() / 'elsewhere')
        with self.assertRaises(ValueError):
            m.install(self.target, self.manifest, self.files)
        self.target.unlink()
        lock = self.target.parent / ('.' + self.target.name + '.lock')
        lock.mkdir()
        with self.assertRaises(FileExistsError):
            m.install(self.target, self.manifest, self.files)
        self.assertTrue(lock.exists())

    def archive(self, files):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            for n,v in files.items():
                z.writestr(n, v)
        return stream.getvalue()

    def test_zip_hash_members_and_traversal(self):
        data = self.archive({m.SKILL+'/'+n:v for n,v in self.files.items()})
        self.assertEqual(m.unpack(data, self.manifest), self.files)
        for files in ({m.SKILL+'/../outside': b'x'}, {m.SKILL+'/SKILL.md': b'changed'}, {m.SKILL+'/extra': b'x'}):
            with self.assertRaises(ValueError):
                m.unpack(self.archive(files), self.manifest)

    def test_host_detection_and_readonly(self):
        root = Path(self.tmp.name).resolve()
        self.assertEqual(m.choose_host('auto', root), 'generic')
        (root/'.agents').mkdir()
        self.assertEqual(m.choose_host('auto', root), 'codex')
        (root/'.claude').mkdir()
        self.assertEqual(m.choose_host('auto', root), 'generic')
        source = Path(__file__).resolve().parents[1]/'skills'/m.SKILL
        files = {p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob('*') if p.is_file()}
        for host in ('codex','claude','workbuddy','qveris','generic'):
            config, scopes = m.profile(host, True, files)
            self.assertTrue(all(s.endswith(':read') for s in scopes.split()))
            if host == 'qveris':
                self.assertEqual(config['mcpServers']['oprun']['issuer'], m.SITE+'/mcp')

    def test_discovery_does_not_claim_authentication(self):
        values = [json.dumps({'resource': m.SITE+'/mcp', 'authorization_servers':[m.SITE+'/mcp']}).encode(),
                  json.dumps({'issuer': m.SITE+'/mcp', 'code_challenge_methods_supported':['S256']}).encode()]
        with patch.object(m, 'fetch', side_effect=values):
            result = m.check_connection()
        self.assertEqual(result['oauth'], 'not_checked')
        self.assertEqual(result['tools'], 'not_checked')
        with patch.object(m, 'fetch', return_value=b'{}'), self.assertRaises(ValueError):
            m.check_connection()

    def test_pinned_download_and_corruption(self):
        bundle = self.archive({m.SKILL+'/'+n:v for n,v in self.files.items()})
        manifest = {**self.manifest, 'repository':m.REPO, 'skill':m.SKILL, 'tag':'v1.3.0', 'files':{m.SKILL+'.zip':m.digest(bundle)}}
        raw = json.dumps(manifest).encode()
        checks = f'{m.digest(raw)}  manifest.json\n{m.digest(bundle)}  {m.SKILL}.zip\n'.encode()
        seen=[]
        def get(url):
            seen.append(url)
            return { 'latest':b'{"tag_name":"v1.3.0"}', 'SHA256SUMS':checks, 'manifest.json':raw, m.SKILL+'.zip':bundle}[url.rsplit('/',1)[1]]
        with patch.object(m,'fetch',side_effect=get):
            self.assertEqual(m.release_bundle()[1], self.files)
        self.assertTrue(all('/v1.3.0/' in url for url in seen[1:]))
        with patch.object(m,'fetch',side_effect=[checks,raw,b'corrupt']), self.assertRaises(ValueError):
            m.release_bundle('v1.3.0')


if __name__ == '__main__':
    unittest.main()
