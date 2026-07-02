# Release Readiness

日本語タイトル: リリース準備状況

status: public-alpha-ready
classification: SAFE_CANDIDATE
last_updated: 2026-07-02

## Current Summary

`agent-personal-vault` is a local OSS candidate for an AI-agent personal data vault.

Core product boundary:

- local-first personal data storage
- raw-free metadata for AI agent planning
- minimum-key raw retrieval only when needed
- explicit final-action boundary before external submission, upload, push, publish, or sharing

`job_hunting_profile` is the first bundled schema.

## Completed

- Standalone package directory exists.
- No real `vault.json` is present.
- No image, SQLite, database, backup, or private data file is present.
- No source references to the originating private project path were found.
- README, SECURITY, CONTRIBUTING, LICENSE, AGENT_PROTOCOL, and PUBLICATION_GATE exist.
- README includes an Alpha Safety Notice.
- README includes a short public-alpha quickstart path for raw-free context, MCP context, consent request, GUI approval, and audit review.
- MCP client setup guidance exists in `docs/MCP_CLIENT_SETUP.md`.
- MCP client setup guidance documents Claude Code tool approval names for restrictive or noninteractive modes.
- CLI supports raw-free `context`.
- CLI supports raw-free `context --task` planning hints.
- CLI supports raw-free `schema`.
- CLI `get` warns before printing a raw value.
- CLI `env` warns before raw-value export.
- CLI `get`, `env`, `set`, and `unset` require raw-free `--purpose` text and write raw-free audit events.
- CLI supports `audit summary` and `audit tail`.
- CLI `get` and `env` require a matching one-time consent token.
- CLI supports `consent request`, `consent approve`, `consent deny`, `consent requests`, direct `consent grant`, and `consent list`.
- GUI supports pending consent request approval and denial.
- GUI displays the issued consent id after approval so the user can pass it to CLI `get`.
- GUI profile saves write raw-free audit events.
- Optional encrypted store backend exists and uses `cryptography` when installed.
- CLI supports `encryption status`, `encryption encrypt`, and `encryption decrypt`.
- Raw-free MCP stdio server exists.
- MCP exposes `apv.schema`, `apv.context`, `apv.check`, `apv.list_masked`, and `apv.request_consent`.
- GUI warns that the project is alpha and not encrypted by default.
- GUI supports raw-free audit summary and recent event review.
- GUI usability smoke checks cover dummy data entry, save status, masked preview toggling, consent approval, and audit visibility.
- Unit tests include raw-free context checks.
- Unit tests cover raw-output CLI warnings.
- Unit tests cover raw-free audit logging, GUI profile-save audit logging, GUI audit viewer raw-free behavior, one-time consent tokens, consent request approval/denial, encryption status, optional encryption dependency behavior, raw-free planning hints, and MCP raw-free behavior.
- Unit tests cover the GUI consent-id handoff and the Claude Code MCP tool approval documentation guard.
- PII scan script exists.
- Release check script exists.
- Makefile exists with `test`, `pii`, `release-check`, and `clean` targets.
- GitHub Actions workflow exists and runs release checks for pull requests and pushes to `main`.
- GitHub Issue templates exist and warn against posting real personal data.
- Local Git preparation guide exists.
- Prior art review exists and README positioning reflects it.
- Product positioning and MVP boundary document exists.
- Reputation risk review and launch messaging documents exist.
- Final publication audit document exists.
- Release/package dry-run planning document exists in `docs/RELEASE_PACKAGE_DRY_RUN_PLAN.md`.

## Latest Verification

Commands run from this directory:

```sh
python3 -m py_compile agent_personal_vault/*.py scripts/pii_scan.py
python3 -m unittest discover -s tests
python3 scripts/pii_scan.py .
python3 scripts/check_release.py
make release-check
```

Results:

```text
py_compile: passed
unittest: 45 tests passed
pii_scan: No obvious private data patterns found
check_release: release checks passed
make release-check: release checks passed
```

Additional local checks:

- CLI smoke test passed.
- Temporary vault file mode was `0600`.
- Temporary vault parent directory mode was `0700`.
- `context` command returned JSON without raw values.
- `schema` command returned public schema metadata without reading a vault file.
- Search for private project path, originating private store path, internal audit/log paths, and username-specific path fragments returned no matches.
- Search for images, `vault.json`, SQLite, and database files returned no matches.
- GitHub Actions workflow was checked locally for checkout, setup-python, pull_request, and release-check steps.
- Release check cleans generated `__pycache__` and `.pytest_cache` directories.
- README avoids category-first novelty claims and points to `docs/PRIOR_ART_REVIEW.md`.
- Product positioning defines what the project is not, MVP exclusions, and messaging rules.
- Public alpha quickstart smoke reached raw-free context, MCP context, consent request, GUI approval, CLI raw retrieval with consent, and raw-free audit review using dummy data.
- GUI smoke checks verified save state, masked preview toggling, consent and audit panels, and panel contrast.
- Clean-clone-like onboarding validation with dummy data reached CLI `context`, MCP `apv.context`, MCP `apv.request_consent`, GUI approval, CLI `get`, and `audit tail`.
- Negative-flow validation covered consent denial, key mismatch, expired consent token, MCP unknown key, MCP invalid action, MCP unknown tool, and MCP invalid arguments.
- Negative-flow outputs were checked for dummy raw values, temporary store path leakage, and secret-like markers.
- MCP client interoperability validation covered generic stdio JSON-RPC, Codex `mcp add/list/get`, Claude Code `mcp add/list/get`, Claude Code project `.mcp.json`, and Claude Code noninteractive tool calls.
- Claude Code restrictive/noninteractive mode requires explicit tool approval for `mcp__agent-personal-vault__apv_context` and `mcp__agent-personal-vault__apv_request_consent`; this is documented in `docs/MCP_CLIENT_SETUP.md`.
- Claude Desktop-like validation covered venv-based install, stdio MCP `apv.context`, MCP `apv.request_consent`, GUI approval/denial through the same local API used by the browser UI, CLI `get` with the GUI-issued consent id, and raw-free audit checks using non-sensitive dummy data.
- Issue #49 terminal-only validation rechecked stdio MCP `apv.context`, `apv.request_consent`, unknown key, invalid action, unknown tool, invalid arguments, CLI approve/deny, one-time consent id use, denied access failure, and raw-free audit summary/tail using non-sensitive dummy data.
- Current main GitHub Actions `test` and CodeQL runs passed after PR #44.
- Current open CodeQL alerts: 0.

## Remaining P0/P1 Risks

No known P0 issue currently blocks continued public-alpha repository availability.

Remaining P1 risks before any release or package publish:

- Encryption is optional and passphrase-managed. OS key store integration and recovery UX remain pending.
- MCP remains intentionally raw-free except for consent request creation. Raw-value MCP tools should not be added without a separate consent, audit, and client-behavior review.
- GUI localhost access is an operator workflow convenience, not a hard multi-user security boundary.
- Package publishing and release artifacts have not been exercised as a distribution channel and remain approval-gated. A dry-run plan exists in `docs/RELEASE_PACKAGE_DRY_RUN_PLAN.md`, but no release, tag, package upload, or announcement has been authorized.
- Public usage is still too early to infer stability, support load, or external user misunderstanding patterns.
- MCP host/client behavior differs. Generic stdio, Codex configuration, and Claude Code configuration were validated, but broader host UI behavior still depends on each client.
- Claude Desktop was validated by configuration shape, generic stdio behavior, and terminal-only/Desktop-like local consent handoff. Full Claude Desktop app restart and in-app live tool-call UX remain unvalidated and should not be run without explicit user approval and a non-interfering environment because it requires editing user-level Desktop config, restarting the app, and operating the user's active GUI.

## Git Status

This directory is a local Git repository.

Latest local commit at this checkpoint is available from:

```text
git log --oneline -1
```

Release creation, package publish, public announcement, and external sharing remain approval-gated.
Distribution dry-run planning is tracked in `docs/RELEASE_PACKAGE_DRY_RUN_PLAN.md`.

## Not Done Without Explicit Approval

The following actions remain stopped:

- release creation
- tag creation
- package publish
- public announcement
- external sharing

## Recommended Next Approval

If the user wants to proceed, the next bounded action is:

```text
Run a release/package dry-run review using `docs/RELEASE_PACKAGE_DRY_RUN_PLAN.md`: confirm versioning, changelog, build artifact contents, rollback, dependency/provenance, Security alerts, and support-load assumptions with dummy data only.
```

This still does not create a GitHub release, tag, publish a package, change repository settings, delete branches, operate Claude Desktop app UI, use API-billed validation, or announce the project publicly. Release creation, tag creation, package publish, repository setting changes, branch deletion, Claude Desktop app UI operation, API-billed validation, and public announcement remain separate approvals.
