import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import publish_npm


class PublishNpmTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tarball = Path(temporary.name) / "oprun-skills.tgz"
        self.artifact = b"verified GitHub Release tarball"
        self.tarball.write_bytes(self.artifact)

    def test_publishes_downloaded_tarball_and_waits_for_registry_readback(self):
        with (
            patch.object(publish_npm, "latest_version", side_effect=["2.5.0", "2.5.0", "2.5.1", "2.5.1"]),
            patch.object(publish_npm, "published_bytes", side_effect=[None, None, self.artifact]) as readback,
            patch.object(publish_npm.subprocess, "run") as run,
            patch.object(publish_npm.time, "sleep") as sleep,
        ):
            publish_npm.publish(self.tarball, "2.5.1")
        run.assert_called_once_with(
            ["npm", "publish", str(self.tarball), "--tag", "latest", "--access", "public",
             "--ignore-scripts", "--registry", publish_npm.REGISTRY],
            check=True,
        )
        self.assertEqual(readback.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_rerun_verifies_existing_latest_without_publishing_again(self):
        with (
            patch.object(publish_npm, "latest_version", return_value="2.5.1"),
            patch.object(publish_npm, "published_bytes", return_value=self.artifact),
            patch.object(publish_npm.subprocess, "run") as run,
        ):
            publish_npm.publish(self.tarball, "2.5.1")
        run.assert_not_called()

    def test_rerun_waits_if_the_package_arrived_before_latest_updated(self):
        with (
            patch.object(publish_npm, "latest_version", side_effect=["2.5.0", "2.5.1"]),
            patch.object(publish_npm, "published_bytes", return_value=self.artifact),
            patch.object(publish_npm.subprocess, "run") as run,
        ):
            publish_npm.publish(self.tarball, "2.5.1")
        run.assert_not_called()

    def test_existing_version_with_different_bytes_is_rejected(self):
        with (
            patch.object(publish_npm, "latest_version", return_value="2.5.1"),
            patch.object(publish_npm, "published_bytes", return_value=b"unrelated tarball"),
            patch.object(publish_npm.subprocess, "run") as run,
            self.assertRaisesRegex(ValueError, "different bytes"),
        ):
            publish_npm.publish(self.tarball, "2.5.1")
        run.assert_not_called()

    def test_older_release_cannot_replace_latest(self):
        with (
            patch.object(publish_npm, "latest_version", return_value="2.10.0"),
            patch.object(publish_npm, "published_bytes") as readback,
            patch.object(publish_npm.subprocess, "run") as run,
        ):
            publish_npm.publish(self.tarball, "2.9.9")
        readback.assert_not_called()
        run.assert_not_called()
