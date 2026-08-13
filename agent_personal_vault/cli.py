"""Command line interface."""

from __future__ import annotations

import argparse
import json
import os
import sys
from getpass import getpass
from pathlib import Path

from .audit import audit_path, audit_summary, audit_tail, begin_audit_operation, migrate_audit_sidecar, write_audit_event
from .consent import (
    MAX_TTL_SECONDS,
    ConsentError,
    consent_path,
    create_consent_request,
    issue_consent,
    list_consent_requests,
    list_consents,
    migrate_consent_sidecar,
    resolve_consent_request,
    prepare_consent_consumption,
)
from .crypto_store import (
    ENCRYPTED_STORAGE,
    EncryptionUnavailableError,
    cryptography_available,
    is_encrypted_payload,
    passphrase_strength_issue,
)
from .private_io import private_file_exists, read_private_json
from .privacy import DISPOSE_CONFIRMATION, dispose_private_state, prune_private_metadata
from .resource_limits import MAX_FIELD_VALUE_BYTES, ResourceLimitError
from .schemas import DERIVED_FIELDS
from .sidecar_store import sidecar_is_encrypted
from .vault import (
    DEFAULT_SCHEMA,
    agent_context,
    check_summary,
    derived_fields,
    export_env_lines,
    get_schema,
    local_user_path,
    load_store,
    masked,
    normalize_value,
    read_store,
    schema_context,
    store_path,
    store_path_warnings,
    validate_key,
    write_store,
)


def resolve_path(args: argparse.Namespace) -> Path:
    return local_user_path(args.store) if args.store else store_path()


def read_passphrase(prompt: str = "Vault passphrase: ") -> str:
    env_value = os.environ.get("AGENT_PERSONAL_VAULT_PASSPHRASE")
    if env_value:
        return env_value
    return getpass(prompt)


def print_store_path_warnings(path: Path) -> None:
    for warning in store_path_warnings(path):
        print(f"# WARNING: {warning}", file=sys.stderr)


def read_bounded_stdin() -> str:
    payload = sys.stdin.buffer.read(MAX_FIELD_VALUE_BYTES + 1)
    if len(payload) > MAX_FIELD_VALUE_BYTES:
        raise ResourceLimitError("vault field exceeds the supported size limit")
    return payload.decode("utf-8").rstrip("\n")


def command_init(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(create=True, path=path, schema_name=args.schema)
    print(f"created_or_exists: {path}")
    print(f"schema: {store['schema']}")
    print("security: local file permissions only; data is not encrypted at rest by default")
    print_store_path_warnings(path)


def command_check(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = read_store(path=path)
    summary = check_summary(store, path)
    print(f"store: {summary['path']}")
    print(f"mode: {summary['mode']}")
    print(f"schema: {summary['schema']}")
    print(f"registered: {summary['registered']}/{summary['total']}")
    print_store_path_warnings(path)
    if summary["required_missing"]:
        print("required_missing:")
        schema = get_schema(store["schema"])
        for key in summary["required_missing"]:
            print(f"- {key}: {schema[key].label}")


def command_context(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = read_store(path=path)
    print(json.dumps(agent_context(store, include_path=args.include_path, path=path, task=args.task), ensure_ascii=False, indent=2))


def command_schema(args: argparse.Namespace) -> None:
    print(json.dumps(schema_context(args.schema), ensure_ascii=False, indent=2))


def command_list(args: argparse.Namespace) -> None:
    store = read_store(path=resolve_path(args))
    schema = get_schema(store["schema"])
    for key, spec in schema.items():
        value = str(store["fields"].get(key, ""))
        print(f"{key}\t{spec.label}\t{masked(value)}")


def command_get(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(path=path)
    key = validate_key(args.key, store["schema"])
    try:
        _grant, operation = prepare_consent_consumption(
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
        operation.try_outcome_unknown()
        raise SystemExit(f"{key} is empty")
    try:
        print(
            "# WARNING: this prints one raw personal value. Do not paste it into logs, public issues, or remote agents.",
            file=sys.stderr,
        )
        print(value)
    except (BrokenPipeError, OSError):
        operation.try_outcome_unknown(raw_returned=True)
        raise
    if not operation.try_delivered(raw_returned=True, action="get"):
        raise OSError("audit outcome finalization failed")


def command_set(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(create=True, path=path, schema_name=args.schema)
    key = validate_key(args.key, store["schema"])
    if key in DERIVED_FIELDS:
        raise SystemExit(f"{key} is derived. Set component fields instead.")
    print(
        "# WARNING: this stores one personal value locally. Data is not encrypted at rest by default and can remain in backups, sync targets, snapshots, or manual copies; use dummy data or values you are comfortable storing on this device.",
        file=sys.stderr,
    )
    print_store_path_warnings(path)
    value = read_bounded_stdin() if args.stdin else getpass(f"{key} value: ")
    store["fields"][key] = normalize_value(key, value)
    operation = begin_audit_operation(vault_path=path, actor="cli", action="set", key=key, purpose=args.purpose)
    write_store(store, path)
    operation.committed()
    try:
        print(f"saved: {key}")
    except (BrokenPipeError, OSError):
        operation.try_outcome_unknown()
        raise
    if not operation.try_delivered():
        raise OSError("audit outcome finalization failed")


def command_unset(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(path=path)
    key = validate_key(args.key, store["schema"])
    if key in DERIVED_FIELDS:
        raise SystemExit(f"{key} is derived. Clear component fields instead.")
    store["fields"][key] = ""
    operation = begin_audit_operation(vault_path=path, actor="cli", action="unset", key=key, purpose=args.purpose)
    write_store(store, path)
    operation.committed()
    try:
        print(f"cleared: {key}")
    except (BrokenPipeError, OSError):
        operation.try_outcome_unknown()
        raise
    if not operation.try_delivered():
        raise OSError("audit outcome finalization failed")


def command_env(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    if not args.i_understand_bulk_raw_export:
        write_audit_event(vault_path=path, actor="cli", action="env_bulk_export", key="*", purpose=args.purpose, outcome="denied")
        raise SystemExit("env bulk raw export requires --i-understand-bulk-raw-export")
    store = load_store(path=path)
    try:
        _grant, operation = prepare_consent_consumption(
            vault_path=path,
            consent_id=args.consent_id,
            action="env",
            key="*",
            purpose=args.purpose,
        )
    except ConsentError as exc:
        write_audit_event(vault_path=path, actor="cli", action="env_bulk_export", key="*", purpose=args.purpose, outcome="denied")
        raise SystemExit(f"consent required: {exc}") from exc
    lines = export_env_lines(store)
    try:
        print(
            "# WARNING: this is a human-only bulk raw export. Do not paste it into logs, public issues, or remote agents.",
            file=sys.stderr,
        )
        print("\n".join(lines))
    except (BrokenPipeError, OSError):
        operation.try_outcome_unknown(raw_returned=bool(lines))
        raise
    if not operation.try_delivered(raw_returned=bool(lines), action="env_bulk_export"):
        raise OSError("audit outcome finalization failed")


def command_audit(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    if args.audit_command == "summary":
        print(json.dumps(audit_summary(path), ensure_ascii=False, indent=2, sort_keys=True))
        return
    result = audit_tail(path, limit=args.limit)
    if result["integrity_warning"]:
        print(
            f"warning: skipped {result['malformed_records_skipped']} malformed audit record(s)",
            file=sys.stderr,
        )
    for event in result["events"]:
        print(json.dumps(event, ensure_ascii=False, sort_keys=True))


def command_encryption(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store_exists = private_file_exists(path)
    encrypted = False
    if store_exists:
        encrypted = is_encrypted_payload(read_private_json(path))
    if args.encryption_command == "status":
        audit_exists = private_file_exists(audit_path(path))
        consent_exists = private_file_exists(consent_path(path))
        print(
            json.dumps(
                {
                    "store_exists": store_exists,
                    "storage": ENCRYPTED_STORAGE if encrypted else "plain-json",
                    "encrypted": encrypted,
                    "cryptography_available": cryptography_available(),
                    "audit_sidecar_exists": audit_exists,
                    "audit_sidecar_encrypted": audit_exists
                    and sidecar_is_encrypted(audit_path(path), kind="audit"),
                    "consent_sidecar_exists": consent_exists,
                    "consent_sidecar_encrypted": consent_exists
                    and sidecar_is_encrypted(consent_path(path), kind="consent"),
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
            strength_issue = passphrase_strength_issue(passphrase)
            if strength_issue is not None and args.allow_weak_passphrase:
                print(
                    "# WARNING: weak passphrase override accepted; copied vault bytes are easier to guess offline.",
                    file=sys.stderr,
                )
            operation = begin_audit_operation(
                vault_path=path,
                actor="cli",
                action="encrypt",
                purpose=args.purpose,
                sidecar_passphrase=passphrase,
            )
            try:
                write_store(
                    store,
                    path,
                    passphrase=passphrase,
                    encrypted=True,
                    allow_weak_passphrase=args.allow_weak_passphrase,
                )
                migrate_consent_sidecar(path, encrypted=True, passphrase=passphrase)
                migrate_audit_sidecar(path, encrypted=True, passphrase=passphrase)
            except ValueError:
                operation.rejected()
                raise
            operation.committed()
            try:
                print("encrypted: true")
            except (BrokenPipeError, OSError):
                operation.try_outcome_unknown()
                raise
            if not operation.try_delivered():
                raise OSError("audit outcome finalization failed")
            return
        if args.encryption_command == "decrypt":
            if not encrypted:
                raise SystemExit("vault is not encrypted")
            if not args.i_understand_plaintext_persistence:
                raise SystemExit(
                    "decrypt requires --i-understand-plaintext-persistence because it replaces the encrypted vault with persistent plaintext"
                )
            passphrase = read_passphrase()
            store = load_store(path=path, passphrase=passphrase)
            operation = begin_audit_operation(
                vault_path=path,
                actor="cli",
                action="decrypt",
                purpose=args.purpose,
                sidecar_passphrase=passphrase,
            )
            try:
                write_store(store, path, passphrase=passphrase, encrypted=False)
                migrate_consent_sidecar(path, encrypted=False, passphrase=passphrase)
                migrate_audit_sidecar(path, encrypted=False, passphrase=passphrase)
            except ValueError:
                operation.rejected()
                raise
            operation.committed()
            try:
                print("encrypted: false")
            except (BrokenPipeError, OSError):
                operation.try_outcome_unknown()
                raise
            if not operation.try_delivered():
                raise OSError("audit outcome finalization failed")
            return
        if args.encryption_command == "protect-sidecars":
            if not encrypted:
                raise SystemExit("sidecar protection requires an encrypted vault")
            passphrase = read_passphrase()
            load_store(path=path, passphrase=passphrase)
            operation = begin_audit_operation(
                vault_path=path,
                actor="cli",
                action="protect_sidecars",
                purpose=args.purpose,
                sidecar_passphrase=passphrase,
            )
            migrate_consent_sidecar(path, encrypted=True, passphrase=passphrase)
            migrate_audit_sidecar(path, encrypted=True, passphrase=passphrase)
            operation.committed()
            try:
                print("sidecars_encrypted: true")
            except (BrokenPipeError, OSError):
                operation.try_outcome_unknown()
                raise
            if not operation.try_delivered():
                raise OSError("audit outcome finalization failed")
            return
    except EncryptionUnavailableError as exc:
        raise SystemExit(str(exc)) from exc


def command_consent(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    if args.consent_command == "grant":
        if args.action == "env" and not args.i_understand_bulk_raw_export:
            raise SystemExit("env bulk raw export consent requires --i-understand-bulk-raw-export")
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
        if args.action == "env" and not args.i_understand_bulk_raw_export:
            raise SystemExit("env bulk raw export request requires --i-understand-bulk-raw-export")
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


def command_privacy(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    if args.privacy_command == "prune":
        result = prune_private_metadata(
            path,
            consent_retention_days=args.consent_retention_days,
            audit_retention_days=args.audit_retention_days,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return
    result = dispose_private_state(path, confirmation=args.confirm)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


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
        ("env", command_env, "Human-only bulk raw export as shell export lines. Not for agent/MCP normal flow."),
    ]:
        cmd = sub.add_parser(name, help=help_text)
        if name == "context":
            cmd.add_argument("--include-path", action="store_true", help="Include the local store path in JSON output.")
            cmd.add_argument("--task", help="Optional raw-free task description for minimum-key planning hints.")
        if name == "env":
            cmd.add_argument(
                "--purpose",
                required=True,
                help="Exact purpose bound to the operation; only an allowlisted code or [redacted] is stored.",
            )
            cmd.add_argument("--consent-id", required=True, help="One-time consent token from consent grant.")
            cmd.add_argument(
                "--i-understand-bulk-raw-export",
                action="store_true",
                help="Required human-only acknowledgement for bulk raw export.",
            )
        cmd.set_defaults(func=func)
    get = sub.add_parser("get", help="Print one raw value. Use only for the minimum required key.")
    get.add_argument("key")
    get.add_argument(
        "--purpose",
        required=True,
        help="Exact purpose bound to raw access; only an allowlisted code or [redacted] is stored.",
    )
    get.add_argument("--consent-id", required=True, help="One-time consent token from consent grant.")
    get.set_defaults(func=command_get)
    set_cmd = sub.add_parser("set", help="Set one value without putting it in shell history.")
    set_cmd.add_argument("key")
    set_cmd.add_argument("--stdin", action="store_true", help="Read value from stdin.")
    set_cmd.add_argument(
        "--purpose", required=True, help="Change purpose; only an allowlisted code or [redacted] is stored."
    )
    set_cmd.set_defaults(func=command_set)
    unset = sub.add_parser("unset", help="Clear one value.")
    unset.add_argument("key")
    unset.add_argument(
        "--purpose", required=True, help="Change purpose; only an allowlisted code or [redacted] is stored."
    )
    unset.set_defaults(func=command_unset)
    audit = sub.add_parser(
        "audit",
        help="Inspect raw-free local audit metadata. Not tamper-evident.",
        description="Inspect raw-free local audit metadata. Not tamper-evident.",
    )
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
    encryption_encrypt.add_argument(
        "--purpose", required=True, help="Migration purpose; only an allowlisted code or [redacted] is stored."
    )
    encryption_encrypt.add_argument(
        "--allow-weak-passphrase",
        action="store_true",
        help="Override the new-passphrase strength gate after accepting the offline-guessing risk.",
    )
    encryption_encrypt.set_defaults(func=command_encryption)
    encryption_decrypt = encryption_sub.add_parser("decrypt", help="Decrypt the local vault back to plain JSON.")
    encryption_decrypt.add_argument(
        "--purpose", required=True, help="Migration purpose; only an allowlisted code or [redacted] is stored."
    )
    encryption_decrypt.add_argument(
        "--i-understand-plaintext-persistence",
        action="store_true",
        help="Required acknowledgement that decrypt replaces the encrypted vault with persistent plaintext.",
    )
    encryption_decrypt.set_defaults(func=command_encryption)
    encryption_sidecars = encryption_sub.add_parser(
        "protect-sidecars",
        help="Encrypt existing consent and audit sidecars for an encrypted vault.",
    )
    encryption_sidecars.add_argument(
        "--purpose", required=True, help="Migration purpose; only an allowlisted code or [redacted] is stored."
    )
    encryption_sidecars.set_defaults(func=command_encryption)
    consent = sub.add_parser(
        "consent",
        help="Create or inspect raw-free consent tokens. Not an authentication boundary.",
        description="Create or inspect raw-free consent tokens. Not an authentication boundary.",
    )
    consent_sub = consent.add_subparsers(dest="consent_command", required=True)
    consent_grant = consent_sub.add_parser("grant", help="Grant a one-time raw access consent token.")
    consent_grant.add_argument("--action", choices=["get", "env"], required=True)
    consent_grant.add_argument("--key", default="*", help="Key for get. Use * for env.")
    consent_grant.add_argument(
        "--purpose",
        required=True,
        help="Exact purpose that must match the later raw command; persisted as a code or [redacted].",
    )
    consent_grant.add_argument(
        "--ttl-seconds",
        type=int,
        default=300,
        help=f"Token lifetime in seconds (1-{MAX_TTL_SECONDS}; default: 300).",
    )
    consent_grant.add_argument(
        "--i-understand-bulk-raw-export",
        action="store_true",
        help="Required human-only acknowledgement when --action env is used.",
    )
    consent_grant.set_defaults(func=command_consent)
    consent_request = consent_sub.add_parser("request", help="Queue a raw access request for human approval.")
    consent_request.add_argument("--action", choices=["get", "env"], required=True)
    consent_request.add_argument("--key", default="*", help="Key for get. Use * for env.")
    consent_request.add_argument(
        "--purpose",
        required=True,
        help="Exact purpose for requested access; persisted as a code or [redacted].",
    )
    consent_request.add_argument(
        "--i-understand-bulk-raw-export",
        action="store_true",
        help="Required human-only acknowledgement when --action env is used.",
    )
    consent_request.set_defaults(func=command_consent)
    consent_requests = consent_sub.add_parser("requests", help="List pending consent requests without raw values.")
    consent_requests.add_argument("--include-resolved", action="store_true")
    consent_requests.set_defaults(func=command_consent)
    consent_approve = consent_sub.add_parser("approve", help="Approve a pending consent request and issue a one-time token.")
    consent_approve.add_argument("request_id")
    consent_approve.add_argument(
        "--ttl-seconds",
        type=int,
        default=300,
        help=f"Token lifetime in seconds (1-{MAX_TTL_SECONDS}; default: 300).",
    )
    consent_approve.set_defaults(func=command_consent)
    consent_deny = consent_sub.add_parser("deny", help="Deny a pending consent request.")
    consent_deny.add_argument("request_id")
    consent_deny.set_defaults(func=command_consent)
    consent_list = consent_sub.add_parser("list", help="List unconsumed consent tokens without raw values.")
    consent_list.add_argument("--include-used", action="store_true")
    consent_list.set_defaults(func=command_consent)
    privacy = sub.add_parser(
        "privacy",
        help="Prune or dispose local private state. Stop GUI and MCP processes first.",
    )
    privacy_sub = privacy.add_subparsers(dest="privacy_command", required=True)
    privacy_prune = privacy_sub.add_parser("prune", help="Remove expired or resolved private metadata beyond retention windows.")
    privacy_prune.add_argument("--consent-retention-days", type=int, default=30)
    privacy_prune.add_argument("--audit-retention-days", type=int, default=90)
    privacy_prune.set_defaults(func=command_privacy)
    privacy_dispose = privacy_sub.add_parser("dispose", help="Remove the vault, consent state, and audit log.")
    privacy_dispose.add_argument(
        "--confirm",
        required=True,
        help=f'Required exact phrase: "{DISPOSE_CONFIRMATION}"',
    )
    privacy_dispose.set_defaults(func=command_privacy)
    return parser


def safe_cli_error(exc: Exception) -> str:
    if isinstance(exc, ConsentError):
        return str(exc)
    if isinstance(exc, json.JSONDecodeError):
        return "store or state file contains invalid JSON"
    if isinstance(exc, FileNotFoundError):
        return "vault does not exist"
    if isinstance(exc, NotADirectoryError):
        return "vault parent path is not a directory"
    if isinstance(exc, PermissionError):
        return "permission denied"
    if isinstance(exc, (ResourceLimitError, UnicodeDecodeError)):
        return "input or state exceeds the supported resource limit"
    message = str(exc)
    if message.startswith("Unknown key: "):
        return "Unknown key"
    return message or exc.__class__.__name__


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except SystemExit:
        raise
    except (ConsentError, ValueError, FileNotFoundError, NotADirectoryError, PermissionError, json.JSONDecodeError) as exc:
        print(f"error: {safe_cli_error(exc)}", file=sys.stderr)
        raise SystemExit(1) from None
    except Exception:
        print("error: operation failed", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
