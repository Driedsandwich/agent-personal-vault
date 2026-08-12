#!/usr/bin/env python3
"""Smoke-test the installed wheel's optional encryption with synthetic data."""

from __future__ import annotations

import base64
import copy
import json
from pathlib import Path

import agent_personal_vault
from agent_personal_vault.crypto_store import (
    DecryptionError,
    cryptography_available,
    decrypt_store_payload,
    encrypt_store_payload,
)


def main() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    imported_package = Path(agent_personal_vault.__file__).resolve()
    if imported_package.is_relative_to(repository_root):
        raise SystemExit("smoke test imported the repository source instead of the installed artifact")
    if not cryptography_available():
        raise SystemExit("installed encrypted extra is unavailable")

    marker = "synthetic-encryption-marker"
    store = {"schema": "synthetic", "fields": {"VALUE": marker}}
    passphrase = "correct horse battery staple"
    encrypted = encrypt_store_payload(store, passphrase)
    serialized = json.dumps(encrypted, sort_keys=True)
    if marker in serialized:
        raise SystemExit("encrypted artifact retained the synthetic plaintext marker")
    if decrypt_store_payload(encrypted, passphrase) != store:
        raise SystemExit("encrypted artifact round trip failed")

    tampered = copy.deepcopy(encrypted)
    ciphertext = bytearray(base64.b64decode(tampered["ciphertext"]))
    ciphertext[-1] ^= 1
    tampered["ciphertext"] = base64.b64encode(ciphertext).decode("ascii")
    try:
        decrypt_store_payload(tampered, passphrase)
    except DecryptionError:
        pass
    else:
        raise SystemExit("tampered encrypted artifact was accepted")

    print("installed encrypted artifact smoke test passed")


if __name__ == "__main__":
    main()
