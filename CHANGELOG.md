# Changelog

日本語タイトル: 変更履歴

status: draft
classification: SAFE_CANDIDATE
last_updated: 2026-07-03

All notable changes to Agent Personal Vault will be documented here.

This file is a draft planning document for a possible future release candidate. It does not authorize a GitHub release, tag creation, package publish, announcement, repository setting change, branch deletion, Claude Desktop GUI operation, or API-billed validation.

## Unreleased

No unreleased changes yet.

## 0.1.3 - 2026-07-03

### Security And Privacy Changes

- Avoid changing permissions on existing custom store parent directories.
- Redact active raw-access consent grant IDs from agent-facing audit and consent listing surfaces.
- Sanitize unexpected MCP error responses so local store paths and internal filesystem details are not returned to MCP clients.
- Require explicit human acknowledgement for `env` bulk raw export and for `consent grant/request --action env`.
- Record guarded bulk raw export attempts as `env_bulk_export` audit events.
- Align the MCP server version with the package version.

### Documentation And Release Hygiene

- Update README install examples to the current public alpha package version, `0.1.3`.
- Treat local build outputs such as `dist/`, `build/`, and `*.egg-info/` as generated release-check cleanup targets so repository-root metadata checks do not pick up stale local package metadata.
- Refresh the package long description from the current README so PyPI can pick up the latest install example and safety-boundary wording after a separately approved package publish.

### Known Limitations

- This preparation does not create a GitHub release, tag, package publish, public announcement, repository setting change, branch deletion, Trusted Publishing activation, Claude Desktop UI operation, or API-billed validation.

## 0.1.2 - 2026-07-02

### Package And Release Preparation

- Refresh the package long description from the corrected README so the PyPI project page no longer shows the old `agent-personal-vault==0.1.0` install examples.

### Known Limitations

- This patch does not change runtime behavior.
- GitHub release creation, tag creation, package publish, and public announcement for v0.1.2 have not been performed.

## 0.1.1 - 2026-07-02

### v0.1.1 Candidate Scope

This v0.1.1 candidate is intentionally small. It includes Project-URL package metadata and documentation/governance updates only.

### User-Visible Changes

- Added raw-free task planning hints so agents can choose smaller candidate key sets before requesting raw access.
- Added public-alpha quickstart guidance for raw-free context, MCP context, consent request, GUI approval, CLI one-key retrieval, and audit review.
- Added MCP client setup guidance for stdio clients, Codex, Claude Desktop-style configuration, and Claude Code tool approval names.
- Added GUI audit summary and recent event viewing.
- Improved GUI consent handoff by displaying the approved consent id for CLI `get`.
- Improved GUI panel contrast and public-alpha usability details.

### Security And Privacy Changes

- Kept MCP raw-free by exposing planning, status, masked listing, and consent-request tools only.
- Allowed derived keys such as `FULL_NAME` in MCP consent requests without returning raw values.
- Added raw-free GUI profile-save audit logging.
- Triaged CodeQL path-injection alerts and kept local path handling bounded to local-user paths.
- Aligned public-alpha raw boundary docs around one-key raw retrieval.
- Fixed the MCP consent boundary so `apv.request_consent` accepts one-key `get` requests only and rejects bulk `env` requests.
- Added tests and release checks for local developer config exclusion, raw-free audit/consent behavior, MCP raw-free behavior, and one-key consent boundaries.

### Documentation And Governance

- Added prior art, product positioning, reputation risk, launch messaging, publication gate, and release readiness documentation.
- Added release/package dry-run planning and pre-RC entry criteria.
- Recorded terminal-only and Claude Desktop-like validation boundaries without claiming full Claude Desktop in-app live UX support.
- Documented that approval commands, including direct `consent grant`, are human-operated and not agent-facing.
- Added PyPI Trusted Publishing planning without enabling publisher settings or an active publishing workflow.
- Added branch cleanup candidate verification without deleting local or remote branches.
- Finalized the pre-announcement checklist, safe/forbidden wording, correction procedure, and public-alpha support-load expectations.
- Added v0.1.1 readiness and RC preparation notes that keep release, tag, package publish, announcement, repository settings, and branch deletion as separate approval lanes.

### Package And Release Preparation

- Added package metadata and console entry points for `agent-personal-vault`, `apv-gui`, and `apv-mcp`.
- Added Project-URL package metadata for Homepage, Source, Issues, and Documentation. This will appear on PyPI only after a future separately approved package publish.
- Performed local release/package dry-run checks for sdist and wheel contents without publishing.
- Updated package license metadata to avoid setuptools deprecation warnings.

### Known Limitations

- The project is public alpha and is not encrypted by default.
- Optional encryption is passphrase-managed; OS key store integration and recovery UX are not implemented.
- GUI localhost access is an operator convenience, not a hard multi-user security boundary.
- MCP host/client behavior differs by client. Generic stdio, Codex, and Claude Code paths have been validated; full Claude Desktop app restart and in-app live tool-call UX remain unvalidated without explicit approval and a non-interfering environment.
- GitHub release creation, tag creation, package publish, and public announcement for v0.1.1 have not been performed.
- PyPI Trusted Publishing is documented as a future hardening step but is not enabled.
- External user feedback and support load remain lightly observed and should be rechecked before release-candidate preparation.
