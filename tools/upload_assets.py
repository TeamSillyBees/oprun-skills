#!/usr/bin/env python3
"""Upload verified assets to an existing draft with web-readable document types."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import quote

REPO = 'TeamSillyBees/oprun-skills'


def content_type(name):
    if name.endswith('.zip'):
        return 'application/zip'
    if name.endswith('.json'):
        return 'application/json'
    if name.endswith(('.md', '.py')) or name == 'SHA256SUMS':
        return 'text/plain; charset=utf-8'
    raise ValueError('Unknown asset type: ' + name)


def verify(directory, tag):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest['repository'] != REPO or manifest['tag'] != tag:
        raise ValueError('Wrong release identity')
    checks = dict(line.split('  ', 1)[::-1] for line in (directory/'SHA256SUMS').read_text().splitlines())
    if set(checks) != {p.name for p in directory.iterdir()} - {'SHA256SUMS'}:
        raise ValueError('Asset set mismatch')
    for name, digest in checks.items():
        if Path(name).name != name or (directory/name).is_symlink():
            raise ValueError('Unsafe asset')
        if hashlib.sha256((directory/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Asset checksum mismatch: ' + name)
    if manifest['files'] != {n:h for n,h in checks.items() if n != 'manifest.json'}:
        raise ValueError('Manifest mismatch')
    for p in directory.iterdir():
        content_type(p.name)
    return manifest


def upload(directory, tag):
    manifest = verify(directory, tag)
    release = json.loads(subprocess.check_output(['gh','api',f'repos/{REPO}/releases/tags/{tag}']))
    if not release['draft'] or release['assets'] or release['target_commitish'] != manifest['revision']:
        raise ValueError('Require an empty draft bound to the full package revision; never overwrite assets')
    for p in sorted(Path(directory).iterdir()):
        subprocess.run(['gh','api','--method','POST','-H','Content-Type: '+content_type(p.name),
                        '--input',str(p), f'https://uploads.github.com/repos/{REPO}/releases/{release["id"]}/assets?name={quote(p.name)}'],
                       check=True, stdout=subprocess.DEVNULL)
        print('Uploaded ' + p.name)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--tag',required=True)
    args=parser.parse_args()
    upload(args.directory,args.tag)
