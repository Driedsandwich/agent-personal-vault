#!/usr/bin/env python3
"""Create and verify the exact artifact bundle approved for package publish."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tarfile
import tomllib
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any


SCHEMA = "apv-release-artifact-manifest/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def distribution_files(dist_dir: Path) -> list[Path]:
    files = sorted(
        path
        for path in dist_dir.iterdir()
        if path.is_file() and not path.is_symlink() and (path.suffix == ".whl" or path.name.endswith(".tar.gz"))
    )
    wheels = [path for path in files if path.suffix == ".whl"]
    sdists = [path for path in files if path.name.endswith(".tar.gz")]
    if len(files) != 2 or len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("release bundle must contain exactly one wheel and one sdist")
    return files


def _normalized_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def project_identity(pyproject_path: Path) -> dict[str, Any]:
    project = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]
    readme = project.get("readme", "")
    readme_path = str(readme) if isinstance(readme, str) else str(readme.get("file", ""))
    if readme_path.lower().endswith(".md"):
        description_content_type = "text/markdown"
    elif readme_path.lower().endswith(".rst"):
        description_content_type = "text/x-rst"
    else:
        description_content_type = "text/plain"
    return {
        "name": str(project["name"]),
        "version": str(project["version"]),
        "summary": str(project.get("description", "")),
        "requires_python": str(project.get("requires-python", "")),
        "description_content_type": description_content_type,
        "project_urls": {str(key): str(value) for key, value in sorted(project.get("urls", {}).items())},
    }


def _embedded_metadata_bytes(path: Path) -> bytes:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as wheel:
            names = [name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")]
            if len(names) != 1:
                raise ValueError("wheel must contain exactly one METADATA file")
            return wheel.read(names[0])
    if path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as sdist:
            members = [
                member
                for member in sdist.getmembers()
                if member.isfile() and Path(member.name).name == "PKG-INFO" and len(Path(member.name).parts) == 2
            ]
            if len(members) != 1:
                raise ValueError("sdist must contain exactly one PKG-INFO file")
            extracted = sdist.extractfile(members[0])
            if extracted is None:
                raise ValueError("sdist PKG-INFO is unreadable")
            return extracted.read()
    raise ValueError("unsupported distribution type")


def embedded_metadata(path: Path) -> dict[str, Any]:
    raw = _embedded_metadata_bytes(path)
    message = BytesParser(policy=policy.default).parsebytes(raw)
    urls: dict[str, str] = {}
    for entry in message.get_all("Project-URL", []):
        label, separator, url = str(entry).partition(",")
        if not separator or not label.strip() or not url.strip() or label.strip() in urls:
            raise ValueError("distribution Project-URL metadata is invalid")
        urls[label.strip()] = url.strip()
    metadata = {
        "metadata_sha256": hashlib.sha256(raw).hexdigest(),
        "metadata_version": str(message.get("Metadata-Version", "")),
        "name": str(message.get("Name", "")),
        "version": str(message.get("Version", "")),
        "summary": str(message.get("Summary", "")),
        "requires_python": str(message.get("Requires-Python", "")),
        "description_content_type": str(message.get("Description-Content-Type", "")).split(";", 1)[0].strip(),
        "project_urls": dict(sorted(urls.items())),
    }
    if not metadata["metadata_version"] or not metadata["name"] or not metadata["version"]:
        raise ValueError("distribution core metadata is incomplete")
    return metadata


def _validate_embedded_identity(metadata: dict[str, Any], project: dict[str, Any]) -> None:
    for key in ("version", "summary", "requires_python", "description_content_type", "project_urls"):
        if metadata.get(key) != project.get(key):
            raise ValueError(f"distribution metadata does not match pyproject: {key}")
    if _normalized_name(str(metadata.get("name", ""))) != _normalized_name(str(project.get("name", ""))):
        raise ValueError("distribution metadata does not match pyproject: name")


def create_manifest(*, dist_dir: Path, pyproject_path: Path, tag: str, commit: str) -> dict[str, Any]:
    project = project_identity(pyproject_path)
    if tag != f"v{project['version']}":
        raise ValueError("release tag does not match project version")
    if not COMMIT_RE.fullmatch(commit):
        raise ValueError("release commit must be a full lowercase Git SHA")
    artifacts = []
    for path in distribution_files(dist_dir):
        metadata = embedded_metadata(path)
        _validate_embedded_identity(metadata, project)
        artifacts.append(
            {
                "name": path.name,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
                "embedded_metadata": metadata,
            }
        )
    return {
        "schema": SCHEMA,
        "source": {"tag": tag, "commit": commit},
        "package": project,
        "artifacts": artifacts,
    }


def validate_manifest_shape(manifest: object) -> dict[str, Any]:
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise ValueError("artifact manifest schema is invalid")
    source = manifest.get("source")
    package = manifest.get("package")
    artifacts = manifest.get("artifacts")
    if not isinstance(source, dict) or not isinstance(package, dict) or not isinstance(artifacts, list):
        raise ValueError("artifact manifest shape is invalid")
    tag = source.get("tag")
    commit = source.get("commit")
    version = package.get("version")
    name = package.get("name")
    if not isinstance(name, str) or not name or not isinstance(tag, str) or not isinstance(version, str) or tag != f"v{version}":
        raise ValueError("artifact manifest tag/version identity is invalid")
    if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
        raise ValueError("artifact manifest commit identity is invalid")
    return manifest


def verify_manifest(
    *,
    dist_dir: Path,
    manifest: object,
    expected_tag: str | None = None,
    expected_commit: str | None = None,
    pyproject_path: Path | None = None,
) -> dict[str, Any]:
    validated = validate_manifest_shape(manifest)
    if expected_tag is not None and validated["source"]["tag"] != expected_tag:
        raise ValueError("artifact manifest does not match the approved tag")
    if expected_commit is not None and validated["source"]["commit"] != expected_commit:
        raise ValueError("artifact manifest does not match the approved commit")
    if pyproject_path is not None and validated["package"] != project_identity(pyproject_path):
        raise ValueError("artifact manifest package identity does not match pyproject")
    records = validated["artifacts"]
    if len(records) != 2:
        raise ValueError("artifact manifest must describe exactly two distributions")
    expected: dict[str, tuple[int, str, dict[str, Any]]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("artifact manifest record is invalid")
        name = record.get("name")
        size = record.get("size")
        digest = record.get("sha256")
        metadata = record.get("embedded_metadata")
        if (
            not isinstance(name, str)
            or Path(name).name != name
            or not isinstance(size, int)
            or size < 0
            or not isinstance(digest, str)
            or not SHA256_RE.fullmatch(digest)
            or not isinstance(metadata, dict)
            or name in expected
        ):
            raise ValueError("artifact manifest record is invalid")
        expected[name] = (size, digest, metadata)

    files = distribution_files(dist_dir)
    if {path.name for path in files} != set(expected):
        raise ValueError("artifact set does not match the approved manifest")
    for path in files:
        size, digest, recorded_metadata = expected[path.name]
        if path.stat().st_size != size or sha256_file(path) != digest:
            raise ValueError(f"artifact bytes do not match the approved manifest: {path.name}")
        actual_metadata = embedded_metadata(path)
        if actual_metadata != recorded_metadata:
            raise ValueError(f"artifact metadata does not match the approved manifest: {path.name}")
        _validate_embedded_identity(actual_metadata, validated["package"])
    return validated


def write_bundle(*, dist_dir: Path, bundle_dir: Path, manifest: dict[str, Any]) -> Path:
    if bundle_dir.exists():
        raise FileExistsError("release bundle output already exists")
    bundle_dist = bundle_dir / "dist"
    bundle_dist.mkdir(parents=True)
    for path in distribution_files(dist_dir):
        shutil.copyfile(path, bundle_dist / path.name)
    manifest_path = bundle_dir / "artifact-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    verify_manifest(dist_dir=bundle_dist, manifest=manifest)
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--tag", required=True)
    create.add_argument("--commit", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--tag", required=True)
    verify.add_argument("--commit", required=True)
    args = parser.parse_args()

    dist_dir = Path("dist") if args.command == "create" else Path("release-bundle/dist")
    manifest_path = Path("release-bundle/artifact-manifest.json")
    pyproject_path = Path("pyproject.toml")

    if args.command == "create":
        manifest = create_manifest(
            dist_dir=dist_dir,
            pyproject_path=pyproject_path,
            tag=args.tag,
            commit=args.commit,
        )
        manifest_path = write_bundle(dist_dir=dist_dir, bundle_dir=Path("release-bundle"), manifest=manifest)
        print(manifest_path.read_text(encoding="utf-8"), end="")
        return 0

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verify_manifest(
        dist_dir=dist_dir,
        manifest=manifest,
        expected_tag=args.tag,
        expected_commit=args.commit,
        pyproject_path=pyproject_path,
    )
    print("artifact manifest verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
