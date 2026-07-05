# RC Approval Plan

日本語タイトル: RC実行前の個別承認計画

status: draft-plan
classification: SAFE_CANDIDATE
last_updated: 2026-07-06

## Purpose

This document separates future release-candidate execution into independent approval lanes.

It is a planning document only. It does not authorize GitHub release creation, tag creation, package publish, public announcement, repository setting changes, branch deletion, Claude Desktop app UI operation, or API-billed validation.

Each lane below requires a separate explicit approval before execution.

Use `docs/RELEASE_READINESS.md` as the source of truth for current published state. Use `docs/RC_APPROVAL_PACKET.md` only as a historical compact packet example unless a future release candidate gets a fresh packet through a dedicated Issue/PR.

## Shared Preflight

Run this preflight before asking for any execution approval:

- Confirm target repository: `Driedsandwich/agent-personal-vault`.
- Confirm target branch is `main`.
- Confirm target commit SHA and subject.
- Confirm intended version from `pyproject.toml`.
- Confirm `CHANGELOG.md` is current and still marked as an Unreleased draft until a release lane is separately approved.
- Confirm `python3 scripts/check_release.py` passes locally.
- Confirm latest GitHub Actions `test` and CodeQL runs on `main` are successful.
- Confirm open Issues and PRs are either zero or explicitly unrelated to release safety.
- Confirm open CodeQL, Dependabot, vulnerability, and secret-scanning alerts are zero, or explicitly documented as accepted risk.
- Confirm release and tag absence before the first release/tag lane.
- Confirm no raw personal data, secrets, local private paths, screenshots, vault files, consent files, audit logs, databases, images, or local developer config are present in the planned artifacts or public text.

Stop if any shared preflight item fails.

## Version Candidate

Current standing candidate:

```text
none
```

The historical first release-candidate packet targeted `0.1.0`; do not reuse that value. Future release candidates must take their version from `pyproject.toml` after a dedicated Issue/PR changes it and passes CI.

Do not bundle a version bump into release execution unless that exact bump was separately approved.

## Changelog And Release Note Source

Use `CHANGELOG.md` `Unreleased` as the source draft for any future release note.

Before asking for release approval, convert the draft into an approval-ready release note summary that keeps these sections visible:

- user-visible changes
- security and privacy changes
- documentation and governance changes
- package and release preparation
- known limitations

The release note must not include raw personal data, local private paths, screenshots, vault files, private support details, or claims of broad security/compliance support.

## Fresh Artifact Hash Procedure

Before any GitHub release or package publish approval request, regenerate artifacts from the target commit in a pinned local environment.

Minimum procedure:

```sh
git switch main
git pull --ff-only
python3 -m venv .venv-release-dry-run
. .venv-release-dry-run/bin/activate
python3 -m pip install --upgrade pip build
python3 -m build
python3 scripts/check_release.py
```

Record:

- target commit SHA
- Python version
- `pip` version
- `build` version
- wheel filename, bytes, entry count, SHA-256
- sdist filename, bytes, entry count, SHA-256
- forbidden-name scan result
- whether artifacts include only expected package, metadata, README, LICENSE, tests, and packaging files

The recorded hashes are evidence for those exact generated files. They are not a cross-environment reproducible-build guarantee.

Delete or ignore local build outputs after the dry-run unless a later PR explicitly adds an artifact workflow.

## Lane 1: GitHub Release Draft

Approval required:

```text
Approve creating a GitHub release draft for Agent Personal Vault at <commit> with version <version>. Do not publish it yet.
```

Allowed after approval:

- Create a draft GitHub release only.
- Use the reviewed release note text.
- Attach no artifact unless the approval explicitly includes attachments.

Still not allowed:

- Publish the release.
- Create or move tags unless separately approved.
- Upload package indexes.
- Announce publicly.

Rollback:

- Delete or close the draft release if it contains incorrect public-safe text.
- Open a corrective Issue if a safety boundary problem is found.
- Do not rely on deletion as the only response if a published release has already occurred.

Post-action verification:

- Release exists only as draft.
- Release text contains no raw values, secrets, private paths, screenshots, vault files, or unsupported security claims.
- No new tag was created unless separately approved.
- Open Issues/PRs and security alerts remain acceptable.

## Lane 2: Tag Creation

Approval required:

```text
Approve creating tag <tag> for Agent Personal Vault at commit <commit>. Do not create or publish a GitHub release and do not publish any package.
```

Allowed after approval:

- Create the approved tag at the approved commit.
- Push only that tag.

Still not allowed:

- Create a GitHub release.
- Publish packages.
- Announce publicly.
- Move or delete tags without a separate approval.

Rollback:

- If the tag is wrong and not externally used, ask for separate approval before deleting or replacing it.
- If external use may have started, prefer a corrective tag/release note plan over silent deletion.

Post-action verification:

- Tag points to the approved commit.
- No release was created unless separately approved.
- CI and security alerts remain acceptable.

## Lane 3: GitHub Release Publish

Approval required:

```text
Approve publishing GitHub release <tag/version> for Agent Personal Vault using the reviewed release text and fresh artifact hash record. Do not publish to a package index and do not announce publicly.
```

Allowed after approval:

- Publish the approved GitHub release.
- Attach only approved artifacts, if the approval explicitly includes attachments.

Still not allowed:

- Package publish.
- SNS, blog, newsletter, or community announcement.
- Repository setting changes.

Rollback:

- If unsafe, stop announcements, mark the release with a corrective note, open a corrective Issue or security advisory as appropriate, and prepare a patch through PR.
- Delete only if separately approved and suitable for the situation.

Post-action verification:

- Release points to the approved tag and commit.
- Release text matches the reviewed text.
- Attached artifacts match approved filenames and hashes, if any were attached.
- Security alerts remain acceptable.

## Lane 4: Package Publish

Approval required:

```text
Approve publishing package <name> version <version> from commit <commit> to <package index> using artifacts with these hashes: <hashes>. Do not create GitHub releases/tags or announce publicly unless separately approved.
```

Allowed after approval:

- Publish only the approved package/version to the approved package index.
- Use only the freshly generated and reviewed artifacts.

Still not allowed:

- Create or publish GitHub releases.
- Create tags.
- Announce publicly.
- Change repository settings.

Rollback:

- If supported by the package index, yank or mark the package unsafe only after separate approval.
- Prepare a corrective patch release through Issue/PR if needed.
- Open a security advisory or Issue when user safety is affected.

Post-action verification:

- Package index shows the expected name and version.
- Published files match the approved hashes where the index exposes them.
- Installation instructions still match the package metadata.
- No unexpected dependency or metadata change appeared.

## Lane 5: Public Announcement

Approval required:

```text
Approve publishing the reviewed announcement text to <channel>. Do not create releases, tags, package publishes, repository setting changes, or branch deletions.
```

Allowed after approval:

- Publish only the approved text to the approved channel.

Required wording constraints:

- Say alpha/local utility.
- Keep optional encryption and local-machine limits visible.
- Do not claim compliance, enterprise security, broad compatibility, or production readiness.
- Do not ask users to post real personal data.
- Link to README, SECURITY, and issue reporting guidance.
- Keep Claude Desktop full app live UX unvalidated unless it is separately approved and tested.
- Follow the pre-announcement checklist in `docs/LAUNCH_MESSAGING.md`.

Rollback:

- Edit or withdraw the announcement if the platform supports it.
- Post a correction if the original text was materially misleading.
- Open a repo Issue for any repeated confusion caused by the announcement.

Post-action verification:

- Published text matches the approved text.
- Links work.
- No real personal data, screenshots with raw values, private paths, or unsupported claims are present.
- Watch for immediate Issues/PRs or support-load signals.

## Shared Stop Conditions

Stop before any lane execution if:

- local release check fails
- GitHub Actions `test` or CodeQL fails
- open security alerts appear
- raw personal data, secrets, local private paths, vault files, consent files, audit logs, screenshots, databases, or images appear in artifacts or public text
- consent bypass or audit raw leakage is suspected
- artifact filenames, sizes, entry counts, or hashes differ from the approval packet without explanation
- two or more independent support signals show the same consent, raw retrieval, MCP setup, or safety-boundary confusion
- the requested action combines multiple lanes without explicitly approving each lane
- the request involves Claude Desktop app UI operation or API-billed validation without separate explicit approval

## Recommended Approval Order

Recommended order:

1. Fresh artifact hash and release-note approval packet.
2. Tag creation.
3. GitHub release draft.
4. GitHub release publish.
5. Package publish, only if distribution beyond GitHub is still desired.
6. Public announcement, only after release/package state is verified.

It is acceptable to stop after any lane and continue public-alpha operation without release, package publish, or announcement.
