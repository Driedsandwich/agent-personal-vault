# Changelog

日本語タイトル: 変更履歴

status: draft
classification: SAFE_CANDIDATE
last_updated: 2026-07-02

All notable changes to Agent Personal Vault will be documented here.

This file is a draft planning document for a possible future release candidate. It does not authorize a GitHub release, tag creation, package publish, announcement, repository setting change, branch deletion, Claude Desktop GUI operation, or API-billed validation.

## Unreleased

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

### Package And Release Preparation

- Added package metadata and console entry points for `agent-personal-vault`, `apv-gui`, and `apv-mcp`.
- Performed local release/package dry-run checks for sdist and wheel contents without publishing.
- Updated package license metadata to avoid setuptools deprecation warnings.

### Known Limitations

- The project is public alpha and is not encrypted by default.
- Optional encryption is passphrase-managed; OS key store integration and recovery UX are not implemented.
- GUI localhost access is an operator convenience, not a hard multi-user security boundary.
- MCP host/client behavior differs by client. Generic stdio, Codex, and Claude Code paths have been validated; full Claude Desktop app restart and in-app live tool-call UX remain unvalidated without explicit approval and a non-interfering environment.
- GitHub release creation, tag creation, package publish, and public announcement have not been performed.
- External user feedback and support load remain lightly observed and should be rechecked before release-candidate preparation.
