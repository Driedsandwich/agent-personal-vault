from __future__ import annotations

import tempfile
import unittest
from email.message import Message
from pathlib import Path
from types import SimpleNamespace

from agent_personal_vault.audit import read_audit_events
from agent_personal_vault.gui import GUI_SESSION_COOKIE, Handler, configure_gui_server
from agent_personal_vault.vault import blank_store, write_json_private


class GuiRequestHeadersTests(unittest.TestCase):
    host = "127.0.0.1:8123"
    origin = f"http://{host}"

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.vault = Path(temp.name) / "vault.json"
        write_json_private(self.vault, blank_store())
        self.server = SimpleNamespace(server_address=("127.0.0.1", 8123))
        self.session = "test-session"
        configure_gui_server(self.server, self.vault, "job_hunting_profile", session_token=self.session, monotonic=lambda: 0)
        self.server.gui_session_expires_at = 60

    def dispatch(self, method: str, path: str, *, host: str, headers: dict[str, str]) -> tuple[int, dict]:
        handler = Handler.__new__(Handler)
        handler.path = path
        handler.server = self.server
        handler.headers = Message()
        handler.headers["Host"] = host
        handler.headers["Cookie"] = f"{GUI_SESSION_COOKIE}={self.session}"
        for name, value in headers.items():
            handler.headers[name] = value
        responses = []
        handler.send_json = lambda status, payload: responses.append((status, payload))
        if method == "POST":
            handler.do_POST()
        else:
            handler.do_GET()
        self.assertEqual(len(responses), 1)
        return responses[0]

    def test_profile_post_checks_request_headers_before_auditing(self) -> None:
        path = "/api/profile/view"
        denied = [
            (self.host, {"Origin": "http://127.0.0.1:8124", "Sec-Fetch-Site": "same-origin"}),
            ("127.0.0.1:8124", {"Origin": self.origin}),
            (self.host, {"Sec-Fetch-Site": "same-site"}),
            (self.host, {}),
        ]
        for host, headers in denied:
            with self.subTest(host=host, headers=headers):
                before = read_audit_events(self.vault, limit=0)
                status, payload = self.dispatch("POST", path, host=host, headers=headers)
                after = read_audit_events(self.vault, limit=0)
                self.assertEqual((status, len(after) - len(before)), (403, 0))
                self.assertEqual(payload, {"error": "forbidden"})
                self.assertEqual(after, before)

        for headers in ({"Origin": self.origin}, {"Sec-Fetch-Site": "same-origin"}):
            with self.subTest(headers=headers):
                status, payload = self.dispatch("POST", path, host=self.host, headers=headers)
                self.assertEqual(status, 200)
                self.assertIn("fields", payload)
        self.assertTrue(any(event["action"] == "profile_view" for event in read_audit_events(self.vault, limit=0)))

    def test_cookie_authenticated_get_checks_host_and_optional_origin(self) -> None:
        path = "/api/consent/requests"
        cases = [
            (self.host, {"Origin": self.origin}, 200),
            (self.host, {}, 200),
            (self.host, {"Origin": "null"}, 403),
            ("localhost:8123", {}, 403),
        ]
        for host, headers, expected in cases:
            with self.subTest(host=host, headers=headers):
                status, payload = self.dispatch("GET", path, host=host, headers=headers)
                self.assertEqual(status, expected)
                self.assertEqual(payload, {"requests": []} if expected == 200 else {"error": "forbidden"})
