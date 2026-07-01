#!/usr/bin/env python3
"""Small pre-publication scanner for accidental private data.

This is intentionally conservative and project-specific. It does not prove
absence of PII; it catches obvious mistakes before a human review.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from scripts.release_policy import SKIP_DIRS, is_skipped_path
except ModuleNotFoundError:
    from release_policy import SKIP_DIRS, is_skipped_path

ALLOWLIST = {
    "090-1234-5678",
    "100-0001",
    "taro@example.test",
    "山田",
    "太郎",
    "やまだ",
    "たろう",
    "サンプル大学",
    "サンプル高等学校",
    "サンプルマンション101",
}

DENY_PATTERNS = [
    re.compile(r"/" + r"Users/[^ \n\t`'\"]+"),
    re.compile(r"[A-Za-z0-9._%+-]+@(?!example\.test\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"0[789]0-\d{4}-\d{4}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".toml",
    ".json",
    ".txt",
    ".yml",
    ".yaml",
    ".gitignore",
}

def should_scan(path: Path) -> bool:
    if is_skipped_path(path):
        return False
    return path.suffix in TEXT_SUFFIXES or path.name in {".gitignore", "LICENSE"}


def scan_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings: list[str] = []
    for pattern in DENY_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0)
            if value in ALLOWLIST:
                continue
            findings.append(f"{path}:{text.count(chr(10), 0, match.start()) + 1}: {pattern.pattern}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan for obvious accidental private data.")
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root)
    findings: list[str] = []
    for path in root.rglob("*"):
        if path.is_file() and should_scan(path):
            findings.extend(scan_file(path))
    if findings:
        print("Potential private data found:", file=sys.stderr)
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print("No obvious private data patterns found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
