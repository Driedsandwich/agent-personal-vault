"""Raw-free audit logging."""

from __future__ import annotations

import json
import re
import secrets
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .crypto_store import EncryptionProfile
from .migration_guard import kdf_write_guard

from .private_io import (
    exclusive_private_lock,
    private_file_exists,
)
from .resource_limits import MAX_AUDIT_BYTES, ResourceLimitError, validate_json_resources
from .sidecar_store import (
    PreparedSidecarWrite,
    commit_prepared_sidecar,
    prepare_sidecar_write,
    read_sidecar_bytes,
    validate_sidecar_passphrase_binding,
    write_sidecar_bytes,
)
from .vault import now_iso, store_path


DEFAULT_LIMIT = 20
OPERATION_ID_PATTERN = re.compile(r"o_[A-Za-z0-9_-]{24}")
OPERATION_STATES = frozenset({"prepared", "committed", "delivered", "rejected", "outcome_unknown"})
PURPOSE_CODES = frozenset(
    {
        "encryption_migration",
        "local_draft",
        "profile_cleanup",
        "profile_setup",
        "profile_update",
        "test_dummy",
    }
)
EMAIL_TOKEN_STRIP = ".,;:()[]{}<>\"'"
DOT_EQUIVALENTS = str.maketrans(
    {
        "。": ".",
        "｡": ".",
        "．": ".",
        "﹒": ".",
        "·": ".",
    }
)
JAPANESE_PREFECTURES = (
    "北海道",
    "青森県",
    "岩手県",
    "宮城県",
    "秋田県",
    "山形県",
    "福島県",
    "茨城県",
    "栃木県",
    "群馬県",
    "埼玉県",
    "千葉県",
    "東京都",
    "神奈川県",
    "新潟県",
    "富山県",
    "石川県",
    "福井県",
    "山梨県",
    "長野県",
    "岐阜県",
    "静岡県",
    "愛知県",
    "三重県",
    "滋賀県",
    "京都府",
    "大阪府",
    "兵庫県",
    "奈良県",
    "和歌山県",
    "鳥取県",
    "島根県",
    "岡山県",
    "広島県",
    "山口県",
    "徳島県",
    "香川県",
    "愛媛県",
    "高知県",
    "福岡県",
    "佐賀県",
    "長崎県",
    "熊本県",
    "大分県",
    "宮崎県",
    "鹿児島県",
    "沖縄県",
)
LOCAL_PATH_LITERAL_PREFIXES = ("/" + "Users/", "/home/", "/var/", "/tmp/")
LOCAL_PATH_REGEX_PREFIXES = (r"[A-Za-z]:\\", r"~[/\\]")
LOCAL_PATH_RE = re.compile(
    r"(?:^|\s)(?:"
    + "|".join(re.escape(prefix) for prefix in LOCAL_PATH_LITERAL_PREFIXES)
    + r"|"
    + "|".join(LOCAL_PATH_REGEX_PREFIXES)
    + r")"
)
DATE_LIKE_RE = re.compile(r"\b(?:19|20)\d{2}[-/.年](?:0?[1-9]|1[0-2])[-/.月](?:0?[1-9]|[12]\d|3[01])日?\b")
POSTAL_CODE_RE = re.compile(r"\b\d{3}-?\d{4}\b")
LONG_IDENTIFIER_RE = re.compile(r"\b\d{8,}\b")
JAPANESE_NAME_PAIR_RE = re.compile(r"(?<![一-龯々])([一-龯々]{1,4})[\s　]+([一-龯々]{1,4})(?![一-龯々])")
SPACED_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]{1,64}\s*@\s*"
    r"[A-Za-z0-9\-]+(?:\s*\.\s*[A-Za-z0-9\-]+)+\b"
)


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


def _looks_like_ungrouped_phone(text: str) -> bool:
    digits = "".join(char for char in text if char.isdigit())
    if len(digits) not in {10, 11}:
        return False
    return digits.startswith(("0", "81"))


def _looks_like_japanese_address(text: str) -> bool:
    if any(prefecture in text for prefecture in JAPANESE_PREFECTURES):
        return True
    return any(marker in text for marker in ("市", "区", "町", "村")) and any(marker in text for marker in ("丁目", "番地", "号"))


def _looks_like_japanese_name_pair(text: str) -> bool:
    for match in JAPANESE_NAME_PAIR_RE.finditer(text):
        left, right = match.groups()
        if left in {"氏名", "名前", "住所", "電話", "メール", "大学", "学校"}:
            continue
        if right in {"入力", "確認", "取得", "下書", "連絡", "項目"}:
            continue
        return True
    return False


def _looks_raw_like(text: str) -> bool:
    return (
        bool(SPACED_EMAIL_RE.search(text))
        or any(_looks_like_email_token(token) for token in text.split())
        or _looks_like_grouped_number(text)
        or _looks_like_ungrouped_phone(text)
        or bool(LOCAL_PATH_RE.search(text))
        or bool(DATE_LIKE_RE.search(text))
        or bool(POSTAL_CODE_RE.search(text))
        or bool(LONG_IDENTIFIER_RE.search(text))
        or _looks_like_japanese_address(text)
        or _looks_like_japanese_name_pair(text)
    )


def _detection_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).translate(DOT_EQUIVALENTS)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Cf")
    return " ".join(normalized.split())


def audit_path(vault_path: Path | None = None) -> Path:
    path = vault_path or store_path()
    return path.parent / "audit.jsonl"


def audit_lock_path(vault_path: Path | None = None) -> Path:
    return audit_path(vault_path).with_suffix(".jsonl.lock")


@contextmanager
def _audit_state_lock(vault_path: Path, *, allow_kdf_incomplete: bool = False):
    """Keep the global KDF guard before the audit lock on every path."""

    with kdf_write_guard(vault_path, allow_incomplete=allow_kdf_incomplete):
        with exclusive_private_lock(audit_lock_path(vault_path)):
            yield


def _clean_text(value: str | None) -> str:
    if value is None:
        return ""
    raw_text = str(value)
    detection_text = _detection_text(raw_text)
    if _looks_raw_like(detection_text):
        return "[redacted]"
    visible_text = "".join(
        f"[U+{ord(char):04X}]" if unicodedata.category(char) == "Cf" else char
        for char in raw_text
    )
    text = " ".join(visible_text.split())
    return text[:240]


def redact_purpose(value: str | None) -> str:
    """Project an arbitrary purpose into a finite, non-private display code."""

    if value is None:
        return ""
    normalized = " ".join(unicodedata.normalize("NFKC", str(value)).split())
    if not normalized:
        return ""
    if normalized in PURPOSE_CODES:
        return normalized
    return "[redacted]"


def redact_consent_id(value: str | None) -> str:
    text = "" if value is None else " ".join(str(value).split())
    if text.startswith("c_"):
        return "c_[redacted]"
    return _clean_text(text)


@dataclass(frozen=True)
class AuditOperation:
    """Durably correlate state, audit, and caller-delivery phases."""

    vault_path: Path
    operation_id: str
    actor: str
    action: str
    key: str | None = None
    purpose: str | None = None
    consent_id: str | None = None
    source: str | None = None
    human_operated: bool | None = None
    request_id: str | None = None
    sidecar_passphrase: str | None = field(default=None, repr=False)

    def _record(
        self,
        state: str,
        *,
        raw_returned: bool = False,
        outcome: str,
        action: str | None = None,
    ) -> dict[str, Any]:
        return write_audit_event(
            vault_path=self.vault_path,
            actor=self.actor,
            action=action or self.action,
            key=self.key,
            raw_returned=raw_returned,
            purpose=self.purpose,
            outcome=outcome,
            consent_id=self.consent_id,
            source=self.source,
            human_operated=self.human_operated,
            request_id=self.request_id,
            operation_id=self.operation_id,
            operation_state=state,
            sidecar_passphrase=self.sidecar_passphrase,
        )

    def committed(self) -> dict[str, Any]:
        return self._record("committed", outcome="committed")

    def delivered(self, *, raw_returned: bool = False, action: str | None = None) -> dict[str, Any]:
        return self._record("delivered", raw_returned=raw_returned, outcome="allowed", action=action)

    def rejected(self) -> dict[str, Any]:
        return self._record("rejected", outcome="denied")

    def outcome_unknown(self, *, raw_returned: bool = False) -> dict[str, Any]:
        return self._record("outcome_unknown", raw_returned=raw_returned, outcome="outcome_unknown")

    def try_delivered(self, *, raw_returned: bool = False, action: str | None = None) -> bool:
        """Finalize after caller output without leaking a late audit failure."""

        try:
            self.delivered(raw_returned=raw_returned, action=action)
        except Exception:
            return False
        return True

    def try_outcome_unknown(self, *, raw_returned: bool = False) -> bool:
        """Record an uncertain outcome when an earlier durable phase is already present."""

        try:
            self.outcome_unknown(raw_returned=raw_returned)
        except Exception:
            return False
        return True


def begin_audit_operation(
    *,
    vault_path: Path,
    actor: str,
    action: str,
    key: str | None = None,
    purpose: str | None = None,
    consent_id: str | None = None,
    source: str | None = None,
    human_operated: bool | None = None,
    request_id: str | None = None,
    sidecar_passphrase: str | None = None,
) -> AuditOperation:
    operation = AuditOperation(
        vault_path=vault_path,
        operation_id="o_" + secrets.token_urlsafe(18),
        actor=actor,
        action=action,
        key=key,
        purpose=purpose,
        consent_id=consent_id,
        source=source,
        human_operated=human_operated,
        request_id=request_id,
        sidecar_passphrase=sidecar_passphrase,
    )
    operation._record("prepared", outcome="pending")
    return operation


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
    source: str | None = None,
    human_operated: bool | None = None,
    request_id: str | None = None,
    operation_id: str | None = None,
    operation_state: str | None = None,
    sidecar_passphrase: str | None = None,
) -> dict[str, Any]:
    path = audit_path(vault_path)
    event: dict[str, Any] = {
        "timestamp": now_iso(),
        "actor": actor,
        "action": action,
        "key": key or "",
        "raw_returned": bool(raw_returned),
        "purpose": redact_purpose(purpose),
        "consent_id": redact_consent_id(consent_id),
        "outcome": outcome,
    }
    if source is not None:
        event["source"] = _clean_text(source)
    if human_operated is not None:
        event["human_operated"] = bool(human_operated)
    if request_id is not None:
        event["request_id"] = _clean_text(request_id)
    if operation_id is not None or operation_state is not None:
        if not isinstance(operation_id, str) or OPERATION_ID_PATTERN.fullmatch(operation_id) is None:
            raise ValueError("audit operation id is invalid")
        if operation_state not in OPERATION_STATES:
            raise ValueError("audit operation state is invalid")
        event["operation_id"] = operation_id
        event["operation_state"] = operation_state
    with _audit_state_lock(vault_path):
        existing = (
            read_sidecar_bytes(
                path,
                vault_path=vault_path,
                kind="audit",
                passphrase=sidecar_passphrase,
                max_bytes=MAX_AUDIT_BYTES,
            )
            if private_file_exists(path)
            else b""
        )
        line = (json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        if len(existing) + len(line) > MAX_AUDIT_BYTES:
            raise ResourceLimitError("private log has reached the supported size limit")
        write_sidecar_bytes(
            path,
            existing + line,
            vault_path=vault_path,
            kind="audit",
            passphrase=sidecar_passphrase,
        )
    return event


def prune_audit_events(
    vault_path: Path,
    *,
    retention_days: int = 90,
    now: datetime | None = None,
    passphrase: str | None = None,
) -> dict[str, int]:
    """Remove valid audit events older than the explicit retention window."""

    if type(retention_days) is not int or retention_days < 1:
        raise ValueError("audit retention days must be a positive integer")
    path = audit_path(vault_path)
    current_time = now or datetime.now(timezone.utc).replace(microsecond=0)
    if current_time.tzinfo is None:
        raise ValueError("audit pruning time must include a timezone")
    cutoff = current_time - timedelta(days=retention_days)
    with _audit_state_lock(vault_path):
        if not private_file_exists(path):
            return {"removed": 0, "retained": 0, "malformed_retained": 0}
        retained: list[bytes] = []
        removed = 0
        malformed_retained = 0
        for raw_line in read_sidecar_bytes(
            path,
            vault_path=vault_path,
            kind="audit",
            passphrase=passphrase,
            max_bytes=MAX_AUDIT_BYTES,
        ).splitlines(keepends=True):
            candidate = raw_line.strip()
            try:
                payload = json.loads(candidate.decode("utf-8"))
                timestamp = datetime.fromisoformat(str(payload["timestamp"])) if isinstance(payload, dict) else None
                if timestamp is None or timestamp.tzinfo is None:
                    raise ValueError
            except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
                retained.append(raw_line)
                malformed_retained += 1
                continue
            if timestamp < cutoff:
                removed += 1
            else:
                purpose = payload.get("purpose")
                sanitized_purpose = redact_purpose(purpose)
                if "purpose" in payload and purpose != sanitized_purpose:
                    payload["purpose"] = sanitized_purpose
                    retained.append((json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
                else:
                    retained.append(raw_line)
        write_sidecar_bytes(
            path,
            b"".join(retained),
            vault_path=vault_path,
            kind="audit",
            passphrase=passphrase,
        )
    return {"removed": removed, "retained": len(retained), "malformed_retained": malformed_retained}


def _read_audit_records(vault_path: Path, *, passphrase: str | None = None) -> tuple[list[dict[str, Any]], int]:
    path = audit_path(vault_path)
    if not private_file_exists(path):
        return [], 0
    events: list[dict[str, Any]] = []
    malformed_records = 0
    for raw_line in read_sidecar_bytes(
        path,
        vault_path=vault_path,
        kind="audit",
        passphrase=passphrase,
        max_bytes=MAX_AUDIT_BYTES,
    ).splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            payload = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            malformed_records += 1
            continue
        if not isinstance(payload, dict):
            malformed_records += 1
            continue
        if "purpose" in payload:
            payload["purpose"] = redact_purpose(payload.get("purpose"))
        events.append(payload)
    return events, malformed_records


def audit_tail(vault_path: Path, limit: int = DEFAULT_LIMIT, *, passphrase: str | None = None) -> dict[str, Any]:
    events, malformed_records = _read_audit_records(vault_path, passphrase=passphrase)
    if limit <= 0:
        selected = events
    else:
        selected = events[-limit:]
    return {
        "events": selected,
        "malformed_records_skipped": malformed_records,
        "integrity_warning": malformed_records > 0,
    }


def read_audit_events(vault_path: Path, limit: int = DEFAULT_LIMIT, *, passphrase: str | None = None) -> list[dict[str, Any]]:
    return list(audit_tail(vault_path, limit=limit, passphrase=passphrase)["events"])


def audit_summary(vault_path: Path, *, passphrase: str | None = None) -> dict[str, Any]:
    result = audit_tail(vault_path, limit=0, passphrase=passphrase)
    events = result["events"]
    by_action: dict[str, int] = {}
    raw_by_key: dict[str, int] = {}
    operation_states: dict[str, str] = {}
    for event in events:
        operation_id = event.get("operation_id")
        operation_state = event.get("operation_state")
        if isinstance(operation_id, str) and operation_state in OPERATION_STATES:
            operation_states[operation_id] = str(operation_state)
            if operation_state not in {"delivered", "rejected", "outcome_unknown"}:
                continue
        action = str(event.get("action") or "")
        by_action[action] = by_action.get(action, 0) + 1
        if event.get("raw_returned"):
            key = str(event.get("key") or "")
            raw_by_key[key] = raw_by_key.get(key, 0) + 1
    delivered_operations = sum(state == "delivered" for state in operation_states.values())
    rejected_operations = sum(state == "rejected" for state in operation_states.values())
    explicit_unknown = sum(state == "outcome_unknown" for state in operation_states.values())
    incomplete_operations = sum(state in {"prepared", "committed"} for state in operation_states.values())
    return {
        "events": len(events),
        "by_action": by_action,
        "raw_access_by_key": raw_by_key,
        "raw_values_included": False,
        "malformed_records_skipped": result["malformed_records_skipped"],
        "integrity_warning": result["integrity_warning"],
        "operation_outcomes": {
            "delivered": delivered_operations,
            "rejected": rejected_operations,
            "outcome_unknown": explicit_unknown + incomplete_operations,
        },
        "incomplete_operations": incomplete_operations,
    }


def migrate_audit_sidecar(vault_path: Path, *, encrypted: bool, passphrase: str) -> bool:
    """Rewrite the audit log with the selected sidecar protection."""

    prepared = prepare_audit_sidecar_migration(
        vault_path,
        encrypted=encrypted,
        passphrase=passphrase,
    )
    return commit_audit_sidecar_migration(prepared, vault_path=vault_path)


def prepare_audit_sidecar_migration(
    vault_path: Path,
    *,
    encrypted: bool,
    passphrase: str,
    profile: EncryptionProfile | None = None,
    allow_kdf_incomplete: bool = False,
) -> PreparedSidecarWrite | None:
    """Validate every audit row and encode the target sidecar without mutation."""

    path = audit_path(vault_path)
    passphrase = validate_sidecar_passphrase_binding(vault_path, passphrase) or passphrase
    with _audit_state_lock(vault_path, allow_kdf_incomplete=allow_kdf_incomplete):
        if not private_file_exists(path):
            return None
        plaintext = read_sidecar_bytes(
            path,
            vault_path=vault_path,
            kind="audit",
            passphrase=passphrase,
            max_bytes=MAX_AUDIT_BYTES,
        )
        for raw_line in plaintext.splitlines():
            if not raw_line.strip():
                continue
            try:
                event = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("audit state is invalid") from exc
            if not isinstance(event, dict):
                raise ValueError("audit state is invalid")
            validate_json_resources(event)
        return prepare_sidecar_write(
            path,
            plaintext,
            vault_path=vault_path,
            kind="audit",
            encrypted=encrypted,
            passphrase=passphrase,
            profile=profile,
        )


def commit_audit_sidecar_migration(
    prepared: PreparedSidecarWrite | None,
    *,
    vault_path: Path,
) -> bool:
    if prepared is None:
        return False
    with _audit_state_lock(vault_path):
        commit_prepared_sidecar(prepared)
    return True
