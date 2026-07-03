# Release/Package Dry-Run Plan

日本語タイトル: 配布前dry-run計画

status: draft-plan
classification: SAFE_CANDIDATE
last_updated: 2026-07-03

## Purpose

This document defines the dry-run checklist for a future GitHub release or package distribution of Agent Personal Vault.

It is a planning document only. It does not authorize a GitHub release, package publish, tag creation, public announcement, repository setting change, branch deletion, Claude Desktop app UI operation, or API-billed review path. Each of those actions requires separate explicit approval, or 明示承認.

Current package state:

- Latest GitHub prerelease: `v0.1.4`.
- Latest PyPI package: `0.1.4`.
- Latest main commit: `ce0abbef2c899e9d0d227080da4b969f9cfde560`.
- Trusted Publishing is not enabled. Package publishes through `v0.1.4` used the manual token fallback lane.
- `v0.1.4` is tagged, published as a GitHub prerelease, and published to PyPI.
- Older sections in this document are historical planning records unless a section explicitly says it is current.

## Scope

Use this plan before any distribution approval request to confirm that the release path is reproducible, reversible enough for an alpha project, and still raw-free by default.

The dry-run should use dummy data only.

After this dry-run evidence is current, use `docs/RC_APPROVAL_PLAN.md` to separate GitHub release, tag creation, package publish, and announcement into independent approval lanes.

## Versioning

- Treat `pyproject.toml` `project.version` as the package version source of truth.
- Do not bump the version without a dedicated Issue, PR, CI result, and explicit approval.
- Before a release approval request, confirm the intended version, target commit SHA, and whether the release is an alpha, patch, or compatibility-breaking change.
- Do not create tags during dry-run planning.

## Changelog

- Build the changelog from merged PRs and linked Issues.
- Separate user-visible changes, security changes, docs-only changes, and known limitations.
- Do not include raw personal data, local paths, private screenshots, private config snippets, or private support details.
- Keep alpha limitations explicit: local-first, raw-free default, consent-gated raw retrieval, and no external submission automation.
- Before RC preparation, prepare a `CHANGELOG.md` draft or release-note draft that covers all merged public-alpha changes since the last release-readiness decision.

## Release Artifact Check

- Confirm the target commit is on `main` and CI is green before proposing a release.
- Inspect the files that would be included in a source distribution or wheel.
- Confirm generated artifacts do not include `vault.json`, consent/audit files, local developer config, images, screenshots, databases, backups, or private paths.
- Keep build outputs out of the repository unless a later PR explicitly adds an ignored local artifact path or CI artifact workflow.
- Record source distribution and wheel filenames plus SHA-256 hashes in the future RC proposal. Hash recording is evidence for the proposal only; it does not authorize upload.
- Treat recorded hashes as evidence for the exact generated files from that dry-run, not as a cross-environment reproducible-build guarantee. Before any separately approved release or package publish action, rebuild from the target commit in a pinned local environment, record fresh filenames, sizes, entry counts, and SHA-256 hashes, and use those fresh hashes for the approval request.

## Package Build Check

Dry-run package build should be performed in an isolated local environment before any publish approval request.

Expected future check:

```sh
python3 -m venv .venv-release-dry-run
. .venv-release-dry-run/bin/activate
python3 -m pip install --upgrade pip build
python3 -m build
python3 scripts/check_release.py
```

Do not upload the built package. If an additional build dependency or packaging workflow change is needed, handle it in a separate PR.

## RC Entry Snapshot

Before asking to move from public alpha into release-candidate preparation, record this snapshot in `docs/RELEASE_READINESS.md` or a linked Issue:

- target `main` commit SHA
- latest successful GitHub Actions `test` run
- latest successful CodeQL run
- open CodeQL alert count
- Dependabot/vulnerability/secret-scanning status
- local `python3 scripts/check_release.py` result
- whether release/tag absence was confirmed
- whether open Issues/PRs or external feedback contain repeated consent, raw retrieval, MCP setup, or safety-boundary confusion
- which MCP hosts are validated and which remain explicitly unvalidated

## Rollback

Because release and package publish actions can be externally cached, rollback must not rely on deletion as the only control.

Prepare these actions before approval:

- stop or withdraw announcement drafts
- publish a corrective patch release if needed
- yank or mark a package release as unsafe only if the package index supports it
- open a security advisory or Issue when the problem affects user safety
- revert docs or code through PR if the repository state is wrong
- keep a short post-incident note that avoids raw personal data and private paths

## Dependency And Provenance

- Confirm the package metadata in `pyproject.toml`: name, version, Python requirement, license, entry points, and optional `encrypted` dependency.
- Confirm no unexpected runtime dependency was added.
- Record the target commit SHA, CI run URL, and artifact hash before a future release.
- Prefer artifacts built from a clean checkout of the target commit.
- Do not claim supply-chain provenance stronger than what was actually verified.

## v0.1.1 Candidate Planning

This section tracks small follow-up candidates after the `v0.1.0` GitHub prerelease and PyPI publish. It is planning only. It does not authorize a version bump, tag, release, package publish, repository setting change, branch deletion, or announcement.

### Project URL Metadata

Candidate: add `[project.urls]` to `pyproject.toml` in a dedicated v0.1.1 PR so PyPI can show canonical project links.

Recommended initial keys:

- `Homepage`: GitHub repository URL.
- `Source`: GitHub repository URL.
- `Issues`: GitHub Issues URL.
- `Documentation`: README or docs entry point URL.

Acceptance checks before implementation:

- Confirm the URLs are public and stable.
- Confirm `python3 -m build`, `twine check`, and `python3 scripts/check_release.py` still pass.
- Confirm the package metadata shown by PyPI matches the intended links after a separately approved future package publish.

### PyPI Trusted Publishing

Candidate: evaluate PyPI Trusted Publishing for a future publish lane so uploads can use a GitHub Actions OIDC workflow instead of a long-lived local API token.

Trusted Publishing should be handled as a separate repository-setting and workflow-change lane because it requires PyPI-side publisher configuration and a GitHub Actions publish workflow. It is not required for emergency token-based maintenance, but it is preferable before repeated package publishes.

Detailed plan: `docs/PYPI_TRUSTED_PUBLISHING_PLAN.md`.

Do not enable it without separate explicit approval for:

- the PyPI project publisher configuration;
- any GitHub Actions workflow that can publish to PyPI;
- any GitHub environment or reviewer protection used by that workflow;
- the first publish attempt through that workflow.

## v0.1.2 Candidate Planning

This section tracks the minimal follow-up candidate after the `v0.1.1` GitHub prerelease and PyPI publish. It is planning only. It does not authorize a version bump, tag, release, package publish, repository setting change, branch deletion, announcement, Claude Desktop app UI operation, or API-billed validation.

### PyPI Long Description Refresh

Issue #102 records that the PyPI project page for `0.1.1` still shows the old `agent-personal-vault==0.1.0` install examples in the long description. The GitHub README on `main` is already corrected to `0.1.1`, but PyPI renders the long description captured inside the uploaded package metadata.

Recommended v0.1.2 scope:

- Keep v0.1.2 as a documentation/package-metadata patch only.
- Include the corrected README long description so PyPI shows `agent-personal-vault==0.1.1` or the then-current version in install examples.
- Avoid runtime behavior changes unless a separate blocker is found before the v0.1.2 approval packet.

Expected release shape if separately approved:

- dedicated version bump from `0.1.1` to `0.1.2`;
- updated CHANGELOG entry describing the PyPI description refresh;
- fresh isolated sdist/wheel build from the target commit;
- `twine check`, SHA-256 recording, Project-URL metadata check, and strict forbidden-file scan;
- separate approvals for tag creation, GitHub prerelease, PyPI package publish, and any announcement.

Trusted Publishing should not be bundled into this minimal v0.1.2 fix by default. It remains a separate repository/PyPI settings lane because it changes the publish mechanism and requires PyPI publisher configuration, GitHub workflow review, and environment protection decisions. It can be prepared in parallel as documentation or a dry-run plan, but activation should require separate explicit approval.

Stop before any v0.1.2 release/tag/package publish request if:

- PyPI already contains the intended version;
- README, CHANGELOG, package version, release notes, and artifact metadata do not agree;
- artifacts include forbidden local/private files;
- Security alerts, CI, open Issues/PRs, or support signals identify a release-blocking issue;
- the requested action would also activate Trusted Publishing, change repository settings, delete branches, announce publicly, operate Claude Desktop app UI, or use API-billed validation without separate explicit approval.

### Branch Cleanup Candidate Verification

Candidate: prune merged `codex/*` branches after verifying that each branch is already merged to `main` or has a tree matching `main`.

Detailed verification: `docs/BRANCH_CLEANUP_CANDIDATES.md`.

Current branch cleanup must stay read-only unless branch deletion is separately approved. A safe verification pass may record:

- local and remote `codex/*` branch counts;
- `git branch --merged main --list "codex/*"` output;
- `git branch -r --merged origin/main --list "origin/codex/*"` output;
- any branch whose tree differs from `main`, with the relevant PR or risk note.

Snapshot from Issue #83 planning:

- Local `codex/*` branches before pushing this planning branch: 31, including the active planning branch.
- Remote `origin/codex/*` branches before pushing this planning branch: 29.
- Simple tree matching against current `main` is not enough for old squash-merged PR branches, because current `main` can include later commits that were not in the old branch tip.
- GitHub PR history is the better first verification source for squash-merged branches: the visible `origin/codex/*` branches checked in this pass had corresponding merged PRs where a PR association was available.
- Local-only `codex/sync-alpha-readiness-docs` appeared in `git branch --merged main --list "codex/*"` and is a potential local cleanup candidate, but still requires separate branch-deletion approval.

Deletion commands remain prohibited in this planning lane. If deletion is later approved, local and remote deletions should be listed explicitly before execution and verified afterward. Use `gh pr merge` without `--delete-branch` unless branch deletion is separately approved.

## Security Alerts

Before requesting release or package publish approval:

- Confirm Dependabot alerts, vulnerability alerts, secret scanning, push protection, and CodeQL state.
- Open security alerts must be either fixed, closed as false positive, or explicitly documented as accepted risk.
- Re-run local release checks after any security-related change.
- Stop if raw personal data, secrets, local private paths, consent bypass, or audit raw leakage is found.

## Support Load

Public alpha support should stay lightweight.

- Keep Issues focused on bugs, docs gaps, and narrow feature requests.
- Ask users not to post real personal data in Issues or PRs.
- Avoid promising response times, production support, or data-recovery guarantees.
- Prefer docs fixes for repeated onboarding questions.
- Treat repeated confusion about consent, raw retrieval, or MCP setup as a release-blocking signal.
- Treat two or more independent reports about the same consent, raw retrieval, MCP setup, or safety-boundary confusion as a stop condition for RC preparation until the confusion is fixed or explicitly accepted as an alpha limitation.

## Forbidden During Dry-Run

The following remain separate explicit approvals:

- GitHub release creation
- tag creation
- package publish
- SNS, blog, newsletter, or community announcement
- repository setting changes
- branch deletion
- Claude Desktop app UI operation
- API-billed review or validation route
- use of real personal data or secrets
- external submission, upload, form send, or account action

## Minimum Exit Criteria

The dry-run plan is complete only when:

- this document is current
- `docs/RELEASE_READINESS.md` references this plan
- local `python3 scripts/check_release.py` passes
- CI passes on the PR that changes the plan
- the PR is merged through the repository's Issue/PR workflow

Meeting these criteria still does not authorize release creation or package publish.

## v0.1.4 Patch Candidate Dry-Run

This section records the package dry-run for the `v0.1.4` patch candidate. It does not create a tag, GitHub release, package publish, announcement, repository setting change, branch deletion, Trusted Publishing activation, Claude Desktop app UI operation, or API-billed validation.

Post-publish status:

- `v0.1.4` has since been tagged, published as a GitHub prerelease, and uploaded to PyPI through the separately approved release/package lanes.
- The uploaded PyPI files were regenerated from tag `v0.1.4` at `ce0abbef2c899e9d0d227080da4b969f9cfde560`; their hashes are listed below.
- Trusted Publishing remains disabled and should be handled as a separate settings/workflow lane.

Candidate scope:

- publish the post-`v0.1.3` boundary cleanup and consent/local-file hardening already merged to `main`;
- keep the release as a patch release;
- keep Trusted Publishing activation outside this patch by default.

Dry-run command shape:

```sh
python -m build --outdir /tmp/apv-v014-rc-dist /tmp/apv-v014-rc-src
twine check /tmp/apv-v014-rc-dist/*
```

Dry-run result:

- `twine check`: passed for sdist and wheel.
- Project-URL metadata present: Homepage, Source, Issues, Documentation.
- Package metadata includes the README install example for `agent-personal-vault==0.1.4` and does not include the old pinned `agent-personal-vault==0.1.3` example.
- Strict forbidden-file scan found no `vault.json`, `consents.json`, `audit.jsonl`, `.pypirc`, `.env`, private job profile path, username-specific path fragment, or `/Users/` path in artifact entries.

Artifacts:

| file | size | entries | SHA-256 |
| --- | ---: | ---: | --- |
| `agent_personal_vault-0.1.4-py3-none-any.whl` | 34,722 bytes | 15 | `08470b40a84f6efcde1661584bf1e647b0001bdecacc6a73925b2a069f8df16e` |
| `agent_personal_vault-0.1.4.tar.gz` | 44,619 bytes | 26 | `d62d2a4c2e8699d1a80fce7c21385bd8d7a057a33a6dfa3103c0d2c81f4c4572` |

Before any future separately approved package publish, regenerate artifacts from the approved tag or target commit and compare the filename, version, metadata, forbidden-file scan, and SHA-256 values. Do not upload dry-run artifacts unless that exact upload is separately approved.
