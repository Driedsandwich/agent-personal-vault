#!/usr/bin/env python3
"""Fail-closed source scanner for accidental private release content."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from scripts.release_policy import SKIP_DIRS, ReleasePolicyError, is_within_root, scan_release_entry, scan_release_tree
except ModuleNotFoundError:
    from release_policy import SKIP_DIRS, ReleasePolicyError, is_within_root, scan_release_entry, scan_release_tree


def should_scan(path: Path) -> bool:
    """All regular release entries are decoded and scanned by the shared policy."""

    return True


def scan_file(path: Path, root: Path | None = None) -> list[str]:
    """Compatibility wrapper for focused checks using the shared policy."""

    if root is not None and not is_within_root(path, root):
        raise ValueError(f"Refusing to scan path outside root: {path}")
    findings = scan_release_entry(path.name, path.read_bytes())
    return [finding.render() for finding in findings]


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan the complete release source inventory.")
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root)
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
    raise SystemExit(main())
