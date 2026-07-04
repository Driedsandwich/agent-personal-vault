"""Raw-free consent token management."""

from __future__ import annotations

import json
import os
import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback path
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt
except ImportError:  # pragma: no cover - Unix fallback path
    msvcrt = None  # type: ignore[assignment]

from .audit import _clean_text, redact_consent_id, write_audit_event
from .vault import ensure_private_dir, now_iso, store_path, write_json_private

DEFAULT_TTL_SECONDS = 300


class ConsentError(ValueError):
    """Raised when a consent token is missing, invalid, expired, or mismatched."""


def consent_path(vault_path: Path | None = None) -> Path:
    path = vault_path or store_path()
    return path.parent / "consents.json"


@contextmanager
def _state_lock(path: Path):
    ensure_private_dir(path.parent)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a+", encoding="utf-8") as handle:
        os.chmod(lock_path, 0o600)
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        elif msvcrt is not None:  # pragma: no cover - Windows fallback path
            handle.seek(0)
            handle.write("0")
            handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            elif msvcrt is not None:  # pragma: no cover - Windows fallback path
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _build_grant(
    *,
    action: str,
    key: str,
    purpose: str,
    ttl_seconds: int,
    actor: str,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    expires_at = now + timedelta(seconds=max(1, ttl_seconds))
    return {
        "id": "c_" + secrets.token_urlsafe(18),
        "action": action,
        "key": key,
        "purpose": _clean_text(purpose),
        "issued_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "used_at": "",
        "actor": actor,
    }


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "grants": [], "requests": []}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ConsentError("consent state is invalid")
    payload.setdefault("version", 1)
    payload.setdefault("grants", [])
    payload.setdefault("requests", [])
    return payload


def _write_state(path: Path, state: dict[str, Any]) -> None:
    write_json_private(path, state)


def _parse_expires_at(value: Any) -> datetime:
    try:
        expires_at = datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ConsentError("consent token expiry is invalid") from exc
    if expires_at.tzinfo is None:
        raise ConsentError("consent token expiry is invalid")
    return expires_at


def issue_consent(
    *,
    vault_path: Path,
    action: str,
    key: str,
    purpose: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    actor: str = "cli",
) -> dict[str, Any]:
    grant = _build_grant(action=action, key=key, purpose=purpose, ttl_seconds=ttl_seconds, actor=actor)
    path = consent_path(vault_path)
    with _state_lock(path):
        state = _load_state(path)
        grants = state.setdefault("grants", [])
        if not isinstance(grants, list):
            raise ConsentError("consent grants are invalid")
        grants.append(grant)
        _write_state(path, state)
    write_audit_event(
        vault_path=vault_path,
        actor=actor,
        action="consent_grant",
        key=key,
        raw_returned=False,
        purpose=purpose,
        outcome="allowed",
        consent_id=grant["id"],
    )
    return grant


def create_consent_request(
    *,
    vault_path: Path,
    action: str,
    key: str,
    purpose: str,
    actor: str = "cli",
) -> dict[str, Any]:
    request = {
        "id": "r_" + secrets.token_urlsafe(18),
        "action": action,
        "key": key,
        "purpose": _clean_text(purpose),
        "requested_at": now_iso(),
        "resolved_at": "",
        "status": "pending",
        "actor": actor,
        "consent_id": "",
    }
    path = consent_path(vault_path)
    with _state_lock(path):
        state = _load_state(path)
        requests = state.setdefault("requests", [])
        if not isinstance(requests, list):
            raise ConsentError("consent requests are invalid")
        requests.append(request)
        _write_state(path, state)
    write_audit_event(
        vault_path=vault_path,
        actor=actor,
        action="consent_request",
        key=key,
        raw_returned=False,
        purpose=purpose,
        outcome="pending",
        consent_id=request["id"],
    )
    return request


def list_consent_requests(vault_path: Path, include_resolved: bool = False) -> list[dict[str, Any]]:
    state = _load_state(consent_path(vault_path))
    requests = state.get("requests", [])
    if not isinstance(requests, list):
        raise ConsentError("consent requests are invalid")
    output = []
    for request in requests:
        if not isinstance(request, dict):
            continue
        if request.get("status") != "pending" and not include_resolved:
            continue
        output.append(
            {
                key: redact_consent_id(str(request.get(key) or "")) if key == "consent_id" else request.get(key, "")
                for key in ["id", "action", "key", "purpose", "requested_at", "resolved_at", "status", "actor", "consent_id"]
            }
        )
    return output


def resolve_consent_request(
    *,
    vault_path: Path,
    request_id: str,
    approve: bool,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    actor: str = "cli",
) -> dict[str, Any]:
    path = consent_path(vault_path)
    audit_event: dict[str, Any] | None = None
    with _state_lock(path):
        state = _load_state(path)
        requests = state.get("requests", [])
        if not isinstance(requests, list):
            raise ConsentError("consent requests are invalid")
        for request in requests:
            if not isinstance(request, dict) or request.get("id") != request_id:
                continue
            if request.get("status") != "pending":
                raise ConsentError("consent request is already resolved")
            request["resolved_at"] = now_iso()
            if not approve:
                request["status"] = "denied"
                _write_state(path, state)
                audit_event = {
                    "action": "consent_deny",
                    "key": str(request.get("key") or ""),
                    "purpose": str(request.get("purpose") or ""),
                    "outcome": "denied",
                    "consent_id": request_id,
                }
                result = {
                    key: request.get(key, "")
                    for key in ["id", "action", "key", "purpose", "requested_at", "resolved_at", "status", "actor", "consent_id"]
                }
                break

            grant = _build_grant(
                action=str(request.get("action") or ""),
                key=str(request.get("key") or ""),
                purpose=str(request.get("purpose") or ""),
                ttl_seconds=ttl_seconds,
                actor=actor,
            )
            grants = state.setdefault("grants", [])
            if not isinstance(grants, list):
                raise ConsentError("consent grants are invalid")
            grants.append(grant)
            request["status"] = "approved"
            request["consent_id"] = grant["id"]
            _write_state(path, state)
            audit_event = {
                "action": "consent_approve",
                "key": str(request.get("key") or ""),
                "purpose": str(request.get("purpose") or ""),
                "outcome": "allowed",
                "consent_id": grant["id"],
            }
            result = {"request_id": request_id, "grant": grant}
            break
        else:
            raise ConsentError("consent request not found")
    if audit_event is not None:
        write_audit_event(vault_path=vault_path, actor=actor, raw_returned=False, **audit_event)
        return result
    raise ConsentError("consent request not found")


def validate_and_consume_consent(
    *,
    vault_path: Path,
    consent_id: str,
    action: str,
    key: str,
    purpose: str,
    actor: str = "cli",
) -> dict[str, Any]:
    path = consent_path(vault_path)
    with _state_lock(path):
        state = _load_state(path)
        grants = state.get("grants", [])
        if not isinstance(grants, list):
            raise ConsentError("consent grants are invalid")
        for grant in grants:
            if not isinstance(grant, dict) or grant.get("id") != consent_id:
                continue
            if grant.get("used_at"):
                raise ConsentError("consent token has already been used")
            if grant.get("action") != action:
                raise ConsentError("consent token action mismatch")
            if grant.get("key") != key:
                raise ConsentError("consent token key mismatch")
            if grant.get("purpose") != _clean_text(purpose):
                raise ConsentError("consent token purpose mismatch")
            expires_at = _parse_expires_at(grant.get("expires_at"))
            if datetime.now(timezone.utc).replace(microsecond=0) > expires_at:
                raise ConsentError("consent token has expired")
            grant["used_at"] = now_iso()
            _write_state(path, state)
            result = dict(grant)
            break
        else:
            raise ConsentError("consent token not found")
    write_audit_event(
        vault_path=vault_path,
        actor=actor,
        action="consent_consume",
        key=key,
        raw_returned=False,
        purpose=purpose,
        outcome="allowed",
        consent_id=consent_id,
    )
    return result


def list_consents(vault_path: Path, include_used: bool = False) -> list[dict[str, Any]]:
    state = _load_state(consent_path(vault_path))
    grants = state.get("grants", [])
    if not isinstance(grants, list):
        raise ConsentError("consent grants are invalid")
    output = []
    for grant in grants:
        if not isinstance(grant, dict):
            continue
        if grant.get("used_at") and not include_used:
            continue
        output.append(
            {
                key: redact_consent_id(str(grant.get(key) or "")) if key == "id" else grant.get(key, "")
                for key in ["id", "action", "key", "purpose", "issued_at", "expires_at", "used_at", "actor"]
            }
        )
    return output
