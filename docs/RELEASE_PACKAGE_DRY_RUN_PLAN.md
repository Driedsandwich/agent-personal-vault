# Release/Package Dry-Run Plan

日本語タイトル: 配布前dry-run計画

status: draft-plan
classification: SAFE_CANDIDATE
last_updated: 2026-07-02

## Purpose

This document defines the dry-run checklist for a future GitHub release or package distribution of Agent Personal Vault.

It is a planning document only. It does not authorize a GitHub release, package publish, tag creation, public announcement, repository setting change, branch deletion, Claude Desktop app UI operation, or API-billed review path. Each of those actions requires separate explicit approval, or 明示承認.

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
