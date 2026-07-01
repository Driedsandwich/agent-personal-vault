"""Shared release-check policy for generated and local-only artifacts."""

from __future__ import annotations

from pathlib import Path

LOCAL_AGENT_CONFIG_DIRS = {
    ".codex",
    ".claude",
    ".cursor",
}

GENERATED_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "dist",
    "build",
}

SKIP_DIRS = GENERATED_DIRS | LOCAL_AGENT_CONFIG_DIRS


def is_skipped_path(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)
