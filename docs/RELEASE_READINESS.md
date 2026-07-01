# Release Readiness

日本語タイトル: リリース準備状況

status: local-ready
classification: SAFE_CANDIDATE
last_updated: 2026-07-01

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
- GUI profile saves write raw-free audit events.
- Optional encrypted store backend exists and uses `cryptography` when installed.
- CLI supports `encryption status`, `encryption encrypt`, and `encryption decrypt`.
- Read-only MCP stdio server exists.
- MCP exposes only `apv.schema`, `apv.context`, `apv.check`, and `apv.list_masked`.
- GUI warns that the project is alpha and not encrypted by default.
- Unit tests include raw-free context checks.
- Unit tests cover raw-output CLI warnings.
- Unit tests cover raw-free audit logging, GUI profile-save audit logging, one-time consent tokens, consent request approval/denial, encryption status, optional encryption dependency behavior, raw-free planning hints, and MCP raw-free behavior.
- PII scan script exists.
- Release check script exists.
- Makefile exists with `test`, `pii`, `release-check`, and `clean` targets.
- GitHub Actions workflow exists for future repository use.
- GitHub Issue templates exist and warn against posting real personal data.
- Local Git preparation guide exists.
- Prior art review exists and README positioning reflects it.
- Product positioning and MVP boundary document exists.
- Reputation risk review and launch messaging documents exist.
- Final publication audit document exists.

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
unittest: 22 tests passed
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

## Git Status

This directory is a local Git repository.

Latest local commit at this checkpoint is available from:

```text
git log --oneline -1
```

Remote creation, push, release creation, package publish, public announcement, and external sharing remain approval-gated.

## Not Done Without Explicit Approval

The following actions remain stopped:

- GitHub repository creation
- `git push`
- release creation
- package publish
- public announcement
- external sharing

## Recommended Next Approval

If the user wants to proceed, the next bounded local action is:

```text
Review docs/EXTERNAL_PUBLICATION_DECISION.md and decide whether to create a private GitHub dry-run repository first.
```

This still does not publish anything externally. Remote creation, push, release creation, package publish, and public announcement remain separate approvals.
