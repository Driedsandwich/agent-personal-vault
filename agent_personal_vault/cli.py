"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from getpass import getpass
from pathlib import Path

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


def command_init(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(create=True, path=path, schema_name=args.schema)
    print(f"created_or_exists: {path}")
    print(f"schema: {store['schema']}")


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
    print(json.dumps(agent_context(store, include_path=args.include_path, path=path), ensure_ascii=False, indent=2))


def command_schema(args: argparse.Namespace) -> None:
    print(json.dumps(schema_context(args.schema), ensure_ascii=False, indent=2))


def command_list(args: argparse.Namespace) -> None:
    store = load_store(path=resolve_path(args))
    schema = get_schema(store["schema"])
    for key, spec in schema.items():
        value = str(store["fields"].get(key, ""))
        print(f"{key}\t{spec.label}\t{masked(value)}")


def command_get(args: argparse.Namespace) -> None:
    store = load_store(path=resolve_path(args))
    key = validate_key(args.key, store["schema"])
    if key in DERIVED_FIELDS:
        value = derived_fields(store["fields"]).get(key, "")
    else:
        value = str(store["fields"].get(key, ""))
    if not value:
        raise SystemExit(f"{key} is empty")
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
    print(f"saved: {key}")


def command_unset(args: argparse.Namespace) -> None:
    path = resolve_path(args)
    store = load_store(path=path)
    key = validate_key(args.key, store["schema"])
    if key in DERIVED_FIELDS:
        raise SystemExit(f"{key} is derived. Clear component fields instead.")
    store["fields"][key] = ""
    write_store(store, path)
    print(f"cleared: {key}")


def command_env(args: argparse.Namespace) -> None:
    store = load_store(path=resolve_path(args))
    print(
        "# WARNING: this prints raw personal data. Do not paste it into logs, public issues, or remote agents.",
        file=sys.stderr,
    )
    print("\n".join(export_env_lines(store)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-first personal data vault for AI agents.")
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
        cmd.set_defaults(func=func)
    get = sub.add_parser("get", help="Print one raw value. Use only for the minimum required key.")
    get.add_argument("key")
    get.set_defaults(func=command_get)
    set_cmd = sub.add_parser("set", help="Set one value without putting it in shell history.")
    set_cmd.add_argument("key")
    set_cmd.add_argument("--stdin", action="store_true", help="Read value from stdin.")
    set_cmd.set_defaults(func=command_set)
    unset = sub.add_parser("unset", help="Clear one value.")
    unset.add_argument("key")
    unset.set_defaults(func=command_unset)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
