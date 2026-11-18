#!/usr/bin/env python3
"""Package the committed Skill and onboarding files without changing prior builds."""

import argparse
import fnmatch
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = "skills/oprun-project-planning"
FIXED_SOURCES = ("release.json", "INSTALL.md", "mcp.json", "tools/package.py", "tools/sync.py", "tools/install.py", "tools/upload_assets.py", "package.json", "cli/core.mjs", "cli/main.mjs", "tools/package-npm.mjs")
# Host import files are published next to the ZIP so users can import them directly.
HOST_CONFIG = "assets/*-mcp.json"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8")


def skill_files(revision="HEAD"):
    """Every committed file of the Skill; the tree synced from OpRun decides the list."""
    listing = git("ls-tree", "-r", "-z", "--name-only", "--full-tree", revision, "--", SKILL_DIR + "/")
    return sorted(path[len(SKILL_DIR) + 1:] for path in filter(None, listing.split("\0")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--npm-tarball", type=Path, help="verified npm pack artifact from this same commit")
    parser.add_argument(
        "--allow-unpushed",
        action="store_true",
        help="skip the remote check (local trial builds only; links will 404)",
    )
    args = parser.parse_args()
    revision = git("rev-parse", "HEAD").strip()
    # Compare normalized content with Git rather than raw bytes: CRLF checkouts
    # (core.autocrlf) stay clean, while edits, staged changes and untracked files
    # under skills/ do not. `git status` is unsuitable: it flags any size change.
    paths = ("--", *FIXED_SOURCES, SKILL_DIR)
    dirty = git("diff", "HEAD", "--name-only", *paths) + git("ls-files", "--others", "--exclude-standard", *paths)
    if dirty:
        raise SystemExit(f"Commit the package source before building:\n{dirty}")
    files = skill_files(revision)
    if "SKILL.md" not in files:
        raise SystemExit(f"{SKILL_DIR}/SKILL.md is not committed")
    sources = (*FIXED_SOURCES, *(f"{SKILL_DIR}/{name}" for name in files))
    contents = {
        path: subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)
        for path in sources
    }

    release = json.loads(contents["release.json"])
    if not re.fullmatch(r"\d+\.\d+\.\d+", release["version"]):
        raise SystemExit("release.json must contain a stable semantic version")
    if release.get("source_merge_status") != "merged" and not args.allow_unpushed:
        raise SystemExit("MCP source is pending review; only a local trial package may be built")
    tag = "v" + release["version"]
    tagged = git("tag", "--list", tag, "--format=%(objectname)^{commit}").strip()
    if tagged and git("rev-parse", tagged).strip() != revision:
        raise SystemExit(f"{tag} already exists on another commit; bump release.json")
    # The standalone INSTALL.md links to blob/<revision>; it must exist remotely.
    if not args.allow_unpushed and not git("branch", "-r", "--contains", revision).strip():
        raise SystemExit(f"Push {revision} before building release assets")
    npm_bytes = None
    if args.npm_tarball:
        if args.npm_tarball.stat().st_size > 16 * 1024 * 1024:
            raise SystemExit("npm package exceeds size limit")
        npm_bytes = args.npm_tarball.read_bytes()
        with tarfile.open(args.npm_tarball, "r:gz") as archive:
            members = archive.getmembers()
            if any(not member.isfile() for member in members) or sum(member.size for member in members) > 16 * 1024 * 1024:
                raise SystemExit("Unsafe npm archive entries")
            entries = {member.name: archive.extractfile(member).read() for member in members}
            expected_names = {"package/" + name for name in ("package.json", "bundle.json", "release.json", "README.md", "INSTALL.md", "cli/core.mjs", "cli/main.mjs")}
            expected_names.update("package/" + SKILL_DIR + "/" + name for name in files)
            if len(entries) != len(members) or set(entries) != expected_names:
                raise SystemExit("Unexpected npm archive files")
            for name in ("release.json", "INSTALL.md", "cli/core.mjs", "cli/main.mjs", *(SKILL_DIR + "/" + name for name in files)):
                if entries["package/" + name] != contents[name]:
                    raise SystemExit("npm archive differs from commit: " + name)
            if entries["package/README.md"] != subprocess.check_output(["git", "show", revision + ":README.md"], cwd=ROOT):
                raise SystemExit("npm README differs from commit")
            npm_manifest = json.loads(entries["package/bundle.json"])
            expected_hashes = {name: hashlib.sha256(contents[SKILL_DIR + "/" + name]).hexdigest() for name in files}
            if npm_manifest != {**release, "revision": revision, "skill_files": expected_hashes}:
                raise SystemExit("npm/ZIP manifest mismatch")
            expected_package = {**json.loads(contents["package.json"]), "oprun": {"source_revision": revision, "mcp_revision": release["mcp_revision"]}}
            if release.get("source_merge_status") != "merged":
                expected_package["private"] = True
            if json.loads(entries["package/package.json"]) != expected_package:
                raise SystemExit("npm package metadata mismatch")
    # A fresh directory prevents overwriting previously reviewed release assets.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    if npm_bytes is not None:
        (args.output_dir / "oprun-skills.tgz").write_bytes(npm_bytes)
    bundle = args.output_dir / "oprun-project-planning.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            info = zipfile.ZipInfo(
                f"oprun-project-planning/{name}", date_time=(1980, 1, 1, 0, 0, 0)
            )
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, contents[f"{SKILL_DIR}/{name}"])

    for name in ("INSTALL.md", "mcp.json", "tools/install.py"):
        data = contents[name]
        if name == "INSTALL.md":
            # The standalone release guide has no repository-relative skills/.
            prefix = f"](https://github.com/{release['repository']}/blob/{revision}/skills/"
            data = data.decode("utf-8").replace("](skills/", prefix).encode("utf-8")
        (args.output_dir / Path(name).name).write_bytes(data)
    for name in files:
        if fnmatch.fnmatchcase(name, HOST_CONFIG):
            (args.output_dir / Path(name).name).write_bytes(contents[f"{SKILL_DIR}/{name}"])
    hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(args.output_dir.iterdir())
    }
    manifest = {
        **release,
        "tag": tag,
        "revision": revision,
        "files": hashes,
        "skill_sha256": hashlib.sha256(contents[f"{SKILL_DIR}/SKILL.md"]).hexdigest(),
        # Installers verify extracted members against this list instead of a hand-kept one.
        "skill_files": {
            name: hashlib.sha256(contents[f"{SKILL_DIR}/{name}"]).hexdigest() for name in files
        },
    }
    manifest_path = args.output_dir / "manifest.json"
    # Bytes, not text mode: Windows would otherwise write CRLF and change the digests.
    manifest_path.write_bytes(
        (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    )
    hashes["manifest.json"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    (args.output_dir / "SHA256SUMS").write_bytes(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(hashes.items())).encode("utf-8")
    )
    print(f"Packaged v{release['version']} from {revision} in {args.output_dir}")


if __name__ == "__main__":
    main()
