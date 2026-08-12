#!/usr/bin/env python3
"""Run non-destructive local release-readiness checks."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

try:
    from scripts.release_policy import SKIP_DIRS, iter_release_files
except ModuleNotFoundError:
    from release_policy import SKIP_DIRS, iter_release_files

ROOT = Path(__file__).resolve().parent.parent


def run_step(name: str, command: list[str], *, env: dict[str, str] | None = None) -> None:
    print(f"== {name}")
    subprocess.run(command, cwd=ROOT, check=True, env=env)


def compile_python_sources() -> None:
    print("== compile Python sources without writing bytecode")
    python_files = sorted(path for path in iter_release_files(ROOT) if path.suffix == ".py")
    if not python_files:
        raise SystemExit("no Python sources found")
    for path in python_files:
        compile(path.read_text(encoding="utf-8", errors="strict"), str(path), "exec")
    print(f"compiled {len(python_files)} Python sources")


def main() -> int:
    compile_python_sources()
    test_env = os.environ.copy()
    test_env["PYTHONDONTWRITEBYTECODE"] = "1"
    run_step("unit tests", [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"], env=test_env)
    run_step("source privacy scan", [sys.executable, "-B", "scripts/pii_scan.py"], env=test_env)
    print("release checks passed; existing build outputs were not modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
