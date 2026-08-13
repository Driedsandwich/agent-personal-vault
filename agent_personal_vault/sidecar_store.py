"""Encryption-aware storage for private consent and audit sidecars."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .crypto_store import (
    ENCRYPTED_SIDECAR_STORAGE,
    decrypt_store_payload,
    decrypt_sidecar_payload,
    encrypt_sidecar_payload,
    is_encrypted_payload,
)
from .private_io import private_file_exists, read_private_bytes, read_private_json, write_private_bytes
from .resource_limits import MAX_PRIVATE_JSON_BYTES, ResourceLimitError, validate_json_resources


@dataclass(frozen=True)
class PreparedSidecarWrite:
    """Fully encoded sidecar bytes that can be committed without more parsing or crypto."""

    path: Path
    payload: bytes


def _passphrase(explicit: str | None = None) -> str:
    value = explicit or os.environ.get("AGENT_PERSONAL_VAULT_PASSPHRASE")
    if not value:
        raise ValueError("Encrypted sidecars require AGENT_PERSONAL_VAULT_PASSPHRASE or an explicit passphrase.")
    return value


def vault_uses_encryption(vault_path: Path) -> bool:
    return private_file_exists(vault_path) and is_encrypted_payload(read_private_json(vault_path))


def _validated_vault_passphrase(vault_payload: object, explicit: str | None = None) -> str:
    passphrase = _passphrase(explicit)
    if not is_encrypted_payload(vault_payload):
        raise ValueError("vault encryption state changed; reload and retry")
    decrypt_store_payload(vault_payload, passphrase)
    return passphrase


def _sidecar_protection(vault_path: Path, passphrase: str | None) -> tuple[bool, str | None]:
    if not private_file_exists(vault_path):
        return False, passphrase
    vault_payload = read_private_json(vault_path)
    if not is_encrypted_payload(vault_payload):
        return False, passphrase
    return True, _validated_vault_passphrase(vault_payload, passphrase)


def validate_sidecar_passphrase_binding(vault_path: Path, passphrase: str | None = None) -> str | None:
    """Prove the selected passphrase opens an encrypted vault before sidecar crypto."""

    _encrypted, validated_passphrase = _sidecar_protection(vault_path, passphrase)
    return validated_passphrase


def is_encrypted_sidecar_payload(payload: object, *, kind: str | None = None) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("storage") == ENCRYPTED_SIDECAR_STORAGE
        and (kind is None or payload.get("kind") == kind)
    )


def sidecar_is_encrypted(path: Path, *, kind: str) -> bool:
    if not private_file_exists(path):
        return False
    try:
        payload = read_private_json(path)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return False
    return is_encrypted_sidecar_payload(payload, kind=kind)


def read_sidecar_bytes(
    path: Path,
    *,
    vault_path: Path,
    kind: str,
    passphrase: str | None = None,
    max_bytes: int = MAX_PRIVATE_JSON_BYTES,
) -> bytes:
    encrypted_limit = min(MAX_PRIVATE_JSON_BYTES, ((max_bytes + 18) // 3) * 4 + 2048)
    raw = read_private_bytes(path, max_bytes=max(max_bytes, encrypted_limit))
    try:
        envelope = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return raw
    if not is_encrypted_sidecar_payload(envelope):
        return raw
    if not is_encrypted_sidecar_payload(envelope, kind=kind):
        raise ValueError("encrypted sidecar kind mismatch")
    plaintext = decrypt_sidecar_payload(envelope, _passphrase(passphrase), kind=kind)
    if len(plaintext) > max_bytes:
        raise ValueError("decrypted sidecar exceeds the supported size limit")
    return plaintext


def write_sidecar_bytes(
    path: Path,
    payload: bytes,
    *,
    vault_path: Path,
    kind: str,
    passphrase: str | None = None,
) -> None:
    protect, passphrase = _sidecar_protection(vault_path, passphrase)
    commit_prepared_sidecar(
        prepare_sidecar_write(
            path,
            payload,
            kind=kind,
            encrypted=protect,
            passphrase=passphrase,
        )
    )


def prepare_sidecar_write(
    path: Path,
    payload: bytes,
    *,
    kind: str,
    encrypted: bool,
    passphrase: str | None,
) -> PreparedSidecarWrite:
    """Encode a complete target sidecar without changing filesystem state."""

    if len(payload) > MAX_PRIVATE_JSON_BYTES:
        raise ResourceLimitError("private state exceeds the supported size limit")
    if encrypted:
        envelope = encrypt_sidecar_payload(payload, _passphrase(passphrase), kind=kind)
        validate_json_resources(envelope)
        encoded = (json.dumps(envelope, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(encoded) > MAX_PRIVATE_JSON_BYTES:
            raise ResourceLimitError("private state exceeds the supported size limit")
    else:
        encoded = payload
    return PreparedSidecarWrite(path=path, payload=encoded)


def commit_prepared_sidecar(prepared: PreparedSidecarWrite) -> None:
    """Commit bytes that were fully parsed, validated, and transformed earlier."""

    write_private_bytes(prepared.path, prepared.payload)


def read_sidecar_json(
    path: Path,
    *,
    vault_path: Path,
    kind: str,
    passphrase: str | None = None,
) -> Any:
    payload = json.loads(read_sidecar_bytes(path, vault_path=vault_path, kind=kind, passphrase=passphrase).decode("utf-8"))
    validate_json_resources(payload)
    return payload


def write_sidecar_json(
    path: Path,
    payload: dict,
    *,
    vault_path: Path,
    kind: str,
    passphrase: str | None = None,
) -> None:
    validate_json_resources(payload)
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(encoded) > MAX_PRIVATE_JSON_BYTES:
        raise ValueError("private state exceeds the supported size limit")
    write_sidecar_bytes(
        path,
        encoded,
        vault_path=vault_path,
        kind=kind,
        passphrase=passphrase,
    )


def prepare_sidecar_migration(
    path: Path,
    *,
    vault_path: Path,
    kind: str,
    encrypted: bool,
    passphrase: str,
    max_bytes: int = MAX_PRIVATE_JSON_BYTES,
) -> PreparedSidecarWrite | None:
    """Read, decrypt, bound, and transform a sidecar without replacing it."""

    passphrase = validate_sidecar_passphrase_binding(vault_path, passphrase) or passphrase
    if not private_file_exists(path):
        return None
    plaintext = read_sidecar_bytes(
        path,
        vault_path=vault_path,
        kind=kind,
        passphrase=passphrase,
        max_bytes=max_bytes,
    )
    return prepare_sidecar_write(
        path,
        plaintext,
        kind=kind,
        encrypted=encrypted,
        passphrase=passphrase,
    )


def migrate_sidecar(
    path: Path,
    *,
    vault_path: Path,
    kind: str,
    encrypted: bool,
    passphrase: str,
    max_bytes: int = MAX_PRIVATE_JSON_BYTES,
) -> bool:
    prepared = prepare_sidecar_migration(
        path,
        vault_path=vault_path,
        kind=kind,
        encrypted=encrypted,
        passphrase=passphrase,
        max_bytes=max_bytes,
    )
    if prepared is None:
        return False
    commit_prepared_sidecar(prepared)
    return True
