from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path

from agent_personal_vault.vault import store_path_warnings


@unittest.skipUnless(os.name == "posix", "POSIX directory permissions are required")
class StoreAncestorWarningTests(unittest.TestCase):
    def test_warns_when_an_ancestor_is_writable_by_others_without_sticky_bit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shared = Path(tmp) / "shared"
            shared.mkdir()
            shared.chmod(0o777)
            vault_dir = shared / "vault"
            vault_dir.mkdir(mode=0o700)
            warnings = store_path_warnings(vault_dir / "vault.json")
            self.assertTrue(any("ancestor directory" in warning for warning in warnings), warnings)
            self.assertFalse(any(tmp in warning for warning in warnings), "warnings must not echo local paths")

    def test_sticky_or_private_ancestors_do_not_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sticky = Path(tmp) / "sticky"
            sticky.mkdir()
            sticky.chmod(0o777 | stat.S_ISVTX)
            private = Path(tmp) / "private"
            private.mkdir(mode=0o700)
            for parent in (sticky, private):
                with self.subTest(parent=parent.name):
                    vault_dir = parent / "vault"
                    vault_dir.mkdir(mode=0o700)
                    warnings = store_path_warnings(vault_dir / "vault.json")
                    self.assertFalse(any("ancestor directory" in warning for warning in warnings), warnings)


if __name__ == "__main__":
    unittest.main()
