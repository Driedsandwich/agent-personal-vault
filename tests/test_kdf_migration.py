from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_personal_vault import crypto_store, kdf_migration, private_io
from agent_personal_vault.audit import audit_path, write_audit_event
from agent_personal_vault.consent import consent_path, issue_consent
from agent_personal_vault.crypto_store import (
    ARGON2ID_V2_PROFILE,
    LEGACY_V1_PROFILE,
    DecryptionError,
    cryptography_available,
    decrypt_store_payload,
    encryption_profile,
    encrypt_store_payload,
)
from agent_personal_vault.kdf_migration import (
    migration_status,
    prepare_kdf_migration,
    resume_kdf_migration,
    rollback_kdf_migration,
    upgrade_kdf,
)
from agent_personal_vault.migration_guard import KDFMigrationIncompleteError, migration_journal_path
from agent_personal_vault.resource_limits import MAX_AUDIT_BYTES, ResourceLimitError
from agent_personal_vault.gui import save_profile_fields
from agent_personal_vault.mcp_server import tool_definitions
from agent_personal_vault.private_io import private_file_exists, read_private_bytes, read_private_json, write_private_bytes
from agent_personal_vault.sidecar_store import (
    commit_prepared_sidecar,
    prepare_sidecar_write,
    read_sidecar_bytes,
    read_sidecar_json,
)
from agent_personal_vault.vault import blank_store, load_store, write_store


@unittest.skipUnless(cryptography_available(), "cryptography with Argon2id is not installed")
class KDFMigrationTests(unittest.TestCase):
    passphrase = "correct horse battery staple"

    def create_v1_vault(self, root: Path, *, with_sidecars: bool = True) -> Path:
        path = root / "vault.json"
        store = blank_store()
        store["fields"]["FAMILY_NAME"] = "Synthetic"
        write_store(store, path, passphrase=self.passphrase, encrypted=True, profile=LEGACY_V1_PROFILE)
        if with_sidecars:
            with mock.patch.dict(os.environ, {"AGENT_PERSONAL_VAULT_PASSPHRASE": self.passphrase}):
                write_audit_event(vault_path=path, actor="test", action="fixture", purpose="test_dummy")
                issue_consent(
                    vault_path=path,
                    action="get",
                    key="FAMILY_NAME",
                    purpose="test_dummy",
                    actor="test",
                    source="direct_grant",
                    human_operated=False,
                )
        return path

    def member_bytes(self, path: Path) -> dict[str, bytes]:
        result = {"vault": read_private_bytes(path)}
        for name, sidecar_path in (("consent", consent_path(path)), ("audit", audit_path(path))):
            if private_file_exists(sidecar_path):
                result[name] = read_private_bytes(sidecar_path)
        return result

    def assert_profile(self, path: Path, profile) -> None:
        self.assertEqual(encryption_profile(read_private_json(path)), profile)
        for kind, sidecar_path in (("consent", consent_path(path)), ("audit", audit_path(path))):
            if private_file_exists(sidecar_path):
                self.assertEqual(encryption_profile(read_private_json(sidecar_path), sidecar=True), profile, kind)

    def test_new_encryption_uses_argon2id_v2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = blank_store()
            write_store(store, path, passphrase=self.passphrase, encrypted=True)
            payload = read_private_json(path)
            self.assertEqual(encryption_profile(payload), ARGON2ID_V2_PROFILE)
            self.assertEqual(payload["memory_kib"], 19 * 1024)
            self.assertEqual(payload["iterations"], 2)
            self.assertEqual(payload["parallelism"], 1)

    def test_legacy_v1_read_and_ordinary_write_preserve_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp))
            loaded = load_store(path=path, passphrase=self.passphrase)
            loaded["fields"]["GIVEN_NAME"] = "Control"
            write_store(loaded, path, passphrase=self.passphrase)
            write_audit_event(
                vault_path=path,
                actor="test",
                action="control",
                purpose="test_dummy",
                sidecar_passphrase=self.passphrase,
            )
            self.assert_profile(path, LEGACY_V1_PROFILE)
            self.assertEqual(load_store(path=path, passphrase=self.passphrase)["fields"]["GIVEN_NAME"], "Control")

    def test_v2_parameter_abuse_is_rejected_before_crypto_work(self) -> None:
        payload = encrypt_store_payload(blank_store(), self.passphrase)
        variants = [
            {**payload, "iterations": True},
            {**payload, "iterations": 3},
            {**payload, "memory_kib": True},
            {**payload, "memory_kib": 2**31},
            {**payload, "parallelism": -1},
            {**payload, "parallelism": 2},
            {**payload, "unexpected": "field"},
        ]
        with mock.patch.object(crypto_store, "_require_crypto") as require_crypto:
            for variant in variants:
                with self.subTest(variant=variant):
                    with self.assertRaisesRegex(DecryptionError, "unsupported encrypted store format"):
                        decrypt_store_payload(variant, self.passphrase)
            require_crypto.assert_not_called()

    def test_explicit_upgrade_round_trips_vault_and_both_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp))
            before_store = load_store(path=path, passphrase=self.passphrase)
            before_consent = read_sidecar_json(
                consent_path(path), vault_path=path, kind="consent", passphrase=self.passphrase
            )
            result = upgrade_kdf(path, self.passphrase)
            self.assertEqual(result["state"], "completed")
            self.assertEqual(result["members"], ["audit", "consent", "vault"])
            self.assert_profile(path, ARGON2ID_V2_PROFILE)
            self.assertEqual(load_store(path=path, passphrase=self.passphrase), before_store)
            self.assertEqual(
                read_sidecar_json(consent_path(path), vault_path=path, kind="consent", passphrase=self.passphrase),
                before_consent,
            )
            self.assertFalse(migration_status(path)["incomplete"])
            self.assertFalse(private_file_exists(migration_journal_path(path)))

    def test_wrong_passphrase_and_malformed_sidecar_leave_all_members_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp))
            before = self.member_bytes(path)
            with self.assertRaises(DecryptionError):
                prepare_kdf_migration(path, "wrong synthetic passphrase")
            self.assertEqual(self.member_bytes(path), before)
            self.assertFalse(private_file_exists(migration_journal_path(path)))

            write_private_bytes(consent_path(path), b'{"version":2,"grants":[')
            malformed = self.member_bytes(path)
            with self.assertRaises((ValueError, json.JSONDecodeError)):
                prepare_kdf_migration(path, self.passphrase)
            self.assertEqual(self.member_bytes(path), malformed)
            self.assertFalse(private_file_exists(migration_journal_path(path)))

    def test_oversize_sidecar_leaves_all_members_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp))
            write_private_bytes(audit_path(path), b"x" * (MAX_AUDIT_BYTES + 1))
            before = self.member_bytes(path)
            with self.assertRaises(ResourceLimitError):
                prepare_kdf_migration(path, self.passphrase)
            self.assertEqual(self.member_bytes(path), before)
            self.assertFalse(private_file_exists(migration_journal_path(path)))

    def test_incomplete_migration_blocks_normal_vault_and_sidecar_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp))
            prepare_kdf_migration(path, self.passphrase)
            store = load_store(path=path, passphrase=self.passphrase)
            with self.assertRaises(KDFMigrationIncompleteError):
                write_store(store, path, passphrase=self.passphrase)
            with self.assertRaises(KDFMigrationIncompleteError):
                write_audit_event(
                    vault_path=path,
                    actor="test",
                    action="blocked",
                    purpose="test_dummy",
                    sidecar_passphrase=self.passphrase,
                )
            rollback_kdf_migration(path, self.passphrase)

    def test_prepared_v1_sidecar_cannot_commit_after_vault_moves_to_v2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp), with_sidecars=False)
            prepared = prepare_sidecar_write(
                audit_path(path),
                b'{"action":"synthetic"}\n',
                vault_path=path,
                kind="audit",
                encrypted=True,
                passphrase=self.passphrase,
            )
            self.assertEqual(prepared.expected_profile, LEGACY_V1_PROFILE)
            self.assertEqual(upgrade_kdf(path, self.passphrase)["state"], "completed")
            with self.assertRaisesRegex(ValueError, "profile changed"):
                commit_prepared_sidecar(prepared)
            self.assertFalse(private_file_exists(audit_path(path)))

    def test_failure_after_first_replace_can_resume_without_reapplying_unknown_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp))
            prepare_kdf_migration(path, self.passphrase)
            real_write = kdf_migration.write_private_bytes
            raised = False

            def fail_after_vault_replace(target: Path, payload: bytes) -> None:
                nonlocal raised
                real_write(target, payload)
                if target == path and not raised:
                    raised = True
                    raise OSError("synthetic post-replace failure")

            with mock.patch.object(kdf_migration, "write_private_bytes", side_effect=fail_after_vault_replace):
                with self.assertRaisesRegex(OSError, "synthetic post-replace failure"):
                    resume_kdf_migration(path, self.passphrase)
            self.assertTrue(migration_status(path)["incomplete"])
            result = resume_kdf_migration(path, self.passphrase)
            self.assertEqual(result["state"], "completed")
            self.assert_profile(path, ARGON2ID_V2_PROFILE)

    def test_preparing_journal_can_resume_after_staging_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp))
            original = self.member_bytes(path)
            real_write = kdf_migration.write_private_bytes

            def fail_first_next_file(target: Path, payload: bytes) -> None:
                if target.name.endswith(".next"):
                    raise OSError("synthetic staging failure")
                real_write(target, payload)

            with mock.patch.object(kdf_migration, "write_private_bytes", side_effect=fail_first_next_file):
                with self.assertRaisesRegex(OSError, "synthetic staging failure"):
                    prepare_kdf_migration(path, self.passphrase)
            self.assertEqual(self.member_bytes(path), original)
            self.assertEqual(migration_status(path)["state"], "preparing")
            self.assertEqual(resume_kdf_migration(path, self.passphrase)["state"], "completed")
            self.assert_profile(path, ARGON2ID_V2_PROFILE)

    def test_failure_after_first_replace_can_rollback_all_members(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp))
            original = self.member_bytes(path)
            prepare_kdf_migration(path, self.passphrase)
            real_write = kdf_migration.write_private_bytes

            def fail_on_consent(target: Path, payload: bytes) -> None:
                if target == consent_path(path):
                    raise OSError("synthetic consent replace failure")
                real_write(target, payload)

            with mock.patch.object(kdf_migration, "write_private_bytes", side_effect=fail_on_consent):
                with self.assertRaisesRegex(OSError, "synthetic consent replace failure"):
                    resume_kdf_migration(path, self.passphrase)
            result = rollback_kdf_migration(path, self.passphrase)
            self.assertEqual(result["state"], "rolled_back")
            self.assertEqual(self.member_bytes(path), original)
            self.assert_profile(path, LEGACY_V1_PROFILE)

    def test_fsync_failure_is_recoverable_by_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp))
            original = self.member_bytes(path)
            prepare_kdf_migration(path, self.passphrase)
            with mock.patch.object(private_io.os, "fsync", side_effect=OSError("synthetic fsync failure")):
                with self.assertRaisesRegex(OSError, "synthetic fsync failure"):
                    resume_kdf_migration(path, self.passphrase)
            self.assertTrue(migration_status(path)["incomplete"])
            self.assertEqual(rollback_kdf_migration(path, self.passphrase)["state"], "rolled_back")
            self.assertEqual(self.member_bytes(path), original)

    def test_replace_failure_is_recoverable_by_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp))
            prepare_kdf_migration(path, self.passphrase)
            with mock.patch.object(private_io.os, "replace", side_effect=OSError("synthetic replace failure")):
                with self.assertRaisesRegex(OSError, "synthetic replace failure"):
                    resume_kdf_migration(path, self.passphrase)
            self.assertTrue(migration_status(path)["incomplete"])
            self.assertEqual(resume_kdf_migration(path, self.passphrase)["state"], "completed")
            self.assert_profile(path, ARGON2ID_V2_PROFILE)

    def test_resume_rollback_and_upgrade_retries_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp))
            original = self.member_bytes(path)
            self.assertEqual(rollback_kdf_migration(path, self.passphrase)["state"], "already_rolled_back")
            self.assertEqual(self.member_bytes(path), original)

            self.assertEqual(upgrade_kdf(path, self.passphrase)["state"], "completed")
            migrated = self.member_bytes(path)
            self.assertEqual(resume_kdf_migration(path, self.passphrase)["state"], "already_completed")
            self.assertEqual(upgrade_kdf(path, self.passphrase)["state"], "already_current")
            self.assertEqual(self.member_bytes(path), migrated)

    def test_gui_write_preserves_v1_and_mcp_does_not_expose_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp))
            store = load_store(path=path, passphrase=self.passphrase)
            with mock.patch.dict(os.environ, {"AGENT_PERSONAL_VAULT_PASSPHRASE": self.passphrase}):
                save_profile_fields(
                    path,
                    store["schema"],
                    {"GIVEN_NAME": "GUI Control"},
                    expected_revision=store["revision"],
                )
            self.assert_profile(path, LEGACY_V1_PROFILE)
            tool_names = {tool["name"] for tool in tool_definitions()}
            self.assertFalse(any("encrypt" in name or "migrat" in name or "kdf" in name for name in tool_names))

    def test_cli_is_only_public_migration_boundary_and_errors_are_path_free(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.create_v1_vault(Path(tmp), with_sidecars=False)
            env = os.environ.copy()
            env["AGENT_PERSONAL_VAULT_PASSPHRASE"] = self.passphrase
            raw_purpose = "synthetic@example.test /home/synthetic/private"
            wrong_env = {**env, "AGENT_PERSONAL_VAULT_PASSPHRASE": "wrong synthetic passphrase"}
            rejected = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "encryption",
                    "upgrade-kdf",
                    "--purpose",
                    raw_purpose,
                ],
                env=wrong_env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(rejected.returncode, 0)
            rejected_output = rejected.stdout + rejected.stderr
            self.assertNotIn(wrong_env["AGENT_PERSONAL_VAULT_PASSPHRASE"], rejected_output)
            self.assertNotIn(str(path), rejected_output)
            self.assertNotIn(raw_purpose, rejected_output)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "encryption",
                    "upgrade-kdf",
                    "--purpose",
                    raw_purpose,
                ],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(self.passphrase, result.stdout + result.stderr)
            self.assertNotIn(str(path), result.stdout + result.stderr)
            self.assertNotIn(raw_purpose, result.stdout + result.stderr)
            self.assertEqual(encryption_profile(read_private_json(path)), ARGON2ID_V2_PROFILE)
            audit_plaintext = read_sidecar_bytes(
                audit_path(path),
                vault_path=path,
                kind="audit",
                passphrase=self.passphrase,
            ).decode("utf-8")
            self.assertNotIn(raw_purpose, audit_plaintext)
            self.assertIn('"purpose": "[redacted]"', audit_plaintext)


if __name__ == "__main__":
    unittest.main()
