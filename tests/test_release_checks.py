from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import check_release, pii_scan


class ReleaseCheckTests(unittest.TestCase):
    def test_pii_scan_skips_local_codex_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local_config = root / ".codex" / "hooks.json"
            local_config.parent.mkdir()
            private_path = "/" + "Users" + "/example/private"
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
        self.assertIn(".codex", pii_scan.SKIP_DIRS)
        self.assertIn(".codex", check_release.SKIP_DIRS)
        self.assertFalse(pii_scan.should_scan(Path(".codex") / "hooks.json"))
        self.assertTrue(pii_scan.should_scan(Path("docs") / "example.md"))


if __name__ == "__main__":
    unittest.main()
