#!/usr/bin/env python3
"""Apply the shared fail-closed release privacy policy to wheel and sdist."""

from __future__ import annotations

import stat
import sys
import tarfile
import zipfile
from pathlib import Path

try:
    from scripts.release_policy import PolicyFinding, ReleasePolicyError, scan_release_entry
except ModuleNotFoundError:
    from release_policy import PolicyFinding, ReleasePolicyError, scan_release_entry


def _scan_wheel(path: Path) -> tuple[int, list[PolicyFinding]]:
    findings: list[PolicyFinding] = []
    count = 0
    seen: set[str] = set()
    with zipfile.ZipFile(path) as wheel:
        for info in wheel.infolist():
            if info.is_dir():
                continue
            if info.filename in seen:
                raise ReleasePolicyError("wheel contains a duplicate entry")
            seen.add(info.filename)
            mode = (info.external_attr >> 16) & 0xFFFF
            file_type = stat.S_IFMT(mode)
            if file_type and file_type != stat.S_IFREG:
                raise ReleasePolicyError("wheel contains a non-regular entry")
            findings.extend(scan_release_entry(info.filename, wheel.read(info)))
            count += 1
    return count, findings


def _scan_sdist(path: Path) -> tuple[int, list[PolicyFinding]]:
    findings: list[PolicyFinding] = []
    count = 0
    seen: set[str] = set()
    with tarfile.open(path, "r:gz") as sdist:
        for member in sdist.getmembers():
            if member.isdir():
                continue
            if member.name in seen:
                raise ReleasePolicyError("sdist contains a duplicate entry")
            seen.add(member.name)
            if not member.isfile():
                raise ReleasePolicyError("sdist contains a non-regular entry")
            extracted = sdist.extractfile(member)
            if extracted is None:
                raise ReleasePolicyError("sdist entry is unreadable")
            findings.extend(scan_release_entry(member.name, extracted.read()))
            count += 1
    return count, findings


def scan_artifacts(dist_dir: Path) -> list[PolicyFinding]:
    if not dist_dir.is_dir() or dist_dir.is_symlink():
        raise ReleasePolicyError("artifact directory is missing or unsafe")
    artifacts = sorted(dist_dir.iterdir())
    if not artifacts:
        raise ReleasePolicyError("artifact inventory is empty")
    for artifact in artifacts:
        if artifact.is_symlink() or not artifact.is_file():
            raise ReleasePolicyError("artifact inventory contains a non-regular entry")
    wheels = [path for path in artifacts if path.suffix == ".whl"]
    sdists = [path for path in artifacts if path.name.endswith(".tar.gz")]
    if len(artifacts) != 2 or len(wheels) != 1 or len(sdists) != 1:
        raise ReleasePolicyError("artifact inventory must contain exactly one wheel and one sdist")
    findings: list[PolicyFinding] = []
    for artifact in artifacts:
        if artifact.suffix == ".whl":
            count, artifact_findings = _scan_wheel(artifact)
        elif artifact.name.endswith(".tar.gz"):
            count, artifact_findings = _scan_sdist(artifact)
        else:
            raise ReleasePolicyError("unexpected artifact type")
        if count == 0:
            raise ReleasePolicyError("release artifact has no regular entries")
        findings.extend(artifact_findings)
    return findings


def main(dist_dir: Path | None = None) -> int:
    dist_dir = Path.cwd() / "dist" if dist_dir is None else dist_dir
    try:
        findings = scan_artifacts(dist_dir)
    except (OSError, ReleasePolicyError, tarfile.TarError, zipfile.BadZipFile) as exc:
        print(f"release artifact scan incomplete: {exc}", file=sys.stderr)
        return 1
    if findings:
        print("Potential private artifact content found:", file=sys.stderr)
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 1
    print("Release privacy policy passed for every artifact entry.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("usage: scan_release_artifacts.py", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main())
