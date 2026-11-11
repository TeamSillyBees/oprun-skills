"""Exercise the shipped Skill as an isolated install, not a repository checkout."""

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("skill_package", ROOT / "tools/package.py")
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class SkillPackageTest(unittest.TestCase):
    def setUp(self):
        (ROOT / "tmp").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="package-test-", dir=ROOT / "tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in package.SOURCES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / name).read_bytes())
        self.git("init", "--quiet")
        self.git("add", "--", *package.SOURCES)
        self.git("-c", "user.name=Package Test", "-c", "user.email=package@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Synthetic package fixture")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.PIPE)

    def build(self, name="dist"):
        output = self.root / name
        with patch.object(package, "ROOT", self.root), patch("sys.argv", ["package.py", "--output-dir", str(output)]), contextlib.redirect_stdout(io.StringIO()):
            package.main()
        return output

    def test_installed_bundle_resolves_every_local_reference(self):
        output = self.build()
        with zipfile.ZipFile(output / "oprun-project-planning.zip") as archive:
            names = set(archive.namelist())
            self.assertEqual(names, {
                "oprun-project-planning/SKILL.md",
                "oprun-project-planning/references/workbuddy.md",
                "oprun-project-planning/assets/workbuddy-mcp.json",
            })
            for name in names:
                path = PurePosixPath(name)
                self.assertFalse(path.is_absolute())
                self.assertNotIn("..", path.parts)
            install = self.root / "isolated-install"
            archive.extractall(install)
        for markdown in install.rglob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", markdown.read_text()):
                if not target.startswith("https://"):
                    self.assertTrue((markdown.parent / target).is_file(), target)
        config = json.loads((install / "oprun-project-planning/assets/workbuddy-mcp.json").read_text())
        self.assertEqual(config, {"mcpServers": {"oprun": {"type": "streamableHttp", "url": "https://www.agi.yifx.vip/mcp"}}})
        self.assertEqual((output / "workbuddy-mcp.json").read_bytes(), (install / "oprun-project-planning/assets/workbuddy-mcp.json").read_bytes())

    def test_manifest_and_checksums_cover_every_asset(self):
        output = self.build()
        manifest = json.loads((output / "manifest.json").read_text())
        self.assertEqual(manifest["revision"], self.git("rev-parse", "HEAD").decode().strip())
        checksums = dict(line.split("  ", 1)[::-1] for line in (output / "SHA256SUMS").read_text().splitlines())
        self.assertEqual(set(checksums), {p.name for p in output.iterdir()} - {"SHA256SUMS"})
        for name, digest in checksums.items():
            self.assertEqual(digest, hashlib.sha256((output / name).read_bytes()).hexdigest())
        self.assertEqual(set(manifest["files"]), set(checksums) - {"manifest.json"})
        for name, digest in manifest["files"].items():
            self.assertEqual(digest, checksums[name])

    def test_standalone_guide_has_no_missing_repository_relative_links(self):
        output = self.build()
        guide = (output / "INSTALL.md").read_text()
        revision = self.git("rev-parse", "HEAD").decode().strip()
        for target in re.findall(r"\]\(([^)]+)\)", guide):
            if not target.startswith("https://"):
                self.assertTrue((output / target).is_file(), target)
            elif "/blob/" in target:
                self.assertIn(f"/blob/{revision}/", target)

    def test_build_is_reproducible(self):
        first, second = self.build("first"), self.build("second")
        self.assertEqual({p.name: p.read_bytes() for p in first.iterdir()}, {p.name: p.read_bytes() for p in second.iterdir()})

    def test_modified_supporting_resource_is_rejected(self):
        resource = self.root / "skills/oprun-project-planning/assets/workbuddy-mcp.json"
        resource.write_text("{}\n")
        with self.assertRaises(SystemExit):
            self.build()
        self.assertFalse((self.root / "dist").exists())

    def test_untracked_files_do_not_enter_the_bundle(self):
        (self.root / "skills/oprun-project-planning/untracked.txt").write_text("Synthetic extra file\n")
        with zipfile.ZipFile(self.build() / "oprun-project-planning.zip") as archive:
            self.assertFalse(any(name.endswith("untracked.txt") for name in archive.namelist()))

    def test_existing_artifacts_are_not_overwritten(self):
        output = self.build()
        before = (output / "oprun-project-planning.zip").read_bytes()
        with self.assertRaises(FileExistsError):
            self.build()
        self.assertEqual(before, (output / "oprun-project-planning.zip").read_bytes())


if __name__ == "__main__":
    unittest.main()
