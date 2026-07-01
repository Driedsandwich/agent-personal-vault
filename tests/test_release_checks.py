from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import check_release, pii_scan, release_policy


class ReleaseCheckTests(unittest.TestCase):
    def test_pii_scan_skips_local_agent_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_path = "/" + "Users" + "/example/private"
            for dirname in release_policy.LOCAL_DEVELOPER_CONFIG_DIRS:
                local_config = root / dirname / "settings.json"
                local_config.parent.mkdir()
                local_config.write_text(f'{{"path": "{private_path}"}}', encoding="utf-8")
            for filename in release_policy.LOCAL_DEVELOPER_CONFIG_FILES:
                (root / filename).write_text(f"local path: {private_path}\n", encoding="utf-8")
            (root / "README.md").write_text("public docs only\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, "scripts/pii_scan.py", str(root)],
                cwd=Path(__file__).resolve().parent.parent,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("No obvious private data patterns found.", result.stdout)

    def test_release_checks_skip_local_developer_config(self) -> None:
        self.assertEqual(pii_scan.SKIP_DIRS, release_policy.SKIP_DIRS)
        self.assertEqual(check_release.SKIP_DIRS, release_policy.SKIP_DIRS)
        for dirname in release_policy.LOCAL_DEVELOPER_CONFIG_DIRS:
            self.assertIn(dirname, release_policy.SKIP_DIRS)
        for filename in release_policy.LOCAL_DEVELOPER_CONFIG_FILES:
            self.assertTrue(release_policy.is_skipped_path(Path(filename)))
        self.assertTrue(pii_scan.should_scan(Path("docs") / "example.md"))

    def test_gitignore_covers_local_developer_config(self) -> None:
        root = Path(__file__).resolve().parent.parent
        gitignore = (root / ".gitignore").read_text(encoding="utf-8").splitlines()
        for dirname in release_policy.LOCAL_DEVELOPER_CONFIG_DIRS:
            self.assertIn(f"/{dirname}/", gitignore)
        for filename in release_policy.LOCAL_DEVELOPER_CONFIG_FILES:
            self.assertIn(f"/{filename}", gitignore)

    def test_untracked_local_developer_config_is_not_release_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            private_path = "/" + "Users" + "/example/private"
            for dirname in release_policy.LOCAL_DEVELOPER_CONFIG_DIRS:
                local_config = root / dirname / "settings.json"
                local_config.parent.mkdir()
                local_config.write_text(f'{{"path": "{private_path}"}}', encoding="utf-8")
            for filename in release_policy.LOCAL_DEVELOPER_CONFIG_FILES:
                (root / filename).write_text(f"local path: {private_path}\n", encoding="utf-8")
            (root / "README.md").write_text("public docs only\n", encoding="utf-8")

            files = {path.relative_to(root) for path in release_policy.iter_release_files(root)}

            self.assertEqual(files, {Path("README.md")})

    def test_forbidden_file_check_skips_local_developer_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for dirname in release_policy.LOCAL_DEVELOPER_CONFIG_DIRS:
                local_file = root / dirname / "local-screenshot.png"
                local_file.parent.mkdir()
                local_file.write_bytes(b"local artifact only")

            old_root = check_release.ROOT
            try:
                check_release.ROOT = root
                check_release.check_forbidden_files()
            finally:
                check_release.ROOT = old_root

    def test_release_files_use_git_tracked_files_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            tracked = root / "README.md"
            tracked.write_text("public docs only\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            (root / ".codex").mkdir()
            (root / ".codex" / "settings.json").write_text(
                '{"path": "/' + 'Users/example/private"}\n',
                encoding="utf-8",
            )
            (root / ".env").write_text(
                "TOKEN=" + "sk-" + "localdeveloperartifact000000\n",
                encoding="utf-8",
            )
            (root / "local-screenshot.png").write_bytes(b"local artifact only")

            files = {path.relative_to(root) for path in release_policy.iter_release_files(root)}

            self.assertEqual(files, {Path("README.md")})

    def test_tracked_local_developer_config_is_still_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            local_config = root / ".codex" / "settings.json"
            local_config.parent.mkdir()
            local_config.write_text(
                '{"path": "/' + 'Users/example/private"}\n',
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "-f", ".codex/settings.json"], cwd=root, check=True)

            files = {path.relative_to(root) for path in release_policy.iter_release_files(root)}
            result = subprocess.run(
                [sys.executable, "scripts/pii_scan.py", str(root)],
                cwd=Path(__file__).resolve().parent.parent,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(files, {Path(".codex/settings.json")})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Potential private data found:", result.stderr)

    def test_tracked_private_text_is_still_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            tracked = root / "README.md"
            tracked.write_text("contact: " + "real" + "@example.com\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)

            findings = pii_scan.scan_file(tracked)

            self.assertTrue(findings)


if __name__ == "__main__":
    unittest.main()
