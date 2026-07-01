"""Shared release-check policy for generated and local-only artifacts."""

from __future__ import annotations

import subprocess
from pathlib import Path

LOCAL_AGENT_CONFIG_DIRS = {
    ".aider",
    ".agents",
    ".codex",
    ".claude",
    ".continue",
    ".cursor",
    ".gemini",
    ".kiro",
    ".opencode",
    ".roo",
    ".zed",
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

LOCAL_DEVELOPER_CONFIG_FILES = {
    ".codex.json",
    ".mcp.json",
    ".aider.conf.yml",
    ".aider.model.settings.yml",
    "AGENTS.md",
    "AGENTS.local.md",
    "CLAUDE.local.md",
    "CODEX.local.md",
}

SKIP_DIRS = GENERATED_DIRS | LOCAL_DEVELOPER_CONFIG_DIRS


def is_skipped_path(path: Path) -> bool:
    return path.name in LOCAL_DEVELOPER_CONFIG_FILES or any(part in SKIP_DIRS for part in path.parts)


def iter_release_files(root: Path) -> list[Path]:
    """Return files that should be checked before release.

    In a Git checkout, release checks inspect tracked repository files only.
    Incidental local agent/editor artifacts such as .codex/hooks.json stay
    outside the release surface while untracked. If they are force-added to Git,
    they are intentionally checked like any other tracked file. For non-Git
    temporary trees used by tests, fall back to a filesystem walk with local
    developer artifacts skipped.
    """

    root = root.resolve()
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return [
            path
            for raw_path in result.stdout.decode("utf-8", errors="ignore").split("\0")
            if raw_path
            for path in [root / raw_path]
            if path.is_file()
        ]

    return [
        path
        for path in root.rglob("*")
        if path.is_file() and not is_skipped_path(path)
    ]
