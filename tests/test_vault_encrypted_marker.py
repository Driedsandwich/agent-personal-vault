from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_personal_vault.crypto_store import SUPPORTED_ENCRYPTION_PROFILES, cryptography_available, encrypt_store_payload
from agent_personal_vault.vault import blank_store, load_store, read_store, write_json_private


class VaultEncryptedMarkerTests(unittest.TestCase):
    @unittest.skipUnless(cryptography_available(), "cryptography is not installed")
    def test_vault_reads_reject_unrecognized_encrypted_storage_without_rewriting(self) -> None:
        passphrase = "test fixture passphrase"
        store = blank_store()
        store["fields"]["POSTAL_CODE"] = "123-4567"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plain_path = root / "plain.json"
            write_json_private(plain_path, store)
            for reader in (read_store, load_store):
                with self.subTest(reader=reader.__name__, storage="plain"):
                    self.assertEqual(reader(path=plain_path), store)
            for profile in SUPPORTED_ENCRYPTION_PROFILES:
                encrypted_path = root / "encrypted.json"
                envelope = encrypt_store_payload(store, passphrase, profile=profile)
                for reader in (read_store, load_store):
                    with self.subTest(reader=reader.__name__, profile=profile.name, storage="supported"):
                        write_json_private(encrypted_path, envelope)
                        self.assertEqual(reader(path=encrypted_path, passphrase=passphrase), store)

                    with self.subTest(reader=reader.__name__, profile=profile.name, storage="unsupported"):
                        write_json_private(encrypted_path, {**envelope, "storage": "unrecognized-format"})
                        before = encrypted_path.read_bytes()
                        with mock.patch.dict("os.environ", {"AGENT_PERSONAL_VAULT_PASSPHRASE": ""}):
                            with self.subTest(check="error"):
                                with self.assertRaisesRegex(ValueError, r"\Aunsupported encrypted store format\Z"):
                                    reader(path=encrypted_path)
                        self.assertEqual(encrypted_path.read_bytes(), before, "vault bytes changed")

    def test_plain_vault_rejects_each_encrypted_envelope_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            for field in ("cipher", "kdf", "iterations", "salt", "nonce", "ciphertext", "memory_kib", "parallelism"):
                with self.subTest(field=field):
                    write_json_private(path, {**blank_store(), field: None})
                    with self.assertRaisesRegex(ValueError, r"\Aunsupported encrypted store format\Z"):
                        read_store(path=path)
