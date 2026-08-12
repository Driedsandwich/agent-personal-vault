#!/usr/bin/env python3
"""Fail-closed source scanner for accidental private release content."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from scripts.release_policy import SKIP_DIRS, ReleasePolicyError, is_within_root, scan_release_entry, scan_release_tree
except ModuleNotFoundError:
    from release_policy import SKIP_DIRS, ReleasePolicyError, is_within_root, scan_release_entry, scan_release_tree

ROOT = Path(__file__).resolve().parent.parent


def should_scan(path: Path) -> bool:
    """All regular release entries are decoded and scanned by the shared policy."""

    return True


def scan_file(path: Path, root: Path | None = None) -> list[str]:
    """Compatibility wrapper for focused checks using the shared policy."""

    if root is not None and not is_within_root(path, root):
        raise ValueError(f"Refusing to scan path outside root: {path}")
    findings = scan_release_entry(path.name, path.read_bytes())
    return [finding.render() for finding in findings]


def main(root: Path | None = None) -> int:
    root = ROOT if root is None else root
    try:
        findings = scan_release_tree(root)
    except (OSError, ReleasePolicyError) as exc:
        print(f"release privacy scan incomplete: {exc}", file=sys.stderr)
        return 1
    if findings:
        print("Potential private release content found:", file=sys.stderr)
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 1
    print("Release privacy policy passed for the complete source inventory.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("usage: pii_scan.py", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main())
