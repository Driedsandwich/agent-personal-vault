"""Shared release-check policy for generated and local-only artifacts."""

from __future__ import annotations

from pathlib import Path

LOCAL_AGENT_CONFIG_DIRS = {
    ".codex",
    ".claude",
    ".continue",
    ".cursor",
    ".windsurf",
}

LOCAL_EDITOR_CONFIG_DIRS = {
    ".idea",
    ".vscode",
}

GENERATED_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "dist",
    "build",
}

LOCAL_DEVELOPER_CONFIG_DIRS = LOCAL_AGENT_CONFIG_DIRS | LOCAL_EDITOR_CONFIG_DIRS

SKIP_DIRS = GENERATED_DIRS | LOCAL_DEVELOPER_CONFIG_DIRS


def is_skipped_path(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)
