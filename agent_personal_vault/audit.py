"""Raw-free audit logging."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from .vault import ensure_private_dir, now_iso, store_path


DEFAULT_LIMIT = 20
EMAIL_TOKEN_STRIP = ".,;:()[]{}<>\"'"
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
        any(_looks_like_email_token(token) for token in text.split())
        or _looks_like_grouped_number(text)
        or _looks_like_ungrouped_phone(text)
        or bool(LOCAL_PATH_RE.search(text))
        or bool(DATE_LIKE_RE.search(text))
        or bool(POSTAL_CODE_RE.search(text))
        or bool(LONG_IDENTIFIER_RE.search(text))
        or _looks_like_japanese_address(text)
        or _looks_like_japanese_name_pair(text)
    )


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
    source: str | None = None,
    human_operated: bool | None = None,
    request_id: str | None = None,
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
    if source is not None:
        event["source"] = _clean_text(source)
    if human_operated is not None:
        event["human_operated"] = bool(human_operated)
    if request_id is not None:
        event["request_id"] = _clean_text(request_id)
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
