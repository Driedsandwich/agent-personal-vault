"""Command line interface."""

from __future__ import annotations

import argparse
import json
import os
import sys
from getpass import getpass
from pathlib import Path

from .audit import audit_summary, read_audit_events, write_audit_event
from .consent import (
    ConsentError,
    create_consent_request,
    issue_consent,
    list_consent_requests,
    list_consents,
    resolve_consent_request,
    validate_and_consume_consent,
)
from .crypto_store import ENCRYPTED_STORAGE, EncryptionUnavailableError, cryptography_available, is_encrypted_payload
from .schemas import DERIVED_FIELDS
from .vault import (
    DEFAULT_SCHEMA,
    agent_context,
    check_summary,
    derived_fields,
    export_env_lines,
    get_schema,
    load_store,
    masked,
    normalize_value,
    schema_context,
    store_path,
    validate_key,
    write_store,
)


def resolve_path(args: argparse.Namespace) -> Path:
    return Path(args.store).expanduser() if args.store else store_path()


def read_passphrase(prompt: str = "Vault passphrase: ") -> str:
    env_value = os.environ.get("AGENT_PERSONAL_VAULT_PASSPHRASE")
    if env_value:
        return env_value
    return getpass(prompt)


def command_init(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(create=True, path=path, schema_name=args.schema)
    print(f"created_or_exists: {path}")
    print(f"schema: {store['schema']}")
    print("security: local file permissions only; data is not encrypted at rest by default")


def command_check(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(path=path)
    summary = check_summary(store, path)
    print(f"store: {summary['path']}")
    print(f"mode: {summary['mode']}")
    print(f"schema: {summary['schema']}")
    print(f"registered: {summary['registered']}/{summary['total']}")
    if summary["required_missing"]:
        print("required_missing:")
        schema = get_schema(store["schema"])
        for key in summary["required_missing"]:
            print(f"- {key}: {schema[key].label}")


def command_context(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(path=path)
    print(json.dumps(agent_context(store, include_path=args.include_path, path=path, task=args.task), ensure_ascii=False, indent=2))


def command_schema(args: argparse.Namespace) -> None:
    print(json.dumps(schema_context(args.schema), ensure_ascii=False, indent=2))


def command_list(args: argparse.Namespace) -> None:
    store = load_store(path=resolve_path(args))
    schema = get_schema(store["schema"])
    for key, spec in schema.items():
        value = str(store["fields"].get(key, ""))
        print(f"{key}\t{spec.label}\t{masked(value)}")


def command_get(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(path=path)
    key = validate_key(args.key, store["schema"])
    try:
        validate_and_consume_consent(
            vault_path=path,
            consent_id=args.consent_id,
            action="get",
            key=key,
            purpose=args.purpose,
        )
    except ConsentError as exc:
        write_audit_event(vault_path=path, actor="cli", action="get", key=key, purpose=args.purpose, outcome="denied")
        raise SystemExit(f"consent required: {exc}") from exc
    if key in DERIVED_FIELDS:
        value = derived_fields(store["fields"]).get(key, "")
    else:
        value = str(store["fields"].get(key, ""))
    if not value:
        raise SystemExit(f"{key} is empty")
    print(
        "# WARNING: this prints one raw personal value. Do not paste it into logs, public issues, or remote agents.",
        file=sys.stderr,
    )
    write_audit_event(
        vault_path=path,
        actor="cli",
        action="get",
        key=key,
        raw_returned=True,
        purpose=args.purpose,
        consent_id=args.consent_id,
    )
    print(value)


def command_set(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(create=True, path=path, schema_name=args.schema)
    key = validate_key(args.key, store["schema"])
    if key in DERIVED_FIELDS:
        raise SystemExit(f"{key} is derived. Set component fields instead.")
    value = sys.stdin.read().rstrip("\n") if args.stdin else getpass(f"{key} value: ")
    store["fields"][key] = normalize_value(key, value)
    write_store(store, path)
    write_audit_event(vault_path=path, actor="cli", action="set", key=key, purpose=args.purpose)
    print(f"saved: {key}")


def command_unset(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(path=path)
    key = validate_key(args.key, store["schema"])
    if key in DERIVED_FIELDS:
        raise SystemExit(f"{key} is derived. Clear component fields instead.")
    store["fields"][key] = ""
    write_store(store, path)
    write_audit_event(vault_path=path, actor="cli", action="unset", key=key, purpose=args.purpose)
    print(f"cleared: {key}")


def command_env(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(path=path)
    try:
        validate_and_consume_consent(
            vault_path=path,
            consent_id=args.consent_id,
            action="env",
            key="*",
            purpose=args.purpose,
        )
    except ConsentError as exc:
        write_audit_event(vault_path=path, actor="cli", action="env", key="*", purpose=args.purpose, outcome="denied")
        raise SystemExit(f"consent required: {exc}") from exc
    print(
        "# WARNING: this prints raw personal data. Do not paste it into logs, public issues, or remote agents.",
        file=sys.stderr,
    )
    lines = export_env_lines(store)
    write_audit_event(
        vault_path=path,
        actor="cli",
        action="env",
        key="*",
        raw_returned=bool(lines),
        purpose=args.purpose,
        consent_id=args.consent_id,
    )
    print("\n".join(lines))


def command_audit(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    if args.audit_command == "summary":
        print(json.dumps(audit_summary(path), ensure_ascii=False, indent=2, sort_keys=True))
        return
    for event in read_audit_events(path, limit=args.limit):
        print(json.dumps(event, ensure_ascii=False, sort_keys=True))


def command_encryption(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    encrypted = False
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            encrypted = is_encrypted_payload(json.load(handle))
    if args.encryption_command == "status":
        print(
            json.dumps(
                {
                    "store_exists": path.exists(),
                    "storage": ENCRYPTED_STORAGE if encrypted else "plain-json",
                    "encrypted": encrypted,
                    "cryptography_available": cryptography_available(),
                    "raw_values_included": False,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return
    try:
        if args.encryption_command == "encrypt":
            if encrypted:
                raise SystemExit("vault is already encrypted")
            store = load_store(path=path)
            passphrase = read_passphrase("New vault passphrase: ")
            confirm = read_passphrase("Confirm vault passphrase: ")
            if passphrase != confirm:
                raise SystemExit("passphrases do not match")
            write_store(store, path, passphrase=passphrase, encrypted=True)
            write_audit_event(vault_path=path, actor="cli", action="encrypt", purpose=args.purpose)
            print("encrypted: true")
            return
        if args.encryption_command == "decrypt":
            if not encrypted:
                raise SystemExit("vault is not encrypted")
            passphrase = read_passphrase()
            store = load_store(path=path, passphrase=passphrase)
            write_store(store, path, encrypted=False)
            write_audit_event(vault_path=path, actor="cli", action="decrypt", purpose=args.purpose)
            print("encrypted: false")
            return
    except EncryptionUnavailableError as exc:
        raise SystemExit(str(exc)) from exc


def command_consent(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    if args.consent_command == "grant":
        key = "*" if args.action == "env" else validate_key(args.key, load_store(path=path)["schema"])
        grant = issue_consent(
            vault_path=path,
            action=args.action,
            key=key,
            purpose=args.purpose,
            ttl_seconds=args.ttl_seconds,
        )
        print(json.dumps(grant, ensure_ascii=False, indent=2, sort_keys=True))
        return
    if args.consent_command == "request":
        key = "*" if args.action == "env" else validate_key(args.key, load_store(path=path)["schema"])
        request = create_consent_request(vault_path=path, action=args.action, key=key, purpose=args.purpose)
        print(json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True))
        return
    if args.consent_command == "requests":
        for request in list_consent_requests(path, include_resolved=args.include_resolved):
            print(json.dumps(request, ensure_ascii=False, sort_keys=True))
        return
    if args.consent_command == "approve":
        result = resolve_consent_request(vault_path=path, request_id=args.request_id, approve=True, ttl_seconds=args.ttl_seconds)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return
    if args.consent_command == "deny":
        result = resolve_consent_request(vault_path=path, request_id=args.request_id, approve=False)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return
    for grant in list_consents(path, include_used=args.include_used):
        print(json.dumps(grant, ensure_ascii=False, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Alpha local personal-data utility for AI agents.")
    parser.add_argument("--store", help="Override vault path. Defaults to AGENT_PERSONAL_VAULT_HOME or XDG data dir.")
    parser.add_argument("--schema", default=DEFAULT_SCHEMA, help="Schema name for init/set when creating a vault.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func, help_text in [
        ("init", command_init, "Create the local private vault."),
        ("check", command_check, "Show metadata and missing required fields without raw values."),
        ("context", command_context, "Print raw-free JSON metadata for AI agents."),
        ("schema", command_schema, "Print raw-free JSON schema metadata."),
        ("list", command_list, "Show all keys with masked values."),
        ("env", command_env, "Print shell export lines for non-empty values."),
    ]:
        cmd = sub.add_parser(name, help=help_text)
        if name == "context":
            cmd.add_argument("--include-path", action="store_true", help="Include the local store path in JSON output.")
            cmd.add_argument("--task", help="Optional raw-free task description for minimum-key planning hints.")
        if name == "env":
            cmd.add_argument("--purpose", required=True, help="Raw access purpose. Stored in audit log without raw values.")
            cmd.add_argument("--consent-id", required=True, help="One-time consent token from consent grant.")
        cmd.set_defaults(func=func)
    get = sub.add_parser("get", help="Print one raw value. Use only for the minimum required key.")
    get.add_argument("key")
    get.add_argument("--purpose", required=True, help="Raw access purpose. Stored in audit log without raw values.")
    get.add_argument("--consent-id", required=True, help="One-time consent token from consent grant.")
    get.set_defaults(func=command_get)
    set_cmd = sub.add_parser("set", help="Set one value without putting it in shell history.")
    set_cmd.add_argument("key")
    set_cmd.add_argument("--stdin", action="store_true", help="Read value from stdin.")
    set_cmd.add_argument("--purpose", required=True, help="Change purpose. Stored in audit log without raw values.")
    set_cmd.set_defaults(func=command_set)
    unset = sub.add_parser("unset", help="Clear one value.")
    unset.add_argument("key")
    unset.add_argument("--purpose", required=True, help="Change purpose. Stored in audit log without raw values.")
    unset.set_defaults(func=command_unset)
    audit = sub.add_parser("audit", help="Inspect raw-free local audit metadata.")
    audit_sub = audit.add_subparsers(dest="audit_command", required=True)
    audit_tail = audit_sub.add_parser("tail", help="Print recent audit events as JSON lines.")
    audit_tail.add_argument("--limit", type=int, default=20)
    audit_tail.set_defaults(func=command_audit)
    audit_summary_cmd = audit_sub.add_parser("summary", help="Print audit counts without raw values.")
    audit_summary_cmd.set_defaults(func=command_audit)
    encryption = sub.add_parser("encryption", help="Inspect or migrate the local vault storage encryption.")
    encryption_sub = encryption.add_subparsers(dest="encryption_command", required=True)
    encryption_status = encryption_sub.add_parser("status", help="Show encryption metadata without reading raw values.")
    encryption_status.set_defaults(func=command_encryption)
    encryption_encrypt = encryption_sub.add_parser("encrypt", help="Encrypt the existing local vault with optional cryptography support.")
    encryption_encrypt.add_argument("--purpose", required=True, help="Raw-free migration purpose. Stored in audit log.")
    encryption_encrypt.set_defaults(func=command_encryption)
    encryption_decrypt = encryption_sub.add_parser("decrypt", help="Decrypt the local vault back to plain JSON.")
    encryption_decrypt.add_argument("--purpose", required=True, help="Raw-free migration purpose. Stored in audit log.")
    encryption_decrypt.set_defaults(func=command_encryption)
    consent = sub.add_parser("consent", help="Create or inspect raw-free consent tokens.")
    consent_sub = consent.add_subparsers(dest="consent_command", required=True)
    consent_grant = consent_sub.add_parser("grant", help="Grant a one-time raw access consent token.")
    consent_grant.add_argument("--action", choices=["get", "env"], required=True)
    consent_grant.add_argument("--key", default="*", help="Key for get. Use * for env.")
    consent_grant.add_argument("--purpose", required=True, help="Raw-free purpose that must match the later raw command.")
    consent_grant.add_argument("--ttl-seconds", type=int, default=300)
    consent_grant.set_defaults(func=command_consent)
    consent_request = consent_sub.add_parser("request", help="Queue a raw access request for human approval.")
    consent_request.add_argument("--action", choices=["get", "env"], required=True)
    consent_request.add_argument("--key", default="*", help="Key for get. Use * for env.")
    consent_request.add_argument("--purpose", required=True, help="Raw-free purpose for the requested access.")
    consent_request.set_defaults(func=command_consent)
    consent_requests = consent_sub.add_parser("requests", help="List pending consent requests without raw values.")
    consent_requests.add_argument("--include-resolved", action="store_true")
    consent_requests.set_defaults(func=command_consent)
    consent_approve = consent_sub.add_parser("approve", help="Approve a pending consent request and issue a one-time token.")
    consent_approve.add_argument("request_id")
    consent_approve.add_argument("--ttl-seconds", type=int, default=300)
    consent_approve.set_defaults(func=command_consent)
    consent_deny = consent_sub.add_parser("deny", help="Deny a pending consent request.")
    consent_deny.add_argument("request_id")
    consent_deny.set_defaults(func=command_consent)
    consent_list = consent_sub.add_parser("list", help="List unconsumed consent tokens without raw values.")
    consent_list.add_argument("--include-used", action="store_true")
    consent_list.set_defaults(func=command_consent)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
