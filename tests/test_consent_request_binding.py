from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_personal_vault.consent import (
    ConsentError,
    consent_path,
    create_consent_request,
    list_consent_requests,
    resolve_consent_request,
)
from agent_personal_vault.vault import blank_store, write_json_private


class ConsentRequestBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.vault = Path(temp.name) / "vault.json"
        self.other_vault = self.vault.with_name("other-vault.json")
        for path in (self.vault, self.other_vault):
            write_json_private(path, blank_store())
        self.request = create_consent_request(
            vault_path=self.vault, action="get", key="POSTAL_CODE", purpose="review"
        )

    def test_requests_are_listed_only_for_their_vault(self) -> None:
        listed = list_consent_requests(self.vault)
        self.assertEqual([record["id"] for record in listed], [self.request["id"]])
        self.assertNotIn("vault_binding", listed[0])
        self.assertNotIn("vault_binding", self.request)
        for include_resolved in (False, True):
            with self.subTest(include_resolved=include_resolved):
                self.assertEqual(list_consent_requests(self.other_vault, include_resolved), [])

    def test_request_resolution_requires_the_matching_vault(self) -> None:
        state_path = consent_path(self.vault)
        before = state_path.read_bytes()
        for approve in (False, True):
            with (
                self.subTest(approve=approve),
                mock.patch(
                    "agent_personal_vault.consent._build_grant",
                    side_effect=AssertionError("grant construction was reached"),
                ),
                mock.patch(
                    "agent_personal_vault.consent.begin_audit_operation",
                    side_effect=AssertionError("resolution audit was reached"),
                ),
            ):
                with self.assertRaises(ConsentError):
                    resolve_consent_request(vault_path=self.other_vault, request_id=self.request["id"], approve=approve)
                self.assertEqual(state_path.read_bytes(), before)

        result = resolve_consent_request(vault_path=self.vault, request_id=self.request["id"], approve=True)
        self.assertEqual(result["request_id"], self.request["id"])
        listed = list_consent_requests(self.vault, include_resolved=True)
        self.assertEqual(listed[0]["status"], "approved")
        self.assertNotIn("vault_binding", listed[0])
        self.assertNotIn("vault_binding", result["grant"])
        state = json.loads(state_path.read_bytes())
        binding = state["requests"][0].get("vault_binding", "")
        self.assertRegex(binding, r"\Asha256:[0-9a-f]{64}\Z")
        self.assertEqual(binding, state["grants"][0]["vault_binding"])

    def test_unbound_requests_are_hidden_and_cannot_be_resolved(self) -> None:
        state_path = consent_path(self.vault)
        state = json.loads(state_path.read_bytes())
        state["requests"][0].pop("vault_binding", None)
        write_json_private(state_path, state)
        with self.subTest(operation="list"):
            self.assertEqual(list_consent_requests(self.vault, include_resolved=True), [])
        for approve in (False, True):
            with (
                self.subTest(approve=approve),
                mock.patch(
                    "agent_personal_vault.consent._build_grant",
                    side_effect=AssertionError("grant construction was reached"),
                ),
                mock.patch(
                    "agent_personal_vault.consent.begin_audit_operation",
                    side_effect=AssertionError("resolution audit was reached"),
                ),
            ):
                with self.assertRaises(ConsentError):
                    resolve_consent_request(vault_path=self.vault, request_id=self.request["id"], approve=approve)
