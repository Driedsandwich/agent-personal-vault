"""Core storage and normalization logic."""

from __future__ import annotations

import json
import os
import re
import shlex
import stat
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback path
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt
except ImportError:  # pragma: no cover - Unix fallback path
    msvcrt = None  # type: ignore[assignment]

from .crypto_store import (
    LATEST_ENCRYPTION_PROFILE,
    EncryptionProfile,
    decrypt_store_payload,
    encryption_profile as payload_encryption_profile,
    encrypt_store_payload,
    is_encrypted_payload,
)
from .migration_guard import kdf_write_guard
from .private_io import (
    ensure_private_directory,
    lexical_absolute_path,
    open_private_lock,
    private_file_exists,
    private_file_stat,
    read_private_json,
    write_private_json,
)
from .schemas import DERIVED_FIELDS, FieldSpec, SCHEMAS
from .resource_limits import MAX_FIELD_VALUE_BYTES, require_text_limit

APP_NAME = "agent-personal-vault"
DEFAULT_SCHEMA = "job_hunting_profile"


class VaultConflictError(ValueError):
    """Raised when a stale in-memory vault would overwrite a newer revision."""


SYNC_PATH_MARKERS = {
    "dropbox": "Dropbox",
    "onedrive": "OneDrive",
    "google drive": "Google Drive",
    "googledrive": "Google Drive",
    "icloud drive": "iCloud Drive",
    "mobile documents": "iCloud Drive",
    "clouddocs": "iCloud Drive",
    "box drive": "Box",
    "box sync": "Box",
    "creative cloud files": "Adobe Creative Cloud",
    "nextcloud": "Nextcloud",
    "synologydrive": "Synology Drive",
    "synology drive": "Synology Drive",
    "mega": "MEGA",
    "resilio sync": "Resilio Sync",
}

TASK_HINTS = [
    {
        "name": "full_name",
        "keywords": ("identity", "name", "氏名", "名前", "本人"),
        "keys": ("FULL_NAME",),
        "reason": "a full name is the narrow candidate for a name request",
    },
    {
        "name": "full_name_kana",
        "keywords": ("name kana", "phonetic name", "ふりがな", "フリガナ", "氏名カナ", "名前カナ"),
        "keys": ("FULL_NAME_KANA",),
        "reason": "a phonetic full name is the narrow candidate for a kana request",
    },
    {
        "name": "birth_date",
        "keywords": ("birth date", "date of birth", "birthday", "生年月日", "誕生日"),
        "keys": ("BIRTH_DATE",),
        "reason": "a birth date is the narrow candidate for a birth-date request",
    },
    {
        "name": "postal_code",
        "keywords": ("postal code", "zip code", "郵便番号"),
        "keys": ("POSTAL_CODE",),
        "reason": "a postal code is the narrow candidate for a postal-code request",
    },
    {
        "name": "address",
        "keywords": ("address", "住所"),
        "keys": ("ADDRESS",),
        "reason": "the submission address is the narrow candidate for an address request",
    },
    {
        "name": "phone",
        "keywords": ("phone", "telephone", "電話", "電話番号"),
        "keys": ("PHONE",),
        "reason": "a phone number is the narrow candidate for a phone request",
    },
    {
        "name": "email",
        "keywords": ("email address", "e-mail address", "email", "e-mail", "メール", "メールアドレス"),
        "keys": ("EMAIL",),
        "reason": "an email address is the narrow candidate for an email request",
    },
    {
        "name": "graduation_period",
        "keywords": ("graduation period", "completion period", "卒業予定", "修了予定"),
        "keys": ("GRADUATION_PERIOD",),
        "reason": "the graduation period is the narrow candidate for an expected-completion request",
    },
    {
        "name": "school_type",
        "keywords": ("school type", "学校区分"),
        "keys": ("SCHOOL_TYPE",),
        "reason": "the school type is the narrow candidate for a school-type request",
    },
    {
        "name": "academic_field_type",
        "keywords": ("academic field type", "文理区分"),
        "keys": ("ACADEMIC_FIELD_TYPE",),
        "reason": "the academic field type is the narrow candidate for a field-type request",
    },
    {
        "name": "university_name",
        "keywords": ("university name", "大学名"),
        "keys": ("UNIVERSITY_NAME",),
        "reason": "the university name is the narrow candidate for a university-name request",
    },
    {
        "name": "faculty_name",
        "keywords": ("faculty name", "学部名"),
        "keys": ("FACULTY_NAME",),
        "reason": "the faculty name is the narrow candidate for a faculty request",
    },
    {
        "name": "department_name",
        "keywords": ("department name", "学科名"),
        "keys": ("DEPARTMENT_NAME",),
        "reason": "the department name is the narrow candidate for a department request",
    },
    {
        "name": "graduate_school_name",
        "keywords": ("graduate school name", "大学院名", "研究科名"),
        "keys": ("GRADUATE_SCHOOL_NAME",),
        "reason": "the graduate-school name is the narrow candidate for a graduate-school request",
    },
    {
        "name": "graduate_major_name",
        "keywords": ("graduate major", "専攻名"),
        "keys": ("GRADUATE_MAJOR_NAME",),
        "reason": "the graduate major is the narrow candidate for a major request",
    },
    {
        "name": "degree",
        "keywords": ("degree", "学位"),
        "keys": ("DEGREE",),
        "reason": "the degree is the narrow candidate for a degree request",
    },
    {
        "name": "university_enrollment_date",
        "keywords": ("university enrollment date", "大学入学年月"),
        "keys": ("ENROLLMENT_DATE",),
        "reason": "the university enrollment date is the narrow candidate for that date request",
    },
    {
        "name": "university_completion_date",
        "keywords": ("university completion date", "大学卒業年月"),
        "keys": ("COMPLETION_DATE",),
        "reason": "the university completion date is the narrow candidate for that date request",
    },
    {
        "name": "graduate_enrollment_date",
        "keywords": ("graduate enrollment date", "大学院入学年月"),
        "keys": ("GRADUATE_ENROLLMENT_DATE",),
        "reason": "the graduate enrollment date is the narrow candidate for that date request",
    },
    {
        "name": "graduate_completion_date",
        "keywords": ("graduate completion date", "大学院修了年月"),
        "keys": ("GRADUATE_COMPLETION_DATE",),
        "reason": "the graduate completion date is the narrow candidate for that date request",
    },
    {
        "name": "high_school_name",
        "keywords": ("high school name", "高校名"),
        "keys": ("HIGH_SCHOOL_NAME",),
        "reason": "the high-school name is the narrow candidate for a high-school request",
    },
    {
        "name": "high_school_graduation_date",
        "keywords": ("high school graduation date", "高校卒業年月"),
        "keys": ("HIGH_SCHOOL_GRADUATION_DATE",),
        "reason": "the high-school graduation date is the narrow candidate for that date request",
    },
    {
        "name": "qualifications",
        "keywords": ("qualification", "license", "資格", "免許", "certification"),
        "keys": ("QUALIFICATIONS",),
        "reason": "qualification fields are commonly needed for credential sections",
    },
    {
        "name": "photo",
        "keywords": ("photo", "picture", "image", "顔写真", "写真", "画像"),
        "keys": ("FACE_PHOTO_PATH",),
        "reason": "photo path is commonly needed when a form requests a profile image",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def local_user_path(value: str | Path) -> Path:
    """Normalize a path explicitly supplied by the local operator."""

    # lgtm[py/path-injection]
    return lexical_absolute_path(Path(value))


def default_data_dir() -> Path:
    override = os.environ.get("AGENT_PERSONAL_VAULT_HOME")
    if override:
        # lgtm[py/path-injection]
        return local_user_path(override)
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        # lgtm[py/path-injection]
        return local_user_path(xdg) / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def store_path(data_dir: Path | None = None) -> Path:
    return (data_dir or default_data_dir()) / "vault.json"


def likely_synced_path_labels(path: Path) -> list[str]:
    """Return best-effort labels for common cloud/sync folder path markers."""

    labels: list[str] = []
    for part in path.expanduser().parts:
        normalized = part.lower().replace("_", " ").replace("-", " ")
        for marker, label in SYNC_PATH_MARKERS.items():
            if marker in normalized and label not in labels:
                labels.append(label)
    return labels


def store_path_warnings(path: Path) -> list[str]:
    labels = likely_synced_path_labels(path)
    if not labels:
        return []
    joined = ", ".join(labels)
    return [
        "store path appears to be under a common synced/cloud-backed folder "
        f"({joined}). Plaintext JSON can persist in backups, sync targets, snapshots, or manual copies; "
        "use dummy data, move the store, or enable optional encryption before storing real data."
    ]


def default_passphrase() -> str | None:
    return os.environ.get("AGENT_PERSONAL_VAULT_PASSPHRASE")


def blank_store(schema_name: str = DEFAULT_SCHEMA) -> dict:
    schema = get_schema(schema_name)
    return {
        "classification": "LOCAL_PRIVATE",
        "sensitivity": "high",
        "app": APP_NAME,
        "schema": schema_name,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "revision": 0,
        "fields": {key: "" for key in schema},
    }


def validate_store_shape(store: object) -> dict:
    if not isinstance(store, dict):
        raise ValueError("vault store is invalid")
    schema = store.get("schema")
    if schema is not None and not isinstance(schema, str):
        raise ValueError("vault store is invalid")
    fields = store.get("fields")
    if fields is not None and not isinstance(fields, dict):
        raise ValueError("vault store is invalid")
    if isinstance(fields, dict):
        for value in fields.values():
            if not isinstance(value, str):
                raise ValueError("vault store is invalid")
            require_text_limit(value, max_bytes=MAX_FIELD_VALUE_BYTES, label="vault field")
    revision = store.get("revision", 0)
    if type(revision) is not int or revision < 0:
        raise ValueError("vault store is invalid")
    return store


def store_revision(store: dict) -> int:
    validate_store_shape(store)
    return int(store.get("revision", 0))


@contextmanager
def _store_lock(path: Path):
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


def get_schema(schema_name: str) -> dict[str, FieldSpec]:
    try:
        return SCHEMAS[schema_name]
    except KeyError as exc:
        allowed = ", ".join(sorted(SCHEMAS))
        raise ValueError(f"Unknown schema: {schema_name}. Allowed: {allowed}") from exc


def ensure_private_dir(path: Path) -> None:
    ensure_private_directory(path)


def write_json_private(path: Path, payload: dict) -> None:
    """Write JSON through the owner-private storage boundary."""

    write_private_json(path, payload)


def _read_normalized_store(
    path: Path,
    schema_name: str,
    passphrase: str | None,
) -> tuple[dict, EncryptionProfile | None, str | None, bool]:
    payload = read_private_json(path)
    encrypted_payload = is_encrypted_payload(payload)
    profile = payload_encryption_profile(payload) if encrypted_payload else None
    effective_passphrase = passphrase or default_passphrase()
    if encrypted_payload:
        if not effective_passphrase:
            raise ValueError("Encrypted vault requires AGENT_PERSONAL_VAULT_PASSPHRASE or an explicit passphrase.")
        store = validate_store_shape(decrypt_store_payload(payload, effective_passphrase))
    else:
        store = validate_store_shape(payload)

    schema = get_schema(str(store.get("schema") or schema_name))
    store = dict(store)
    fields = dict(store.get("fields", {}))
    store["fields"] = fields
    changed = "revision" not in store
    store.setdefault("revision", 0)
    for key in schema:
        if key not in fields:
            fields[key] = ""
            changed = True
    for key in DERIVED_FIELDS:
        if key in fields:
            fields.pop(key, None)
            changed = True
    return store, profile, effective_passphrase, changed


def read_store(
    path: Path | None = None,
    schema_name: str = DEFAULT_SCHEMA,
    passphrase: str | None = None,
) -> dict:
    """Read and normalize a store in memory without creating or rewriting files."""

    path = path or store_path()
    store, _profile, _passphrase, _changed = _read_normalized_store(path, schema_name, passphrase)
    return store


def load_store(create: bool = False, path: Path | None = None, schema_name: str = DEFAULT_SCHEMA, passphrase: str | None = None) -> dict:
    path = path or store_path()
    ensure_private_dir(path.parent)
    if not private_file_exists(path):
        if not create:
            raise FileNotFoundError(f"Vault does not exist: {path}")
        store = blank_store(schema_name)
        write_store(store, path)
        return store

    store, profile, effective_passphrase, changed = _read_normalized_store(path, schema_name, passphrase)
    if changed:
        write_store(store, path, passphrase=effective_passphrase, encrypted=profile is not None, profile=profile)
    return store


def write_store(
    store: dict,
    path: Path | None = None,
    passphrase: str | None = None,
    encrypted: bool | None = None,
    *,
    allow_weak_passphrase: bool = False,
    profile: EncryptionProfile | None = None,
) -> None:
    path = path or store_path()
    ensure_private_dir(path.parent)
    expected_revision = store_revision(store)
    with kdf_write_guard(path):
        with _store_lock(path):
            existing_encrypted = False
            existing_profile: EncryptionProfile | None = None
            current_revision = 0
            if private_file_exists(path):
                existing_payload = read_private_json(path)
                existing_encrypted = is_encrypted_payload(existing_payload)
                if existing_encrypted:
                    existing_profile = payload_encryption_profile(existing_payload)
                    effective_passphrase = passphrase or default_passphrase()
                    if not effective_passphrase:
                        raise ValueError(
                            "Encrypted vault write requires AGENT_PERSONAL_VAULT_PASSPHRASE or an explicit passphrase."
                        )
                    existing_store = validate_store_shape(decrypt_store_payload(existing_payload, effective_passphrase))
                else:
                    existing_store = validate_store_shape(existing_payload)
                current_revision = store_revision(existing_store)
            if current_revision != expected_revision:
                raise VaultConflictError("vault changed; reload and retry")

            next_store = dict(store)
            next_store["fields"] = dict(store.get("fields", {}))
            next_store["updated_at"] = now_iso()
            next_store["revision"] = current_revision + 1
            if encrypted is None:
                encrypted = existing_encrypted
            payload = next_store
            if encrypted:
                effective_passphrase = passphrase or default_passphrase()
                if not effective_passphrase:
                    raise ValueError(
                        "Encrypted vault write requires AGENT_PERSONAL_VAULT_PASSPHRASE or an explicit passphrase."
                    )
                selected_profile = profile or existing_profile or LATEST_ENCRYPTION_PROFILE
                payload = encrypt_store_payload(
                    next_store,
                    effective_passphrase,
                    allow_weak_passphrase=allow_weak_passphrase or existing_encrypted,
                    profile=selected_profile,
                )
            write_json_private(path, payload)
            store["updated_at"] = next_store["updated_at"]
            store["revision"] = next_store["revision"]


def validate_key(key: str, schema_name: str = DEFAULT_SCHEMA) -> str:
    normalized = key.strip().upper()
    schema = get_schema(schema_name)
    if normalized not in schema and normalized not in DERIVED_FIELDS:
        allowed = ", ".join([*schema, *DERIVED_FIELDS])
        raise ValueError(f"Unknown key: {key}. Allowed: {allowed}")
    return normalized


def normalize_ascii(value: str) -> str:
    table = str.maketrans({
        **{chr(ord("０") + i): str(i) for i in range(10)},
        **{chr(ord("Ａ") + i): chr(ord("A") + i) for i in range(26)},
        **{chr(ord("ａ") + i): chr(ord("a") + i) for i in range(26)},
        "＠": "@",
        "．": ".",
        "＿": "_",
        "－": "-",
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "―": "-",
        "ー": "-",
        "−": "-",
    })
    return value.translate(table)


def normalize_postal_code(value: str) -> str:
    digits = re.sub(r"\D", "", normalize_ascii(value))
    if len(digits) == 7:
        return f"{digits[:3]}-{digits[3:]}"
    return normalize_ascii(value).strip()


def normalize_phone(value: str) -> str:
    text = normalize_ascii(value).strip()
    if not text:
        return ""
    if re.fullmatch(r"[0-9]+", text):
        if text.startswith("0") and len(text) in {10, 11}:
            return text
        raise ValueError("invalid phone number")
    if not re.fullmatch(r"[0-9]{2,4}-[0-9]{2,4}-[0-9]{3,4}", text):
        raise ValueError("invalid phone number")
    if not text.startswith("0") or len(text.replace("-", "")) not in {10, 11}:
        raise ValueError("invalid phone number")
    return text


def normalize_date_like(value: str) -> str:
    text = normalize_ascii(value).strip()
    if not text:
        return ""
    match = re.fullmatch(r"([0-9]{4})年([0-9]{1,2})月(?:([0-9]{1,2})日)?", text)
    if match is None:
        match = re.fullmatch(r"([0-9]{4})([/\.\- ])([0-9]{1,2})(?:\2([0-9]{1,2}))?", text)
        if match is not None:
            year, _separator, month, day = match.groups()
        else:
            compact = re.fullmatch(r"([0-9]{4})([0-9]{2})([0-9]{2})?", text)
            if compact is None:
                raise ValueError("invalid date value")
            year, month, day = compact.groups()
    else:
        year, month, day = match.groups()
    if not year or not month:
        raise ValueError("invalid date value")
    try:
        if day is not None:
            normalized = date(int(year), int(month), int(day))
            return normalized.isoformat()
        normalized_month = date(int(year), int(month), 1)
    except ValueError:
        raise ValueError("invalid date value") from None
    return f"{normalized_month.year:04d}-{normalized_month.month:02d}"


def normalize_value(key: str, value: str) -> str:
    require_text_limit(value, max_bytes=MAX_FIELD_VALUE_BYTES, label="vault field")
    if key == "POSTAL_CODE":
        return normalize_postal_code(value)
    if key == "PHONE":
        return normalize_phone(value)
    if key == "EMAIL":
        return normalize_ascii(value).strip().lower()
    if key in {
        "BIRTH_DATE",
        "ENROLLMENT_DATE",
        "GRADUATE_ENROLLMENT_DATE",
        "HIGH_SCHOOL_GRADUATION_DATE",
    }:
        return normalize_date_like(value)
    if key in {
        "FAMILY_NAME",
        "GIVEN_NAME",
        "FAMILY_NAME_KANA",
        "GIVEN_NAME_KANA",
        "PREFECTURE",
        "CITY_ADDRESS",
        "STREET_ADDRESS",
        "BUILDING_NAME",
        "ADDRESS",
    }:
        return re.sub(r"[ \t]+", " ", value).strip()
    return value


def derived_fields(fields: dict) -> dict[str, str]:
    family = str(fields.get("FAMILY_NAME", "")).strip()
    given = str(fields.get("GIVEN_NAME", "")).strip()
    family_kana = str(fields.get("FAMILY_NAME_KANA", "")).strip()
    given_kana = str(fields.get("GIVEN_NAME_KANA", "")).strip()
    return {
        "FULL_NAME": "　".join(part for part in [family, given] if part),
        "FULL_NAME_KANA": "　".join(part for part in [family_kana, given_kana] if part),
        "NAME_SEPARATOR": "全角スペース",
    }


def planning_hints(store: dict, task: str) -> dict:
    """Return conservative raw-free candidate keys for a task description."""
    query = " ".join(str(task).lower().split())[:240]
    schema = get_schema(str(store["schema"]))
    fields = store.get("fields", {})
    matched = []
    seen: set[str] = set()
    remaining_query = query
    specific_first = sorted(
        enumerate(TASK_HINTS),
        key=lambda item: max(len(keyword) for keyword in item[1]["keywords"]),
        reverse=True,
    )
    selected_hints = []
    for original_index, hint in specific_first:
        keywords = sorted((keyword.lower() for keyword in hint["keywords"]), key=len, reverse=True)
        matched_keyword = next((keyword for keyword in keywords if keyword in remaining_query), None)
        if matched_keyword is None:
            continue
        selected_hints.append((original_index, hint))
        for keyword in keywords:
            remaining_query = remaining_query.replace(keyword, " ")

    for _, hint in sorted(selected_hints):
        keys = []
        for key in hint["keys"]:
            if key in seen:
                continue
            seen.add(key)
            if key in DERIVED_FIELDS:
                keys.append(
                    {
                        "key": key,
                        "label": DERIVED_FIELDS[key],
                        "group": "derived",
                        "derived": True,
                        "filled": bool(derived_fields(fields).get(key, "").strip()),
                    }
                )
                continue
            spec = schema.get(key)
            if spec is None:
                continue
            keys.append(
                {
                    "key": key,
                    "label": spec.label,
                    "group": spec.group,
                    "derived": False,
                    "filled": bool(str(fields.get(key, "")).strip()),
                }
            )
        if keys:
            matched.append(
                {
                    "hint": hint["name"],
                    "reason": hint["reason"],
                    "candidate_keys": keys,
                }
            )
    return {
        "task": "[redacted]" if query else "",
        "task_echoed": False,
        "raw_values_included": False,
        "conservative": True,
        "matched_hints": matched,
        "raw_access_next_step": "Request one key at a time with consent only after the user confirms it is needed.",
    }


def masked(value: str) -> str:
    if not value:
        return "(empty)"
    return f"(filled, {len(value)} chars)"


def check_summary(store: dict, path: Path) -> dict:
    schema = get_schema(str(store["schema"]))
    fields = store.get("fields", {})
    missing = [key for key, spec in schema.items() if not spec.optional and not str(fields.get(key, "")).strip()]
    file_info = private_file_stat(path)
    return {
        "path": str(path),
        "mode": oct(stat.S_IMODE(file_info.st_mode)) if file_info is not None else "missing",
        "schema": store["schema"],
        "registered": sum(bool(str(fields.get(key, "")).strip()) for key in schema),
        "total": len(schema),
        "required_missing": missing,
    }


def agent_context(store: dict, include_path: bool = False, path: Path | None = None, task: str | None = None) -> dict:
    """Return metadata for an AI agent without raw personal values."""
    schema = get_schema(str(store["schema"]))
    fields = store.get("fields", {})
    required_missing = [
        {"key": key, "label": spec.label, "group": spec.group}
        for key, spec in schema.items()
        if not spec.optional and not str(fields.get(key, "")).strip()
    ]
    filled_keys = [
        {"key": key, "label": spec.label, "group": spec.group}
        for key, spec in schema.items()
        if str(fields.get(key, "")).strip()
    ]
    context = {
        "app": APP_NAME,
        "schema": store["schema"],
        "classification": "LOCAL_PRIVATE_METADATA",
        "raw_values_included": False,
        "registered": len(filled_keys),
        "total": len(schema),
        "required_missing": required_missing,
        "filled_keys": filled_keys,
        "derived_keys": [{"key": key, "label": label} for key, label in DERIVED_FIELDS.items()],
        "safe_default_command": "agent-personal-vault context",
        "raw_access_rule": "Use get <KEY> only for the minimum required key, and never paste raw values into logs, public artifacts, remote agents, or external services without explicit user approval.",
        "final_action_boundary": [
            "external upload",
            "form submission",
            "account registration",
            "email sending",
            "public sharing",
            "repository push",
        ],
    }
    if include_path and path is not None:
        context["store_path"] = str(path)
    if task:
        context["planning_hints"] = planning_hints(store, task)
    return context


def schema_context(schema_name: str = DEFAULT_SCHEMA) -> dict:
    """Return schema metadata without any stored user values."""
    schema = get_schema(schema_name)
    return {
        "app": APP_NAME,
        "schema": schema_name,
        "classification": "PUBLIC_SCHEMA_METADATA",
        "raw_values_included": False,
        "fields": [
            {
                "key": key,
                "label": spec.label,
                "group": spec.group,
                "sensitivity": spec.sensitivity,
                "optional": spec.optional,
                "input_type": spec.input_type,
                "has_options": bool(spec.options),
            }
            for key, spec in schema.items()
        ],
        "derived_fields": [{"key": key, "label": label} for key, label in DERIVED_FIELDS.items()],
    }


def export_env_lines(store: dict) -> list[str]:
    schema = get_schema(str(store["schema"]))
    combined = {**store.get("fields", {}), **derived_fields(store.get("fields", {}))}
    lines = []
    for key in [*schema, *DERIVED_FIELDS]:
        value = str(combined.get(key, ""))
        if value:
            lines.append(f"export APV_{key}={shlex.quote(value)}")
    return lines
