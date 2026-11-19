#!/usr/bin/env python3
"""Publish the verified npm tarball from a stable GitHub Release."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from install import unpack
from upload_assets import verify


REGISTRY = "https://registry.npmjs.org"
NAME = "oprun-skills"
TARBALL = "oprun-skills.tgz"
STABLE_VERSION = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"


def verify_release(directory, tag):
    if not re.fullmatch(f"v{STABLE_VERSION}", tag):
        raise ValueError(f"Expected a stable release tag: {tag}")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    tagged = subprocess.check_output(
        ["git", "rev-parse", f"refs/tags/{tag}^{{commit}}"], text=True
    ).strip()
    if tagged != revision:
        raise ValueError("Release tag and checked-out commit differ")
    subprocess.run(["git", "merge-base", "--is-ancestor", revision, "origin/main"], check=True)

    manifest = verify(directory, tag)
    tarball = directory / TARBALL
    with TemporaryDirectory(prefix="oprun-release-verification-") as temporary:
        expected = Path(temporary) / "expected"
        # Reuse the packager's npm member and metadata checks against the tagged
        # commit. Publish the downloaded tarball, never the verification output.
        subprocess.run(
            [sys.executable, "tools/package.py", "--output-dir", str(expected), "--npm-tarball", str(tarball)],
            check=True,
        )
        baseline = json.loads((expected / "manifest.json").read_text())
        if (manifest.keys() != baseline.keys()
                or any(manifest[key] != value for key, value in baseline.items() if key != "files")):
            raise ValueError("Release manifest differs from the tagged package source")
        if manifest["files"].keys() != baseline["files"].keys():
            raise ValueError("Release asset list differs from the tagged package source")
        for name, digest in baseline["files"].items():
            # ZIP compression can vary by Python/zlib version. Verify its
            # unpacked content against the same Skill hashes as the npm bundle.
            if name == "oprun-project-planning.zip":
                unpack((directory / name).read_bytes(), baseline)
            elif manifest["files"][name] != digest:
                raise ValueError(f"Release asset differs from the tagged source: {name}")
    return manifest["version"]


def registry_read(path, *, allow_missing=False):
    request = Request(f"{REGISTRY}{path}?readback={time.time_ns()}", headers={"Cache-Control": "no-cache"})
    try:
        with urlopen(request, timeout=10) as response:
            return response.read()
    except HTTPError as error:
        if allow_missing and error.code == 404:
            return None
        raise


def latest_version():
    return json.loads(registry_read(f"/-/package/{NAME}/dist-tags"))["latest"]


def published_bytes(version):
    return registry_read(f"/{NAME}/-/{NAME}-{version}.tgz", allow_missing=True)


def matches_package(remote, local):
    if remote is None:
        return False
    if remote != local:
        raise ValueError("The npm version contains different bytes from the GitHub Release")
    return True


def publish(tarball, version):
    local = tarball.read_bytes()
    latest = latest_version()
    if not re.fullmatch(STABLE_VERSION, latest):
        raise ValueError(f"Expected a stable npm latest version: {latest}")
    if tuple(map(int, latest.split("."))) > tuple(map(int, version.split("."))):
        print(f"npm latest is already newer ({latest}); skipping {version}")
        return

    already_published = matches_package(published_bytes(version), local)
    if already_published and latest == version:
        print(f"Verified npm {NAME}@{version} is already latest")
        return

    if not already_published and latest != version:
        subprocess.run(
            ["npm", "publish", str(tarball), "--tag", "latest", "--access", "public",
             "--ignore-scripts", "--registry", REGISTRY],
            check=True,
        )
    for attempt in range(24):
        try:
            if latest_version() == version and matches_package(published_bytes(version), local):
                print(f"Verified npm {NAME}@{version} is latest and matches GitHub")
                return
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504):
                raise
        except (URLError, TimeoutError):
            pass
        if attempt < 23:
            time.sleep(5)
    raise TimeoutError(f"npm has not confirmed {NAME}@{version} as latest with the expected bytes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    directory = args.directory.resolve()
    version = verify_release(directory, args.tag)
    if args.verify_only:
        print(f"Verified GitHub Release {args.tag} and npm tarball")
    else:
        publish(directory / TARBALL, version)


if __name__ == "__main__":
    main()
