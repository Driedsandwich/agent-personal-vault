#!/usr/bin/env python3
"""Smoke-test the installed wheel's optional encryption with synthetic data."""

from __future__ import annotations

import base64
import copy
import json
import os
import tempfile
from importlib import metadata
from pathlib import Path

import agent_personal_vault
from agent_personal_vault.crypto_store import (
    ARGON2ID_V2_PROFILE,
    DecryptionError,
    LEGACY_V1_PROFILE,
    cryptography_available,
    decrypt_store_payload,
    encryption_profile,
    encrypt_store_payload,
)
from agent_personal_vault.kdf_migration import upgrade_kdf
from agent_personal_vault.private_io import read_private_json
from agent_personal_vault.vault import blank_store, load_store, write_store


def main() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    imported_package = Path(agent_personal_vault.__file__).resolve()
    if imported_package.is_relative_to(repository_root):
        raise SystemExit("smoke test imported the repository source instead of the installed artifact")
    if not cryptography_available():
        raise SystemExit("installed encrypted extra is unavailable")
    requirements = metadata.requires("agent-personal-vault") or []
    normalized_requirements = {requirement.replace(" ", "").replace("'", '"') for requirement in requirements}
    expected_requirement = 'cryptography>=50.0.0;extra=="encrypted"'
    if expected_requirement not in normalized_requirements:
        raise SystemExit("installed artifact does not advertise the supported encrypted dependency floor")
    expected_version = os.environ.get("APV_EXPECTED_CRYPTOGRAPHY_VERSION")
    if expected_version and metadata.version("cryptography") != expected_version:
        raise SystemExit("installed encrypted dependency does not match the requested exact-floor version")

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

    with tempfile.TemporaryDirectory() as tmp:
        vault_path = Path(tmp) / "vault.json"
        legacy_store = blank_store()
        legacy_store["fields"]["FAMILY_NAME"] = "Synthetic"
        write_store(
            legacy_store,
            vault_path,
            passphrase=passphrase,
            encrypted=True,
            profile=LEGACY_V1_PROFILE,
        )
        result = upgrade_kdf(vault_path, passphrase)
        if result["state"] != "completed":
            raise SystemExit("installed artifact KDF migration did not complete")
        if encryption_profile(read_private_json(vault_path)) != ARGON2ID_V2_PROFILE:
            raise SystemExit("installed artifact KDF migration retained the legacy profile")
        if load_store(path=vault_path, passphrase=passphrase) != legacy_store:
            raise SystemExit("installed artifact KDF migration changed vault data")

    print("installed encrypted artifact smoke test passed")


if __name__ == "__main__":
    main()
