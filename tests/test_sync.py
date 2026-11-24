"""The distributed Skill must be an exact copy of a merged OpRun commit."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("skill_sync", ROOT / "tools/sync.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)
SOURCE = sync.SOURCE_DIR
COMMIT = ("-c", "user.name=Sync Test", "-c", "user.email=sync@example.invalid", "-c", "commit.gpgsign=false",
          "commit", "--quiet")


def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd, stderr=subprocess.PIPE).decode().strip()


class SkillSyncTest(unittest.TestCase):
    def setUp(self):
        (ROOT / "tmp").mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(prefix="sync-test-", dir=ROOT / "tmp")
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        # Synthetic OpRun repository whose main holds the reviewed Skill.
        self.oprun = base / "oprun"
        self.write(self.oprun / SOURCE / "SKILL.md", "# Skill\n\nSee [guide](references/guide.md).\n")
        self.write(self.oprun / SOURCE / "references/guide.md", "Synthetic guide\n")
        self.write(self.oprun / "services/server.go", "package main\n")
        git(self.oprun, "init", "--quiet")
        git(self.oprun, "add", ".")
        git(self.oprun, *COMMIT, "-m", "Synthetic OpRun main")
        git(self.oprun, "update-ref", "refs/remotes/origin/main", "HEAD")
        self.main = git(self.oprun, "rev-parse", "HEAD")
        # Synthetic distribution repository with a stale, hand-edited Skill.
        self.dist = base / "dist"
        self.write(self.dist / "release.json", json.dumps({"version": "1.0.0", "mcp_revision": "0" * 40}, indent=2) + "\n")
        self.write(self.dist / "skills/oprun-project-planning/SKILL.md", "stale\n")
        self.write(self.dist / "skills/oprun-project-planning/references/old.md", "removed upstream\n")
        git(self.dist, "init", "--quiet")
        git(self.dist, "add", ".")
        git(self.dist, *COMMIT, "-m", "Synthetic distribution")

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode())

    def run_sync(self, *args, source=None, flag="--source"):
        with patch.object(sync, "ROOT", self.dist), patch("sys.argv", ["sync.py", flag, str(source or self.oprun), *args]), \
                contextlib.redirect_stdout(io.StringIO()):
            sync.main()

    def skill(self):
        target = self.dist / "skills/oprun-project-planning"
        return {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob("*") if p.is_file()}

    def test_sync_mirrors_the_source_tree_and_records_its_commit(self):
        self.run_sync()
        self.assertEqual(self.skill(), {"SKILL.md": b"# Skill\n\nSee [guide](references/guide.md).\n",
                                        "references/guide.md": b"Synthetic guide\n"})
        self.assertFalse((self.dist / "skills/oprun-project-planning/references/old.md").exists())
        release = json.loads((self.dist / "release.json").read_text(encoding="utf-8"))
        # The published identifier keeps its value although the Skill is now read from oprun-v2; see PUBLISHED_SOURCE.
        self.assertEqual(release, {"version": "1.0.0", "mcp_revision": self.main, "source_repository": "TeamSillyBees/oprun-mcp", "source_merge_status": "merged"})
        self.run_sync("--check")

    def test_the_paths_are_the_ones_the_real_repositories_use(self):
        # The fixtures are built from these constants, so a typo in one of them would pass every other test.
        self.assertEqual(sync.SOURCE_DIR, "mcp/skills/oprun-project-planning")
        self.assertEqual(sync.FORMER_SOURCE_DIR, "skills/oprun-project-planning")

    def test_install_guide_names_the_published_source(self):
        # INSTALL.md is packaged and read by agents. Whoever changes the identifier has to change it there too.
        published = json.loads((ROOT / "release.json").read_text(encoding="utf-8"))["source_repository"]
        self.assertEqual(published, sync.PUBLISHED_SOURCE)
        self.assertIn(published.split("/")[1], (ROOT / "INSTALL.md").read_text(encoding="utf-8"))

    def former_repository(self, files):
        repository = self.dist.parent / "former"
        for name, text in files.items():
            self.write(repository / name, text)
        git(repository, "init", "--quiet")
        git(repository, "add", ".")
        git(repository, *COMMIT, "-m", "Synthetic oprun-mcp main")
        git(repository, "update-ref", "refs/remotes/origin/main", "HEAD")
        return repository, git(repository, "rev-parse", "HEAD")

    def record(self, commit, skill):
        self.write(self.dist / "release.json", json.dumps({"version": "1.0.0", "mcp_revision": commit}) + "\n")
        self.write(self.dist / "skills/oprun-project-planning/SKILL.md", skill)
        (self.dist / "skills/oprun-project-planning/references/old.md").unlink()

    def test_release_recorded_before_the_source_moved_still_checks_but_cannot_be_synced_from(self):
        # Releases 1.2.0 to 2.6.3 record oprun-mcp commits, where the Skill sat at the repository root.
        former, recorded = self.former_repository({sync.FORMER_SOURCE_DIR + "/SKILL.md": "# Before the merge\n"})
        self.record(recorded, "# Before the merge\n")
        self.run_sync("--check", source=former)
        # The frozen repository must not be copied from again: its Skill no longer receives changes.
        with self.assertRaises(SystemExit) as refused:
            self.run_sync(source=former)
        self.assertIn("TeamSillyBees/oprun-v2", str(refused.exception))
        self.assertEqual(json.loads((self.dist / "release.json").read_text(encoding="utf-8"))["mcp_revision"], recorded)
        # The former flag name leads to the same answer rather than to an argument error.
        with self.assertRaises(SystemExit) as renamed:
            self.run_sync(source=former, flag="--oprun-mcp")
        self.assertIn("TeamSillyBees/oprun-v2", str(renamed.exception))
        self.run_sync(flag="--oprun-mcp")

    def test_former_path_is_only_used_when_the_commit_has_nothing_at_the_new_one(self):
        # Both paths present: today's path wins, also for --check.
        both, commit = self.former_repository({sync.SOURCE_DIR + "/SKILL.md": "# New path\n",
                                               sync.FORMER_SOURCE_DIR + "/SKILL.md": "# Old path\n"})
        self.record(commit, "# Old path\n")
        with self.assertRaises(SystemExit) as stale:
            self.run_sync("--check", source=both)
        self.assertIn("changed SKILL.md", str(stale.exception))
        # Something at today's path but no SKILL.md: a broken tree, not a release from before the move.
        git(both, "rm", "--quiet", sync.SOURCE_DIR + "/SKILL.md")
        self.write(both / sync.SOURCE_DIR / "references/guide.md", "Guide without a Skill\n")
        git(both, "add", ".")
        git(both, *COMMIT, "-m", "Incomplete Skill")
        incomplete = git(both, "rev-parse", "HEAD")
        self.write(self.dist / "release.json", json.dumps({"version": "1.0.0", "mcp_revision": incomplete}) + "\n")
        with self.assertRaises(SystemExit) as broken:
            self.run_sync("--check", source=both)
        self.assertIn("SKILL.md is missing", str(broken.exception))

    def test_unknown_commit_is_reported_in_words(self):
        self.write(self.dist / "release.json", json.dumps({"version": "1.0.0", "mcp_revision": "1" * 40}) + "\n")
        with self.assertRaises(SystemExit) as unknown:
            self.run_sync("--check")
        self.assertIn("is not a commit in", str(unknown.exception))
        self.assertIn("Fetch that clone", str(unknown.exception))

    def test_check_reports_hand_edits_and_extra_files(self):
        self.run_sync()
        self.write(self.dist / "skills/oprun-project-planning/references/guide.md", "edited here\n")
        with self.assertRaises(SystemExit) as edited:
            self.run_sync("--check")
        self.assertIn("changed references/guide.md", str(edited.exception))
        self.run_sync()
        self.write(self.dist / "skills/oprun-project-planning/notes.md", "extra\n")
        with self.assertRaises(SystemExit) as extra:
            self.run_sync("--check")
        self.assertIn("extra notes.md", str(extra.exception))

    def test_check_accepts_crlf_checkout_of_identical_content(self):
        self.run_sync()
        git(self.dist, "config", "core.autocrlf", "true")
        guide = self.dist / "skills/oprun-project-planning/references/guide.md"
        guide.write_bytes(guide.read_bytes().replace(b"\n", b"\r\n"))
        self.run_sync("--check")

    def test_unmerged_commit_is_rejected_unless_explicitly_allowed(self):
        git(self.oprun, "checkout", "--quiet", "-b", "feature")
        self.write(self.oprun / SOURCE / "SKILL.md", "# Unreviewed\n")
        git(self.oprun, *COMMIT, "-am", "Unmerged change")
        with self.assertRaises(SystemExit):
            self.run_sync("--ref", "feature")
        self.assertEqual(self.skill()["SKILL.md"], b"stale\n")
        self.run_sync("--ref", "feature", "--allow-unmerged")
        self.assertEqual(self.skill()["SKILL.md"], b"# Unreviewed\n")

    def test_symlinks_in_the_source_tree_are_rejected(self):
        blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=self.oprun, input=b"../../../services/server.go",
                              capture_output=True, check=True).stdout.decode().strip()
        git(self.oprun, "update-index", "--add", "--cacheinfo", f"120000,{blob},{SOURCE}/references/link.md")
        git(self.oprun, *COMMIT, "-m", "Symlink")
        git(self.oprun, "update-ref", "refs/remotes/origin/main", "HEAD")
        with self.assertRaises(SystemExit):
            self.run_sync()
        self.assertEqual(self.skill()["SKILL.md"], b"stale\n")


if __name__ == "__main__":
    unittest.main()
