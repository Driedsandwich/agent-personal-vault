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
unittest: 51 tests passed
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
- Issue #53 local release/package dry-run built sdist and wheel from a clean-checkout-equivalent worktree, checked artifact hashes, confirmed package contents contained no forbidden vault, consent, audit, private config, image, database, or local secret files, and updated package license metadata to avoid setuptools deprecation warnings before any release or package publish.
- Current main GitHub Actions `test`, CodeQL, and dependency graph update passed after PR #58.
- Current open CodeQL alerts: 0.
- Fable 5 review found one P1 raw-boundary mismatch in MCP `apv.request_consent`; PR #60 fixed the public-alpha MCP path to accept one-key `get` consent requests only and reject bulk `env` requests.

## Current Release Decision

Decision: proceed to release-candidate preparation through Issue/PR workflow. Do not create a release candidate artifact, GitHub release, tag, package publish, or announcement yet.

Rationale:

- Local release/package dry-run, artifact inspection, package metadata correction, release checks, CI, CodeQL, and Security alert coverage are in good shape for continued public-alpha repository availability.
- No known P0 issue currently blocks public-alpha use.
- Post-PR #60 observation found no security, consent, raw leakage, onboarding, or support-load issue requiring a fix.
- Remaining P1 risks still affect distribution confidence and must stay visible during RC preparation: optional/passphrase-managed encryption, GUI localhost boundary, MCP host/client differences, limited support-load observation, and full Claude Desktop app restart plus in-app live tool-call UX remaining unvalidated without explicit approval and a non-interfering environment.
- Package build artifacts were validated locally, but no externally distributed release, tag, package index upload, or public support cycle has been exercised.

## RC Preparation Checklist

RC preparation is allowed only as checklist, documentation, and local dry-run work through Issue/PR workflow. It does not authorize release creation, tag creation, package publish, announcement, repository setting changes, branch deletion, Claude Desktop app UI operation, or API-billed validation.

- Version candidate: keep `0.1.0` as the current alpha package version unless a dedicated versioning Issue/PR proposes a different pre-release or patch version. Any actual version change requires explicit approval for that change and still does not authorize release/tag/publish.
- CHANGELOG: keep `CHANGELOG.md` as the source for the future release note draft. Before any release approval request, review the Unreleased section for user-visible changes, security/privacy changes, docs/governance changes, package prep, and known limitations.
- Artifact hash confirmation: rerun the clean-copy-equivalent local build immediately before any release approval request and compare the generated filenames, SHA-256 hashes, entry counts, and forbidden-name scan with the latest recorded dry-run.
- Rollback preparation: prepare a short rollback note before any release approval request. It should cover withdrawing announcements, opening corrective Issues/advisories, reverting docs/code through PR, and publishing a corrective patch only if separately approved.
- Support expectation: keep public-alpha and any RC candidate support best-effort only. Do not promise response times, production support, data recovery, or broad client compatibility.
- Stop conditions: stop RC preparation if CI fails, CodeQL/security alerts open, raw personal data or secrets are found, consent bypass is reported, audit raw leakage is suspected, release/tag/package artifacts contain forbidden files, or two or more independent support signals show the same consent/raw retrieval/MCP setup confusion.
- MCP host differences: keep generic stdio, Codex, and Claude Code as validated paths. Do not claim full Claude Desktop app restart or in-app live tool-call UX support unless separately approved and tested in a non-interfering environment.
- Approval boundary: after this checklist is complete, ask separately before GitHub release creation, tag creation, package publish, public announcement, repository setting changes, branch deletion, Claude Desktop app UI operation, or API-billed validation.

## Pre-RC Draft Snapshot

This section records the current draft inputs for a future release-candidate preparation decision. It is not a release-candidate approval and does not authorize release creation, tag creation, package publish, announcement, repository setting changes, branch deletion, Claude Desktop app UI operation, or API-billed validation.

- Target version: keep `pyproject.toml` at `0.1.0` for the current public-alpha line unless a later dedicated versioning Issue/PR chooses a different pre-release or patch version.
- Version bump policy: do not bump the version in documentation-only readiness PRs. Any version bump must be a dedicated Issue/PR with CI and explicit user approval for that exact bump. A version bump still would not authorize release, tag, package publish, or announcement.
- Changelog draft: `CHANGELOG.md` exists as an unreleased draft and separates user-visible changes, security/privacy changes, documentation/governance, package/release preparation, and known limitations.
- Support expectation: public alpha support is best-effort only. No response-time, production support, data recovery, or compatibility guarantee should be promised before a separate support policy is approved.
- Support-load signal: two or more independent reports about the same consent, raw retrieval, MCP setup, or safety-boundary confusion should block RC preparation until addressed or explicitly accepted as an alpha limitation.
- MCP host differences: generic stdio, Codex, and Claude Code remain the validated paths. Full Claude Desktop app restart and in-app live tool-call UX remain unvalidated and must stay visible as a limitation unless separately approved.
- Fresh artifact hash dry-run: completed locally from a temporary clean-copy-equivalent source tree without upload. Artifacts were built into a temporary directory, not committed. `agent_personal_vault-0.1.0-py3-none-any.whl` SHA-256: `498b480d7b33802e18ef026d9cf5d77af5ceba98e4b145751e3d513019b78740` (33121 bytes, 15 entries, no forbidden name hits). `agent_personal_vault-0.1.0.tar.gz` SHA-256: `3d6a59e8cce3872d5ba19b0e35298fe8be15cf1c8a7f5c2e194c34f5e173d4ea` (41427 bytes, 26 entries, no forbidden name hits).

Next release-candidate gate:

- At least one additional lightweight public-alpha observation cycle shows no security, consent, raw leakage, onboarding, or support-load issue that requires a fix.
- Release candidate checklist is prepared through Issue/PR and includes version bump policy, changelog draft, artifact hashes, rollback plan, Security alert snapshot, and support expectation.
- The user separately approves release candidate preparation. This approval would still not authorize GitHub release creation, tag creation, package publish, or announcement.

## RC Entry Exit Criteria

Before proposing a release-candidate preparation cycle, the project must satisfy all criteria below through Issue/PR workflow:

- Observation cycle: at least one post-PR #60 lightweight public-alpha observation cycle is complete, and the record covers open Issues/PRs, Actions, CodeQL, Dependabot/security alerts, release/tag absence, README display, and external feedback. Any security, consent, raw leakage, onboarding, or repeated support-load issue found in that cycle must be fixed or explicitly documented as an accepted alpha risk before RC preparation.
- Security snapshot: the RC proposal must record the target `main` commit SHA, latest successful `test` and CodeQL runs, open CodeQL alert count, Dependabot/vulnerability/secret-scanning status, and local `python3 scripts/check_release.py` result.
- Changelog draft: a `CHANGELOG.md` draft or equivalent release-note draft must summarize merged changes since public alpha, separating user-visible changes, security/privacy changes, docs-only changes, and known limitations. It must not include raw personal data, local private paths, screenshots, vault files, or private support details.
- Versioning: the proposal must state the intended `pyproject.toml` version, whether the change is alpha/patch/breaking, and whether a version bump PR is required. No version bump, tag, or release is implied by meeting this criterion.
- Artifact hashes: a clean-checkout-equivalent local build must record sdist and wheel filenames plus SHA-256 hashes, and must confirm the artifacts exclude vault, consent, audit, private config, image, database, backup, and local secret files.
- Support-load signal: repeated confusion about consent, raw retrieval, MCP setup, or safety boundaries is release-blocking when it appears in two or more independent Issues, PRs, or external feedback items in the observation window.
- MCP host differences: generic stdio, Codex, and Claude Code behavior must remain documented as validated. Full Claude Desktop app restart and in-app live tool-call UX may remain unvalidated only if the RC proposal explicitly keeps that limitation visible and does not claim Claude Desktop live UX support.

## Remaining P0/P1 Risks

No known P0 issue currently blocks continued public-alpha repository availability.

Remaining P1 risks before any release candidate, release, or package publish:

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
Continue public-alpha lightweight observation for one cycle. Confirm open Issues/PRs, Actions, Security alerts, release/tag absence, README display, support-load signals, and external feedback. If no blocker appears, prepare a release-candidate checklist draft through Issue/PR without creating a release, tag, package publish, or announcement.
```

This still does not create a GitHub release, tag, publish a package, change repository settings, delete branches, operate Claude Desktop app UI, use API-billed validation, or announce the project publicly. Release creation, tag creation, package publish, repository setting changes, branch deletion, Claude Desktop app UI operation, API-billed validation, and public announcement remain separate approvals.
