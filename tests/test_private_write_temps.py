from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from agent_personal_vault.audit import audit_path
from agent_personal_vault.consent import consent_path
from agent_personal_vault.privacy import DISPOSE_CONFIRMATION, dispose_private_state
from agent_personal_vault.private_io import write_private_bytes
from agent_personal_vault.vault import blank_store, load_store, read_store, write_json_private


def write_temp(target: Path, identifier: str, *, old: bool = False) -> Path:
    path = target.with_name(f".{target.name}.{identifier * 24}.tmp")
    path.write_bytes(b"fixture")
    path.chmod(0o600)
    if old:
        timestamp = time.time() - 2 * 24 * 60 * 60
        os.utime(path, (timestamp, timestamp))
    return path


class PrivateWriteTempsTests(unittest.TestCase):
    def test_open_removes_only_stale_private_write_temps(self) -> None:
        for reader in (read_store, load_store):
            with self.subTest(reader=reader.__name__), tempfile.TemporaryDirectory() as tmp:
                vault = Path(tmp) / "vault.json"
                write_json_private(vault, blank_store())
                before = vault.read_bytes()
                targets = (vault, consent_path(vault), audit_path(vault))
                stale = [write_temp(target, "a", old=True) for target in targets]
                fresh = write_temp(vault, "b")
                unrelated = write_temp(vault.with_name("unrelated.json"), "a", old=True)
                invalid_name = write_temp(vault, "x", old=True)
                shared_mode = write_temp(vault, "c", old=True)
                shared_mode.chmod(0o644)
                linked = write_temp(vault, "d", old=True)
                alias = linked.with_name("kept-link")
                os.link(linked, alias)
                symlink = write_temp(vault, "e", old=True)
                symlink.unlink()
                symlink.symlink_to(unrelated)
                directory = write_temp(vault, "f", old=True)
                directory.unlink()
                directory.mkdir()

                reader(path=vault)
                self.assertEqual(vault.read_bytes(), before)
                self.assertTrue(all(path.exists() for path in (fresh, unrelated, invalid_name, shared_mode, linked, alias)))
                self.assertTrue(symlink.is_symlink())
                self.assertTrue(directory.is_dir())
                self.assertEqual([path.exists() for path in stale], [False, False, False])

    def test_dispose_removes_private_write_temps_without_primary_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault.json"
            targets = (vault, consent_path(vault), audit_path(vault))
            temps = [write_temp(target, "a") for target in targets]
            unrelated = write_temp(vault.with_name("unrelated.json"), "a", old=True)

            result = dispose_private_state(vault, confirmation=DISPOSE_CONFIRMATION)

            self.assertEqual(result, {"vault_removed": False, "consent_removed": False, "audit_removed": False})
            self.assertTrue(unrelated.exists())
            self.assertEqual([path.exists() for path in temps], [False, False, False])

    def test_interrupted_private_write_cleans_up_its_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault.json"
            write_private_bytes(vault, b"original")

            with mock.patch("agent_personal_vault.private_io.os.fsync", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    write_private_bytes(vault, b"replacement")

            self.assertEqual(vault.read_bytes(), b"original")
            self.assertEqual([path.name for path in vault.parent.iterdir()], [vault.name])
