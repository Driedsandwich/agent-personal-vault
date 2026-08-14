"""Fail-closed coordination for versioned KDF migrations."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Iterator

from .private_io import exclusive_private_lock, lexical_absolute_path, private_file_exists


class KDFMigrationIncompleteError(RuntimeError):
    """Raised when a normal write encounters an unfinished KDF migration."""


_ACTIVE_GUARDS: ContextVar[frozenset[str]] = ContextVar("apv_kdf_migration_guards", default=frozenset())


def migration_journal_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(vault_path.suffix + ".kdf-migration.json")


def migration_lock_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(vault_path.suffix + ".kdf-migration.lock")


def migration_incomplete(vault_path: Path) -> bool:
    return private_file_exists(migration_journal_path(vault_path))


@contextmanager
def kdf_write_guard(vault_path: Path, *, allow_incomplete: bool = False) -> Iterator[None]:
    """Serialize state writes with migration and reject unfinished transactions."""

    key = str(lexical_absolute_path(vault_path))
    active = _ACTIVE_GUARDS.get()
    if key in active:
        if migration_incomplete(vault_path) and not allow_incomplete:
            raise KDFMigrationIncompleteError("encryption migration is incomplete; use resume or rollback")
        yield
        return
    with exclusive_private_lock(migration_lock_path(vault_path)):
        if migration_incomplete(vault_path) and not allow_incomplete:
            raise KDFMigrationIncompleteError("encryption migration is incomplete; use resume or rollback")
        token = _ACTIVE_GUARDS.set(active | {key})
        try:
            yield
        finally:
            _ACTIVE_GUARDS.reset(token)
