"""Single fail-closed privacy policy for source and release artifacts."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
from dataclasses import dataclass
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

LOCAL_EDITOR_CONFIG_DIRS = {".idea", ".vscode"}

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
    ".cursorrules",
    ".codex.json",
    ".mcp.json",
    ".aider.conf.yml",
    ".aider.model.settings.yml",
    "AGENTS.md",
    "AGENTS.local.md",
    "CLAUDE.md",
    "CLAUDE.local.md",
    "CODEX.md",
    "CODEX.local.md",
    "GEMINI.md",
}

SKIP_DIRS = GENERATED_DIRS | LOCAL_DEVELOPER_CONFIG_DIRS

FORBIDDEN_NAMES = {
    ".env",
    ".pypirc",
    "audit.jsonl",
    "consents.json",
    "vault.json",
}

FORBIDDEN_SUFFIXES = {
    ".db",
    ".heic",
    ".jpeg",
    ".jpg",
    ".png",
    ".sqlite",
}

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

# Keep private fragments split in source so the scanner does not publish them in
# diagnostics or match its own policy definition.
FORBIDDEN_LITERALS = {
    "maintainer-home-path": "/" + "Users/" + "kishimoto" + "satoshi",
    "private-profile-path": "private/" + "job_profile",
    "private-project-path": "personal-ai" + "-os",
    "private-backup-path": "job-profile" + "-backups",
    "private-audit-path": "memory" + "-audit",
    "private-inbox-path": "inbox" + "-log",
    "maintainer-name-fragment": "kishimoto" + "satoshi",
}

DENY_PATTERNS = {
    "macos-user-path": re.compile("/" + r"Users/[^ \n\t`'\"]+"),
    "windows-user-path": re.compile(r"[A-Za-z]:\\Users\\[^ \n\t`'\"]+", re.IGNORECASE),
    "non-example-email": re.compile(r"[A-Za-z0-9._%+-]+@(?!example\.test\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "mobile-phone": re.compile(r"0[789]0-\d{4}-\d{4}"),
    "openai-style-token": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "github-classic-token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "github-fine-grained-token": re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    "aws-access-key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private-key-block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


class ReleasePolicyError(ValueError):
    """Raised when the release inventory cannot be checked completely."""


@dataclass(frozen=True)
class PolicyFinding:
    entry: str
    rule: str
    line: int | None = None

    def render(self) -> str:
        entry_id = hashlib.sha256(self.entry.encode("utf-8")).hexdigest()[:16]
        location = f"entry-sha256:{entry_id}"
        if self.line is not None:
            location = f"{location}:line-{self.line}"
        return f"{location}: {self.rule}"


def is_within_root(path: Path, root: Path) -> bool:
    path = Path(os.path.abspath(path))
    root = Path(os.path.abspath(root))
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def is_generated_dir_name(name: str) -> bool:
    return name in GENERATED_DIRS or name.endswith(".egg-info")


def is_skipped_path(path: Path) -> bool:
    return path.name in LOCAL_DEVELOPER_CONFIG_FILES or any(
        part in SKIP_DIRS or is_generated_dir_name(part) for part in path.parts
    )


def is_generated_path(path: Path) -> bool:
    return any(part in GENERATED_DIRS or is_generated_dir_name(part) for part in path.parts)


def validated_entry_parts(name: str) -> tuple[str, ...]:
    """Return canonical relative archive/source parts or fail closed."""

    if (
        not name
        or name.startswith("/")
        or "\\" in name
        or "\x00" in name
        or re.match(r"^[A-Za-z]:", name)
    ):
        raise ReleasePolicyError("release entry path is not canonical")
    parts = tuple(name.split("/"))
    if any(part in {"", ".", ".."} for part in parts):
        raise ReleasePolicyError("release entry path is not canonical")
    return parts


def _tracked_release_files(root: Path, raw_inventory: bytes) -> list[Path]:
    try:
        decoded = raw_inventory.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ReleasePolicyError("Git release inventory is not valid UTF-8") from exc
    names = [name for name in decoded.split("\0") if name]
    if not names:
        raise ReleasePolicyError("Git release inventory is empty")
    paths: list[Path] = []
    for name in names:
        parts = validated_entry_parts(name)
        path = root.joinpath(*parts)
        if not is_within_root(path, root):
            raise ReleasePolicyError("tracked release entry escapes root")
        try:
            info = path.lstat()
        except FileNotFoundError as exc:
            raise ReleasePolicyError("tracked release entry is missing") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise ReleasePolicyError("tracked release entry is not a regular file")
        paths.append(path)
    return paths


def _walk_release_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        kept_dirs: list[str] = []
        for name in sorted(dirnames):
            path = directory_path / name
            if is_generated_path(path.relative_to(root)):
                continue
            if path.is_symlink():
                raise ReleasePolicyError("release inventory contains a symbolic-link directory")
            kept_dirs.append(name)
        dirnames[:] = kept_dirs
        for name in sorted(filenames):
            path = directory_path / name
            relative = path.relative_to(root)
            if is_generated_path(relative):
                continue
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise ReleasePolicyError("release inventory contains a symbolic-link file")
            if not stat.S_ISREG(info.st_mode):
                raise ReleasePolicyError("release inventory entry is not a regular file")
            paths.append(path)
    if not paths:
        raise ReleasePolicyError("filesystem release inventory is empty")
    return paths


def iter_release_files(root: Path) -> list[Path]:
    """Return a complete, regular-file-only release source inventory."""

    root = Path(os.path.abspath(root))
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return _tracked_release_files(root, result.stdout)
    return _walk_release_files(root)


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _scan_text(name: str, text: str, *, include_line: bool) -> list[PolicyFinding]:
    findings: list[PolicyFinding] = []
    for label, needle in FORBIDDEN_LITERALS.items():
        start = text.find(needle)
        if start >= 0:
            line = _line_number(text, start) if include_line else None
            findings.append(PolicyFinding(name, label, line))
    for label, pattern in DENY_PATTERNS.items():
        for match in pattern.finditer(text):
            if match.group(0) in ALLOWLIST:
                continue
            line = _line_number(text, match.start()) if include_line else None
            findings.append(PolicyFinding(name, label, line))
    return findings


def scan_release_entry(name: str, data: bytes) -> list[PolicyFinding]:
    """Apply the same filename and text policy to one source/archive entry."""

    parts = validated_entry_parts(name)
    findings: list[PolicyFinding] = []
    lowered_parts = {part.lower() for part in parts}
    for forbidden_name in sorted(FORBIDDEN_NAMES):
        if forbidden_name.lower() in lowered_parts:
            findings.append(PolicyFinding(name, f"forbidden-name:{forbidden_name}"))
    suffix = Path(parts[-1]).suffix.lower()
    if suffix in FORBIDDEN_SUFFIXES:
        findings.append(PolicyFinding(name, f"forbidden-suffix:{suffix}"))
    findings.extend(_scan_text(name, name, include_line=False))
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        findings.append(PolicyFinding(name, "undecodable-content"))
        return findings
    findings.extend(_scan_text(name, text, include_line=True))
    return findings


def scan_release_tree(root: Path) -> list[PolicyFinding]:
    root = Path(os.path.abspath(root))
    findings: list[PolicyFinding] = []
    files = iter_release_files(root)
    for path in files:
        before = path.stat(follow_symlinks=False)
        data = path.read_bytes()
        after = path.stat(follow_symlinks=False)
        identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        if identity_before != identity_after or len(data) != before.st_size:
            raise ReleasePolicyError("release entry changed while scanning")
        findings.extend(scan_release_entry(path.relative_to(root).as_posix(), data))
    return findings
