"""Core storage and normalization logic."""

from __future__ import annotations

import json
import os
import re
import shlex
import stat
from datetime import datetime, timezone
from pathlib import Path

from .crypto_store import decrypt_store_payload, encrypt_store_payload, is_encrypted_payload
from .schemas import DERIVED_FIELDS, FieldSpec, SCHEMAS

APP_NAME = "agent-personal-vault"
DEFAULT_SCHEMA = "job_hunting_profile"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_data_dir() -> Path:
    override = os.environ.get("AGENT_PERSONAL_VAULT_HOME")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg).expanduser() / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def store_path(data_dir: Path | None = None) -> Path:
    return (data_dir or default_data_dir()) / "vault.json"


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
        "fields": {key: "" for key in schema},
    }


def get_schema(schema_name: str) -> dict[str, FieldSpec]:
    try:
        return SCHEMAS[schema_name]
    except KeyError as exc:
        allowed = ", ".join(sorted(SCHEMAS))
        raise ValueError(f"Unknown schema: {schema_name}. Allowed: {allowed}") from exc


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)


def enforce_file_mode(path: Path) -> None:
    if path.exists():
        os.chmod(path, 0o600)


def load_store(create: bool = False, path: Path | None = None, schema_name: str = DEFAULT_SCHEMA, passphrase: str | None = None) -> dict:
    path = path or store_path()
    ensure_private_dir(path.parent)
    if not path.exists():
        if not create:
            raise FileNotFoundError(f"Vault does not exist: {path}")
        store = blank_store(schema_name)
        write_store(store, path)
        return store

    enforce_file_mode(path)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    encrypted_payload = is_encrypted_payload(payload)
    effective_passphrase = passphrase or default_passphrase()
    if encrypted_payload:
        if not effective_passphrase:
            raise ValueError("Encrypted vault requires AGENT_PERSONAL_VAULT_PASSPHRASE or an explicit passphrase.")
        store = decrypt_store_payload(payload, effective_passphrase)
    else:
        store = payload

    schema = get_schema(str(store.get("schema") or schema_name))
    fields = store.setdefault("fields", {})
    changed = False
    for key in schema:
        if key not in fields:
            fields[key] = ""
            changed = True
    for key in DERIVED_FIELDS:
        if key in fields:
            fields.pop(key, None)
            changed = True
    if changed:
        write_store(store, path, passphrase=effective_passphrase, encrypted=encrypted_payload)
    return store


def write_store(store: dict, path: Path | None = None, passphrase: str | None = None, encrypted: bool | None = None) -> None:
    path = path or store_path()
    ensure_private_dir(path.parent)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    store["updated_at"] = now_iso()
    if encrypted is None:
        encrypted = False
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as handle:
                    encrypted = is_encrypted_payload(json.load(handle))
            except json.JSONDecodeError:
                encrypted = False
    payload = store
    if encrypted:
        effective_passphrase = passphrase or default_passphrase()
        if not effective_passphrase:
            raise ValueError("Encrypted vault write requires AGENT_PERSONAL_VAULT_PASSPHRASE or an explicit passphrase.")
        payload = encrypt_store_payload(store, effective_passphrase)
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.chmod(tmp_path, 0o600)
    tmp_path.replace(path)
    enforce_file_mode(path)


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
    digits = re.sub(r"\D", "", normalize_ascii(value))
    if len(digits) == 11:
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
    return normalize_ascii(value).strip()


def normalize_date_like(value: str) -> str:
    text = normalize_ascii(value).strip()
    match = re.match(r"^(\d{4})[年/.\- ]?(\d{1,2})(?:[月/.\- ]?(\d{1,2})日?)?$", text)
    if not match:
        return text
    year, month, day = match.groups()
    if day:
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return f"{year}-{month.zfill(2)}"


def normalize_value(key: str, value: str) -> str:
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


def masked(value: str) -> str:
    if not value:
        return "(empty)"
    return f"(filled, {len(value)} chars)"


def check_summary(store: dict, path: Path) -> dict:
    schema = get_schema(str(store["schema"]))
    fields = store.get("fields", {})
    missing = [key for key, spec in schema.items() if not spec.optional and not str(fields.get(key, "")).strip()]
    return {
        "path": str(path),
        "mode": oct(stat.S_IMODE(path.stat().st_mode)) if path.exists() else "missing",
        "schema": store["schema"],
        "registered": sum(bool(str(fields.get(key, "")).strip()) for key in schema),
        "total": len(schema),
        "required_missing": missing,
    }


def agent_context(store: dict, include_path: bool = False, path: Path | None = None) -> dict:
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
