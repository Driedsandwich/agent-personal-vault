"""Raw-free audit logging."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .vault import ensure_private_dir, now_iso, store_path


DEFAULT_LIMIT = 20
EMAIL_TOKEN_STRIP = ".,;:()[]{}<>\"'"


def _looks_like_email_token(token: str) -> bool:
    token = token.strip(EMAIL_TOKEN_STRIP)
    local, separator, domain = token.partition("@")
    if separator != "@" or not local or "." not in domain:
        return False
    suffix = domain.rsplit(".", 1)[-1]
    return len(suffix) >= 2 and suffix.isalpha()


def _looks_like_grouped_number(text: str) -> bool:
    if "-" not in text and " " not in text:
        return False
    digits = "".join(char for char in text if char.isdigit())
    if len(digits) not in {7, 10, 11}:
        return False
    groups = [group for group in text.replace("-", " ").split() if any(char.isdigit() for char in group)]
    return len(groups) >= 2


def _looks_raw_like(text: str) -> bool:
    return any(_looks_like_email_token(token) for token in text.split()) or _looks_like_grouped_number(text)


def audit_path(vault_path: Path | None = None) -> Path:
    path = vault_path or store_path()
    return path.parent / "audit.jsonl"


def _clean_text(value: str | None) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if _looks_raw_like(text):
        return "[redacted]"
    return text[:240]


def redact_consent_id(value: str | None) -> str:
    text = "" if value is None else " ".join(str(value).split())
    if text.startswith("c_"):
        return "c_[redacted]"
    return _clean_text(text)


def write_audit_event(
    *,
    vault_path: Path,
    actor: str,
    action: str,
    key: str | None = None,
    raw_returned: bool = False,
    purpose: str | None = None,
    outcome: str = "allowed",
    consent_id: str | None = None,
) -> dict[str, Any]:
    path = audit_path(vault_path)
    ensure_private_dir(path.parent)
    event: dict[str, Any] = {
        "timestamp": now_iso(),
        "actor": actor,
        "action": action,
        "key": key or "",
        "raw_returned": bool(raw_returned),
        "purpose": _clean_text(purpose),
        "consent_id": redact_consent_id(consent_id),
        "outcome": outcome,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
        handle.write("\n")
    os.chmod(path, 0o600)
    return event


def read_audit_events(vault_path: Path, limit: int = DEFAULT_LIMIT) -> list[dict[str, Any]]:
    path = audit_path(vault_path)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                events.append(payload)
    if limit <= 0:
        return events
    return events[-limit:]


def audit_summary(vault_path: Path) -> dict[str, Any]:
    events = read_audit_events(vault_path, limit=0)
    by_action: dict[str, int] = {}
    raw_by_key: dict[str, int] = {}
    for event in events:
        action = str(event.get("action") or "")
        by_action[action] = by_action.get(action, 0) + 1
        if event.get("raw_returned"):
            key = str(event.get("key") or "")
            raw_by_key[key] = raw_by_key.get(key, 0) + 1
    return {
        "events": len(events),
        "by_action": by_action,
        "raw_access_by_key": raw_by_key,
        "raw_values_included": False,
    }
