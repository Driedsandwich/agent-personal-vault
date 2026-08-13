"""Owner-private, link-resistant filesystem helpers for vault state."""

from __future__ import annotations

import errno
import json
import os
import secrets
import stat
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TextIO


PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
_DARWIN_SYSTEM_LINKS = {"var", "tmp", "etc"}


def _is_posix() -> bool:
    return os.name == "posix"


def _open_flags(*flags: int) -> int:
    value = 0
    for flag in flags:
        value |= flag
    value |= getattr(os, "O_CLOEXEC", 0)
    value |= getattr(os, "O_NOFOLLOW", 0)
    return value


def lexical_absolute_path(path: Path) -> Path:
    """Normalize dot segments without resolving user-controlled symbolic links."""

    # Operator-selected storage paths are intentional. All filesystem access is
    # revalidated by private_directory_fd's held-fd, no-follow component walk.
    normalized = Path(os.path.abspath(os.fspath(Path(path).expanduser())))
    if sys.platform != "darwin" or len(normalized.parts) < 2 or normalized.parts[1] not in _DARWIN_SYSTEM_LINKS:
        return normalized
    alias = Path(normalized.anchor) / normalized.parts[1]
    try:
        info = alias.lstat()
        target = os.readlink(alias)
    except OSError:
        return normalized
    expected = f"private/{normalized.parts[1]}"
    if stat.S_ISLNK(info.st_mode) and target.lstrip("/") == expected:
        return Path(normalized.anchor) / "private" / Path(*normalized.parts[1:])
    return normalized


def _validate_private_directory(fd: int) -> None:
    info = os.fstat(fd)
    if not stat.S_ISDIR(info.st_mode):
        raise NotADirectoryError("vault parent path is not a directory")
    if _is_posix():
        if info.st_uid != os.geteuid():
            raise PermissionError("vault parent directory must be owned by the current user")
        if stat.S_IMODE(info.st_mode) & 0o077:
            raise PermissionError("vault parent directory must not be accessible by group or other users")


def _validate_private_file(fd: int, *, repair_mode: bool = False) -> None:
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode):
        raise PermissionError("vault state path must be a regular file")
    if _is_posix():
        if info.st_uid != os.geteuid():
            raise PermissionError("vault state file must be owned by the current user")
        if info.st_nlink != 1:
            raise PermissionError("vault state file must have exactly one hard link")
        if stat.S_IMODE(info.st_mode) & 0o077:
            if repair_mode and hasattr(os, "fchmod"):
                os.fchmod(fd, PRIVATE_FILE_MODE)
            else:
                raise PermissionError("vault state file must not be accessible by group or other users")


@contextmanager
def private_directory_fd(path: Path, *, create: bool = True) -> Iterator[int]:
    """Hold and validate the directory used for one storage operation."""

    path = lexical_absolute_path(path)
    if not _is_posix():
        raise PermissionError("owner-private link-safe storage is unavailable on this platform")

    flags = _open_flags(os.O_RDONLY, getattr(os, "O_DIRECTORY", 0))
    fd = os.open(path.anchor, flags)
    try:
        for component in path.parts[1:]:
            try:
                next_fd = os.open(component, flags, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(component, PRIVATE_DIR_MODE, dir_fd=fd)
                except FileExistsError:
                    pass
                next_fd = os.open(component, flags, dir_fd=fd)
            except OSError as exc:
                try:
                    component_info = os.stat(component, dir_fd=fd, follow_symlinks=False)
                except OSError:
                    component_info = None
                if exc.errno == errno.ELOOP or (
                    component_info is not None and stat.S_ISLNK(component_info.st_mode)
                ):
                    raise PermissionError("vault parent path must not contain symbolic links") from None
                raise
            os.close(fd)
            fd = next_fd
        _validate_private_directory(fd)
        yield fd
    finally:
        os.close(fd)


def ensure_private_directory(path: Path) -> None:
    with private_directory_fd(path):
        pass


def _relative_name(path: Path) -> str:
    name = Path(path).name
    if not name or name in {".", ".."}:
        raise ValueError("vault state filename is invalid")
    return name


def _stat_at(path: Path, directory_fd: int) -> os.stat_result:
    return os.stat(_relative_name(path), dir_fd=directory_fd, follow_symlinks=False)


def private_file_exists(path: Path) -> bool:
    try:
        with private_directory_fd(path.parent, create=False) as directory_fd:
            try:
                info = _stat_at(path, directory_fd)
            except FileNotFoundError:
                return False
            if not stat.S_ISREG(info.st_mode):
                raise PermissionError("vault state path must be a regular file")
            if _is_posix() and (info.st_uid != os.geteuid() or info.st_nlink != 1):
                raise PermissionError("vault state file ownership or link count is unsafe")
            return True
    except FileNotFoundError:
        return False


def private_file_stat(path: Path) -> os.stat_result | None:
    """Return validated file metadata without following links."""

    try:
        with private_directory_fd(path.parent, create=False) as directory_fd:
            try:
                info = _stat_at(path, directory_fd)
            except FileNotFoundError:
                return None
            if not stat.S_ISREG(info.st_mode):
                raise PermissionError("vault state path must be a regular file")
            if _is_posix() and (info.st_uid != os.geteuid() or info.st_nlink != 1):
                raise PermissionError("vault state file ownership or link count is unsafe")
            return info
    except FileNotFoundError:
        return None


def _open_file_fd(
    path: Path,
    flags: int,
    *,
    create_mode: int = PRIVATE_FILE_MODE,
    create_parent: bool = True,
    repair_mode: bool = False,
) -> int:
    with private_directory_fd(path.parent, create=create_parent) as directory_fd:
        try:
            fd = os.open(_relative_name(path), _open_flags(flags), create_mode, dir_fd=directory_fd)
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise PermissionError("vault state path must not be a symbolic link") from None
            raise
        try:
            _validate_private_file(fd, repair_mode=repair_mode)
        except Exception:
            os.close(fd)
            raise
        return fd


def read_private_text(path: Path) -> str:
    fd = _open_file_fd(path, os.O_RDONLY, create_parent=False)
    with os.fdopen(fd, "r", encoding="utf-8") as handle:
        return handle.read()


def read_private_bytes(path: Path) -> bytes:
    fd = _open_file_fd(path, os.O_RDONLY, create_parent=False)
    with os.fdopen(fd, "rb") as handle:
        return handle.read()


def read_private_json(path: Path) -> object:
    return json.loads(read_private_text(path))


def _validate_replace_target(path: Path, directory_fd: int) -> None:
    try:
        info = _stat_at(path, directory_fd)
    except FileNotFoundError:
        return
    if not stat.S_ISREG(info.st_mode):
        raise PermissionError("vault state replacement target must be a regular file")
    if _is_posix() and (info.st_uid != os.geteuid() or info.st_nlink != 1):
        raise PermissionError("vault state replacement target ownership or link count is unsafe")


def write_private_text(path: Path, text: str) -> None:
    """Atomically replace a private state file using a unique exclusive temporary file."""

    with private_directory_fd(path.parent) as directory_fd:
        temp_name = f".{_relative_name(path)}.{secrets.token_hex(12)}.tmp"
        fd = os.open(
            temp_name,
            _open_flags(os.O_WRONLY, os.O_CREAT, os.O_EXCL),
            PRIVATE_FILE_MODE,
            dir_fd=directory_fd,
        )
        try:
            _validate_private_file(fd, repair_mode=True)
            handle_fd = fd
            fd = -1
            with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            _validate_replace_target(path, directory_fd)
            os.replace(temp_name, _relative_name(path), src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
            os.fsync(directory_fd)
        except Exception:
            if fd >= 0:
                os.close(fd)
            try:
                os.unlink(temp_name, dir_fd=directory_fd)
            except OSError as exc:
                if exc.errno != errno.ENOENT:
                    raise
            raise


def write_private_json(path: Path, payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    write_private_text(path, text)


def append_private_line(path: Path, line: str) -> None:
    if "\n" in line or "\r" in line:
        raise ValueError("private line must not contain line breaks")
    payload = f"{line}\n".encode("utf-8")
    fd = _open_file_fd(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, repair_mode=True)
    try:
        written = os.write(fd, payload)
        if written != len(payload):
            raise OSError("incomplete private line append")
        os.fsync(fd)
    finally:
        os.close(fd)


@contextmanager
def open_private_lock(path: Path) -> Iterator[TextIO]:
    fd = _open_file_fd(path, os.O_RDWR | os.O_APPEND | os.O_CREAT, repair_mode=True)
    with os.fdopen(fd, "a+", encoding="utf-8") as handle:
        yield handle
