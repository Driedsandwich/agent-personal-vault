"""Optional encrypted store backend.

This module intentionally relies on the `cryptography` package when encryption is
used. It does not implement custom cryptographic primitives.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import unicodedata
from typing import Any

ENCRYPTED_STORAGE = "encrypted-json-v1"
ENCRYPTED_SIDECAR_STORAGE = "encrypted-sidecar-json-v1"
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
    {
        "agentpersonalvault",
        "letmein",
        "password",
        "password123",
        "qwertyuiop",
        "test passphrase",
    }
)


class EncryptionUnavailableError(RuntimeError):
    """Raised when the optional encryption dependency is unavailable."""


class DecryptionError(ValueError):
    """Raised when encrypted store decryption fails."""


def cryptography_available() -> bool:
    try:
        import cryptography  # noqa: F401
    except ImportError:
        return False
    return True


def _require_crypto() -> tuple[Any, Any, Any]:
    try:
        from cryptography.exceptions import InvalidTag
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError as exc:
        raise EncryptionUnavailableError(
            "Encryption requires the optional 'cryptography' package. Install with: pip install 'agent-personal-vault[encrypted]'"
        ) from exc
    return AESGCM, PBKDF2HMAC, (hashes, InvalidTag)


def is_encrypted_payload(payload: object) -> bool:
    return isinstance(payload, dict) and payload.get("storage") == ENCRYPTED_STORAGE


def _derive_key(passphrase: str, salt: bytes, iterations: int = KDF_ITERATIONS) -> bytes:
    AESGCM, PBKDF2HMAC, crypto = _require_crypto()
    hashes, _invalid_tag = crypto
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return kdf.derive(passphrase.encode("utf-8"))


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
    expected_storage: str = ENCRYPTED_STORAGE,
    expected_kind: str | None = None,
) -> tuple[int, bytes, bytes, bytes]:
    version = payload.get("version")
    if (
        payload.get("app") != "agent-personal-vault"
        or payload.get("storage") != expected_storage
        or type(version) is not int
        or version != 1
        or payload.get("kdf") != KDF_NAME
        or payload.get("cipher") != "AES-256-GCM"
    ):
        raise DecryptionError("unsupported encrypted store format")
    if expected_kind is not None and payload.get("kind") != expected_kind:
        raise DecryptionError("unsupported encrypted store format")
    iterations = payload.get("iterations")
    if type(iterations) is not int or iterations not in SUPPORTED_KDF_ITERATIONS:
        raise DecryptionError("unsupported encrypted store format")
    salt = _decode_envelope_component(payload, "salt", exact_bytes=SALT_BYTES)
    nonce = _decode_envelope_component(payload, "nonce", exact_bytes=NONCE_BYTES)
    ciphertext = _decode_envelope_component(
        payload,
        "ciphertext",
        min_bytes=AES_GCM_TAG_BYTES,
        max_bytes=MAX_ENCRYPTED_CIPHERTEXT_BYTES,
    )
    return iterations, salt, nonce, ciphertext


def encrypt_store_payload(store: dict, passphrase: str, *, allow_weak_passphrase: bool = False) -> dict:
    if not passphrase:
        raise ValueError("passphrase is required")
    strength_issue = passphrase_strength_issue(passphrase)
    if strength_issue is not None and not allow_weak_passphrase:
        raise ValueError(f"passphrase is too weak for new encryption: {strength_issue}")
    AESGCM, _PBKDF2HMAC, _crypto = _require_crypto()
    salt = os.urandom(SALT_BYTES)
    nonce = os.urandom(NONCE_BYTES)
    key = _derive_key(passphrase, salt)
    plaintext = json.dumps(store, ensure_ascii=False, sort_keys=True).encode("utf-8")
    if len(plaintext) > MAX_ENCRYPTED_PLAINTEXT_BYTES:
        raise ValueError("store is too large for encrypted storage")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return {
        "app": "agent-personal-vault",
        "storage": ENCRYPTED_STORAGE,
        "version": 1,
        "cipher": "AES-256-GCM",
        "kdf": KDF_NAME,
        "iterations": KDF_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }


def decrypt_store_payload(payload: dict, passphrase: str) -> dict:
    if not passphrase:
        raise ValueError("passphrase is required")
    if not is_encrypted_payload(payload):
        raise DecryptionError("store payload is not encrypted")
    iterations, salt, nonce, ciphertext = _validate_encrypted_payload(payload)
    AESGCM, _PBKDF2HMAC, crypto = _require_crypto()
    _hashes, invalid_tag = crypto
    try:
        key = _derive_key(passphrase, salt, iterations=iterations)
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    except invalid_tag as exc:
        raise DecryptionError("invalid passphrase or corrupted encrypted store") from exc
    except Exception as exc:
        raise DecryptionError("failed to decrypt encrypted store") from exc
    decoded = json.loads(plaintext.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise DecryptionError("decrypted store is invalid")
    return decoded


def encrypt_sidecar_payload(payload: bytes, passphrase: str, *, kind: str) -> dict:
    """Encrypt one private metadata sidecar with a kind-bound AEAD envelope."""

    if not passphrase:
        raise ValueError("passphrase is required")
    if kind not in {"audit", "consent"}:
        raise ValueError("sidecar kind is invalid")
    if len(payload) > MAX_ENCRYPTED_PLAINTEXT_BYTES:
        raise ValueError("sidecar is too large for encrypted storage")
    AESGCM, _PBKDF2HMAC, _crypto = _require_crypto()
    salt = os.urandom(SALT_BYTES)
    nonce = os.urandom(NONCE_BYTES)
    key = _derive_key(passphrase, salt)
    aad = f"agent-personal-vault:{ENCRYPTED_SIDECAR_STORAGE}:{kind}:v1".encode("ascii")
    ciphertext = AESGCM(key).encrypt(nonce, payload, aad)
    return {
        "app": "agent-personal-vault",
        "storage": ENCRYPTED_SIDECAR_STORAGE,
        "kind": kind,
        "version": 1,
        "cipher": "AES-256-GCM",
        "kdf": KDF_NAME,
        "iterations": KDF_ITERATIONS,
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
    iterations, salt, nonce, ciphertext = _validate_encrypted_payload(
        payload,
        expected_storage=ENCRYPTED_SIDECAR_STORAGE,
        expected_kind=kind,
    )
    AESGCM, _PBKDF2HMAC, crypto = _require_crypto()
    _hashes, invalid_tag = crypto
    aad = f"agent-personal-vault:{ENCRYPTED_SIDECAR_STORAGE}:{kind}:v1".encode("ascii")
    try:
        key = _derive_key(passphrase, salt, iterations=iterations)
        return AESGCM(key).decrypt(nonce, ciphertext, aad)
    except invalid_tag as exc:
        raise DecryptionError("invalid passphrase or corrupted encrypted sidecar") from exc
    except Exception as exc:
        raise DecryptionError("failed to decrypt encrypted sidecar") from exc
