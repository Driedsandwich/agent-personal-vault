from __future__ import annotations

import contextlib
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path

from scripts import check_release, pii_scan, release_artifact_manifest, release_policy


class ReleaseCheckTests(unittest.TestCase):
    def test_current_publication_gate_and_consent_guidance_match_published_state(self) -> None:
        root = Path(__file__).resolve().parent.parent
        candidate = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        gate = (root / "docs" / "PUBLICATION_GATE.md").read_text(encoding="utf-8")
        readiness = (root / "docs" / "RELEASE_READINESS.md").read_text(encoding="utf-8")
        readme = (root / "README.md").read_text(encoding="utf-8")
        mcp_setup = (root / "docs" / "MCP_CLIENT_SETUP.md").read_text(encoding="utf-8")
        dry_run = (root / "docs" / "RELEASE_PACKAGE_DRY_RUN_PLAN.md").read_text(encoding="utf-8")

        gate_release = re.search(r"Latest GitHub prerelease: `v([^`]+)`", gate)
        gate_package = re.search(r"Latest PyPI package: `([^`]+)`", gate)
        readiness_release = re.search(r"Latest GitHub prerelease: `v([^`]+)`", readiness)
        readiness_package = re.search(r"Latest PyPI package: `([^`]+)`", readiness)
        self.assertIsNotNone(gate_release)
        self.assertIsNotNone(gate_package)
        self.assertIsNotNone(readiness_release)
        self.assertIsNotNone(readiness_package)

        published = gate_package.group(1)
        self.assertEqual(gate_release.group(1), published)
        self.assertEqual(readiness_release.group(1), published)
        self.assertEqual(readiness_package.group(1), published)
        self.assertIn(f"Treat `v{published}` as the latest published prerelease", gate)

        candidate_parts = tuple(map(int, candidate.split(".")))
        published_parts = tuple(map(int, published.split(".")))
        self.assertIn(
            candidate_parts,
            (published_parts, (*published_parts[:2], published_parts[2] + 1)),
        )
        self.assertIn("`consent list` はtokenを `c_[redacted]` として表示", readme)
        self.assertIn("consent idは復元できません", readme)
        self.assertIn("`consent list` はtokenを `c_[redacted]` として表示", mcp_setup)
        self.assertIn("consent idを失った場合は復元できない", mcp_setup)
        self.assertIn("新しいrequestを作成", mcp_setup)
        self.assertNotIn("`consent list` で未使用tokenを確認", mcp_setup)

        candidate_heading = re.search(
            rf"^## v{re.escape(candidate)} .* Patch Candidate Dry-Run$",
            dry_run,
            re.MULTILINE,
        )
        self.assertIsNotNone(candidate_heading)
        assert candidate_heading is not None
        candidate_start = candidate_heading.start()
        following = dry_run[candidate_heading.end() :]
        next_heading = re.search(r"^## v\d+\.\d+\.\d+ .* Patch Candidate Dry-Run$", following, re.MULTILINE)
        candidate_end = (
            len(dry_run)
            if next_heading is None
            else candidate_heading.end() + next_heading.start()
        )
        candidate_dry_run = dry_run[candidate_start:candidate_end]

        local_table = candidate_dry_run.index("Artifact records:")
        local_disclaimer = candidate_dry_run.index("These hashes identify this dry-run's files only.")
        stop_conditions = candidate_dry_run.index("Stop conditions before any later merge or publish lane:")
        self.assertLess(local_table, local_disclaimer)
        self.assertLess(local_disclaimer, stop_conditions)

    def test_required_test_workflow_pins_third_party_actions(self) -> None:
        root = Path(__file__).resolve().parent.parent
        workflow = (root / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        references = re.findall(r"uses:\s*([^@\s]+)@([^\s#]+)", workflow)

        self.assertEqual(len(references), 4)
        for action, revision in references:
            with self.subTest(action=action):
                self.assertRegex(revision, r"\A[0-9a-f]{40}\Z")

    def test_release_scanner_clis_reject_path_arguments_without_echoing_them(self) -> None:
        root = Path(__file__).resolve().parent.parent
        private_path = "/" + "Users" + "/example/private"

        for script in ("scripts/pii_scan.py", "scripts/scan_release_artifacts.py"):
            result = subprocess.run(
                [sys.executable, script, private_path],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("usage:", result.stderr)
            self.assertNotIn(private_path, result.stderr)

    def _manifest_fixture(self, root: Path) -> tuple[Path, Path]:
        dist = root / "dist"
        dist.mkdir()
        metadata = (
            "Metadata-Version: 2.4\n"
            "Name: agent-personal-vault\n"
            "Version: 1.2.3\n"
            "Summary: Fixture package\n"
            "Requires-Python: >=3.11\n"
            "Description-Content-Type: text/markdown\n"
            "Project-URL: Homepage, https://example.test/project\n"
            "\n"
            "# Fixture\n"
        ).encode()
        wheel = dist / "agent_personal_vault-1.2.3-py3-none-any.whl"
        with zipfile.ZipFile(wheel, "w") as archive:
            archive.writestr("agent_personal_vault-1.2.3.dist-info/METADATA", metadata)
        sdist = dist / "agent_personal_vault-1.2.3.tar.gz"
        with tarfile.open(sdist, "w:gz") as archive:
            info = tarfile.TarInfo("agent_personal_vault-1.2.3/PKG-INFO")
            info.size = len(metadata)
            archive.addfile(info, io.BytesIO(metadata))
        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            '[project]\n'
            'name = "agent-personal-vault"\n'
            'version = "1.2.3"\n'
            'description = "Fixture package"\n'
            'requires-python = ">=3.11"\n'
            'readme = "README.md"\n'
            '[project.urls]\n'
            'Homepage = "https://example.test/project"\n',
            encoding="utf-8",
        )
        return dist, pyproject

    def test_release_artifact_manifest_binds_exact_bytes_and_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist, pyproject = self._manifest_fixture(root)
            commit = "a" * 40
            manifest = release_artifact_manifest.create_manifest(
                dist_dir=dist,
                pyproject_path=pyproject,
                tag="v1.2.3",
                commit=commit,
            )

            verified = release_artifact_manifest.verify_manifest(
                dist_dir=dist,
                manifest=manifest,
                expected_tag="v1.2.3",
                expected_commit=commit,
                pyproject_path=pyproject,
            )

            self.assertEqual(verified["source"], {"tag": "v1.2.3", "commit": commit})
            self.assertEqual(len(verified["artifacts"]), 2)
            for artifact in verified["artifacts"]:
                self.assertEqual(artifact["embedded_metadata"]["name"], "agent-personal-vault")
                self.assertEqual(artifact["embedded_metadata"]["version"], "1.2.3")
                self.assertEqual(
                    artifact["embedded_metadata"]["project_urls"],
                    {"Homepage": "https://example.test/project"},
                )

    def test_release_artifact_manifest_rejects_embedded_metadata_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist, pyproject = self._manifest_fixture(root)
            pyproject.write_text(pyproject.read_text().replace('version = "1.2.3"', 'version = "1.2.4"'))

            with self.assertRaisesRegex(ValueError, "distribution metadata does not match pyproject: version"):
                release_artifact_manifest.create_manifest(
                    dist_dir=dist,
                    pyproject_path=pyproject,
                    tag="v1.2.4",
                    commit="c" * 40,
                )

    def test_release_artifact_manifest_rejects_tamper_and_extra_distribution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist, pyproject = self._manifest_fixture(root)
            manifest = release_artifact_manifest.create_manifest(
                dist_dir=dist,
                pyproject_path=pyproject,
                tag="v1.2.3",
                commit="b" * 40,
            )
            wheel = dist / "agent_personal_vault-1.2.3-py3-none-any.whl"
            wheel.write_bytes(b"tampered")

            with self.assertRaisesRegex(ValueError, "artifact bytes do not match"):
                release_artifact_manifest.verify_manifest(dist_dir=dist, manifest=manifest)

            (root / "fresh").mkdir()
            dist, _ = self._manifest_fixture(root / "fresh")
            (dist / "unexpected-1.2.3-py3-none-any.whl").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "exactly one wheel and one sdist"):
                release_artifact_manifest.verify_manifest(dist_dir=dist, manifest=manifest)

    def test_publish_workflow_uses_hash_locked_tools_and_verifies_bundle(self) -> None:
        root = Path(__file__).resolve().parent.parent
        workflow = (root / ".github" / "workflows" / "pypi-publish.yml").read_text(encoding="utf-8")
        requirements = (root / ".github" / "release-requirements.txt").read_text(encoding="utf-8")
        pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertIn("--require-hashes", workflow)
        self.assertIn("--only-binary=:all:", workflow)
        self.assertIn("python -m build --no-isolation", workflow)
        self.assertIn("artifact-manifest.json", workflow)
        self.assertIn("Verify exact environment-approved artifact bytes", workflow)
        self.assertIn("source_commit: ${{ steps.source_identity.outputs.commit }}", workflow)
        self.assertIn('--commit "${APV_SOURCE_COMMIT}"', workflow)
        self.assertNotIn("--pyproject", workflow)
        self.assertNotIn("--dist", workflow)
        self.assertNotIn("--manifest", workflow)
        self.assertIn('test "$(git rev-parse HEAD)" = "${APV_SOURCE_COMMIT}"', workflow)
        self.assertEqual(workflow.count("actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd"), 2)
        self.assertIn("packages-dir: release-bundle/dist/", workflow)
        self.assertNotIn("pip install --upgrade pip build twine", workflow)
        self.assertEqual(pyproject["build-system"]["requires"], ["setuptools==84.0.0"])
        self.assertIn('python-version: "3.13.14"', workflow)
        self.assertEqual(workflow.count('python-version: "3.13.14"'), 2)
        for package in ["build", "packaging", "pip", "pyproject-hooks", "setuptools"]:
            self.assertRegex(requirements, rf"(?m)^{package}==[^ ]+ \\$")
        self.assertEqual(requirements.count("--hash=sha256:"), 5)
        self.assertIn("embedded_metadata(path)", (root / "scripts" / "release_artifact_manifest.py").read_text())

    def test_pii_scan_checks_local_agent_config_without_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_path = "/" + "Users" + "/example/private"
            for dirname in release_policy.LOCAL_DEVELOPER_CONFIG_DIRS:
                local_config = root / dirname / "settings.json"
                local_config.parent.mkdir()
                local_config.write_text(f'{{"path": "{private_path}"}}', encoding="utf-8")
            for filename in release_policy.LOCAL_DEVELOPER_CONFIG_FILES:
                (root / filename).write_text(f"local path: {private_path}\n", encoding="utf-8")
            (root / "README.md").write_text("public docs only\n", encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                returncode = pii_scan.main(root)

            self.assertNotEqual(returncode, 0)
            self.assertIn("Potential private release content found:", stderr.getvalue())
            self.assertNotIn(private_path, stderr.getvalue())

    def test_release_checks_preserve_git_local_config_policy(self) -> None:
        self.assertEqual(pii_scan.SKIP_DIRS, release_policy.SKIP_DIRS)
        self.assertEqual(check_release.SKIP_DIRS, release_policy.SKIP_DIRS)
        for dirname in release_policy.LOCAL_DEVELOPER_CONFIG_DIRS:
            self.assertIn(dirname, release_policy.SKIP_DIRS)
        for filename in release_policy.LOCAL_DEVELOPER_CONFIG_FILES:
            self.assertTrue(release_policy.is_skipped_path(Path(filename)))
        self.assertTrue(pii_scan.should_scan(Path("docs") / "example.md"))

    def test_mcp_docs_include_claude_code_tool_approval_names(self) -> None:
        root = Path(__file__).resolve().parent.parent
        docs = (root / "docs" / "MCP_CLIENT_SETUP.md").read_text(encoding="utf-8")

        self.assertIn("mcp__agent-personal-vault__apv_context", docs)
        self.assertIn("mcp__agent-personal-vault__apv_request_consent", docs)
        self.assertIn("dontAsk", docs)

    def test_public_issue_forms_reject_secrets_and_link_private_reporting(self) -> None:
        root = Path(__file__).resolve().parent.parent
        template_dir = root / ".github" / "ISSUE_TEMPLATE"
        private_report_url = (
            "https://github.com/Driedsandwich/agent-personal-vault/security/advisories/new"
        )
        required_secret_classes = (
            "credentials",
            "API keys",
            "passphrases",
            "private keys",
            "cookies",
            "consent IDs",
            "tokenized GUI URLs",
        )

        public_forms = sorted(path for path in template_dir.glob("*.yml") if path.name != "config.yml")
        self.assertEqual(
            [path.name for path in public_forms],
            ["bug_report.yml", "security_report.yml"],
        )
        for form in public_forms:
            text = form.read_text(encoding="utf-8")
            guidance, safety = text.split("    id: safety", maxsplit=1)
            self.assertIn(private_report_url, text, form.name)
            for secret_class in required_secret_classes:
                self.assertIn(secret_class, guidance, form.name)
                self.assertIn(secret_class, safety, form.name)
            self.assertIn("required: true", safety, form.name)

        config = (template_dir / "config.yml").read_text(encoding="utf-8")
        security = (root / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn(private_report_url, config)
        self.assertIn(private_report_url, security)

    def test_quickstart_docs_use_venv_before_editable_install(self) -> None:
        root = Path(__file__).resolve().parent.parent
        readme = (root / "README.md").read_text(encoding="utf-8")
        mcp_docs = (root / "docs" / "MCP_CLIENT_SETUP.md").read_text(encoding="utf-8")

        for docs in [readme, mcp_docs]:
            self.assertIn("python3 -m venv .venv", docs)
            self.assertIn(". .venv/bin/activate", docs)
            self.assertLess(docs.index("python3 -m venv .venv"), docs.index("python3 -m pip install -e ."))

    def test_claude_desktop_docs_keep_ui_validation_boundary(self) -> None:
        root = Path(__file__).resolve().parent.parent
        mcp_docs = (root / "docs" / "MCP_CLIENT_SETUP.md").read_text(encoding="utf-8")
        readiness = (root / "docs" / "RELEASE_READINESS.md").read_text(encoding="utf-8")
        roadmap = (root / "docs" / "SECURITY_AND_AGENT_INTEGRATION_ROADMAP.md").read_text(encoding="utf-8")

        self.assertIn("人間作業を邪魔しない", mcp_docs)
        self.assertIn("terminal-only", readiness)
        self.assertIn("Full Claude Desktop app restart and in-app live tool-call UX remain unvalidated", readiness)
        self.assertIn("明示承認", roadmap)

    def test_release_package_dry_run_plan_keeps_publish_boundary(self) -> None:
        root = Path(__file__).resolve().parent.parent
        readme = (root / "README.md").read_text(encoding="utf-8")
        readiness = (root / "docs" / "RELEASE_READINESS.md").read_text(encoding="utf-8")
        plan = (root / "docs" / "RELEASE_PACKAGE_DRY_RUN_PLAN.md").read_text(encoding="utf-8")

        self.assertIn("docs/RELEASE_PACKAGE_DRY_RUN_PLAN.md", readme)
        self.assertIn("docs/RELEASE_PACKAGE_DRY_RUN_PLAN.md", readiness)
        for required in [
            "version",
            "changelog",
            "artifact",
            "package publish",
            "rollback",
            "provenance",
            "Security Alerts",
            "support",
            "GitHub release",
            "tag creation",
            "明示承認",
            "Claude Desktop app UI operation",
            "API-billed",
        ]:
            self.assertIn(required, plan)

    def test_agent_docs_keep_one_key_raw_boundary(self) -> None:
        root = Path(__file__).resolve().parent.parent
        readme = (root / "README.md").read_text(encoding="utf-8")
        protocol = (root / "docs" / "AGENT_PROTOCOL.md").read_text(encoding="utf-8")
        mcp_docs = (root / "docs" / "MCP_CLIENT_SETUP.md").read_text(encoding="utf-8")

        for docs in [readme, protocol]:
            self.assertNotIn('consent request --action env --key "*"', docs)
            self.assertIn("one-key", docs)
        self.assertIn("AIエージェント自身に承認コマンドを実行させない", readme)
        self.assertIn("Agents must not run approval commands for themselves", protocol)
        self.assertIn("not part of the public-alpha agent protocol", protocol)
        self.assertIn("AIエージェント自身に承認コマンドを実行させない", mcp_docs)

    def test_gitignore_covers_local_developer_config(self) -> None:
        root = Path(__file__).resolve().parent.parent
        gitignore = (root / ".gitignore").read_text(encoding="utf-8").splitlines()
        for dirname in release_policy.LOCAL_DEVELOPER_CONFIG_DIRS:
            self.assertIn(f"/{dirname}/", gitignore)
        for filename in release_policy.LOCAL_DEVELOPER_CONFIG_FILES:
            self.assertIn(f"/{filename}", gitignore)

    def test_non_git_local_developer_config_is_release_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            private_path = "/" + "Users" + "/example/private"
            for dirname in release_policy.LOCAL_DEVELOPER_CONFIG_DIRS:
                local_config = root / dirname / "settings.json"
                local_config.parent.mkdir()
                local_config.write_text(f'{{"path": "{private_path}"}}', encoding="utf-8")
            for filename in release_policy.LOCAL_DEVELOPER_CONFIG_FILES:
                (root / filename).write_text(f"local path: {private_path}\n", encoding="utf-8")
            (root / "README.md").write_text("public docs only\n", encoding="utf-8")

            files = {path.relative_to(root) for path in release_policy.iter_release_files(root)}

            expected = {Path("README.md"), *map(Path, release_policy.LOCAL_DEVELOPER_CONFIG_FILES)}
            expected.update(Path(dirname) / "settings.json" for dirname in release_policy.LOCAL_DEVELOPER_CONFIG_DIRS)
            self.assertEqual(files, expected)

    def test_non_git_root_local_agent_config_files_are_release_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            private_path = "/" + "Users" + "/example/private"
            for filename in release_policy.LOCAL_DEVELOPER_CONFIG_FILES:
                (root / filename).write_text(f"local path: {private_path}\n", encoding="utf-8")
            (root / "README.md").write_text("public docs only\n", encoding="utf-8")

            files = {path.relative_to(root) for path in release_policy.iter_release_files(root)}

            self.assertEqual(files, {Path("README.md"), *map(Path, release_policy.LOCAL_DEVELOPER_CONFIG_FILES)})

    def test_untracked_codex_hooks_do_not_trigger_release_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            tracked = root / "README.md"
            tracked.write_text("public docs only\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            local_hook = root / ".codex" / "hooks.json"
            local_hook.parent.mkdir()
            local_hook.write_text(
                '{"path": "/' + 'Users/example/private", "token": "sk-' + 'localdeveloperartifact000000"}\n',
                encoding="utf-8",
            )

            files = {path.relative_to(root) for path in release_policy.iter_release_files(root)}
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                returncode = pii_scan.main(root)

            self.assertEqual(files, {Path("README.md")})
            self.assertEqual(returncode, 0, stderr.getvalue())

    def test_shared_policy_rejects_non_git_local_developer_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for dirname in release_policy.LOCAL_DEVELOPER_CONFIG_DIRS:
                local_file = root / dirname / "local-screenshot.png"
                local_file.parent.mkdir()
                local_file.write_bytes(b"local artifact only")
            (root / "README.md").write_text("public docs only\n", encoding="utf-8")

            findings = release_policy.scan_release_tree(root)
            self.assertEqual(
                sum(finding.rule == "forbidden-suffix:.png" for finding in findings),
                len(release_policy.LOCAL_DEVELOPER_CONFIG_DIRS),
            )

    def test_release_files_use_git_tracked_files_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            tracked = root / "README.md"
            tracked.write_text("public docs only\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            (root / ".codex").mkdir()
            (root / ".codex" / "settings.json").write_text(
                '{"path": "/' + 'Users/example/private"}\n',
                encoding="utf-8",
            )
            (root / ".env").write_text(
                "TOKEN=" + "sk-" + "localdeveloperartifact000000\n",
                encoding="utf-8",
            )
            (root / "local-screenshot.png").write_bytes(b"local artifact only")

            files = {path.relative_to(root) for path in release_policy.iter_release_files(root)}

            self.assertEqual(files, {Path("README.md")})

    def test_non_git_release_files_skip_build_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "README.md").write_text("public docs only\n", encoding="utf-8")
            (root / "dist").mkdir()
            (root / "dist" / "package.tar.gz").write_bytes(b"generated artifact")
            egg_info = root / "agent_personal_vault.egg-info"
            egg_info.mkdir()
            (egg_info / "PKG-INFO").write_text("Version: 0.1.0\n", encoding="utf-8")

            files = {path.relative_to(root) for path in release_policy.iter_release_files(root)}

            self.assertEqual(files, {Path("README.md")})

    def test_release_check_exposes_no_destructive_generated_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "dist").mkdir()
            (root / "dist" / "package.whl").write_bytes(b"generated artifact")
            (root / "build").mkdir()
            (root / "build" / "temp.txt").write_text("generated\n", encoding="utf-8")
            egg_info = root / "agent_personal_vault.egg-info"
            egg_info.mkdir()
            (egg_info / "PKG-INFO").write_text("Version: 0.1.0\n", encoding="utf-8")

            self.assertFalse(hasattr(check_release, "clean_generated"))
            self.assertTrue((root / "dist" / "package.whl").exists())
            self.assertTrue((root / "build" / "temp.txt").exists())
            self.assertTrue((egg_info / "PKG-INFO").exists())

    def test_tracked_local_developer_config_is_still_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            local_config = root / ".codex" / "settings.json"
            local_config.parent.mkdir()
            local_config.write_text(
                '{"path": "/' + 'Users/example/private"}\n',
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "-f", ".codex/settings.json"], cwd=root, check=True)

            files = {path.relative_to(root) for path in release_policy.iter_release_files(root)}
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                returncode = pii_scan.main(root)

            self.assertEqual(files, {Path(".codex/settings.json")})
            self.assertNotEqual(returncode, 0)
            self.assertIn("Potential private release content found:", stderr.getvalue())

    def test_tracked_private_text_is_still_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            tracked = root / "README.md"
            tracked.write_text("contact: " + "real" + "@example.com\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)

            findings = pii_scan.scan_file(tracked)

            self.assertTrue(findings)

    def test_release_files_reject_symlink_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp).resolve()
            outside_file = Path(outside).resolve() / "secret.md"
            outside_file.write_text("contact: " + "real" + "@example.com\n", encoding="utf-8")
            (root / "README.md").write_text("public docs only\n", encoding="utf-8")
            (root / "linked.md").symlink_to(outside_file)

            with self.assertRaisesRegex(release_policy.ReleasePolicyError, "symbolic-link"):
                release_policy.iter_release_files(root)

    def test_pii_scan_refuses_path_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp).resolve()
            outside_file = Path(outside).resolve() / "secret.md"
            outside_file.write_text("contact: " + "real" + "@example.com\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                pii_scan.scan_file(outside_file, root=root)


if __name__ == "__main__":
    unittest.main()
