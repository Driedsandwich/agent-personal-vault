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
            for dirname in release_policy.LOCAL_AGENT_CONFIG_DIRS:
                local_config = root / dirname / "settings.json"
                local_config.parent.mkdir()
                local_config.write_text(f'{{"path": "{private_path}"}}', encoding="utf-8")
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

    def test_release_checks_skip_local_codex_config(self) -> None:
        self.assertEqual(pii_scan.SKIP_DIRS, release_policy.SKIP_DIRS)
        self.assertEqual(check_release.SKIP_DIRS, release_policy.SKIP_DIRS)
        self.assertIn(".codex", release_policy.SKIP_DIRS)
        self.assertIn(".claude", release_policy.SKIP_DIRS)
        self.assertIn(".cursor", release_policy.SKIP_DIRS)
        self.assertFalse(pii_scan.should_scan(Path(".codex") / "hooks.json"))
        self.assertFalse(pii_scan.should_scan(Path(".claude") / "settings.json"))
        self.assertFalse(pii_scan.should_scan(Path(".cursor") / "mcp.json"))
        self.assertTrue(pii_scan.should_scan(Path("docs") / "example.md"))


if __name__ == "__main__":
    unittest.main()
