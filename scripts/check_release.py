#!/usr/bin/env python3
"""Run local release-readiness checks."""

from __future__ import annotations

import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_NAMES = {
    "audit.jsonl",
    "consents.json",
    "vault.json",
}

FORBIDDEN_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".heic",
    ".sqlite",
    ".db",
}

FORBIDDEN_TEXT = [
    "/" + "Users/" + "kishimoto" + "satoshi",
    "private/" + "job_profile",
    "personal-ai" + "-os",
    "job-profile" + "-backups",
    "memory" + "-audit",
    "inbox" + "-log",
    "kishimoto" + "satoshi",
]

SKIP_DIRS = {".git", ".venv", ".codex", "__pycache__", "dist", "build", ".pytest_cache"}
TEXT_SUFFIXES = {".py", ".md", ".toml", ".json", ".txt", ".yml", ".yaml"}


def run_step(name: str, command: list[str]) -> None:
    print(f"== {name}")
    subprocess.run(command, cwd=ROOT, check=True)


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def check_forbidden_files() -> None:
    print("== forbidden files")
    findings = []
    for path in iter_files():
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            findings.append(path.relative_to(ROOT))
    if findings:
        for finding in findings:
            print(f"forbidden file: {finding}", file=sys.stderr)
        raise SystemExit(1)
    print("no forbidden files found")


def check_forbidden_text() -> None:
    print("== forbidden text")
    findings = []
    for path in iter_files():
        if path.suffix not in TEXT_SUFFIXES and path.name not in {".gitignore", "LICENSE"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in FORBIDDEN_TEXT:
            if needle in text:
                findings.append((path.relative_to(ROOT), needle))
    if findings:
        for path, needle in findings:
            print(f"forbidden text: {path}: {needle}", file=sys.stderr)
        raise SystemExit(1)
    print("no forbidden text found")


def clean_generated() -> None:
    print("== clean generated files")
    for path in ROOT.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    for path in ROOT.rglob(".pytest_cache"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    print("generated files cleaned")


def main() -> int:
    run_step("py_compile", [sys.executable, "-m", "py_compile", *map(str, (ROOT / "agent_personal_vault").glob("*.py")), str(ROOT / "scripts/pii_scan.py")])
    run_step("unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests"])
    run_step("pii scan", [sys.executable, "scripts/pii_scan.py", "."])
    check_forbidden_files()
    check_forbidden_text()
    clean_generated()
    print("release checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
