from __future__ import annotations

import io
import socket
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from agent_personal_vault import gui



def _same_origin_headers(server) -> bytes:
    host = f"127.0.0.1:{server.server_address[1]}"
    return f"Host: {host}\r\nOrigin: http://{host}\r\n".encode("ascii")

class GuiConnectionLimitsTests(unittest.TestCase):
    def run_with_server(self, check):
        def serve(server):
            server.daemon_threads = False
            check(server)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            with (
                mock.patch.object(ThreadingHTTPServer, "serve_forever", serve),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                gui.run_server(0, False, path, "job_hunting_profile")

    def exchange(self, server, request):
        handler_socket, client_socket = socket.socketpair()
        with handler_socket, client_socket:
            client_socket.settimeout(1.0)
            client_socket.sendall(request)
            server.process_request(handler_socket, ("127.0.0.1", 0))
            with client_socket.makefile("rb") as response:
                return response.read()

    def test_header_read_deadline_closes_connection(self):
        def check(server):
            request = b"GET / HTTP/1.0\r\nHost: localhost\r\n"
            self.assertEqual(self.exchange(server, request), b"")

        with mock.patch.object(gui, "GUI_REQUEST_TIMEOUT_SECONDS", 0.05, create=True):
            self.run_with_server(check)

    def test_request_reads_share_one_deadline(self):
        def check(server):
            request = b"GET / HTTP/1.0\r\nHost: localhost\r\n"
            with mock.patch.object(gui.time, "monotonic", side_effect=[100.0, 100.0, 111.0]):
                self.assertEqual(self.exchange(server, request), b"")

        with mock.patch.object(gui, "GUI_REQUEST_TIMEOUT_SECONDS", 10.0, create=True):
            self.run_with_server(check)

    def test_authenticated_body_read_deadline_closes_connection(self):
        def check(server):
            server.gui_session_expires_at = server.monotonic() + gui.GUI_SESSION_TTL_SECONDS
            cookie = f"{gui.GUI_SESSION_COOKIE}={server.gui_session_token}".encode("ascii")
            request = (
                b"POST /api/storage/acknowledge HTTP/1.0\r\n" + _same_origin_headers(server) + b"Cookie: " + cookie
                + b"\r\nContent-Length: 2\r\n\r\n{"
            )
            self.assertEqual(self.exchange(server, request), b"")

        with mock.patch.object(gui, "GUI_REQUEST_TIMEOUT_SECONDS", 0.05, create=True):
            self.run_with_server(check)

    def test_active_request_limit_closes_connection_and_recovers_capacity(self):
        def check(server):
            first, second, third = mock.sentinel.first, mock.sentinel.second, mock.sentinel.third
            address = ("127.0.0.1", 0)
            with (
                mock.patch.object(ThreadingHTTPServer, "process_request") as start_worker,
                mock.patch.object(server, "finish_request") as finish_worker,
                mock.patch.object(server, "shutdown_request") as close_connection,
            ):
                server.process_request(first, address)
                server.process_request(second, address)
                start_worker.assert_called_once_with(first, address)
                close_connection.assert_called_once_with(second)

                server.process_request_thread(first, address)
                finish_worker.assert_called_once_with(first, address)
                close_connection.assert_called_with(first)
                server.process_request(third, address)
                self.assertEqual(start_worker.call_args_list, [mock.call(first, address), mock.call(third, address)])

        with mock.patch.object(gui, "GUI_MAX_ACTIVE_REQUESTS", 1, create=True):
            self.run_with_server(check)

    def test_complete_authenticated_request_succeeds(self):
        def check(server):
            server.gui_session_expires_at = server.monotonic() + gui.GUI_SESSION_TTL_SECONDS
            cookie = f"{gui.GUI_SESSION_COOKIE}={server.gui_session_token}".encode("ascii")
            context, _ = gui.storage_context(server.store_path, server.storage_context_secret)
            body = f'{{"storage_context":"{context}"}}'.encode("ascii")
            request = (
                b"POST /api/storage/acknowledge HTTP/1.0\r\n" + _same_origin_headers(server) + b"Cookie: " + cookie
                + f"\r\nContent-Length: {len(body)}\r\n\r\n".encode("ascii")
                + body
            )
            response = self.exchange(server, request)
            self.assertTrue(response.startswith(b"HTTP/1.0 200 "))
            self.assertTrue(response.endswith(b'{"ok": true}'))

        self.run_with_server(check)
