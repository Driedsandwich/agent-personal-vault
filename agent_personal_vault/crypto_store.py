"""Optional encrypted store backend built from versioned cryptography profiles."""

from __future__ import annotations

import base64
import binascii
import json
import os
import unicodedata
from dataclasses import dataclass
from typing import Any

ENCRYPTED_STORAGE_V1 = "encrypted-json-v1"
ENCRYPTED_STORAGE_V2 = "encrypted-json-v2"
ENCRYPTED_SIDECAR_STORAGE_V1 = "encrypted-sidecar-json-v1"
ENCRYPTED_SIDECAR_STORAGE_V2 = "encrypted-sidecar-json-v2"
ENCRYPTED_STORAGE = ENCRYPTED_STORAGE_V1
ENCRYPTED_SIDECAR_STORAGE = ENCRYPTED_SIDECAR_STORAGE_V1
KDF_NAME = "pbkdf2-hmac-sha256"
KDF_ITERATIONS = 390_000
SUPPORTED_KDF_ITERATIONS = frozenset({KDF_ITERATIONS})
SALT_BYTES = 16
NONCE_BYTES = 12
AES_GCM_TAG_BYTES = 16
MAX_ENCRYPTED_PLAINTEXT_BYTES = 8 * 1024 * 1024
MAX_ENCRYPTED_CIPHERTEXT_BYTES = MAX_ENCRYPTED_PLAINTEXT_BYTES + AES_GCM_TAG_BYTES
MIN_NEW_PASSPHRASE_LENGTH = 12
COMMON_WEAK_PASSPHRASES = frozenset(
    {"agentpersonalvault", "letmein", "password", "password123", "qwertyuiop", "test passphrase"}
)


@dataclass(frozen=True)
class EncryptionProfile:
    """One immutable, allowlisted envelope and key-derivation profile."""

    name: str
    version: int
    kdf: str
    vault_storage: str
    sidecar_storage: str
    iterations: int
    memory_kib: int | None = None
    parallelism: int | None = None


LEGACY_V1_PROFILE = EncryptionProfile(
    "v1-pbkdf2-sha256-390k", 1, KDF_NAME, ENCRYPTED_STORAGE_V1, ENCRYPTED_SIDECAR_STORAGE_V1, KDF_ITERATIONS
)
ARGON2ID_V2_PROFILE = EncryptionProfile(
    "v2-argon2id-19m-t2-p1",
    2,
    "argon2id",
    ENCRYPTED_STORAGE_V2,
    ENCRYPTED_SIDECAR_STORAGE_V2,
    2,
    19 * 1024,
    1,
)
LATEST_ENCRYPTION_PROFILE = ARGON2ID_V2_PROFILE
SUPPORTED_ENCRYPTION_PROFILES = (LEGACY_V1_PROFILE, ARGON2ID_V2_PROFILE)


class EncryptionUnavailableError(RuntimeError):
    """Raised when the optional encryption dependency is unavailable."""


class DecryptionError(ValueError):
    """Raised when encrypted store decryption fails."""


def cryptography_available() -> bool:
    try:
        from cryptography.hazmat.primitives.kdf.argon2 import Argon2id  # noqa: F401
    except ImportError:
        return False
    return True


def _require_crypto() -> tuple[Any, Any, Any, Any]:
    try:
        from cryptography.exceptions import InvalidTag
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError as exc:
        raise EncryptionUnavailableError(
            "Encryption requires the optional 'cryptography' package. Install with: pip install 'agent-personal-vault[encrypted]'"
        ) from exc
    return AESGCM, PBKDF2HMAC, Argon2id, (hashes, InvalidTag)


def is_encrypted_payload(payload: object) -> bool:
    return isinstance(payload, dict) and payload.get("storage") in {
        profile.vault_storage for profile in SUPPORTED_ENCRYPTION_PROFILES
    }


def is_encrypted_sidecar_payload(payload: object, *, kind: str | None = None) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("storage") in {profile.sidecar_storage for profile in SUPPORTED_ENCRYPTION_PROFILES}
        and (kind is None or payload.get("kind") == kind)
    )


def encryption_profile(payload: object, *, sidecar: bool = False) -> EncryptionProfile:
    if not isinstance(payload, dict):
        raise DecryptionError("unsupported encrypted store format")
    storage = payload.get("storage")
    for profile in SUPPORTED_ENCRYPTION_PROFILES:
        expected = profile.sidecar_storage if sidecar else profile.vault_storage
        if storage == expected and payload.get("version") == profile.version:
            return profile
    raise DecryptionError("unsupported encrypted store format")


def _derive_key(passphrase: str, salt: bytes, profile: EncryptionProfile) -> bytes:
    _AESGCM, PBKDF2HMAC, Argon2id, crypto = _require_crypto()
    hashes, _invalid_tag = crypto
    if profile.kdf == KDF_NAME:
        return PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt, iterations=profile.iterations
        ).derive(passphrase.encode("utf-8"))
    if profile.kdf == "argon2id" and profile.memory_kib is not None and profile.parallelism is not None:
        return Argon2id(
            salt=salt,
            length=32,
            iterations=profile.iterations,
            lanes=profile.parallelism,
            memory_cost=profile.memory_kib,
        ).derive(passphrase.encode("utf-8"))
    raise DecryptionError("unsupported encrypted store format")


def passphrase_strength_issue(passphrase: str) -> str | None:
    candidate = unicodedata.normalize("NFKC", passphrase).strip()
    if len(candidate) < MIN_NEW_PASSPHRASE_LENGTH:
        return f"use at least {MIN_NEW_PASSPHRASE_LENGTH} characters"
    normalized = candidate.casefold()
    if normalized in COMMON_WEAK_PASSPHRASES or len(set(candidate)) < 4:
        return "choose a less predictable value"
    return None


def _decode_envelope_component(
    payload: dict,
    name: str,
    *,
    exact_bytes: int | None = None,
    min_bytes: int | None = None,
    max_bytes: int | None = None,
) -> bytes:
    value = payload.get(name)
    if not isinstance(value, str):
        raise DecryptionError("unsupported encrypted store format")
    byte_limit = exact_bytes if exact_bytes is not None else max_bytes
    if byte_limit is not None and len(value) > ((byte_limit + 2) // 3) * 4:
        raise DecryptionError("unsupported encrypted store format")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, UnicodeError, ValueError) as exc:
        raise DecryptionError("unsupported encrypted store format") from exc
    if base64.b64encode(decoded).decode("ascii") != value:
        raise DecryptionError("unsupported encrypted store format")
    if exact_bytes is not None and len(decoded) != exact_bytes:
        raise DecryptionError("unsupported encrypted store format")
    if min_bytes is not None and len(decoded) < min_bytes:
        raise DecryptionError("unsupported encrypted store format")
    if max_bytes is not None and len(decoded) > max_bytes:
        raise DecryptionError("unsupported encrypted store format")
    return decoded


def _validate_encrypted_payload(
    payload: dict,
    *,
    expected_kind: str | None = None,
) -> tuple[EncryptionProfile, bytes, bytes, bytes]:
    sidecar = expected_kind is not None
    profile = encryption_profile(payload, sidecar=sidecar)
    expected_storage = profile.sidecar_storage if sidecar else profile.vault_storage
    required = {"app", "storage", "version", "cipher", "kdf", "iterations", "salt", "nonce", "ciphertext"}
    if sidecar:
        required.add("kind")
    if profile.version == 2:
        required.update({"memory_kib", "parallelism"})
    if (
        set(payload) != required
        or payload.get("app") != "agent-personal-vault"
        or payload.get("storage") != expected_storage
        or type(payload.get("version")) is not int
        or payload.get("version") != profile.version
        or payload.get("kdf") != profile.kdf
        or payload.get("cipher") != "AES-256-GCM"
        or (sidecar and payload.get("kind") != expected_kind)
    ):
        raise DecryptionError("unsupported encrypted store format")
    if type(payload.get("iterations")) is not int or payload.get("iterations") != profile.iterations:
        raise DecryptionError("unsupported encrypted store format")
    if profile.version == 2 and (
        type(payload.get("memory_kib")) is not int
        or payload.get("memory_kib") != profile.memory_kib
        or type(payload.get("parallelism")) is not int
        or payload.get("parallelism") != profile.parallelism
    ):
        raise DecryptionError("unsupported encrypted store format")
    salt = _decode_envelope_component(payload, "salt", exact_bytes=SALT_BYTES)
    nonce = _decode_envelope_component(payload, "nonce", exact_bytes=NONCE_BYTES)
    ciphertext = _decode_envelope_component(
        payload,
        "ciphertext",
        min_bytes=AES_GCM_TAG_BYTES,
        max_bytes=MAX_ENCRYPTED_CIPHERTEXT_BYTES,
    )
    return profile, salt, nonce, ciphertext


def _aad(profile: EncryptionProfile, *, sidecar_kind: str | None = None) -> bytes | None:
    if profile.version == 1 and sidecar_kind is None:
        return None
    storage = profile.sidecar_storage if sidecar_kind is not None else profile.vault_storage
    suffix = f":{sidecar_kind}" if sidecar_kind is not None else ""
    return f"agent-personal-vault:{storage}{suffix}:v{profile.version}".encode("ascii")


def _profile_fields(profile: EncryptionProfile) -> dict[str, int | str]:
    fields: dict[str, int | str] = {"version": profile.version, "kdf": profile.kdf, "iterations": profile.iterations}
    if profile.version == 2:
        fields["memory_kib"] = int(profile.memory_kib or 0)
        fields["parallelism"] = int(profile.parallelism or 0)
    return fields


def encrypt_store_payload(
    store: dict,
    passphrase: str,
    *,
    allow_weak_passphrase: bool = False,
    profile: EncryptionProfile = LATEST_ENCRYPTION_PROFILE,
) -> dict:
    if not passphrase:
        raise ValueError("passphrase is required")
    if profile not in SUPPORTED_ENCRYPTION_PROFILES:
        raise ValueError("encryption profile is unsupported")
    strength_issue = passphrase_strength_issue(passphrase)
    if strength_issue is not None and not allow_weak_passphrase:
        raise ValueError(f"passphrase is too weak for new encryption: {strength_issue}")
    AESGCM, _PBKDF2HMAC, _Argon2id, _crypto = _require_crypto()
    salt = os.urandom(SALT_BYTES)
    nonce = os.urandom(NONCE_BYTES)
    key = _derive_key(passphrase, salt, profile)
    plaintext = json.dumps(store, ensure_ascii=False, sort_keys=True).encode("utf-8")
    if len(plaintext) > MAX_ENCRYPTED_PLAINTEXT_BYTES:
        raise ValueError("store is too large for encrypted storage")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, _aad(profile))
    return {
        "app": "agent-personal-vault",
        "storage": profile.vault_storage,
        "cipher": "AES-256-GCM",
        **_profile_fields(profile),
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }


def decrypt_store_payload(payload: dict, passphrase: str) -> dict:
    if not passphrase:
        raise ValueError("passphrase is required")
    if not is_encrypted_payload(payload):
        raise DecryptionError("store payload is not encrypted")
    profile, salt, nonce, ciphertext = _validate_encrypted_payload(payload)
    AESGCM, _PBKDF2HMAC, _Argon2id, crypto = _require_crypto()
    _hashes, invalid_tag = crypto
    try:
        key = _derive_key(passphrase, salt, profile)
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, _aad(profile))
    except invalid_tag as exc:
        raise DecryptionError("invalid passphrase or corrupted encrypted store") from exc
    except DecryptionError:
        raise
    except Exception as exc:
        raise DecryptionError("failed to decrypt encrypted store") from exc
    try:
        decoded = json.loads(plaintext.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DecryptionError("decrypted store is invalid") from exc
    if not isinstance(decoded, dict):
        raise DecryptionError("decrypted store is invalid")
    return decoded


def encrypt_sidecar_payload(
    payload: bytes,
    passphrase: str,
    *,
    kind: str,
    profile: EncryptionProfile = LATEST_ENCRYPTION_PROFILE,
) -> dict:
    """Encrypt one private metadata sidecar with a kind-bound AEAD envelope."""

    if not passphrase:
        raise ValueError("passphrase is required")
    if kind not in {"audit", "consent"}:
        raise ValueError("sidecar kind is invalid")
    if profile not in SUPPORTED_ENCRYPTION_PROFILES:
        raise ValueError("encryption profile is unsupported")
    if len(payload) > MAX_ENCRYPTED_PLAINTEXT_BYTES:
        raise ValueError("sidecar is too large for encrypted storage")
    AESGCM, _PBKDF2HMAC, _Argon2id, _crypto = _require_crypto()
    salt = os.urandom(SALT_BYTES)
    nonce = os.urandom(NONCE_BYTES)
    key = _derive_key(passphrase, salt, profile)
    ciphertext = AESGCM(key).encrypt(nonce, payload, _aad(profile, sidecar_kind=kind))
    return {
        "app": "agent-personal-vault",
        "storage": profile.sidecar_storage,
        "kind": kind,
        "cipher": "AES-256-GCM",
        **_profile_fields(profile),
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }


def decrypt_sidecar_payload(payload: dict, passphrase: str, *, kind: str) -> bytes:
    """Decrypt one metadata sidecar and reject cross-kind envelope swaps."""

    if not passphrase:
        raise ValueError("passphrase is required")
    if kind not in {"audit", "consent"}:
        raise ValueError("sidecar kind is invalid")
    profile, salt, nonce, ciphertext = _validate_encrypted_payload(payload, expected_kind=kind)
    AESGCM, _PBKDF2HMAC, _Argon2id, crypto = _require_crypto()
    _hashes, invalid_tag = crypto
    try:
        key = _derive_key(passphrase, salt, profile)
        return AESGCM(key).decrypt(nonce, ciphertext, _aad(profile, sidecar_kind=kind))
    except invalid_tag as exc:
        raise DecryptionError("invalid passphrase or corrupted encrypted sidecar") from exc
    except DecryptionError:
        raise
    except Exception as exc:
        raise DecryptionError("failed to decrypt encrypted sidecar") from exc
