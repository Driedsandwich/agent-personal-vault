"""Optional encrypted store backend.

This module intentionally relies on the `cryptography` package when encryption is
used. It does not implement custom cryptographic primitives.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any

ENCRYPTED_STORAGE = "encrypted-json-v1"
KDF_NAME = "pbkdf2-hmac-sha256"
KDF_ITERATIONS = 390_000


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


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    AESGCM, PBKDF2HMAC, crypto = _require_crypto()
    hashes, _invalid_tag = crypto
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=KDF_ITERATIONS)
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt_store_payload(store: dict, passphrase: str) -> dict:
    if not passphrase:
        raise ValueError("passphrase is required")
    AESGCM, _PBKDF2HMAC, _crypto = _require_crypto()
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive_key(passphrase, salt)
    plaintext = json.dumps(store, ensure_ascii=False, sort_keys=True).encode("utf-8")
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
    if payload.get("kdf") != KDF_NAME or payload.get("cipher") != "AES-256-GCM":
        raise DecryptionError("unsupported encrypted store format")
    AESGCM, _PBKDF2HMAC, crypto = _require_crypto()
    _hashes, invalid_tag = crypto
    try:
        salt = base64.b64decode(str(payload["salt"]))
        nonce = base64.b64decode(str(payload["nonce"]))
        ciphertext = base64.b64decode(str(payload["ciphertext"]))
        key = _derive_key(passphrase, salt)
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    except invalid_tag as exc:
        raise DecryptionError("invalid passphrase or corrupted encrypted store") from exc
    except Exception as exc:
        raise DecryptionError("failed to decrypt encrypted store") from exc
    decoded = json.loads(plaintext.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise DecryptionError("decrypted store is invalid")
    return decoded
