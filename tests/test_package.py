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
        skill = ROOT / package.SKILL_DIR
        self.skill_files = sorted(p.relative_to(skill).as_posix() for p in skill.rglob("*") if p.is_file())
        self.sources = [*package.FIXED_SOURCES, *(f"{package.SKILL_DIR}/{name}" for name in self.skill_files)]
        for name in self.sources:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / name).read_bytes())
        # Package fixture represents a reviewed upstream commit; test pending
        # source behavior separately instead of inheriting this checkout state.
        release_path=self.root/"release.json"
        release=json.loads(release_path.read_text());release["source_merge_status"]="merged"
        release_path.write_text(json.dumps(release,indent=2)+"\n")
        self.git("init", "--quiet")
        self.git("add", "--", *self.sources)
        self.git("-c", "user.name=Package Test", "-c", "user.email=package@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Synthetic package fixture")
        # Release builds require the commit to be on a remote branch.
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.PIPE)

    def build(self, name="dist", *extra):
        output = self.root / name
        with patch.object(package, "ROOT", self.root), patch("sys.argv", ["package.py", "--output-dir", str(output), *extra]), contextlib.redirect_stdout(io.StringIO()):
            package.main()
        return output

    def test_installed_bundle_resolves_every_local_reference(self):
        output = self.build()
        with zipfile.ZipFile(output / "oprun-project-planning.zip") as archive:
            names = set(archive.namelist())
            # Exactly the committed Skill tree: nothing hand-listed, nothing extra.
            self.assertEqual(names, {f"oprun-project-planning/{name}" for name in self.skill_files})
            self.assertIn("oprun-project-planning/SKILL.md", names)
            for name in names:
                path = PurePosixPath(name)
                self.assertFalse(path.is_absolute())
                self.assertNotIn("..", path.parts)
            install = self.root / "isolated-install"
            archive.extractall(install)
        for markdown in install.rglob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", markdown.read_text(encoding="utf-8")):
                if not target.startswith("https://"):
                    self.assertTrue((markdown.parent / target).is_file(), target)
        config = json.loads((install / "oprun-project-planning/assets/workbuddy-mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(config, {"mcpServers": {"oprun": {"type": "streamableHttp", "url": "https://www.agi.yifx.vip/mcp"}}})
        self.assertEqual((output / "workbuddy-mcp.json").read_bytes(), (install / "oprun-project-planning/assets/workbuddy-mcp.json").read_bytes())

    def test_qveris_import_keeps_oauth_and_the_path_scoped_issuer(self):
        output = self.build()
        config = json.loads((output / "qveris-mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(set(config["mcpServers"]), {"oprun"})
        server = config["mcpServers"]["oprun"]
        self.assertEqual(server["type"], "http")
        self.assertEqual(server["authMode"], "oauth")
        self.assertEqual(server["issuer"], "https://www.agi.yifx.vip/mcp")
        self.assertEqual(server["url"], server["issuer"])
        self.assertEqual(server["scope"].split(), [
            "plan:read", "plan:propose", "plan:generate", "plan:publish",
            "match:read", "match:propose", "delivery:read", "delivery:submit",
            "files:read", "files:write", "execution:read", "execution:propose",
            "acceptance:propose", "release:propose", "funding:propose", "settlement:read", "settlement:propose"])
        self.assertEqual(set(server), {"type", "url", "authMode", "issuer", "scope"})
        with zipfile.ZipFile(output / "oprun-project-planning.zip") as archive:
            self.assertEqual(archive.read("oprun-project-planning/assets/qveris-mcp.json"),
                             (output / "qveris-mcp.json").read_bytes())

    def test_readonly_profile_preserves_oauth_and_only_reads(self):
        output = self.build()
        expected = {"qveris-readonly-mcp.json": {"plan:read", "match:read", "delivery:read", "files:read", "execution:read", "settlement:read"}}
        self.assertFalse((output / "qveris-worker-mcp.json").exists())
        self.assertFalse((output / "qveris-publisher-mcp.json").exists())
        with zipfile.ZipFile(output / "oprun-project-planning.zip") as archive:
            for name, scopes in expected.items():
                with self.subTest(profile=name):
                    raw = (output / name).read_bytes()
                    server = json.loads(raw)["mcpServers"]["oprun"]
                    self.assertEqual(server["authMode"], "oauth")
                    self.assertEqual(server["issuer"], "https://www.agi.yifx.vip/mcp")
                    self.assertEqual(server["url"], server["issuer"])
                    self.assertEqual(set(server["scope"].split()), scopes)
                    self.assertEqual(set(server), {"type", "url", "authMode", "issuer", "scope"})
                    self.assertEqual(raw, archive.read(f"oprun-project-planning/assets/{name}"))

    def test_modified_qveris_resource_is_rejected(self):
        resource = self.root / "skills/oprun-project-planning/assets/qveris-mcp.json"
        resource.write_text("{}\n")
        with self.assertRaises(SystemExit):
            self.build()
        self.assertFalse((self.root / "dist").exists())

    def test_manifest_and_checksums_cover_every_asset(self):
        output = self.build()
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["revision"], self.git("rev-parse", "HEAD").decode().strip())
        checksums = dict(line.split("  ", 1)[::-1] for line in (output / "SHA256SUMS").read_text(encoding="utf-8").splitlines())
        self.assertEqual(set(checksums), {p.name for p in output.iterdir()} - {"SHA256SUMS"})
        for name, digest in checksums.items():
            self.assertEqual(digest, hashlib.sha256((output / name).read_bytes()).hexdigest())
        self.assertEqual(set(manifest["files"]), set(checksums) - {"manifest.json"})
        for name, digest in manifest["files"].items():
            self.assertEqual(digest, checksums[name])

    def test_standalone_guide_has_no_missing_repository_relative_links(self):
        output = self.build()
        guide = (output / "INSTALL.md").read_text(encoding="utf-8")
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

    def test_untracked_skill_file_blocks_the_build(self):
        # The local tree must equal the committed (synced) tree before packaging.
        (self.root / "skills/oprun-project-planning/untracked.txt").write_text("Synthetic extra file\n")
        with self.assertRaises(SystemExit):
            self.build()
        self.assertFalse((self.root / "dist").exists())

    def test_committed_new_skill_file_ships_without_code_changes(self):
        new = "skills/oprun-project-planning/assets/example-mcp.json"
        (self.root / new).write_text("{}\n", encoding="utf-8")
        self.git("add", new)
        self.commit_change("mcp.json", (self.root / "mcp.json").read_text(encoding="utf-8") + " ")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        output = self.build()
        with zipfile.ZipFile(output / "oprun-project-planning.zip") as archive:
            self.assertIn("oprun-project-planning/assets/example-mcp.json", archive.namelist())
        self.assertTrue((output / "example-mcp.json").is_file())

    def test_manifest_lists_every_skill_member_with_its_digest(self):
        output = self.build()
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        with zipfile.ZipFile(output / "oprun-project-planning.zip") as archive:
            members = {name.removeprefix("oprun-project-planning/"): hashlib.sha256(archive.read(name)).hexdigest()
                       for name in archive.namelist()}
        self.assertEqual(manifest["skill_files"], members)
        hosts = {name.rsplit("/", 1)[-1] for name in members if name.startswith("assets/") and name.endswith("-mcp.json")}
        self.assertEqual(hosts, {p.name for p in output.glob("*-mcp.json")})

    def test_existing_artifacts_are_not_overwritten(self):
        output = self.build()
        before = (output / "oprun-project-planning.zip").read_bytes()
        with self.assertRaises(FileExistsError):
            self.build()
        self.assertEqual(before, (output / "oprun-project-planning.zip").read_bytes())

    def commit_change(self, path, text):
        (self.root / path).write_text(text, encoding="utf-8")
        self.git("-c", "user.name=Package Test", "-c", "user.email=package@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "--quiet", "-am", "Synthetic follow-up")

    def test_crlf_checkout_of_committed_sources_still_builds(self):
        # Windows checkouts with core.autocrlf=true hold CRLF files over LF blobs.
        self.git("config", "core.autocrlf", "true")
        for name in self.sources:
            path = self.root / name
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        output = self.build()
        with zipfile.ZipFile(output / "oprun-project-planning.zip") as archive:
            self.assertNotIn(b"\r\n", archive.read("oprun-project-planning/SKILL.md"))

    def test_untracked_package_source_is_rejected(self):
        self.git("rm", "--quiet", "--cached", "mcp.json")
        with self.assertRaises(SystemExit):
            self.build()
        self.assertFalse((self.root / "dist").exists())

    def test_unpushed_revision_is_rejected_unless_explicitly_allowed(self):
        self.commit_change("mcp.json", "{}\n")
        with self.assertRaises(SystemExit):
            self.build()
        self.assertFalse((self.root / "dist").exists())
        self.assertTrue((self.build("trial", "--allow-unpushed") / "manifest.json").is_file())

    def test_existing_version_tag_on_another_commit_is_rejected(self):
        version = json.loads((self.root / "release.json").read_text(encoding="utf-8"))["version"]
        self.git("tag", f"v{version}")
        self.build("same-commit")
        self.commit_change("mcp.json", "{}\n")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        with self.assertRaises(SystemExit):
            self.build()


    def test_pending_upstream_requires_explicit_trial(self):
        p=self.root/"release.json";v=json.loads(p.read_text());v["source_merge_status"]="pending";p.write_text(json.dumps(v)+"\n")
        self.git("add","release.json")
        self.git("-c","user.name=Package Test","-c","user.email=package@example.invalid","-c","commit.gpgsign=false","commit","--quiet","-m","Pending synthetic source")
        self.git("update-ref","refs/remotes/origin/main","HEAD")
        with self.assertRaisesRegex(SystemExit,"pending review"):
            self.build()
        self.build("trial","--allow-unpushed")


if __name__ == "__main__":
    unittest.main()
