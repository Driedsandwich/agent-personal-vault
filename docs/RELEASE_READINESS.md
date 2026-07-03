# Release Readiness

日本語タイトル: リリース準備状況

status: public-alpha-ready
classification: SAFE_CANDIDATE
last_updated: 2026-07-04

## Current Summary

`agent-personal-vault` is a local OSS candidate for an AI-agent personal data vault.

Current distribution snapshot:

- Latest GitHub prerelease: `v0.1.5`.
- Latest PyPI package: `0.1.5`.
- Latest Trusted Publisher documentation checkpoint before this status refresh: `329534a10cd2ac00141a1bd4d323d27709c5c4b3`.
- Open Issue #108 was closed after the PyPI long description was refreshed by the `v0.1.3` package publish.
- Trusted Publishing setup is validated by the `v0.1.5` PyPI publish through the OIDC lane. Package publishes through `v0.1.4` used the manual token fallback lane.
- The manual `publish-package` workflow exists and was used for the first OIDC publish after GitHub environment approval.
- GitHub environment `pypi` exists with required reviewer `Driedsandwich`, `prevent_self_review: false`, protected-branches-only deployment policy, no environment secrets, no stored PyPI token, and `can_admins_bypass: true`.
- PyPI Trusted Publisher is configured according to the PyPI project management UI confirmed by the project owner: GitHub, repository `Driedsandwich/agent-personal-vault`, workflow `pypi-publish.yml`, environment `pypi`.
- The Trusted Publisher was used successfully for the `v0.1.5` PyPI publish.
- First OIDC publish preflight planning and follow-up evidence are tracked in Issue #142, Issue #146, and `docs/RELEASE_PACKAGE_DRY_RUN_PLAN.md`.
- The v0.1.5 GitHub prerelease and PyPI package include the Trusted Publishing infrastructure-validation patch.
- Historical sections below may mention earlier `v0.1.0` to `v0.1.2` checkpoints as evidence records. Do not treat those historical checkpoints as the current package state.

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

## Prerelease Graduation Criteria

日本語要約: stable/GA扱いへ進む前の最低条件。

The project should remain a public alpha / prerelease until all criteria below are explicitly rechecked in a dedicated Issue/PR.

- README, PyPI long description, GUI, and CLI help continue to state that stored data is not encrypted by default.
- First-use and save-time UX actively warns users to use dummy data or values they are comfortable storing locally.
- `audit summary`, `audit tail`, GUI audit view, MCP responses, and error responses are covered by tests that prevent raw personal values, full active consent ids, local private paths, or secrets from leaking.
- `get` remains one-key, consent-gated, and warning-bearing; `env` remains human-only, bulk-acknowledged, and outside agent/MCP normal flow.
- MCP continues to expose raw-free planning/status/consent-request tools only, with no raw-value or external-action tools.
- consent tokens remain one-time, short-lived, and protected against double consume under concurrent access.
- Issue templates, support guidance, and docs continue to reject real personal data, screenshots with raw values, vault files, consent files, audit logs, local private paths, and tokens in public support.
- CodeQL, Dependabot/security alerts, local release-check, and main CI are green at the time of any graduation decision.
- At-rest encryption remains either optional with clear limitations or is promoted only after a separate design, migration, and rollback review.

Stop before stable/GA wording if any criterion is unknown, stale, or failing.

## v0.1.1 Readiness Snapshot

Status date: 2026-07-02.

This historical snapshot summarized the v0.1.1 candidate state after the post-`v0.1.0` preparation pass. The dedicated version bump was tracked separately in Issue #98. This snapshot does not authorize GitHub release, tag creation, package publish, public announcement, repository setting change, branch deletion, Claude Desktop app UI operation, or API-billed validation.

### Current State

- `v0.1.0` was published as a GitHub prerelease and was the PyPI package version at this historical checkpoint.
- `main` contains the post-publish documentation and packaging metadata follow-ups.
- Open Issues/PRs were 0/0 at the start of the Issue #94 readiness pass.
- Latest `main` test and CodeQL were successful at the start of the Issue #94 readiness pass.
- Open CodeQL, Dependabot, and secret scanning alerts were 0 at the start of the Issue #94 readiness pass.

### Candidate Changes To Include

The current v0.1.1 candidate should stay small.

- Project URL metadata: include the already-merged `[project.urls]` package metadata from Issue #86 / PR #87. This is the only current code/package metadata change intended for v0.1.1.
- Documentation readiness: include the Trusted Publishing plan, branch cleanup candidate verification, and pre-announcement checklist updates as documentation/governance improvements.
- Safety posture: keep the existing raw-free default, one-key raw retrieval boundary, no bulk raw export, and no unsupported security/compliance claims.

### Changes To Exclude Unless Separately Approved

Do not include these in v0.1.1 by default:

- PyPI Trusted Publishing activation. At the v0.1.1 historical checkpoint, PyPI publisher settings, GitHub environment protection, and an active publishing workflow were still future separate approval lanes.
- Branch deletion. Candidate evidence is documented in `docs/BRANCH_CLEANUP_CANDIDATES.md`, but local or remote branch deletion remains a separate explicit approval.
- Public announcement. The checklist is documented in `docs/LAUNCH_MESSAGING.md`, but SNS/blog/community posting remains a separate explicit approval per channel and text.
- New MCP raw-value tools, broader raw retrieval, or bulk raw export.
- Claude Desktop full app restart or in-app live tool-call UX claims. That UX remains unvalidated unless separately approved and tested in a non-interfering environment.
- Production, enterprise, compliance, privacy guarantee, data recovery, or broad MCP/client compatibility claims.

### Release/Tag/Package Publish Stop Conditions

Stop before any v0.1.1 release, tag, or package publish request if any of these are true:

- `main` is not clean locally or does not match `origin/main`.
- Open Issues/PRs include unresolved release safety, consent, raw leakage, install, packaging, MCP setup, or support-load concerns.
- Latest `main` test, CodeQL, Dependency Graph, Dependabot, secret scanning, or local `python3 scripts/check_release.py` is failing or unknown.
- Any raw personal data, secret, token, local private path, screenshot with raw values, vault file, consent file, audit file, database, backup, or private support detail appears in docs, release text, artifacts, workflow logs, PRs, or Issues.
- The package version, target commit, tag, release text, changelog, or artifact hashes do not match the approval packet.
- A fresh isolated build and `twine check` have not been run from the intended target commit.
- PyPI already contains the intended version.
- Two or more independent support signals show the same consent, raw retrieval, MCP setup, install, or safety-boundary confusion.
- Any action would require repository settings, PyPI publisher settings, branch deletion, public announcement, Claude Desktop app UI operation, or API-billed validation without separate explicit approval.

### Next Gate

The next safe step after the v0.1.1 release-candidate preparation pass is the dedicated v0.1.1 version bump Issue/PR, not a release action.

That preparation should:

- confirm the version should be `0.1.1`;
- update `pyproject.toml` version only in the dedicated version bump PR;
- prepare or update `CHANGELOG.md`;
- run a fresh isolated package build from the intended target commit;
- record sdist/wheel filenames, sizes, entry counts, SHA-256 hashes, and strict forbidden-file scan results;
- verify PyPI metadata expectations, including Project URL display after a future publish;
- prepare rollback notes and per-lane approval text.

Completing that preparation still would not authorize GitHub release creation, tag creation, package publish, public announcement, repository setting changes, branch deletion, Claude Desktop app UI operation, or API-billed validation.

## v0.1.1 RC Preparation Snapshot

Status date: 2026-07-02.

Tracking Issue: #96.

This snapshot prepares a possible v0.1.1 release candidate and records the dedicated version bump evidence from Issue #98. It does not authorize GitHub release, tag creation, package publish, public announcement, repository setting change, branch deletion, Claude Desktop app UI operation, or API-billed validation.

### Intended Scope

Keep v0.1.1 narrow:

- Include the already-merged Project-URL package metadata for Homepage, Source, Issues, and Documentation.
- Include documentation and governance updates for Trusted Publishing planning, branch cleanup candidate verification, pre-announcement checks, and v0.1.1 readiness.
- Keep runtime behavior unchanged unless a later Issue/PR explicitly identifies a release-blocking bug.

Do not include by default:

- PyPI Trusted Publishing activation.
- GitHub Actions package-publish workflow activation.
- repository setting changes or GitHub environment protection changes.
- branch deletion.
- SNS/blog/community announcement.
- MCP raw-value tool expansion or bulk raw export.
- Claude Desktop full app live UX support claims.

### Version Bump Policy

`pyproject.toml` is now bumped to `0.1.1` through Issue #98.

This version bump does not authorize release creation, tag creation, package publish, public announcement, repository setting changes, branch deletion, Claude Desktop app UI operation, or API-billed validation.

### CHANGELOG State

`CHANGELOG.md` now has an empty `Unreleased` section and a `0.1.1 - 2026-07-02` section for the current release-candidate content.

Before any release approval request:

- confirm the `0.1.1 - 2026-07-02` section still matches merged changes;
- convert the relevant content into a release-note approval draft;
- keep known limitations visible;
- exclude raw personal data, local paths, screenshots, vault files, consent files, audit files, tokens, and private support details.

### Fresh Isolated Artifact Dry-Run

Dry-run command shape:

```sh
rm -rf /tmp/apv-v011-rc-src /tmp/apv-v011-rc-venv /tmp/apv-v011-rc-dist
mkdir -p /tmp/apv-v011-rc-src /tmp/apv-v011-rc-dist
git archive HEAD | tar -x -C /tmp/apv-v011-rc-src
python3 -m venv /tmp/apv-v011-rc-venv
/tmp/apv-v011-rc-venv/bin/python -m pip install --upgrade pip build twine
/tmp/apv-v011-rc-venv/bin/python -m build --outdir /tmp/apv-v011-rc-dist /tmp/apv-v011-rc-src
/tmp/apv-v011-rc-venv/bin/twine check /tmp/apv-v011-rc-dist/*
```

Build environment:

- Target source: `git archive HEAD` plus the Issue #98 worktree version bump and changelog updates.
- Python: local `python3` venv using Python 3.14 at dry-run time.
- `pip`: 26.1.2.
- `build`: 1.5.0.
- `twine`: 6.2.0.

Artifact evidence from this preparation run:

| File | Bytes | Entries | SHA-256 |
|---|---:|---:|---|
| `agent_personal_vault-0.1.1-py3-none-any.whl` | 33471 | 15 | `c202905fe52c85882437985978e86d2f028602b87d8c3a66a5b3553593cfdf6a` |
| `agent_personal_vault-0.1.1.tar.gz` | 42018 | 26 | `18d51459916330bbd5139fdd86b83b7a4444a017f5924affca135bac5d5f0e18` |

Interpretation:

- These artifacts are evidence for the current v0.1.1 version-bump worktree only.
- Fresh artifacts must still be regenerated immediately before any separately approved package publish.
- `twine check` passed for both files.
- A strict artifact forbidden-file check found no `.env`, `.pypirc`, raw vault data files, consent data files, audit log files, database files, or image files in the generated sdist/wheel.
- The dry-run wheel metadata reported `Version: 0.1.1`.

### PyPI Metadata Expectation

Current PyPI version at preparation time: `0.1.0`.

Current PyPI metadata does not show the new Project-URL entries because the metadata has not been published yet.

Expected after a future separately approved v0.1.1 package publish:

- Homepage: `https://github.com/Driedsandwich/agent-personal-vault`
- Source: `https://github.com/Driedsandwich/agent-personal-vault`
- Issues: `https://github.com/Driedsandwich/agent-personal-vault/issues`
- Documentation: `https://github.com/Driedsandwich/agent-personal-vault#readme`

The dry-run wheel metadata contained all four `Project-URL` entries.

### Rollback Preparation

Before any v0.1.1 release or publish approval request, prepare a short approval-packet rollback note:

- If release text is wrong before publish, edit the draft or close it.
- If a published GitHub release is wrong, stop announcements, add a corrective note or prepare a patch through PR, and delete only with separate approval when appropriate.
- If a package publish is wrong, consider yanking only if PyPI supports it and only after separate approval; otherwise prepare a corrective patch release through Issue/PR.
- If safety, raw leakage, or consent bypass is involved, stop public messaging and use the security reporting path.
- Do not rely on deleting tags, releases, branches, or package files as the only rollback plan.

### Stop Conditions

Stop before any v0.1.1 release, tag, package publish, or announcement request if:

- local `main` is not clean or does not match `origin/main`;
- open Issues/PRs include unresolved release safety, packaging, install, consent, raw leakage, MCP setup, or support-load concerns;
- latest `main` test, CodeQL, Dependency Graph, local release check, or security alert state is failing or unknown;
- PyPI already contains the intended version;
- fresh artifacts have not been regenerated and checked from the final intended release commit;
- artifacts contain forbidden files or unexpected private/developer files;
- release notes, CHANGELOG, approval packet, target commit, tag, version, and artifact hashes do not agree;
- public text contains unsupported security/compliance/production claims;
- any raw personal data, secret, token, local private path, screenshot with raw values, vault file, consent file, audit file, database, backup, or private support detail appears in public text, docs, artifacts, logs, Issues, or PRs;
- two or more independent support signals show the same consent, raw retrieval, MCP setup, install, or safety-boundary confusion;
- the requested action would require repository settings, PyPI publisher settings, branch deletion, public announcement, Claude Desktop app UI operation, or API-billed validation without separate explicit approval.

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

## RC Candidate Final Dry-Run Snapshot

This is the final local dry-run snapshot for deciding whether to ask for a separate RC/release action. It still does not authorize release creation, tag creation, package publish, announcement, repository setting changes, branch deletion, Claude Desktop app UI operation, or API-billed validation.

- Tracking Issue: #67.
- Target commit for this dry-run: `5209055 docs: add RC preparation checklist`.
- Version candidate: keep `0.1.0` for the current alpha line. No version bump is included in this dry-run.
- CHANGELOG: `CHANGELOG.md` remains an Unreleased draft and is the current release-note source. It includes user-visible changes, security/privacy changes, docs/governance, package prep, and known limitations.
- Security snapshot: latest `main` test and CodeQL are successful. Open CodeQL alerts, Dependabot alerts, and secret scanning alerts are 0. Vulnerability alerts endpoint returns `204 No Content`.
- Repository snapshot: releases 0, tags 0, open PRs 0. The only open Issue during this dry-run is the tracking Issue for this work. Stars, watchers/subscribers, and forks are 0. Traffic API reported 8 views and 47 clones.
- Artifact dry-run: completed from a temporary clean-copy-equivalent source tree without upload. Artifacts were built into a temporary directory and were not committed.
  - `agent_personal_vault-0.1.0-py3-none-any.whl`: SHA-256 `fbf280d1f77cc6c81c4cbff1d297cdceb0d7c1b726eb3e443534a949ee124fcb`, 33121 bytes, 15 entries, no forbidden name hits.
  - `agent_personal_vault-0.1.0.tar.gz`: SHA-256 `265544a427176dcb468a16caeb70b870ce628b837db7c5ac88e18fb7d2e3b5d2`, 41448 bytes, 26 entries, no forbidden name hits.
- Artifact hash interpretation: these hashes are evidence for this exact local dry-run only. A later isolated rebuild matched the artifact names, wheel size, and entry counts but produced different SHA-256 hashes under a different local build environment. Treat that as a reason to regenerate and record fresh hashes from a pinned target environment immediately before any separately approved release or package publish action, not as approval to reuse these hashes.
- Rollback note: if a future release or package publish is separately approved and then found unsafe, stop announcements, open a corrective Issue or security advisory as appropriate, revert docs/code through PR, and publish a corrective patch only with separate approval. Do not rely on deletion as the sole rollback path.
- Support expectation: best-effort only. Do not promise response times, production support, data recovery, or broad MCP/client compatibility.
- Stop conditions: do not proceed to any release action if CI fails, CodeQL/security alerts open, raw personal data or secrets appear, consent bypass is reported, audit raw leakage is suspected, artifacts include forbidden files, or repeated support signals show the same consent/raw retrieval/MCP setup confusion.
- MCP host differences: generic stdio, Codex, and Claude Code remain the validated paths. Full Claude Desktop app restart and in-app live tool-call UX remain unvalidated and must not be claimed as supported.

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
Individual approval lanes for release drafting/publishing, tag creation, package publish, and announcement are tracked in `docs/RC_APPROVAL_PLAN.md`.
The current pre-execution review packet is tracked in `docs/RC_APPROVAL_PACKET.md`.

## Not Done Without Explicit Approval

The following actions remain stopped:

- release creation
- tag creation
- package publish
- public announcement
- external sharing

## Recommended Next Approval

Current v0.1.4 candidate decision:

- Outcome: `v0.1.4` was released as a GitHub prerelease and published to PyPI.
- Reason: v0.1.4 carries the user-facing safety-boundary docs and consent-state hardening that were not present in the PyPI `0.1.3` package.
- Scope stayed narrow: version bump to `0.1.4`, CHANGELOG finalization, fresh isolated artifact build from the target commit, hash recording, GitHub tag/release lanes, and PyPI publish lane.
- Do not bundle Trusted Publishing activation into this patch by default. It remains a separate repository/PyPI settings lane.
- Stop if local release-check, PR CI, CodeQL, Dependabot/security alerts, PyPI version availability, or artifact forbidden-file scan fails.
- Trusted Publishing introduction should be split into separate future approvals: workflow PR, GitHub environment setup, PyPI publisher setup, and first OIDC publish.

Latest v0.1.4 publish checks:

- Local `python3 scripts/check_release.py`: pass on `ce0abbef2c899e9d0d227080da4b969f9cfde560`.
- Main `test` workflow: success on `ce0abbef2c899e9d0d227080da4b969f9cfde560`.
- Main `CodeQL` workflow: success on `ce0abbef2c899e9d0d227080da4b969f9cfde560`.
- Open GitHub Issues/PRs: `0 / 0` at the checkpoint.
- Open CodeQL alerts: `0`.
- Open Dependabot alerts: `0`.
- PyPI latest: `0.1.4`.
- GitHub release `v0.1.4`: published as a prerelease.
- v0.1.4 candidate and publish evidence are tracked in `docs/RELEASE_PACKAGE_DRY_RUN_PLAN.md`.

v0.1.4 uploaded artifact evidence:

- Built from tag `v0.1.4` at `ce0abbef2c899e9d0d227080da4b969f9cfde560`.
- `agent_personal_vault-0.1.4-py3-none-any.whl`: 34,722 bytes, 15 entries, SHA-256 `08470b40a84f6efcde1661584bf1e647b0001bdecacc6a73925b2a069f8df16e`, no forbidden artifact name hits.
- `agent_personal_vault-0.1.4.tar.gz`: 44,619 bytes, 26 entries, SHA-256 `d62d2a4c2e8699d1a80fce7c21385bd8d7a057a33a6dfa3103c0d2c81f4c4572`, no forbidden artifact name hits.

If the user wants to proceed, the next bounded action is:

```text
Run the post-v0.1.4 lightweight observation cycle: confirm the GitHub prerelease, PyPI page, clean install, console scripts, README/PyPI description, Actions, security alerts, open Issue/PR state, and external feedback. Issue or PR only small corrections discovered by that observation.
```

This still does not create a new GitHub release, tag, package publish, repository setting change, branch deletion, Trusted Publishing activation, Claude Desktop app UI operation, API-billed validation, or public announcement. Future release creation, tag creation, package publish, repository setting changes, branch deletion, Trusted Publishing activation, Claude Desktop app UI operation, API-billed validation, and public announcement remain separate approvals.

## Trusted Publishing Approval Packet

Status date: 2026-07-04.

Current state:

- Package publishes through `v0.1.4` used the manual token fallback lane.
- `v0.1.5` was published to PyPI through the Trusted Publishing OIDC lane.
- `.github/workflows/pypi-publish.yml` exists as the manual workflow-dispatch path for the OIDC publish lane.
- GitHub environment `pypi` exists with required reviewer `Driedsandwich`, `prevent_self_review: false`, protected-branches-only deployment policy, no environment secrets, no stored PyPI token, and `can_admins_bypass: true`.
- PyPI Trusted Publisher is configured according to the PyPI project management UI confirmed by the project owner: GitHub, repository `Driedsandwich/agent-personal-vault`, workflow `pypi-publish.yml`, environment `pypi`.
- The first OIDC workflow result confirms the PyPI Trusted Publisher identity through the `v0.1.5` publish.
- PyPI `0.1.5` is published.
- Do not attempt to republish an existing PyPI version.

Recommended sequencing:

1. Use Trusted Publishing as the normal path for future separately approved package publishes after a dedicated version-bump PR, fresh artifact, CI, security, PyPI availability, and release-note checks.
2. Consider disabling admin bypass as a separate repository-settings approval.
3. Keep manual token publishing as an emergency fallback only.

Stop before any Trusted Publishing publish if the workflow can publish from an unapproved branch, the environment lacks human approval, PyPI settings do not exactly match the workflow identity, artifacts contain forbidden files, the package version already exists on PyPI, or any real personal data, secrets, private paths, or private support details appear in logs or artifacts.
