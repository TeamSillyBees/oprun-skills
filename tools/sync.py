#!/usr/bin/env python3
"""Copy the reviewed Skill from an OpRun main commit; never edit skills/ by hand.

The OpRun repository (integrations/agent-skills/oprun-project-planning) is the
only source. This repository distributes an exact snapshot of it and records
the source commit as release.json "oprun_revision".
"""

import argparse
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = "integrations/agent-skills/oprun-project-planning"
TARGET_DIR = "skills/oprun-project-planning"


def run(cwd, *args, binary=False):
    output = subprocess.check_output(["git", *args], cwd=cwd)
    return output if binary else output.decode("utf-8")


def source_tree(oprun, commit):
    """Return {relative path: blob id} for the Skill at commit, regular files only."""
    entries = {}
    listing = run(oprun, "ls-tree", "-r", "-z", "--full-tree", commit, "--", SOURCE_DIR + "/")
    for entry in filter(None, listing.split("\0")):
        meta, path = entry.split("\t", 1)
        mode, kind, blob = meta.split()
        # Symlinks or submodules would let a reviewed tree point outside itself.
        if kind != "blob" or mode not in ("100644", "100755"):
            raise SystemExit(f"Only regular files may be distributed: {path}")
        entries[path[len(SOURCE_DIR) + 1:]] = blob
    if "SKILL.md" not in entries:
        raise SystemExit(f"{SOURCE_DIR}/SKILL.md is missing at {commit}")
    return entries


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
    parser.add_argument("--oprun", type=Path, required=True, help="local clone of TeamSillyBees/oprun")
    parser.add_argument("--ref", default="origin/main", help="OpRun commit to copy (default: origin/main)")
    parser.add_argument("--check", action="store_true",
                        help="verify skills/ equals the commit recorded in release.json; change nothing")
    parser.add_argument("--allow-unmerged", action="store_true",
                        help="permit a commit not on OpRun origin/main (local trials only, never release)")
    args = parser.parse_args()
    release_path = ROOT / "release.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    target = ROOT / TARGET_DIR

    ref = release["oprun_revision"] if args.check else args.ref
    commit = run(args.oprun, "rev-parse", "--verify", f"{ref}^{{commit}}").strip()
    entries = source_tree(args.oprun, commit)
    if args.check:
        problems = drift(target, entries)
        if problems:
            raise SystemExit(f"{TARGET_DIR} differs from OpRun {commit}:\n  " + "\n  ".join(problems)
                             + "\nRun tools/sync.py instead of editing skills/ directly.")
        print(f"{TARGET_DIR} matches OpRun {commit}")
        return

    merged = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "origin/main"], cwd=args.oprun)
    if merged.returncode != 0 and not args.allow_unmerged:
        raise SystemExit(f"{commit} is not on OpRun origin/main; fetch it or merge the Skill change first")

    for name, path in local_files(target).items():
        if name not in entries:
            path.unlink()
    for name, blob in entries.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(run(args.oprun, "cat-file", "blob", blob, binary=True))
    for directory in sorted((p for p in target.rglob("*") if p.is_dir()), reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()

    release["oprun_revision"] = commit
    release_path.write_bytes((json.dumps(release, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"Synced {len(entries)} files from OpRun {commit}; review the diff, then bump release.json version")


if __name__ == "__main__":
    main()
