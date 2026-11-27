from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_personal_vault import crypto_store
from agent_personal_vault.kdf_migration import upgrade_kdf
from agent_personal_vault.private_io import read_private_json, write_private_json
from agent_personal_vault.vault import blank_store, load_store


@unittest.skipUnless(crypto_store.cryptography_available(), "cryptography is not installed")
class PassphrasePolicyTests(unittest.TestCase):
    def test_new_encryption_rejects_common_passphrases(self):
        for passphrase in (
            "password1234",
            "!!PaSsWoRd-82057!!",
            "##LET ME IN-806337!",
            "ＷＥＬＣＯＭＥ＊９２０５７３１８",
            "correct horse battery staple",
        ):
            with self.subTest(passphrase=passphrase):
                with self.assertRaisesRegex(ValueError, "passphrase is too weak"):
                    crypto_store.encrypt_store_payload(blank_store(), passphrase)

    def test_new_encryption_requires_sixteen_characters(self):
        with self.assertRaisesRegex(ValueError, "use at least 16 characters"):
            crypto_store.encrypt_store_payload(blank_store(), "Pebble-Vern7!?")

    def test_new_encryption_rejects_repetition_and_simple_sequences(self):
        for passphrase in (
            "mmmmmmmmmmmmJ7!?",
            "m7v2m7v2m7v2m7v2",
            "1234567890123456",
            "abcdefghijklmnop",
            "qwertyuiopasdfghj",
            "abcd-1234-qwer-zxcv",
        ):
            with self.subTest(passphrase=passphrase):
                with self.assertRaisesRegex(ValueError, "passphrase is too weak"):
                    crypto_store.encrypt_store_payload(blank_store(), passphrase)

    def test_new_encryption_round_trips_a_long_passphrase(self):
        store = blank_store()
        for passphrase in (
            "Q&f7^Ms2#Zw8!Lp?",
            "Quartz! Lantern7 Otter% Drift",
            "liberty property first understanding",
            "Qx!76-4321-bM%VnZ",
        ):
            with self.subTest(length=len(passphrase)):
                encrypted = crypto_store.encrypt_store_payload(store, passphrase)
                self.assertEqual(crypto_store.decrypt_store_payload(encrypted, passphrase), store)

    def test_cli_requires_explicit_override_for_new_encryption(self):
        passphrase = "!!PaSsWoRd-82057!!"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            original = load_store(create=True, path=path)
            before = path.read_bytes()
            command = [
                sys.executable, "-m", "agent_personal_vault.cli", "--store", str(path),
                "encryption", "encrypt", "--purpose", "compatibility override",
            ]
            env = {**os.environ, "AGENT_PERSONAL_VAULT_PASSPHRASE": passphrase}

            refused = subprocess.run(command, capture_output=True, text=True, env=env)

            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("passphrase is too weak", refused.stderr)
            self.assertEqual(path.read_bytes(), before)
            self.assertNotIn(passphrase, refused.stdout + refused.stderr)

            accepted = subprocess.run(
                [*command, "--allow-weak-passphrase"], capture_output=True, text=True, env=env,
            )

            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertIn("weak passphrase override", accepted.stderr)
            self.assertNotIn(passphrase, accepted.stdout + accepted.stderr)
            self.assertTrue(crypto_store.is_encrypted_payload(read_private_json(path)))
            self.assertEqual(load_store(path=path, passphrase=passphrase)["fields"], original["fields"])

    def test_existing_passphrase_remains_readable_across_kdf_upgrade(self):
        passphrase = "Pebble-Vern7!?"
        store = blank_store()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            legacy = crypto_store.encrypt_store_payload(
                store, passphrase, profile=crypto_store.LEGACY_V1_PROFILE, allow_weak_passphrase=True,
            )
            write_private_json(path, legacy)
            self.assertEqual(load_store(path=path, passphrase=passphrase), store)

            upgrade_kdf(path, passphrase)

            self.assertEqual(crypto_store.encryption_profile(read_private_json(path)), crypto_store.ARGON2ID_V2_PROFILE)
            self.assertEqual(load_store(path=path, passphrase=passphrase), store)
