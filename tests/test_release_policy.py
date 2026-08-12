from __future__ import annotations

import io
import json
import os
import subprocess
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from scripts import check_release
from scripts.release_policy import ReleasePolicyError, iter_release_files, scan_release_entry, scan_release_tree
from scripts.scan_release_artifacts import scan_artifacts


class ReleasePolicyTests(unittest.TestCase):
    def _write_clean_artifacts(self, dist: Path) -> None:
        with zipfile.ZipFile(dist / "example-1.0-py3-none-any.whl", "w") as wheel:
            wheel.writestr("example/__init__.py", b'__version__ = "1.0"\n')
        with tarfile.open(dist / "example-1.0.tar.gz", "w:gz") as sdist:
            data = b'__version__ = "1.0"\n'
            member = tarfile.TarInfo("example-1.0/example/__init__.py")
            member.size = len(data)
            sdist.addfile(member, io.BytesIO(data))

    def test_shared_policy_rejects_private_text_and_undecodable_content(self) -> None:
        private_email = "private.person@" + "private.invalid"
        payload = f'contact = "{private_email}"\n'.encode()
        source = scan_release_entry("package/example.py", payload)
        artifact = scan_release_entry("example/package/example.py", payload)
        undecodable = scan_release_entry("package/data.bin", b"\xff\xfe")

        self.assertEqual([finding.rule for finding in source], ["non-example-email"])
        self.assertEqual([finding.rule for finding in artifact], ["non-example-email"])
        self.assertEqual([finding.rule for finding in undecodable], ["undecodable-content"])

    def test_non_git_inventory_rejects_empty_and_symbolic_link_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ReleasePolicyError, "inventory is empty"):
                iter_release_files(root)
            target = root / "target.txt"
            target.write_text("safe\n", encoding="utf-8")
            (root / "alias.txt").symlink_to(target)
            with self.assertRaisesRegex(ReleasePolicyError, "symbolic-link"):
                iter_release_files(root)

    def test_git_inventory_rejects_missing_tracked_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            tracked = root / "tracked.txt"
            tracked.write_text("safe\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
            tracked.unlink()
            with self.assertRaisesRegex(ReleasePolicyError, "tracked release entry is missing"):
                iter_release_files(root)

    def test_artifact_scan_requires_complete_pair_and_rejects_nonregular_member(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            with zipfile.ZipFile(dist / "example-1.0-py3-none-any.whl", "w") as wheel:
                wheel.writestr("example/__init__.py", b"safe\n")
            with self.assertRaisesRegex(ReleasePolicyError, "exactly one wheel and one sdist"):
                scan_artifacts(dist)

            with tarfile.open(dist / "example-1.0.tar.gz", "w:gz") as sdist:
                member = tarfile.TarInfo("example-1.0/link")
                member.type = tarfile.SYMTYPE
                member.linkname = "target"
                sdist.addfile(member)
            with self.assertRaisesRegex(ReleasePolicyError, "non-regular entry"):
                scan_artifacts(dist)

    def test_release_entry_rejects_noncanonical_path(self) -> None:
        for name in (
            "../escape.txt",
            "/absolute.txt",
            "C:/absolute.txt",
            "folder\\windows.txt",
            "folder//empty.txt",
            "folder/null\x00name.txt",
        ):
            with self.subTest(name=name), self.assertRaisesRegex(ReleasePolicyError, "not canonical"):
                scan_release_entry(name, b"safe\n")

    def test_private_entry_name_is_detected_without_echo(self) -> None:
        private_email = "private.person@" + "private.invalid"
        name = f"package/{private_email}/notes.txt"
        rendered = "\n".join(finding.render() for finding in scan_release_entry(name, b"safe\n"))

        self.assertIn("non-example-email", rendered)
        self.assertIn("entry-sha256:", rendered)
        self.assertNotIn(private_email, rendered)

    def test_artifact_scan_uses_shared_policy_for_every_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            self._write_clean_artifacts(dist)
            self.assertEqual(scan_artifacts(dist), [])

            with zipfile.ZipFile(dist / "example-1.0-py3-none-any.whl", "a") as wheel:
                private_email = "private.person@" + "private.invalid"
                wheel.writestr("example/private.txt", f"{private_email}\n".encode())
            findings = scan_artifacts(dist)
            self.assertTrue(any(finding.rule == "non-example-email" for finding in findings))

    def test_release_check_preserves_preexisting_build_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "tests").mkdir()
            (root / "dist").mkdir()
            for name in ("check_release.py", "pii_scan.py", "release_policy.py"):
                (root / "scripts" / name).write_bytes((Path("scripts") / name).read_bytes())
            (root / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "tests" / "test_example.py").write_text(
                "import unittest\n\nclass ExampleTests(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            marker = root / "dist" / "reviewed-artifact.marker"
            marker.write_text("preserve exact bytes\n", encoding="utf-8")
            before = marker.read_bytes()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "example.py", "scripts", "tests"], check=True)

            with mock.patch.object(check_release, "ROOT", root):
                self.assertEqual(check_release.main(), 0)

            self.assertEqual(marker.read_bytes(), before)
            self.assertFalse((root / "__pycache__").exists())
            self.assertFalse((root / "tests" / "__pycache__").exists())

    def test_source_scan_rejects_private_data_without_echoing_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = "private.person@" + "private.invalid"
            (root / "note.txt").write_text(payload, encoding="utf-8")
            findings = scan_release_tree(root)
            rendered = "\n".join(finding.render() for finding in findings)
            self.assertIn("non-example-email", rendered)
            self.assertNotIn(payload, rendered)


if __name__ == "__main__":
    unittest.main()
