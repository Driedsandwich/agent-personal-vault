from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import check_release, pii_scan, release_policy


class ReleaseCheckTests(unittest.TestCase):
    def test_pii_scan_skips_local_agent_config(self) -> None:
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

            result = subprocess.run(
                [sys.executable, "scripts/pii_scan.py", str(root)],
                cwd=Path(__file__).resolve().parent.parent,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("No obvious private data patterns found.", result.stdout)

    def test_release_checks_skip_local_developer_config(self) -> None:
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

    def test_untracked_local_developer_config_is_not_release_surface(self) -> None:
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

            self.assertEqual(files, {Path("README.md")})

    def test_root_local_agent_config_files_are_not_release_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            private_path = "/" + "Users" + "/example/private"
            for filename in release_policy.LOCAL_DEVELOPER_CONFIG_FILES:
                (root / filename).write_text(f"local path: {private_path}\n", encoding="utf-8")
            (root / "README.md").write_text("public docs only\n", encoding="utf-8")

            files = {path.relative_to(root) for path in release_policy.iter_release_files(root)}

            self.assertEqual(files, {Path("README.md")})

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
            result = subprocess.run(
                [sys.executable, "scripts/pii_scan.py", str(root)],
                cwd=Path(__file__).resolve().parent.parent,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(files, {Path("README.md")})
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_forbidden_file_check_skips_local_developer_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for dirname in release_policy.LOCAL_DEVELOPER_CONFIG_DIRS:
                local_file = root / dirname / "local-screenshot.png"
                local_file.parent.mkdir()
                local_file.write_bytes(b"local artifact only")

            old_root = check_release.ROOT
            try:
                check_release.ROOT = root
                check_release.check_forbidden_files()
            finally:
                check_release.ROOT = old_root

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

    def test_clean_generated_removes_build_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "dist").mkdir()
            (root / "dist" / "package.whl").write_bytes(b"generated artifact")
            (root / "build").mkdir()
            (root / "build" / "temp.txt").write_text("generated\n", encoding="utf-8")
            egg_info = root / "agent_personal_vault.egg-info"
            egg_info.mkdir()
            (egg_info / "PKG-INFO").write_text("Version: 0.1.0\n", encoding="utf-8")

            old_root = check_release.ROOT
            try:
                check_release.ROOT = root
                check_release.clean_generated()
            finally:
                check_release.ROOT = old_root

            self.assertFalse((root / "dist").exists())
            self.assertFalse((root / "build").exists())
            self.assertFalse(egg_info.exists())

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
            result = subprocess.run(
                [sys.executable, "scripts/pii_scan.py", str(root)],
                cwd=Path(__file__).resolve().parent.parent,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(files, {Path(".codex/settings.json")})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Potential private data found:", result.stderr)

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

            files = {path.relative_to(root) for path in release_policy.iter_release_files(root)}

            self.assertEqual(files, {Path("README.md")})

    def test_pii_scan_refuses_path_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp).resolve()
            outside_file = Path(outside).resolve() / "secret.md"
            outside_file.write_text("contact: " + "real" + "@example.com\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                pii_scan.scan_file(outside_file, root=root)


if __name__ == "__main__":
    unittest.main()
