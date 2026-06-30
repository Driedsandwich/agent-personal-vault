"""Raw-free audit logging."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .vault import ensure_private_dir, now_iso, store_path


DEFAULT_LIMIT = 20


def audit_path(vault_path: Path | None = None) -> Path:
    path = vault_path or store_path()
    return path.parent / "audit.jsonl"


def _clean_text(value: str | None) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    return text[:240]


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
        "consent_id": _clean_text(consent_id),
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
