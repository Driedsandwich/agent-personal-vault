"""Crash-recoverable, explicit migration between allowlisted encryption profiles."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .audit import audit_path, prepare_audit_sidecar_migration
from .consent import consent_path, prepare_consent_sidecar_migration
from .crypto_store import (
    ARGON2ID_V2_PROFILE,
    LEGACY_V1_PROFILE,
    EncryptionProfile,
    decrypt_sidecar_payload,
    decrypt_store_payload,
    encryption_profile,
    encrypt_store_payload,
    is_encrypted_payload,
)
from .migration_guard import kdf_write_guard, migration_incomplete, migration_journal_path
from .private_io import (
    private_file_exists,
    read_private_bytes,
    read_private_json,
    remove_private_file,
    write_private_bytes,
    write_private_json,
)
from .sidecar_store import PreparedSidecarWrite
from .vault import validate_store_shape


JOURNAL_SCHEMA = "apv-kdf-migration/v1"
MEMBER_NAMES = ("vault", "consent", "audit")
HASH_PATTERN = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class MigrationMember:
    name: str
    path: Path
    backup_path: Path
    next_path: Path


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _encoded_json(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _members(vault_path: Path) -> dict[str, MigrationMember]:
    paths = {
        "vault": vault_path,
        "consent": consent_path(vault_path),
        "audit": audit_path(vault_path),
    }
    return {
        name: MigrationMember(
            name=name,
            path=path,
            backup_path=vault_path.parent / f".{vault_path.name}.kdf-migration.{name}.bak",
            next_path=vault_path.parent / f".{vault_path.name}.kdf-migration.{name}.next",
        )
        for name, path in paths.items()
    }


def _read_present_originals(vault_path: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for name, member in _members(vault_path).items():
        if name == "vault" or private_file_exists(member.path):
            result[name] = read_private_bytes(member.path)
    return result


def _prepared_payload(prepared: PreparedSidecarWrite | None) -> bytes | None:
    return None if prepared is None else prepared.payload


def _prepare_targets(vault_path: Path, passphrase: str) -> tuple[dict[str, bytes], dict[str, bytes]]:
    originals = _read_present_originals(vault_path)
    vault_payload = json.loads(originals["vault"].decode("utf-8"))
    if not is_encrypted_payload(vault_payload):
        raise ValueError("KDF migration requires an encrypted vault")
    if encryption_profile(vault_payload) != LEGACY_V1_PROFILE:
        raise ValueError("vault KDF is already current or unsupported")
    store = validate_store_shape(decrypt_store_payload(vault_payload, passphrase))
    targets = {
        "vault": _encoded_json(
            encrypt_store_payload(
                store,
                passphrase,
                allow_weak_passphrase=True,
                profile=ARGON2ID_V2_PROFILE,
            )
        )
    }
    prepared_consent = prepare_consent_sidecar_migration(
        vault_path,
        encrypted=True,
        passphrase=passphrase,
        profile=ARGON2ID_V2_PROFILE,
    )
    prepared_audit = prepare_audit_sidecar_migration(
        vault_path,
        encrypted=True,
        passphrase=passphrase,
        profile=ARGON2ID_V2_PROFILE,
    )
    for name, prepared in (("consent", prepared_consent), ("audit", prepared_audit)):
        payload = _prepared_payload(prepared)
        if payload is not None:
            targets[name] = payload
    if set(targets) != set(originals):
        raise ValueError("migration member set changed; retry")
    _verify_target_round_trips(targets, passphrase, expected_store=store)
    return originals, targets


def _verify_target_round_trips(targets: dict[str, bytes], passphrase: str, *, expected_store: dict | None = None) -> None:
    vault_payload = json.loads(targets["vault"].decode("utf-8"))
    store = validate_store_shape(decrypt_store_payload(vault_payload, passphrase))
    if expected_store is not None and store != expected_store:
        raise ValueError("migrated vault round-trip mismatch")
    for kind in ("consent", "audit"):
        if kind not in targets:
            continue
        envelope = json.loads(targets[kind].decode("utf-8"))
        plaintext = decrypt_sidecar_payload(envelope, passphrase, kind=kind)
        if kind == "consent":
            state = json.loads(plaintext.decode("utf-8"))
            if not isinstance(state, dict) or not isinstance(state.get("grants"), list) or not isinstance(
                state.get("requests"), list
            ):
                raise ValueError("migrated consent state is invalid")
        else:
            for line in plaintext.splitlines():
                if line.strip() and not isinstance(json.loads(line.decode("utf-8")), dict):
                    raise ValueError("migrated audit state is invalid")


def _initial_journal(originals: dict[str, bytes]) -> dict[str, Any]:
    return {
        "schema": JOURNAL_SCHEMA,
        "state": "preparing",
        "source_profile": LEGACY_V1_PROFILE.name,
        "target_profile": ARGON2ID_V2_PROFILE.name,
        "members": {
            name: {"original_sha256": _sha256(payload), "original_size": len(payload)}
            for name, payload in sorted(originals.items())
        },
        "applied": [],
    }


def _validate_journal(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {
        "schema",
        "state",
        "source_profile",
        "target_profile",
        "members",
        "applied",
    }:
        raise ValueError("KDF migration journal is invalid")
    if (
        payload.get("schema") != JOURNAL_SCHEMA
        or payload.get("state") not in {"preparing", "ready"}
        or payload.get("source_profile") != LEGACY_V1_PROFILE.name
        or payload.get("target_profile") != ARGON2ID_V2_PROFILE.name
    ):
        raise ValueError("KDF migration journal is invalid")
    members = payload.get("members")
    applied = payload.get("applied")
    if not isinstance(members, dict) or not set(members).issubset(MEMBER_NAMES) or "vault" not in members:
        raise ValueError("KDF migration journal is invalid")
    if not isinstance(applied, list) or len(applied) != len(set(applied)) or not set(applied).issubset(members):
        raise ValueError("KDF migration journal is invalid")
    for record in members.values():
        required = {"original_sha256", "original_size"}
        if payload["state"] == "ready":
            required.update({"target_sha256", "target_size"})
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError("KDF migration journal is invalid")
        for key in ("original_sha256", "target_sha256"):
            if key in record and (not isinstance(record[key], str) or HASH_PATTERN.fullmatch(record[key]) is None):
                raise ValueError("KDF migration journal is invalid")
        for key in ("original_size", "target_size"):
            if key in record and (type(record[key]) is not int or record[key] < 1):
                raise ValueError("KDF migration journal is invalid")
    return payload


def _load_journal(vault_path: Path) -> dict[str, Any]:
    if not migration_incomplete(vault_path):
        raise ValueError("no incomplete KDF migration exists")
    return _validate_journal(read_private_json(migration_journal_path(vault_path)))


def _matches(path: Path, expected: str) -> bool:
    return private_file_exists(path) and _sha256(read_private_bytes(path)) == expected


def _write_staging(vault_path: Path, originals: dict[str, bytes], targets: dict[str, bytes], journal: dict[str, Any]) -> dict:
    members = _members(vault_path)
    for name in originals:
        write_private_bytes(members[name].backup_path, originals[name])
        write_private_bytes(members[name].next_path, targets[name])
    ready = dict(journal)
    ready["state"] = "ready"
    ready["members"] = {
        name: {
            **journal["members"][name],
            "target_sha256": _sha256(targets[name]),
            "target_size": len(targets[name]),
        }
        for name in originals
    }
    write_private_json(migration_journal_path(vault_path), ready)
    return ready


def prepare_kdf_migration(vault_path: Path, passphrase: str) -> dict[str, Any]:
    with kdf_write_guard(vault_path):
        originals, targets = _prepare_targets(vault_path, passphrase)
        journal = _initial_journal(originals)
        write_private_json(migration_journal_path(vault_path), journal)
        ready = _write_staging(vault_path, originals, targets, journal)
        return {"state": ready["state"], "members": sorted(ready["members"]), "target_profile": ready["target_profile"]}


def _recover_preparing(vault_path: Path, passphrase: str, journal: dict[str, Any]) -> dict[str, Any]:
    current = _read_present_originals(vault_path)
    if set(current) != set(journal["members"]):
        raise ValueError("migration member set changed; rollback required")
    for name, payload in current.items():
        if _sha256(payload) != journal["members"][name]["original_sha256"]:
            raise ValueError("migration source changed; rollback required")
    originals, targets = _prepare_targets(vault_path, passphrase)
    return _write_staging(vault_path, originals, targets, journal)


def _cleanup(vault_path: Path, member_names: set[str]) -> None:
    members = _members(vault_path)
    for name in member_names:
        remove_private_file(members[name].next_path)
    for name in member_names:
        remove_private_file(members[name].backup_path)
    remove_private_file(migration_journal_path(vault_path))


def _validate_completed_profile(
    vault_path: Path,
    passphrase: str,
    expected_profile: EncryptionProfile,
) -> list[str]:
    """Validate a completed state before treating a repeated command as idempotent."""

    payloads = _read_present_originals(vault_path)
    for name, payload in payloads.items():
        envelope = json.loads(payload.decode("utf-8"))
        profile = encryption_profile(envelope, sidecar=name != "vault")
        if profile != expected_profile:
            raise ValueError("vault and metadata encryption profiles do not match")
    _verify_target_round_trips(payloads, passphrase)
    return sorted(payloads)


def resume_kdf_migration(vault_path: Path, passphrase: str) -> dict[str, Any]:
    with kdf_write_guard(vault_path, allow_incomplete=True):
        if not migration_incomplete(vault_path):
            names = _validate_completed_profile(vault_path, passphrase, ARGON2ID_V2_PROFILE)
            return {"state": "already_completed", "members": names, "target_profile": ARGON2ID_V2_PROFILE.name}
        journal = _load_journal(vault_path)
        if journal["state"] == "preparing":
            journal = _recover_preparing(vault_path, passphrase, journal)
        members = _members(vault_path)
        names = set(journal["members"])
        target_bytes: dict[str, bytes] = {}
        current_hashes = {name: _sha256(read_private_bytes(members[name].path)) for name in names}
        all_target = all(
            current_hashes[name] == journal["members"][name]["target_sha256"] for name in names
        )
        for name in names:
            record = journal["members"][name]
            current_hash = current_hashes[name]
            if not _matches(members[name].backup_path, record["original_sha256"]):
                if not all_target:
                    raise ValueError("migration backup is missing or invalid; rollback is unavailable")
            if private_file_exists(members[name].next_path):
                candidate = read_private_bytes(members[name].next_path)
                if _sha256(candidate) != record["target_sha256"]:
                    raise ValueError("migration staging file is invalid")
                target_bytes[name] = candidate
            elif current_hash != record["target_sha256"]:
                raise ValueError("migration staging file is missing")
        if target_bytes:
            complete_targets = {
                name: target_bytes.get(name, read_private_bytes(members[name].path)) for name in names
            }
            _verify_target_round_trips(complete_targets, passphrase)
        for name in MEMBER_NAMES:
            if name not in names:
                continue
            record = journal["members"][name]
            current = read_private_bytes(members[name].path)
            current_hash = _sha256(current)
            if current_hash == record["original_sha256"]:
                write_private_bytes(members[name].path, target_bytes[name])
            elif current_hash != record["target_sha256"]:
                raise ValueError("migration target changed; rollback required")
            if _sha256(read_private_bytes(members[name].path)) != record["target_sha256"]:
                raise ValueError("migration target verification failed")
            if name not in journal["applied"]:
                journal["applied"].append(name)
                write_private_json(migration_journal_path(vault_path), journal)
        _cleanup(vault_path, names)
        return {"state": "completed", "members": sorted(names), "target_profile": journal["target_profile"]}


def rollback_kdf_migration(vault_path: Path, passphrase: str) -> dict[str, Any]:
    with kdf_write_guard(vault_path, allow_incomplete=True):
        if not migration_incomplete(vault_path):
            names = _validate_completed_profile(vault_path, passphrase, LEGACY_V1_PROFILE)
            return {"state": "already_rolled_back", "members": names, "source_profile": LEGACY_V1_PROFILE.name}
        journal = _load_journal(vault_path)
        members = _members(vault_path)
        names = set(journal["members"])
        if journal["state"] == "preparing":
            current = _read_present_originals(vault_path)
            if set(current) != names or any(
                _sha256(current[name]) != journal["members"][name]["original_sha256"] for name in names
            ):
                raise ValueError("migration source changed; rollback cannot continue")
        else:
            originals: dict[str, bytes] = {}
            for name in names:
                record = journal["members"][name]
                if not _matches(members[name].backup_path, record["original_sha256"]):
                    raise ValueError("migration backup is missing or invalid")
                originals[name] = read_private_bytes(members[name].backup_path)
                current_hash = _sha256(read_private_bytes(members[name].path))
                if current_hash not in {record["original_sha256"], record["target_sha256"]}:
                    raise ValueError("migration target changed; rollback cannot continue")
            vault_payload = json.loads(originals["vault"].decode("utf-8"))
            validate_store_shape(decrypt_store_payload(vault_payload, passphrase))
            for name in MEMBER_NAMES:
                if name not in names:
                    continue
                write_private_bytes(members[name].path, originals[name])
                if _sha256(read_private_bytes(members[name].path)) != journal["members"][name]["original_sha256"]:
                    raise ValueError("migration rollback verification failed")
        _cleanup(vault_path, names)
        return {"state": "rolled_back", "members": sorted(names), "source_profile": journal["source_profile"]}


def upgrade_kdf(vault_path: Path, passphrase: str) -> dict[str, Any]:
    if migration_incomplete(vault_path):
        return resume_kdf_migration(vault_path, passphrase)
    payload = read_private_json(vault_path)
    if is_encrypted_payload(payload) and encryption_profile(payload) == ARGON2ID_V2_PROFILE:
        names = _validate_completed_profile(vault_path, passphrase, ARGON2ID_V2_PROFILE)
        return {"state": "already_current", "members": names, "target_profile": ARGON2ID_V2_PROFILE.name}
    prepare_kdf_migration(vault_path, passphrase)
    return resume_kdf_migration(vault_path, passphrase)


def migration_status(vault_path: Path) -> dict[str, Any]:
    if not migration_incomplete(vault_path):
        return {"incomplete": False}
    journal = _load_journal(vault_path)
    return {
        "incomplete": True,
        "state": journal["state"],
        "source_profile": journal["source_profile"],
        "target_profile": journal["target_profile"],
        "members": sorted(journal["members"]),
        "applied": list(journal["applied"]),
    }
