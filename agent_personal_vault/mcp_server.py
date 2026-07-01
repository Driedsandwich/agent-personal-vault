"""Minimal raw-free MCP stdio server.

This exposes only raw-free tools. It intentionally does not expose get, env,
set, unset, or any raw-returning operation.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .consent import create_consent_request
from .vault import agent_context, check_summary, get_schema, load_store, local_user_path, schema_context, store_path, validate_key

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "agent-personal-vault"
SERVER_VERSION = "0.1.0"


def text_json(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            }
        ]
    }


def tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "apv.schema",
            "description": "Return public schema metadata without reading stored personal values.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "apv.context",
            "description": "Return raw-free vault context for AI-agent planning, optionally with minimum-key task hints.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Optional raw-free task description for minimum-key planning hints."},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "apv.check",
            "description": "Return raw-free vault status and missing required keys.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "apv.list_masked",
            "description": "Return all schema keys with masked values only. No raw values are returned.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "apv.request_consent",
            "description": "Create a raw-free one-key consent request for later human approval. No raw values are returned.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["get", "env"]},
                    "key": {"type": "string", "description": "Schema key for get, or * for env."},
                    "purpose": {"type": "string", "description": "Raw-free reason shown to the human approver."},
                },
                "required": ["action", "purpose"],
                "additionalProperties": False,
            },
        },
    ]


class MCPServer:
    def __init__(self, path: Path, schema_name: str) -> None:
        self.path = path
        self.schema_name = schema_name

    def response(self, request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def error(self, request_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}
        if name == "apv.schema":
            return text_json(schema_context(self.schema_name))
        if name == "apv.context":
            store = load_store(path=self.path)
            return text_json(agent_context(store, include_path=False, path=self.path, task=str(arguments.get("task") or "")))
        if name == "apv.check":
            store = load_store(path=self.path)
            summary = check_summary(store, self.path)
            summary["raw_values_included"] = False
            summary.pop("path", None)
            return text_json(summary)
        if name == "apv.list_masked":
            store = load_store(path=self.path)
            schema = get_schema(store["schema"])
            fields = store.get("fields", {})
            payload = {
                "schema": store["schema"],
                "raw_values_included": False,
                "values": [
                    {
                        "key": key,
                        "label": spec.label,
                        "group": spec.group,
                        "filled": bool(str(fields.get(key, "")).strip()),
                        "length": len(str(fields.get(key, ""))) if str(fields.get(key, "")).strip() else 0,
                    }
                    for key, spec in schema.items()
                ],
            }
            return text_json(payload)
        if name == "apv.request_consent":
            store = load_store(path=self.path)
            action = str(arguments.get("action") or "")
            if action not in {"get", "env"}:
                raise ValueError("action must be get or env")
            key = "*" if action == "env" else str(arguments.get("key") or "")
            if action == "get":
                key = validate_key(key, store["schema"])
            purpose = str(arguments.get("purpose") or "").strip()
            if not purpose:
                raise ValueError("purpose is required")
            request = create_consent_request(
                vault_path=self.path,
                action=action,
                key=key,
                purpose=purpose,
                actor="mcp",
            )
            payload = {
                "raw_values_included": False,
                "request": request,
                "next_step": "Approve or deny this request in the GUI or with `agent-personal-vault consent approve|deny`.",
            }
            return text_json(payload)
        raise KeyError(name)

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = str(message.get("method", ""))
        request_id = message.get("id")
        if method == "notifications/initialized":
            return None
        if method == "initialize":
            return self.response(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            )
        if method == "tools/list":
            return self.response(request_id, {"tools": tool_definitions()})
        if method == "tools/call":
            params = message.get("params", {})
            if not isinstance(params, dict):
                return self.error(request_id, -32602, "Invalid params")
            try:
                arguments = params.get("arguments", {})
                if arguments is None:
                    arguments = {}
                if not isinstance(arguments, dict):
                    return self.error(request_id, -32602, "Invalid arguments")
                return self.response(request_id, self.call_tool(str(params.get("name", "")), arguments))
            except KeyError:
                return self.error(request_id, -32601, "Unknown tool")
            except ValueError as exc:
                return self.error(request_id, -32602, str(exc))
            except Exception as exc:
                return self.error(request_id, -32000, str(exc))
        return self.error(request_id, -32601, "Method not found")

    def serve(self) -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
                if not isinstance(message, dict):
                    raise ValueError("message must be an object")
                response = self.handle(message)
            except Exception as exc:
                response = self.error(None, -32700, str(exc))
            if response is not None:
                print(json.dumps(response, ensure_ascii=False), flush=True)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the raw-free Agent Personal Vault MCP stdio server.")
    parser.add_argument("--store", help="Override vault path.")
    parser.add_argument("--schema", default="job_hunting_profile")
    args = parser.parse_args(argv)
    MCPServer(local_user_path(args.store) if args.store else store_path(), args.schema).serve()


if __name__ == "__main__":
    main()
