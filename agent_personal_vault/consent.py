"""Raw-free consent token management."""

from __future__ import annotations

import hashlib
import re
import secrets
import unicodedata
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
from .private_io import open_private_lock, private_file_exists, read_private_json
from .vault import now_iso, store_path, write_json_private

DEFAULT_TTL_SECONDS = 300
REQUEST_ID_PATTERN = re.compile(r"r_[A-Za-z0-9_-]{24}")
PURPOSE_BINDING_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")


class ConsentError(ValueError):
    """Raised when a consent token is missing, invalid, expired, or mismatched."""


def _validate_request_id(value: Any) -> str:
    if not isinstance(value, str) or REQUEST_ID_PATTERN.fullmatch(value) is None:
        raise ConsentError("consent request id is invalid")
    return value


def _normalize_purpose(value: Any) -> str:
    if not isinstance(value, str):
        raise ConsentError("consent purpose is invalid")
    if any(unicodedata.category(char) == "Cf" for char in value):
        raise ConsentError("consent purpose contains unsupported format controls")
    normalized = unicodedata.normalize("NFKC", value)
    if any(unicodedata.category(char) == "Cf" for char in normalized):
        raise ConsentError("consent purpose contains unsupported format controls")
    normalized = " ".join(normalized.split())
    if not normalized:
        raise ConsentError("consent purpose is required")
    return normalized


def _purpose_binding(normalized_purpose: str) -> str:
    digest = hashlib.sha256(normalized_purpose.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _validate_purpose_binding(value: Any) -> str:
    if not isinstance(value, str) or PURPOSE_BINDING_PATTERN.fullmatch(value) is None:
        raise ConsentError("consent purpose binding is invalid")
    return value


def _validate_stored_purpose(value: Any) -> str:
    if not isinstance(value, str):
        raise ConsentError("consent purpose is invalid")
    if any(unicodedata.category(char) == "Cf" for char in value):
        raise ConsentError("consent purpose contains unsupported format controls")
    return value


def _public_record(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "purpose_binding"}


def consent_path(vault_path: Path | None = None) -> Path:
    path = vault_path or store_path()
    return path.parent / "consents.json"


@contextmanager
def _state_lock(path: Path):
    lock_path = path.with_suffix(path.suffix + ".lock")
    with open_private_lock(lock_path) as handle:
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
    source: str,
    human_operated: bool,
    purpose_binding: str | None = None,
) -> dict[str, Any]:
    if purpose_binding is None:
        normalized_purpose = _normalize_purpose(purpose)
        purpose_binding = _purpose_binding(normalized_purpose)
        display_purpose = _clean_text(normalized_purpose)
    else:
        purpose_binding = _validate_purpose_binding(purpose_binding)
        display_purpose = _validate_stored_purpose(purpose)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    expires_at = now + timedelta(seconds=max(1, ttl_seconds))
    return {
        "id": "c_" + secrets.token_urlsafe(18),
        "action": action,
        "key": key,
        "purpose": display_purpose,
        "purpose_binding": purpose_binding,
        "issued_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "used_at": "",
        "actor": actor,
        "source": source,
        "human_operated": bool(human_operated),
    }


def _load_state(path: Path) -> dict[str, Any]:
    if not private_file_exists(path):
        return {"version": 1, "grants": [], "requests": []}
    payload = read_private_json(path)
    if not isinstance(payload, dict):
        raise ConsentError("consent state is invalid")
    payload.setdefault("version", 1)
    payload.setdefault("grants", [])
    payload.setdefault("requests", [])
    requests = payload["requests"]
    if isinstance(requests, list):
        for request in requests:
            if isinstance(request, dict):
                _validate_request_id(request.get("id"))
                _validate_stored_purpose(request.get("purpose"))
                if "purpose_binding" in request:
                    _validate_purpose_binding(request.get("purpose_binding"))
    grants = payload["grants"]
    if isinstance(grants, list):
        for grant in grants:
            if isinstance(grant, dict):
                _validate_stored_purpose(grant.get("purpose"))
                if "purpose_binding" in grant:
                    _validate_purpose_binding(grant.get("purpose_binding"))
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
    source: str = "direct_grant",
    human_operated: bool = True,
) -> dict[str, Any]:
    grant = _build_grant(
        action=action,
        key=key,
        purpose=purpose,
        ttl_seconds=ttl_seconds,
        actor=actor,
        source=source,
        human_operated=human_operated,
    )
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
        source=source,
        human_operated=human_operated,
    )
    return _public_record(grant)


def create_consent_request(
    *,
    vault_path: Path,
    action: str,
    key: str,
    purpose: str,
    actor: str = "cli",
) -> dict[str, Any]:
    normalized_purpose = _normalize_purpose(purpose)
    request = {
        "id": "r_" + secrets.token_urlsafe(18),
        "action": action,
        "key": key,
        "purpose": _clean_text(normalized_purpose),
        "purpose_binding": _purpose_binding(normalized_purpose),
        "requested_at": now_iso(),
        "resolved_at": "",
        "status": "pending",
        "actor": actor,
        "source": "request",
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
        source="request",
        human_operated=False,
        request_id=request["id"],
    )
    return _public_record(request)


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
    request_id = _validate_request_id(request_id)
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
            request["resolved_by"] = actor
            request["resolution_source"] = "request_approval"
            if not approve:
                request["status"] = "denied"
                _write_state(path, state)
                audit_event = {
                    "action": "consent_deny",
                    "key": str(request.get("key") or ""),
                    "purpose": str(request.get("purpose") or ""),
                    "outcome": "denied",
                    "consent_id": request_id,
                    "source": "request_denial",
                    "human_operated": actor in {"cli", "gui"},
                    "request_id": request_id,
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
                source="request_approval",
                human_operated=actor in {"cli", "gui"},
                purpose_binding=_validate_purpose_binding(request.get("purpose_binding")),
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
                "source": "request_approval",
                "human_operated": actor in {"cli", "gui"},
                "request_id": request_id,
            }
            result = {"request_id": request_id, "grant": _public_record(grant)}
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
    normalized_purpose = _normalize_purpose(purpose)
    provided_binding = _purpose_binding(normalized_purpose)
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
            stored_binding = _validate_purpose_binding(grant.get("purpose_binding"))
            if not secrets.compare_digest(stored_binding, provided_binding):
                raise ConsentError("consent token purpose mismatch")
            expires_at = _parse_expires_at(grant.get("expires_at"))
            if datetime.now(timezone.utc).replace(microsecond=0) > expires_at:
                raise ConsentError("consent token has expired")
            grant["used_at"] = now_iso()
            _write_state(path, state)
            result = _public_record(grant)
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
