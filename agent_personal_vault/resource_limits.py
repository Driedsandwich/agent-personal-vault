"""Conservative application-level resource limits for local inputs and state."""

from __future__ import annotations

from typing import Any


MAX_PRIVATE_JSON_BYTES = 12 * 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 20_000
MAX_JSON_STRING_BYTES = MAX_PRIVATE_JSON_BYTES
MAX_FIELD_VALUE_BYTES = 64 * 1024
MAX_PURPOSE_BYTES = 4 * 1024
MAX_GUI_BODY_BYTES = 1024 * 1024
MAX_MCP_MESSAGE_BYTES = 256 * 1024
MAX_CONSENT_RECORDS = 2_000
MAX_AUDIT_BYTES = 8 * 1024 * 1024


class ResourceLimitError(ValueError):
    """Raised when input or retained state exceeds a documented hard limit."""


def utf8_size(value: str) -> int:
    return len(value.encode("utf-8"))


def require_text_limit(value: str, *, max_bytes: int, label: str) -> str:
    if utf8_size(value) > max_bytes:
        raise ResourceLimitError(f"{label} exceeds the supported size limit")
    return value


def validate_json_resources(value: Any) -> None:
    """Bound depth, node count, and strings after a byte-bounded JSON parse."""

    remaining = MAX_JSON_NODES
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        remaining -= 1
        if remaining < 0:
            raise ResourceLimitError("JSON state exceeds the supported structure limit")
        if depth > MAX_JSON_DEPTH:
            raise ResourceLimitError("JSON state exceeds the supported depth limit")
        if isinstance(current, str):
            require_text_limit(current, max_bytes=MAX_JSON_STRING_BYTES, label="JSON string")
        elif isinstance(current, dict):
            for key, child in current.items():
                if not isinstance(key, str):
                    raise ResourceLimitError("JSON object key is invalid")
                require_text_limit(key, max_bytes=MAX_JSON_STRING_BYTES, label="JSON object key")
                stack.append((child, depth + 1))
        elif isinstance(current, list):
            stack.extend((child, depth + 1) for child in current)
