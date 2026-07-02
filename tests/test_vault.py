from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_personal_vault.audit import audit_path, read_audit_events
from agent_personal_vault.consent import consent_path, list_consent_requests
from agent_personal_vault.crypto_store import cryptography_available, is_encrypted_payload
from agent_personal_vault.gui import audit_view_payload, page_html, save_profile_fields
from agent_personal_vault.vault import (
    agent_context,
    check_summary,
    derived_fields,
    local_user_path,
    load_store,
    normalize_date_like,
    normalize_phone,
    normalize_postal_code,
    normalize_value,
    planning_hints,
    schema_context,
    store_path,
    write_store,
)


class VaultTests(unittest.TestCase):
    def grant_consent(self, path: Path, action: str, key: str, purpose: str) -> str:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_personal_vault.cli",
                "--store",
                str(path),
                "consent",
                "grant",
                "--action",
                action,
                "--key",
                key,
                "--purpose",
                purpose,
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return str(json.loads(result.stdout)["id"])

    def request_consent(self, path: Path, action: str, key: str, purpose: str) -> str:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_personal_vault.cli",
                "--store",
                str(path),
                "consent",
                "request",
                "--action",
                action,
                "--key",
                key,
                "--purpose",
                purpose,
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return str(json.loads(result.stdout)["id"])

    def test_default_store_uses_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("AGENT_PERSONAL_VAULT_HOME")
            os.environ["AGENT_PERSONAL_VAULT_HOME"] = tmp
            try:
                self.assertEqual(store_path(), Path(tmp).resolve() / "vault.json")
            finally:
                if old is None:
                    os.environ.pop("AGENT_PERSONAL_VAULT_HOME", None)
                else:
                    os.environ["AGENT_PERSONAL_VAULT_HOME"] = old

    def test_local_user_path_resolves_explicit_store_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            expected = Path(tmp).resolve() / "vault.json"
            self.assertEqual(local_user_path(Path(tmp) / "." / "vault.json"), expected)

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

    def test_planning_hints_are_raw_free_and_conservative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            store["fields"]["EMAIL"] = "private.person@example.test"
            write_store(store, path)
            hints = planning_hints(load_store(path=path), "応募フォームの氏名とメール連絡先を下書きする")
            encoded = json.dumps(hints, ensure_ascii=False)
            self.assertFalse(hints["raw_values_included"])
            self.assertTrue(hints["conservative"])
            self.assertIn("FULL_NAME", encoded)
            self.assertIn("EMAIL", encoded)
            self.assertNotIn("山田", encoded)
            self.assertNotIn("private.person@example.test", encoded)

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

    def test_cli_context_task_outputs_raw_free_planning_hints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            store["fields"]["EMAIL"] = "private.person@example.test"
            write_store(store, path)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "context",
                    "--task",
                    "応募フォームの氏名とメール連絡先を下書きする",
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            payload = json.loads(result.stdout)
            self.assertFalse(payload["raw_values_included"])
            self.assertIn("planning_hints", payload)
            self.assertIn("FULL_NAME", result.stdout)
            self.assertIn("EMAIL", result.stdout)
            self.assertNotIn("山田", result.stdout)
            self.assertNotIn("private.person@example.test", result.stdout)

    def test_cli_list_does_not_return_raw_fragments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["EMAIL"] = "private.person@example.test"
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            result = subprocess.run(
                [sys.executable, "-m", "agent_personal_vault.cli", "--store", str(path), "list"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertIn("EMAIL", result.stdout)
            self.assertIn("(filled, 27 chars)", result.stdout)
            self.assertNotIn("private", result.stdout)
            self.assertNotIn("example", result.stdout)
            self.assertNotIn("山田", result.stdout)

    def test_cli_env_warns_on_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            purpose = "test raw export warning"
            consent_id = self.grant_consent(path, "env", "*", purpose)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "env",
                    "--purpose",
                    purpose,
                    "--consent-id",
                    consent_id,
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertIn("WARNING", result.stderr)
            self.assertIn("APV_FAMILY_NAME", result.stdout)

    def test_cli_get_warns_on_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            purpose = "test one-key retrieval"
            consent_id = self.grant_consent(path, "get", "FAMILY_NAME", purpose)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "get",
                    "FAMILY_NAME",
                    "--purpose",
                    purpose,
                    "--consent-id",
                    consent_id,
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertIn("WARNING", result.stderr)
            self.assertEqual(result.stdout.strip(), "山田")

    def test_cli_audit_log_excludes_raw_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            purpose = "local draft"
            consent_id = self.grant_consent(path, "get", "FAMILY_NAME", purpose)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "get",
                    "FAMILY_NAME",
                    "--purpose",
                    purpose,
                    "--consent-id",
                    consent_id,
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            log_path = audit_path(path)
            self.assertTrue(log_path.exists())
            self.assertEqual(stat.S_IMODE(log_path.stat().st_mode), 0o600)
            events = read_audit_events(path, limit=10)
            encoded = json.dumps(events, ensure_ascii=False)
            self.assertIn("FAMILY_NAME", encoded)
            self.assertIn("local draft", encoded)
            self.assertNotIn("山田", encoded)

    def test_cli_audit_summary_is_raw_free(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["EMAIL"] = "taro@example.test"
            write_store(store, path)
            purpose = "local shell export"
            consent_id = self.grant_consent(path, "env", "*", purpose)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "env",
                    "--purpose",
                    purpose,
                    "--consent-id",
                    consent_id,
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            result = subprocess.run(
                [sys.executable, "-m", "agent_personal_vault.cli", "--store", str(path), "audit", "summary"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            payload = json.loads(result.stdout)
            self.assertFalse(payload["raw_values_included"])
            self.assertGreaterEqual(payload["events"], 1)
            self.assertEqual(payload["by_action"]["env"], 1)
            self.assertNotIn("taro@example.test", result.stdout)

    def test_cli_set_and_unset_write_raw_free_audit_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "set",
                    "FAMILY_NAME",
                    "--stdin",
                    "--purpose",
                    "test input",
                ],
                check=True,
                input="山田\n",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "unset",
                    "FAMILY_NAME",
                    "--purpose",
                    "test clear",
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            events = read_audit_events(path, limit=10)
            encoded = json.dumps(events, ensure_ascii=False)
            self.assertIn('"action": "set"', encoded)
            self.assertIn('"action": "unset"', encoded)
            self.assertNotIn("山田", encoded)

    def test_gui_profile_save_writes_raw_free_audit_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            save_profile_fields(
                path,
                "job_hunting_profile",
                {
                    "FAMILY_NAME": "山田",
                    "EMAIL": "private.person@example.test",
                },
            )
            store = load_store(path=path)
            self.assertEqual(store["fields"]["FAMILY_NAME"], "山田")
            self.assertEqual(store["fields"]["EMAIL"], "private.person@example.test")
            log_path = audit_path(path)
            self.assertTrue(log_path.exists())
            self.assertEqual(stat.S_IMODE(log_path.stat().st_mode), 0o600)
            events = read_audit_events(path, limit=10)
            encoded = json.dumps(events, ensure_ascii=False)
            self.assertIn('"actor": "gui"', encoded)
            self.assertIn('"action": "profile_save"', encoded)
            self.assertIn('"key": "*"', encoded)
            self.assertNotIn("山田", encoded)
            self.assertNotIn("private.person@example.test", encoded)

    def test_gui_audit_view_payload_omits_raw_values_and_purpose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            store["fields"]["EMAIL"] = "private.person@example.test"
            write_store(store, path)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "set",
                    "GIVEN_NAME",
                    "--stdin",
                    "--purpose",
                    "raw-looking purpose 山田 private.person@example.test",
                ],
                check=True,
                input="太郎\n",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            payload = audit_view_payload(path)
            encoded = json.dumps(payload, ensure_ascii=False)
            self.assertFalse(payload["raw_values_included"])
            self.assertFalse(payload["summary"]["raw_values_included"])
            self.assertIn('"action": "set"', encoded)
            self.assertIn('"key": "GIVEN_NAME"', encoded)
            self.assertNotIn("山田", encoded)
            self.assertNotIn("太郎", encoded)
            self.assertNotIn("private.person@example.test", encoded)
            self.assertNotIn("raw-looking purpose", encoded)
            self.assertNotIn("purpose", encoded)
            self.assertNotIn("consent_id", encoded)

    def test_gui_page_shows_approved_consent_id_handoff(self) -> None:
        html = page_html("dummy-token", "job_hunting_profile")

        self.assertIn('id="consentResult"', html)
        self.assertIn("data.result.grant.id", html)
        self.assertIn("--consent-id", html)
        self.assertIn("CLI get", html)

    def test_gui_page_warns_on_bulk_consent_requests(self) -> None:
        html = page_html("dummy-token", "job_hunting_profile")

        self.assertIn("bulk-warning", html)
        self.assertIn("一括raw export", html)
        self.assertIn('req.action === "env" || req.key === "*"', html)

    def test_cli_get_requires_consent_and_logs_denial_without_raw_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "get",
                    "FAMILY_NAME",
                    "--purpose",
                    "missing consent",
                    "--consent-id",
                    "missing",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("consent required", result.stderr)
            self.assertEqual(result.stdout, "")
            encoded = json.dumps(read_audit_events(path, limit=10), ensure_ascii=False)
            self.assertIn('"outcome": "denied"', encoded)
            self.assertNotIn("山田", encoded)

    def test_cli_consent_token_is_one_time_and_raw_free(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            purpose = "one time access"
            consent_id = self.grant_consent(path, "get", "FAMILY_NAME", purpose)
            self.assertTrue(consent_path(path).exists())
            self.assertEqual(stat.S_IMODE(consent_path(path).stat().st_mode), 0o600)
            command = [
                sys.executable,
                "-m",
                "agent_personal_vault.cli",
                "--store",
                str(path),
                "get",
                "FAMILY_NAME",
                "--purpose",
                purpose,
                "--consent-id",
                consent_id,
            ]
            first = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            second = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(first.stdout.strip(), "山田")
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("already been used", second.stderr)
            consent_text = consent_path(path).read_text(encoding="utf-8")
            self.assertNotIn("山田", consent_text)

    def test_cli_consent_list_is_raw_free(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["EMAIL"] = "taro@example.test"
            write_store(store, path)
            self.grant_consent(path, "get", "EMAIL", "email access")
            result = subprocess.run(
                [sys.executable, "-m", "agent_personal_vault.cli", "--store", str(path), "consent", "list"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertIn("EMAIL", result.stdout)
            self.assertNotIn("taro@example.test", result.stdout)

    def test_cli_consent_request_approve_enables_one_raw_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            purpose = "queued access"
            request_id = self.request_consent(path, "get", "FAMILY_NAME", purpose)
            approve = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "consent",
                    "approve",
                    request_id,
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            consent_id = json.loads(approve.stdout)["grant"]["id"]
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "get",
                    "FAMILY_NAME",
                    "--purpose",
                    purpose,
                    "--consent-id",
                    consent_id,
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.stdout.strip(), "山田")
            consent_text = consent_path(path).read_text(encoding="utf-8")
            self.assertIn('"status": "approved"', consent_text)
            self.assertNotIn("山田", consent_text)

    def test_cli_consent_request_deny_does_not_issue_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["EMAIL"] = "taro@example.test"
            write_store(store, path)
            request_id = self.request_consent(path, "get", "EMAIL", "deny access")
            deny = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "consent",
                    "deny",
                    request_id,
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            payload = json.loads(deny.stdout)
            self.assertEqual(payload["status"], "denied")
            listing = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "consent",
                    "list",
                    "--include-used",
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(listing.stdout.strip(), "")
            self.assertNotIn("taro@example.test", consent_path(path).read_text(encoding="utf-8"))

    def test_cli_encryption_status_is_raw_free(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            result = subprocess.run(
                [sys.executable, "-m", "agent_personal_vault.cli", "--store", str(path), "encryption", "status"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            payload = json.loads(result.stdout)
            self.assertFalse(payload["encrypted"])
            self.assertFalse(payload["raw_values_included"])
            self.assertNotIn("山田", result.stdout)

    def test_cli_encrypt_requires_optional_crypto_or_roundtrips_without_raw_plaintext(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            env = {**os.environ, "AGENT_PERSONAL_VAULT_PASSPHRASE": "test passphrase"}
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_personal_vault.cli",
                    "--store",
                    str(path),
                    "encryption",
                    "encrypt",
                    "--purpose",
                    "test encrypt",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            if not cryptography_available():
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("cryptography", result.stderr)
                self.assertIn("山田", path.read_text(encoding="utf-8"))
                return
            self.assertEqual(result.returncode, 0, result.stderr)
            encrypted_payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(is_encrypted_payload(encrypted_payload))
            self.assertNotIn("山田", path.read_text(encoding="utf-8"))
            loaded = load_store(path=path, passphrase="test passphrase")
            self.assertEqual(loaded["fields"]["FAMILY_NAME"], "山田")

    def test_mcp_server_exposes_only_raw_free_read_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            store["fields"]["EMAIL"] = "taro@example.test"
            write_store(store, path)
            messages = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "apv.context", "arguments": {"task": "応募フォームの氏名とメール連絡先を下書きする"}},
                },
                {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "apv.list_masked", "arguments": {}}},
            ]
            result = subprocess.run(
                [sys.executable, "-m", "agent_personal_vault.mcp_server", "--store", str(path)],
                input="\n".join(json.dumps(message) for message in messages) + "\n",
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            responses = [json.loads(line) for line in result.stdout.splitlines()]
            tools = responses[1]["result"]["tools"]
            tool_names = {tool["name"] for tool in tools}
            self.assertEqual(tool_names, {"apv.schema", "apv.context", "apv.check", "apv.list_masked", "apv.request_consent"})
            request_tool = next(tool for tool in tools if tool["name"] == "apv.request_consent")
            self.assertEqual(request_tool["inputSchema"]["properties"]["action"]["enum"], ["get"])
            self.assertEqual(request_tool["inputSchema"]["required"], ["action", "key", "purpose"])
            self.assertNotIn("山田", result.stdout)
            self.assertNotIn("taro@example.test", result.stdout)
            self.assertNotIn("ta...st", result.stdout)
            self.assertIn("raw_values_included", result.stdout)
            self.assertIn("planning_hints", result.stdout)
            self.assertIn("FULL_NAME", result.stdout)
            self.assertIn("EMAIL", result.stdout)

    def test_mcp_consent_request_is_raw_free_and_audited(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            messages = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "apv.request_consent",
                        "arguments": {
                            "action": "get",
                            "key": "FAMILY_NAME",
                            "purpose": "prepare local draft for user review",
                        },
                    },
                },
            ]
            result = subprocess.run(
                [sys.executable, "-m", "agent_personal_vault.mcp_server", "--store", str(path)],
                input="\n".join(json.dumps(message) for message in messages) + "\n",
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotIn("山田", result.stdout)
            responses = [json.loads(line) for line in result.stdout.splitlines()]
            payload = json.loads(responses[1]["result"]["content"][0]["text"])
            self.assertFalse(payload["raw_values_included"])
            self.assertEqual(payload["request"]["action"], "get")
            self.assertEqual(payload["request"]["key"], "FAMILY_NAME")
            self.assertEqual(payload["request"]["actor"], "mcp")
            requests = list_consent_requests(path)
            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0]["actor"], "mcp")
            events = read_audit_events(path, limit=10)
            self.assertTrue(any(event["action"] == "consent_request" and event["actor"] == "mcp" for event in events))
            self.assertNotIn("山田", json.dumps(events, ensure_ascii=False))

    def test_mcp_consent_request_rejects_env_bulk_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            write_store(store, path)
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "apv.request_consent",
                    "arguments": {
                        "action": "env",
                        "key": "*",
                        "purpose": "bulk export should not be agent-facing",
                    },
                },
            }
            result = subprocess.run(
                [sys.executable, "-m", "agent_personal_vault.mcp_server", "--store", str(path)],
                input=json.dumps(message) + "\n",
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            response = json.loads(result.stdout)
            self.assertEqual(response["error"]["code"], -32602)
            self.assertIn("one-key get", response["error"]["message"])
            self.assertEqual(list_consent_requests(path), [])
            self.assertNotIn("山田", result.stdout)

    def test_mcp_consent_request_accepts_derived_get_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            store = load_store(create=True, path=path)
            store["fields"]["FAMILY_NAME"] = "山田"
            store["fields"]["GIVEN_NAME"] = "太郎"
            write_store(store, path)
            messages = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "apv.request_consent",
                        "arguments": {
                            "action": "get",
                            "key": "FULL_NAME",
                            "purpose": "prepare local draft for user review",
                        },
                    },
                },
            ]
            result = subprocess.run(
                [sys.executable, "-m", "agent_personal_vault.mcp_server", "--store", str(path)],
                input="\n".join(json.dumps(message) for message in messages) + "\n",
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotIn("山田", result.stdout)
            self.assertNotIn("太郎", result.stdout)
            responses = [json.loads(line) for line in result.stdout.splitlines()]
            payload = json.loads(responses[1]["result"]["content"][0]["text"])
            self.assertFalse(payload["raw_values_included"])
            self.assertEqual(payload["request"]["action"], "get")
            self.assertEqual(payload["request"]["key"], "FULL_NAME")
            self.assertEqual(payload["request"]["actor"], "mcp")
            requests = list_consent_requests(path)
            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0]["key"], "FULL_NAME")
            events = read_audit_events(path, limit=10)
            self.assertTrue(any(event["action"] == "consent_request" and event["key"] == "FULL_NAME" for event in events))
            self.assertNotIn("山田", json.dumps(events, ensure_ascii=False))
            self.assertNotIn("太郎", json.dumps(events, ensure_ascii=False))

    def test_mcp_consent_request_rejects_unknown_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            load_store(create=True, path=path)
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "apv.request_consent",
                    "arguments": {
                        "action": "get",
                        "key": "UNKNOWN",
                        "purpose": "prepare local draft for user review",
                    },
                },
            }
            result = subprocess.run(
                [sys.executable, "-m", "agent_personal_vault.mcp_server", "--store", str(path)],
                input=json.dumps(message) + "\n",
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            response = json.loads(result.stdout)
            self.assertEqual(response["error"]["code"], -32602)
            self.assertIn("Unknown key: UNKNOWN", response["error"]["message"])
            self.assertIn("FULL_NAME", response["error"]["message"])


if __name__ == "__main__":
    unittest.main()
