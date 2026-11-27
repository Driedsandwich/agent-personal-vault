from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_personal_vault.audit import (
    commit_audit_sidecar_migration,
    prepare_audit_sidecar_migration,
    read_audit_events,
    write_audit_event,
)
from agent_personal_vault.consent import (
    commit_consent_sidecar_migration,
    issue_consent,
    list_consents,
    prepare_consent_sidecar_migration,
    validate_and_consume_consent,
)
from agent_personal_vault.private_io import remove_private_file, write_private_bytes
from agent_personal_vault.sidecar_store import commit_prepared_sidecar, prepare_sidecar_write
from agent_personal_vault.vault import load_store


class SidecarMigrationTests(unittest.TestCase):
    def test_consent_sidecar_migration_preserves_consumption_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            load_store(create=True, path=path)
            scope = {"vault_path": path, "action": "get", "key": "EMAIL", "purpose": "test_dummy", "actor": "test"}
            grant = issue_consent(**scope)
            options = {"encrypted": False, "passphrase": "test passphrase"}
            self.assertTrue(commit_consent_sidecar_migration(prepare_consent_sidecar_migration(path, **options)))
            prepared = prepare_consent_sidecar_migration(path, **options)

            used = validate_and_consume_consent(consent_id=grant["id"], **scope)
            with self.assertRaisesRegex(ValueError, "sidecar changed; reload and retry"):
                commit_consent_sidecar_migration(prepared)
            self.assertTrue(used["used_at"])
            self.assertEqual(list_consents(path, include_used=True)[0]["used_at"], used["used_at"])

    def test_audit_sidecar_migration_preserves_new_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            load_store(create=True, path=path)
            event = {"vault_path": path, "actor": "test", "purpose": "test_dummy"}
            write_audit_event(action="check", **event)
            options = {"encrypted": False, "passphrase": "test passphrase"}
            prepared = prepare_audit_sidecar_migration(path, **options)
            self.assertTrue(commit_audit_sidecar_migration(prepared, vault_path=path))
            prepared = prepare_audit_sidecar_migration(path, **options)

            write_audit_event(action="list", **event)
            with self.assertRaisesRegex(ValueError, "sidecar changed; reload and retry"):
                commit_audit_sidecar_migration(prepared, vault_path=path)
            self.assertEqual([row["action"] for row in read_audit_events(path, limit=10)], ["check", "list"])

    def test_prepared_sidecar_write_checks_source_presence(self) -> None:
        for source_exists in (False, True):
            with self.subTest(source_exists=source_exists), tempfile.TemporaryDirectory() as tmp:
                vault_path = Path(tmp) / "vault.json"
                path = Path(tmp) / "audit.jsonl"
                if source_exists:
                    write_private_bytes(path, b"")
                prepared = prepare_sidecar_write(
                    path, b"{}\n", vault_path=vault_path, kind="audit", encrypted=False, passphrase=None
                )
                if source_exists:
                    remove_private_file(path)
                else:
                    write_private_bytes(path, b"")

                with self.assertRaisesRegex(ValueError, "sidecar changed; reload and retry"):
                    commit_prepared_sidecar(prepared)
                if source_exists:
                    self.assertFalse(path.exists())
                else:
                    self.assertEqual(path.read_bytes(), b"")
