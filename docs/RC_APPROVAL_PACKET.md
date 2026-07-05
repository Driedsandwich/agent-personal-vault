# Historical RC Approval Packet

日本語タイトル: 過去のRC実行前レビュー用承認パケット

status: historical-snapshot
classification: SAFE_CANDIDATE
last_updated: 2026-07-05

## Purpose

This packet preserves the historical pre-`v0.1.0` release-candidate evidence and approval text that were used before the first public-alpha release.

It is no longer the current execution packet. The project is now public alpha, with latest GitHub prerelease `v0.1.11` and latest PyPI package `0.1.11`. Current release and package-publish state is tracked in `docs/RELEASE_READINESS.md`, `docs/RELEASE_PACKAGE_DRY_RUN_PLAN.md`, and `docs/PYPI_TRUSTED_PUBLISHING_PLAN.md`.

It remains for audit history only. It does not authorize GitHub release creation, tag creation, package publish, public announcement, repository setting changes, branch deletion, Claude Desktop app UI operation, or API-billed validation.

Use `docs/RC_APPROVAL_PLAN.md` as the detailed lane policy if a future version requires a new approval packet. Do not reuse this historical `0.1.0` packet for any future release.

## Current Distribution Notice

- Latest GitHub prerelease: `v0.1.11`.
- Latest PyPI package: `0.1.11`.
- Normal package publish path: PyPI Trusted Publishing OIDC.
- Manual token publish path: emergency fallback only.
- Future tag, release, package publish, repository setting change, branch deletion, PyPI token change/deletion, Claude Desktop app UI operation, API-billed validation, or public announcement still requires a separate explicit approval lane.

## Historical Target Snapshot

- Repository: `Driedsandwich/agent-personal-vault`
- Repository visibility: public
- Default branch: `main`
- Execution target commit: fill from `git rev-parse origin/main` immediately before a separate execution approval.
- Execution target commit subject: fill from `git log -1 --pretty=%s origin/main` immediately before a separate execution approval.
- Last reviewed baseline before this packet: `1bc53b9ba94c86830c367943ee139063b1688f2d` (`docs: add RC approval packet`).
- Historical version candidate: `0.1.0`
- Package name: `agent-personal-vault`
- Python requirement: `>=3.11`
- License: MIT
- Release note source: `CHANGELOG.md` `Unreleased`

Do not treat the baseline commit above as the current execution target. Reconfirm the final execution target commit immediately before any separate future execution approval.

## Historical CI And Security Snapshot

Latest checked `main` runs at this historical checkpoint:

- GitHub Actions `test`: success
- CodeQL: success

Repository state at this historical checkpoint:

- open PRs: 0
- open Issues: 0
- open CodeQL alerts: 0
- open Dependabot alerts: 0
- open secret scanning alerts: 0
- vulnerability alerts endpoint: `204 No Content`
- GitHub releases: 0 at this historical checkpoint
- Git tags: 0 at this historical checkpoint

Local release gate to rerun before any execution approval:

```sh
python3 scripts/check_release.py
```

For current release work, use the current release-readiness documents instead of this historical snapshot.

## Historical Preflight Snapshot

Recorded on 2026-07-02 before any release, tag, package publish, or announcement action.

- Target source: `origin/main`
- Target commit: `ae89c5d7cd9d953d395ac25daad495727c1d0c9f`
- Target commit subject: `docs: make RC target approval-time filled`
- Historical version candidate: `0.1.0`
- GitHub Actions `test`: success
- CodeQL: success
- open PRs: 0
- open Issues: 0
- open CodeQL alerts: 0
- open Dependabot alerts: 0
- open secret scanning alerts: 0
- vulnerability alerts endpoint: `204 No Content`
- GitHub releases: 0 at this historical checkpoint
- Git tags: 0 at this historical checkpoint
- Release note check: the draft below was compared with `CHANGELOG.md`, `docs/LAUNCH_MESSAGING.md`, and `SECURITY.md`; no wording change was required for this preflight.

Fresh local artifact dry-run:

- Source: `git archive origin/main` extracted into a temporary directory.
- Build environment: temporary local virtual environment, deleted after the check.
- Python: `Python 3.14.6`
- pip: `pip 26.1.2`
- build: `build 1.5.0`
- Upload: none.
- Repository artifacts left behind: none.

Artifacts:

| File | Bytes | Entries | SHA-256 | Forbidden-name hits |
|---|---:|---:|---|---|
| `agent_personal_vault-0.1.0-py3-none-any.whl` | 33200 | 15 | `b00357c06b0e7f860953557274bd3fd5eef79098a4f5c9ebd622c1a35c5777b3` | none |
| `agent_personal_vault-0.1.0.tar.gz` | 41418 | 26 | `e9c3f42cbc753367a35c1ec92077029439749bcaf9e3624f33a05a31f0ae7c4a` | none |

Forbidden-name scan covered vault, consent, audit, private, backup, database, image, local `.venv`, `.codex`, and `.claude` style paths. These hashes are evidence for this exact generated-file set only and are not a cross-environment reproducible-build guarantee.

Do not use these artifact hashes or target commits for current release decisions.

## Historical Release Note Draft

Draft source: `CHANGELOG.md` `Unreleased`.

Suggested GitHub release note body for review:

```markdown
## Agent Personal Vault 0.1.0 alpha

Agent Personal Vault is an alpha local utility for AI-agent workflows that need raw-free personal-data metadata and explicit one-key retrieval.

### User-visible changes

- Added raw-free task planning hints so agents can choose smaller candidate key sets before requesting raw access.
- Added public-alpha quickstart guidance for raw-free context, MCP context, consent request, GUI approval, CLI one-key retrieval, and audit review.
- Added MCP client setup guidance for stdio clients, Codex, Claude Desktop-style configuration, and Claude Code tool approval names.
- Added GUI audit summary and recent event viewing.
- Improved GUI consent handoff by displaying the approved consent id for CLI `get`.
- Improved GUI panel contrast and public-alpha usability details.

### Security and privacy changes

- Kept MCP raw-free by exposing planning, status, masked listing, and consent-request tools only.
- Added raw-free GUI profile-save audit logging.
- Aligned public-alpha raw boundary docs around one-key raw retrieval.
- Fixed MCP consent requests so `apv.request_consent` accepts one-key `get` requests only and rejects bulk `env` requests.
- Added tests and release checks for local developer config exclusion, raw-free audit/consent behavior, MCP raw-free behavior, and one-key consent boundaries.

### Documentation and governance

- Added prior art, product positioning, reputation risk, launch messaging, publication gate, release readiness, and RC approval planning documentation.
- Recorded terminal-only and Claude Desktop-like validation boundaries without claiming full Claude Desktop in-app live UX support.
- Documented that approval commands, including direct `consent grant`, are human-operated and not agent-facing.

### Package preparation

- Added package metadata and console entry points for `agent-personal-vault`, `apv-gui`, and `apv-mcp`.
- Performed local release/package dry-run checks for sdist and wheel contents without publishing.
- Updated package license metadata to avoid setuptools deprecation warnings.

### Known limitations

- This is public alpha software.
- Stored data is not encrypted by default.
- Optional encryption is passphrase-managed; OS key store integration and recovery UX are not implemented.
- Consent tokens and audit logs are workflow controls, not a hard security boundary against a process with the same OS user shell access.
- GUI localhost access is an operator convenience, not a hard multi-user security boundary.
- MCP host/client behavior differs by client. Generic stdio, Codex, and Claude Code paths have been validated. Full Claude Desktop app restart and in-app live tool-call UX remain unvalidated without explicit approval and a non-interfering environment.
- Do not post real personal data, screenshots with raw values, vault files, tokens, local private paths, or private support details in Issues or PRs.
```

Before any release approval, re-check this text against `docs/LAUNCH_MESSAGING.md`, `SECURITY.md`, and the current `CHANGELOG.md`.

## Fresh Artifact Hash Procedure

Run this only as a local dry-run before requesting a release or package-publish execution approval. Do not upload artifacts.

```sh
git switch main
git pull --ff-only
python3 -m venv .venv-release-dry-run
. .venv-release-dry-run/bin/activate
python3 -m pip install --upgrade pip build
python3 -m build
python3 scripts/check_release.py
```

Record in the execution approval request:

- target commit SHA
- Python version
- `pip` version
- `build` version
- wheel filename, bytes, entry count, SHA-256
- sdist filename, bytes, entry count, SHA-256
- forbidden-name scan result
- whether artifacts exclude `vault.json`, consent files, audit logs, local developer config, images, screenshots, databases, backups, and private paths

Recorded hashes are evidence for those exact generated files only. They are not a cross-environment reproducible-build guarantee.

## Approval Lane Text

Use exactly one approval lane at a time. If a user request combines lanes, split it and ask for separate approvals.

### Lane 1: GitHub release draft

```text
Approve creating a GitHub release draft for Agent Personal Vault at commit <commit> with version 0.1.0. Do not publish it, do not create or move tags, do not publish packages, and do not announce publicly.
```

### Lane 2: tag creation

```text
Approve creating tag <tag> for Agent Personal Vault at commit <commit>. Do not create or publish a GitHub release, do not publish any package, and do not announce publicly.
```

Recommended tag name if approved later:

```text
v0.1.0
```

### Lane 3: GitHub release publish

```text
Approve publishing GitHub release <tag/version> for Agent Personal Vault using the reviewed release text and fresh artifact hash record. Do not publish to a package index and do not announce publicly.
```

### Lane 4: package publish

```text
Approve publishing package agent-personal-vault version 0.1.0 from commit <commit> to <package index> using artifacts with these hashes: <hashes>. Do not create GitHub releases/tags or announce publicly unless separately approved.
```

### Lane 5: public announcement

```text
Approve publishing the reviewed announcement text to <channel>. Do not create releases, tags, package publishes, repository setting changes, or branch deletions.
```

## Shared Stop Conditions

Stop before any approval or execution if:

- target commit changed unexpectedly
- version changed without a dedicated approved Issue/PR
- local `python3 scripts/check_release.py` fails
- latest `main` GitHub Actions `test` or CodeQL fails
- open CodeQL, Dependabot, vulnerability, or secret-scanning alerts appear
- open Issues/PRs raise release safety, consent, raw leakage, MCP setup, or support-load concerns
- release or tag already exists unexpectedly
- fresh artifacts include forbidden files or unexpected entries
- raw personal data, secrets, local private paths, screenshots, vault files, consent files, audit logs, databases, images, or private support details appear in release text, artifacts, PRs, or announcement drafts
- artifact hashes differ from the approval request without explanation
- the requested action combines multiple approval lanes without separate explicit approval
- the requested action involves Claude Desktop app UI operation or API-billed validation without separate explicit approval

## Post-Action Verification Checklist

After any separately approved lane execution, verify only the scope of that lane:

- target commit and version match the approval
- no unapproved lane was executed
- release/tag/package/announcement state matches the approved action
- release text or announcement text matches the reviewed text
- attached or published artifacts match approved filenames and hashes when applicable
- open Issues/PRs remain acceptable
- latest relevant CI/security status remains acceptable
- no raw data, secrets, private paths, screenshots, vault files, consent files, audit logs, databases, images, or unsupported security claims were introduced

## Current Recommendation

Do not execute any lane from this packet automatically.

If the project proceeds, the lowest-risk next step is a review-only pass over this packet and the generated release note text. Execution should remain separated into the approval lanes above.
