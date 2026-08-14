#!/usr/bin/env python3
"""Measure candidate local encryption KDF profiles with synthetic inputs."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import time
from concurrent.futures import ProcessPoolExecutor

from cryptography import __version__ as cryptography_version
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


SYNTHETIC_PASSPHRASE = b"correct horse battery staple"
SYNTHETIC_SALT = b"synthetic-salt!"
PROFILES = {
    "argon2id-19m-t2-p1": ("argon2id", {"memory_cost": 19 * 1024, "iterations": 2, "lanes": 1}),
    "argon2id-32m-t2-p1": ("argon2id", {"memory_cost": 32 * 1024, "iterations": 2, "lanes": 1}),
    "argon2id-64m-t2-p1": ("argon2id", {"memory_cost": 64 * 1024, "iterations": 2, "lanes": 1}),
    "pbkdf2-sha256-600k": ("pbkdf2", {"iterations": 600_000}),
    "pbkdf2-sha256-1200k": ("pbkdf2", {"iterations": 1_200_000}),
}


def _derive(profile_name: str) -> tuple[str, float]:
    kind, parameters = PROFILES[profile_name]
    started = time.perf_counter()
    if kind == "argon2id":
        Argon2id(
            salt=SYNTHETIC_SALT,
            length=32,
            iterations=parameters["iterations"],
            lanes=parameters["lanes"],
            memory_cost=parameters["memory_cost"],
        ).derive(SYNTHETIC_PASSPHRASE)
    else:
        PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=SYNTHETIC_SALT,
            iterations=parameters["iterations"],
        ).derive(SYNTHETIC_PASSPHRASE)
    return profile_name, (time.perf_counter() - started) * 1000


def _normal_measurements(runs: int) -> dict[str, dict[str, float | int]]:
    results: dict[str, dict[str, float | int]] = {}
    for profile_name in PROFILES:
        _derive(profile_name)
        values = [_derive(profile_name)[1] for _ in range(runs)]
        results[profile_name] = {
            "runs": runs,
            "median_ms": round(statistics.median(values), 3),
            "min_ms": round(min(values), 3),
            "max_ms": round(max(values), 3),
        }
    return results


def _contended_measurements(workers: int, operations: int) -> dict[str, dict[str, float | int]]:
    results: dict[str, dict[str, float | int]] = {}
    for profile_name in PROFILES:
        started = time.perf_counter()
        with ProcessPoolExecutor(max_workers=workers) as executor:
            values = [duration for _name, duration in executor.map(_derive, [profile_name] * operations)]
        results[profile_name] = {
            "workers": workers,
            "operations": operations,
            "median_ms": round(statistics.median(values), 3),
            "max_ms": round(max(values), 3),
            "batch_wall_ms": round((time.perf_counter() - started) * 1000, 3),
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=7)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--operations", type=int, default=12)
    args = parser.parse_args()
    if args.runs < 1 or args.workers < 1 or args.operations < args.workers:
        parser.error("runs/workers must be positive and operations must be at least workers")

    result = {
        "schema": "apv-kdf-benchmark/v1",
        "synthetic_only": True,
        "environment": {
            "platform": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "logical_cpus": os.cpu_count(),
            "cryptography": cryptography_version,
        },
        "normal_single_process": _normal_measurements(args.runs),
        "constrained_proxy_four_competing_processes": _contended_measurements(args.workers, args.operations),
        "notes": [
            "Synthetic benchmark only; the constrained profile uses competing worker processes and is not a physical low-end device measurement.",
            "Timing is design evidence, not a CI pass/fail threshold.",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
