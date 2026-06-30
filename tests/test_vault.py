from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_personal_vault.vault import (
    agent_context,
    check_summary,
    derived_fields,
    load_store,
    normalize_date_like,
    normalize_phone,
    normalize_postal_code,
    normalize_value,
    schema_context,
    store_path,
    write_store,
)


class VaultTests(unittest.TestCase):
    def test_default_store_uses_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("AGENT_PERSONAL_VAULT_HOME")
            os.environ["AGENT_PERSONAL_VAULT_HOME"] = tmp
            try:
                self.assertEqual(store_path(), Path(tmp) / "vault.json")
            finally:
                if old is None:
                    os.environ.pop("AGENT_PERSONAL_VAULT_HOME", None)
                else:
                    os.environ["AGENT_PERSONAL_VAULT_HOME"] = old

    def test_store_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            self.assertEqual(store["schema"], "job_hunting_profile")

    def test_normalizers(self) -> None:
        self.assertEqual(normalize_postal_code("１０００００１"), "100-0001")
        self.assertEqual(normalize_phone("０９０１２３４５６７８"), "090-1234-5678")
        self.assertEqual(normalize_date_like("2000年4月1日"), "2000-04-01")
        self.assertEqual(normalize_value("EMAIL", "ＴＡＲＯ＠ＥＸＡＭＰＬＥ．ＴＥＳＴ"), "taro@example.test")

    def test_derived_fields(self) -> None:
        fields = {
            "FAMILY_NAME": "山田",
            "GIVEN_NAME": "太郎",
            "FAMILY_NAME_KANA": "やまだ",
            "GIVEN_NAME_KANA": "たろう",
        }
        derived = derived_fields(fields)
        self.assertEqual(derived["FULL_NAME"], "山田　太郎")
        self.assertEqual(derived["FULL_NAME_KANA"], "やまだ　たろう")
        self.assertEqual(derived["NAME_SEPARATOR"], "全角スペース")

    def test_check_summary_has_no_raw_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            summary = check_summary(load_store(path=path), path)
            encoded = json.dumps(summary, ensure_ascii=False)
            self.assertNotIn("山田", encoded)
            self.assertIn("required_missing", summary)

    def test_agent_context_has_no_raw_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            store["fields"]["EMAIL"] = "taro@example.test"
            write_store(store, path)
            context = agent_context(load_store(path=path))
            encoded = json.dumps(context, ensure_ascii=False)
            self.assertFalse(context["raw_values_included"])
            self.assertNotIn("山田", encoded)
            self.assertNotIn("taro@example.test", encoded)
            self.assertIn("filled_keys", context)

    def test_schema_context_has_no_raw_values(self) -> None:
        context = schema_context("job_hunting_profile")
        encoded = json.dumps(context, ensure_ascii=False)
        self.assertFalse(context["raw_values_included"])
        self.assertIn("fields", context)
        self.assertNotIn("taro@example.test", encoded)

    def test_cli_schema_outputs_without_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing_store = Path(tmp) / "missing.json"
            result = subprocess.run(
                [sys.executable, "-m", "agent_personal_vault.cli", "--store", str(missing_store), "schema"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schema"], "job_hunting_profile")
            self.assertFalse(payload["raw_values_included"])
            self.assertFalse(missing_store.exists())

    def test_cli_context_outputs_raw_free_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            result = subprocess.run(
                [sys.executable, "-m", "agent_personal_vault.cli", "--store", str(path), "context"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            payload = json.loads(result.stdout)
            self.assertFalse(payload["raw_values_included"])
            self.assertNotIn("山田", result.stdout)

    def test_cli_env_warns_on_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            result = subprocess.run(
                [sys.executable, "-m", "agent_personal_vault.cli", "--store", str(path), "env"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertIn("WARNING", result.stderr)
            self.assertIn("APV_FAMILY_NAME", result.stdout)


if __name__ == "__main__":
    unittest.main()
