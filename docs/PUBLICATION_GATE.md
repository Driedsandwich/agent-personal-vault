# Publication Gate

日本語タイトル: 公開・配布承認ゲート

status: public-alpha-gate
classification: SAFE_CANDIDATE
last_updated: 2026-07-05

## Current Position

This project is now a public-alpha OSS repository.

Current distribution state:

- Repository visibility: public.
- Latest GitHub prerelease: `v0.1.11`.
- Latest PyPI package: `0.1.11`.
- Normal package publish path: PyPI Trusted Publishing OIDC.
- Manual token publish path: emergency fallback only.

This gate now applies to future irreversible or external actions. Do not create another release, tag, package publish, public announcement, repository setting change, branch deletion, PyPI token change/deletion, Claude Desktop app UI operation, or API-billed validation unless a human explicitly approves that specific action.

## Scope

Project name:

```text
agent-personal-vault
```

Core purpose:

```text
Local-first personal data vault for AI agents with a bundled profile schema.
```

## Must Pass Before Future External Actions

- No real `vault.json` exists in this tree.
- No `private/`, backup, screenshot, local log, or machine-specific absolute path is included.
- `python3 -m unittest discover -s tests` passes.
- `python3 scripts/pii_scan.py .` passes.
- `python3 -m py_compile agent_personal_vault/*.py scripts/pii_scan.py` passes.
- `python3 scripts/check_release.py` passes.
- `make release-check` passes when `make` is available.
- `.github/workflows/test.yml` exists and runs `python scripts/check_release.py`.
- README explains data handling, final-action boundary, and optional at-rest encryption being off by default.
- README has a visible Alpha Safety Notice near the top.
- README acknowledges prior art and avoids novelty overclaiming.
- `docs/PRIOR_ART_REVIEW.md` exists.
- `docs/PRODUCT_POSITIONING.md` exists and defines differentiation, MVP scope, and messaging rules.
- `docs/REPUTATION_RISK_REVIEW.md` exists and publication messaging avoids security overclaims.
- `docs/LAUNCH_MESSAGING.md` exists and public announcement copy follows it.
- `docs/SECURITY_AND_AGENT_INTEGRATION_ROADMAP.md` exists and MCP/raw-access claims follow it.
- `docs/FINAL_PUBLICATION_AUDIT.md` exists and summarizes local publication gate status.
- `docs/EXTERNAL_PUBLICATION_DECISION.md` exists and summarizes publication name, publication method, launch copy, CI, and expression-risk decisions.
- `docs/PRIVATE_DRY_RUN_REPORT.md` exists and summarizes the private GitHub dry-run.
- `docs/PUBLIC_RELEASE_REVIEW.md` exists and records the public visibility review.
- `docs/AGENT_PROTOCOL.md` explains the safe AI-agent flow and raw access boundary.
- GitHub Issue templates warn users not to post real personal data, screenshots, logs, or vault files.
- Pull Request template exists and warns against personal data, screenshots, vault files, local paths, and raw logs.
- `docs/OSS_GOVERNANCE.md` exists and defines Issue, PR, and branch-protection operation.
- CLI `get` and `env` warn on stderr before printing raw values.
- CLI `get`, `env`, `set`, and `unset` require raw-free `--purpose` text and write raw-free audit events.
- CLI `audit summary` and `audit tail` expose audit metadata without raw values.
- CLI `list` reports filled status and length without raw fragments.
- CLI `get` and `env` require a matching one-time consent token from a human-operated approval flow or explicit direct grant.
- README and SECURITY explain that consent tokens and audit logs are workflow controls, not a hard boundary against same-OS-user shell access.
- GUI can approve or deny pending consent requests without exposing raw values.
- Optional encrypted store backend exists, is off by default, and does not claim complete security.
- README and SECURITY explain that encryption requires optional dependency and user-managed passphrase.
- MCP server exposes only raw-free read tools and no raw-returning or write tools.
- MCP `apv.list_masked` does not return raw value fragments.
- `vault.json`, `audit.jsonl`, and `consents.json` are blocked from release candidates.
- GUI visibly warns that the project is alpha and not encrypted by default.
- SECURITY.md exists.
- CONTRIBUTING.md exists.
- LICENSE exists.
- `.gitignore` excludes real vault data, images, local secrets, and build artifacts.
- Additional release creation, tag creation, package publish, public announcement, repository setting changes, branch deletion, PyPI token changes/deletion, Claude Desktop app UI operation, and API-billed validation remain stopped until separately approved.
- `main` branch protection requires PR-based changes and CI status checks for ongoing public-alpha operations.

## Current Verification Commands

Run from this directory:

```sh
python3 -m py_compile agent_personal_vault/*.py scripts/pii_scan.py
python3 -m unittest discover -s tests
python3 scripts/pii_scan.py .
python3 scripts/check_release.py
make release-check
```

Optional CLI smoke test:

```sh
tmpdir=$(mktemp -d)
python3 -m agent_personal_vault.cli --store "$tmpdir/vault.json" init
python3 -m agent_personal_vault.cli --store "$tmpdir/vault.json" check
ls -l "$tmpdir/vault.json"
```

Optional GUI smoke test:

```sh
tmpdir=$(mktemp -d)
python3 -m agent_personal_vault.gui --port 0 --store "$tmpdir/vault.json"
```

Confirm the printed URL binds to `127.0.0.1`, then stop with `Ctrl-C`.

## Current Release Decision

Current posture:

1. Keep the project in public alpha.
2. Treat `v0.1.11` as the latest published prerelease and PyPI package.
3. Use Trusted Publishing OIDC as the normal package publish lane for future separately approved versions.
4. Stop before any new release, tag, package publish, public announcement, repository setting change, branch deletion, PyPI token change/deletion, Claude Desktop app UI operation, or API-billed validation and request explicit approval.

Local Git initialization and the first local commit are complete. See [LOCAL_GIT_PREP.md](LOCAL_GIT_PREP.md) only if this directory is recreated or moved.
