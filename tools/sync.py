#!/usr/bin/env python3
"""Distribute the reviewed Skill from a fixed commit of the repository that owns it.

The Skill source lives in TeamSillyBees/oprun-v2 under mcp/skills/; this repository is a verified mirror.
Releases 1.2.0 to 2.6.3 were cut from TeamSillyBees/oprun-mcp. That repository was merged into oprun-v2 with
its history, so the commits those releases record exist in oprun-v2 as well, with the Skill at its old path.
"""

import argparse
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
# Where a maintainer gets the Skill from today.
SOURCE_REPOSITORY = "TeamSillyBees/oprun-v2"
SOURCE_DIR = "mcp/skills/oprun-project-planning"
# Where the Skill sat in oprun-mcp before the merge. Only --check reads it, for releases recorded back then.
FORMER_SOURCE_DIR = "skills/oprun-project-planning"
TARGET_DIR = "skills/oprun-project-planning"
# The identifier written to release.json and from there into the published manifests. It stays what it has
# been: the MCP server's integration manifest publishes the same value (mcp/tools/generate.py in oprun-v2),
# and INSTALL.md names it. Change it only together with those, as a deliberate release.
PUBLISHED_SOURCE = "TeamSillyBees/oprun-mcp"


def run(cwd, *args, binary=False):
    output = subprocess.check_output(["git", *args], cwd=cwd)
    return output if binary else output.decode("utf-8")


def source_tree(source, commit, directory=SOURCE_DIR):
    """Return {relative path: blob id} for the Skill under directory at commit, regular files only."""
    entries = {}
    listing = run(source, "ls-tree", "-r", "-z", "--full-tree", commit, "--", directory + "/")
    for entry in filter(None, listing.split("\0")):
        meta, path = entry.split("\t", 1)
        mode, kind, blob = meta.split()
        # Symlinks or submodules would let a reviewed tree point outside itself.
        if kind != "blob" or mode not in ("100644", "100755"):
            raise SystemExit(f"Only regular files may be distributed: {path}")
        entries[path[len(directory) + 1:]] = blob
    return entries


def exists(source, commit, path):
    """Whether the commit has anything at path, whatever kind of entry it is."""
    return subprocess.run(["git", "cat-file", "-e", f"{commit}:{path}"], cwd=source,
                          stderr=subprocess.DEVNULL).returncode == 0


def local_files(target):
    return {p.relative_to(target).as_posix(): p for p in target.rglob("*") if p.is_file()} if target.is_dir() else {}


def drift(target, entries):
    """Compare by Git blob id so CRLF checkouts of identical content still match."""
    local = local_files(target)
    problems = [f"missing {name}" for name in sorted(set(entries) - set(local))]
    problems += [f"extra {name}" for name in sorted(set(local) - set(entries))]
    for name in sorted(set(entries) & set(local)):
        blob = run(ROOT, "hash-object", "--path", f"{TARGET_DIR}/{name}", str(local[name])).strip()
        if blob != entries[name]:
            problems.append(f"changed {name}")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, dest="source", help=f"local clone of {SOURCE_REPOSITORY}")
    # The former name of --source. It still parses, so an old command line reaches the checks below and is
    # told where the Skill lives now, instead of stopping at an argument error.
    parser.add_argument("--oprun-mcp", type=Path, dest="source", help=argparse.SUPPRESS)
    parser.add_argument("--ref", default="origin/main", help="source commit to copy (default: origin/main)")
    parser.add_argument("--check", action="store_true",
                        help="verify skills/ equals the commit recorded in release.json; change nothing")
    parser.add_argument("--allow-unmerged", action="store_true",
                        help="permit a commit not on the source's origin/main (local trials only, never release)")
    args = parser.parse_args()
    if args.source is None:
        parser.error("--source is required")
    release_path = ROOT / "release.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    target = ROOT / TARGET_DIR

    ref = release["mcp_revision"] if args.check else args.ref
    try:
        commit = run(args.source, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").strip()
    except subprocess.CalledProcessError:
        raise SystemExit(f"{ref} is not a commit in {args.source}. Fetch that clone, "
                         f"or pass an up-to-date clone of {SOURCE_REPOSITORY} with --source.")
    entries = source_tree(args.source, commit)
    # A release recorded before the repositories were merged: the Skill sat at the root of oprun-mcp.
    # Only when the commit has nothing at all at today's path, so a broken tree there is never papered over.
    former = args.check and not exists(args.source, commit, SOURCE_DIR)
    if former:
        entries = source_tree(args.source, commit, FORMER_SOURCE_DIR)
    if "SKILL.md" not in entries:
        raise SystemExit(f"{SOURCE_DIR}/SKILL.md is missing at {commit}. The Skill is maintained in {SOURCE_REPOSITORY} "
                         f"under {SOURCE_DIR}: pass an up-to-date clone of that repository with --source, "
                         "and a commit made after the Skill moved there.")
    if args.check:
        problems = drift(target, entries)
        if problems:
            raise SystemExit(f"{TARGET_DIR} differs from source commit {commit}:\n  " + "\n  ".join(problems)
                             + "\nRun tools/sync.py instead of editing skills/ directly.")
        print(f"{TARGET_DIR} matches {FORMER_SOURCE_DIR if former else SOURCE_DIR} at source commit {commit}")
        return

    merged = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "origin/main"], cwd=args.source)
    if merged.returncode != 0 and not args.allow_unmerged:
        raise SystemExit(f"{commit} is not on {SOURCE_REPOSITORY} origin/main; fetch it or merge the Skill change first")

    for name, path in local_files(target).items():
        if name not in entries:
            path.unlink()
    for name, blob in entries.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(run(args.source, "cat-file", "blob", blob, binary=True))
    for directory in sorted((p for p in target.rglob("*") if p.is_dir()), reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()

    release.pop("oprun_revision", None)
    release["mcp_revision"] = commit
    release["source_repository"] = PUBLISHED_SOURCE
    release["source_merge_status"] = "merged" if merged.returncode == 0 else "pending"
    release_path.write_bytes((json.dumps(release, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"Synced {len(entries)} files from {SOURCE_REPOSITORY} {commit}; review the diff, then bump release.json version")


if __name__ == "__main__":
    main()
