"""Explicit retention and complete local-state disposal operations."""

from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path

from .audit import audit_lock_path, audit_path, prune_audit_events
from .consent import consent_path, prune_consent_records
from .migration_guard import kdf_write_guard, migration_incomplete
from .private_io import exclusive_private_lock, private_file_stat, remove_private_file


DISPOSE_CONFIRMATION = "delete local vault state"


def prune_private_metadata(
    vault_path: Path,
    *,
    consent_retention_days: int = 30,
    audit_retention_days: int = 90,
) -> dict[str, int]:
    if type(consent_retention_days) is not int or consent_retention_days < 1:
        raise ValueError("consent retention days must be a positive integer")
    if type(audit_retention_days) is not int or audit_retention_days < 1:
        raise ValueError("audit retention days must be a positive integer")
    consent_result = prune_consent_records(vault_path, retention_days=consent_retention_days)
    audit_result = prune_audit_events(vault_path, retention_days=audit_retention_days)
    return {
        **consent_result,
        "audit_removed": audit_result["removed"],
        "audit_retained": audit_result["retained"],
        "audit_malformed_retained": audit_result["malformed_retained"],
    }


def dispose_private_state(vault_path: Path, *, confirmation: str) -> dict[str, bool]:
    """Remove the known vault data files while preserving the parent and unrelated files."""

    if confirmation != DISPOSE_CONFIRMATION:
        raise ValueError("private state disposal requires the exact confirmation phrase")
    consent_state_path = consent_path(vault_path)
    data_paths = [vault_path, consent_state_path, audit_path(vault_path)]
    if not migration_incomplete(vault_path) and not any(
        private_file_stat(data_path) is not None for data_path in data_paths
    ):
        return {"vault_removed": False, "consent_removed": False, "audit_removed": False}
    with kdf_write_guard(vault_path):
        lock_paths = [
            vault_path.with_suffix(vault_path.suffix + ".lock"),
            consent_state_path.with_suffix(consent_state_path.suffix + ".lock"),
            audit_lock_path(vault_path),
        ]
        with ExitStack() as stack:
            for lock_path in lock_paths:
                stack.enter_context(exclusive_private_lock(lock_path))
            for data_path in data_paths:
                private_file_stat(data_path)
            return {
                "vault_removed": remove_private_file(vault_path),
                "consent_removed": remove_private_file(consent_state_path),
                "audit_removed": remove_private_file(audit_path(vault_path)),
            }
