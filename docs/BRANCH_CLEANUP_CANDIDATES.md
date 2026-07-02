# Branch Cleanup Candidates

日本語タイトル: branch整理の削除候補検証

status: draft-evidence
classification: SAFE_CANDIDATE
last_updated: 2026-07-02

## Purpose

This document records a read-only verification pass for local and remote `codex/*` branches.

It does not authorize local branch deletion, remote branch deletion, repository setting changes, release/tag creation, package publish, public announcement, Claude Desktop app UI operation, or API-billed validation.

## Verification Summary

Snapshot:

- Local `codex/*`: 34.
- Remote `origin/codex/*`: 32.
- Unique `codex/*` names: 34.
- Active verification branch at the time of the check: `codex/branch-cleanup-verification-90`.
- Open Issues/PRs before this verification Issue: 0/0.

Result:

- 31 local+remote branches had corresponding merged PRs and their current branch tips matched the recorded PR head SHA.
- 1 local-only branch, `codex/sync-alpha-readiness-docs`, was `git branch --merged main` but had no visible PR evidence in the current `gh pr list --state all --limit 200` result.
- 1 active local-only branch, `codex/branch-cleanup-verification-90`, was the branch used to create this report and must not be treated as a cleanup candidate until its PR is complete.
- No branch was deleted.

## Tree Difference Interpretation

Most old squash-merged branches show `Tree vs main: differs`. That is expected and does not by itself mean the branch is unmerged or unsafe to delete.

Reason: PRs were squash-merged into `main`, and `main` has continued to advance after those branch tips. The stronger evidence for cleanup is:

1. the corresponding GitHub PR is `MERGED`;
2. the current branch tip still matches the PR head SHA;
3. there is no post-merge branch-only commit detected.

For local-only branches with no PR evidence, use `git branch --merged main` as weaker evidence and keep the risk higher.

## Candidate Table

| Branch | Scope | PR evidence | Branch tip | Tree vs main | Cleanup classification |
|---|---|---|---|---|---|
| `codex/add-gui-audit-viewer` | local+remote | #32 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/add-mcp-client-setup-docs` | local+remote | #30 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/add-public-alpha-quickstart` | local+remote | #28 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/allow-derived-mcp-consent` | local+remote | #26 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/approval-time-target-77` | local+remote | #78 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/branch-cleanup-verification-90` | local-only | - | git-merged | same | keep: active verification branch |
| `codex/clarify-rc-artifact-hashes-69` | local+remote | #70 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/claude-code-mcp-tool-approval-43` | local+remote | #44 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/claude-desktop-live-ux-49` | local+remote | #50 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/claude-desktop-ux-validation-47` | local+remote | #48 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/fix-gui-panel-contrast` | local+remote | #34 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/gui-consent-id-onboarding-40` | local+remote | #41 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/local-release-dry-run-53` | local+remote | #54 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/mcp-one-key-consent-boundary` | local+remote | #60 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/pre-rc-draft` | local+remote | #64 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/pre-release-risk-decision-55` | local+remote | #56 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/project-url-metadata-86` | local+remote | #87 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/public-alpha-checkpoint-review` | local+remote | #36 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/public-alpha-readiness-refresh-45` | local+remote | #46 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/pypi-install-docs-81` | local+remote | #82 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/raw-boundary-docs-57` | local+remote | #58 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/rc-approval-packet-73` | local+remote | #74 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/rc-approval-plan-71` | local+remote | #72 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/rc-entry-exit-criteria` | local+remote | #62 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/rc-final-dry-run` | local+remote | #68 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/rc-preflight-artifacts-79` | local+remote | #80 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/rc-prep-checklist` | local+remote | #66 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/refresh-rc-approval-packet-75` | local+remote | #76 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/release-package-dry-run-51` | local+remote | #52 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/sync-alpha-readiness-docs` | local-only | - | git-merged | differs | candidate: git-merged, no PR evidence |
| `codex/sync-public-alpha-readiness-docs` | local+remote | #24 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/triage-codeql-path-injection` | local+remote | #39 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |
| `codex/trusted-publishing-plan-88` | local+remote | #89 MERGED | matches PR head | same | candidate: merged PR, no branch-only commits detected |
| `codex/v011-planning-83` | local+remote | #84 MERGED | matches PR head | differs | candidate: merged PR, no branch-only commits detected |

## Deletion Risk

Low-risk future cleanup candidates, subject to separate explicit branch-deletion approval:

- local+remote branches whose PR evidence is `MERGED` and whose branch tip matches the PR head SHA;
- local-only branches that are `git branch --merged main`, if the user only wants local cleanup.

Higher-risk or hold cases:

- the active verification branch for this document;
- branches with no PR evidence and no git-merged evidence;
- branches where the current branch tip differs from the recorded PR head SHA;
- any branch linked to an open PR, unmerged PR, or unreconciled worktree state.

## Future Deletion Procedure

If branch deletion is separately approved later:

1. Re-run this verification immediately before deletion.
2. List exact local branches and remote branches to delete.
3. Do not include the active working branch.
4. Delete local and remote branches in separate command groups.
5. Verify counts afterward.
6. Confirm open Issue/PR state and `main` clean state afterward.

Do not use `gh pr merge --delete-branch` unless branch deletion was explicitly approved in the current request.
