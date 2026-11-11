#!/usr/bin/env python3
"""Package the committed Skill and onboarding files without changing prior builds."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "release.json",
    "skills/oprun-project-planning/SKILL.md",
    "INSTALL.md",
    "mcp.json",
    "tools/package.py",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    contents = {}
    for path in SOURCES:
        contents[path] = subprocess.check_output(
            ["git", "show", f"{revision}:{path}"], cwd=ROOT
        )
        if (ROOT / path).read_bytes() != contents[path]:
            raise SystemExit(f"Commit the package source before building: {path}")

    release = json.loads(contents["release.json"])
    if not re.fullmatch(r"\d+\.\d+\.\d+", release["version"]):
        raise SystemExit("release.json must contain a stable semantic version")
    # A fresh directory prevents overwriting previously reviewed release assets.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    bundle = args.output_dir / "oprun-project-planning.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        info = zipfile.ZipInfo(
            "oprun-project-planning/SKILL.md", date_time=(1980, 1, 1, 0, 0, 0)
        )
        info.external_attr = 0o100644 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, contents["skills/oprun-project-planning/SKILL.md"])

    for name in ("INSTALL.md", "mcp.json"):
        (args.output_dir / name).write_bytes(contents[name])
    hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(args.output_dir.iterdir())
    }
    manifest = {
        **release,
        "tag": "v" + release["version"],
        "revision": revision,
        "files": hashes,
        "skill_sha256": hashlib.sha256(
            contents["skills/oprun-project-planning/SKILL.md"]
        ).hexdigest(),
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    hashes["manifest.json"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    (args.output_dir / "SHA256SUMS").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(hashes.items())),
        encoding="utf-8",
    )
    print(f"Packaged v{release['version']} from {revision} in {args.output_dir}")


if __name__ == "__main__":
    main()
