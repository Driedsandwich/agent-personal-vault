# Release Readiness

日本語タイトル: リリース準備状況

status: local-ready
classification: SAFE_CANDIDATE

## Current Summary

`agent-personal-vault` is a local OSS candidate for an AI-agent personal data vault.

Core product boundary:

- local-first personal data storage
- raw-free metadata for AI agent planning
- minimum-key raw retrieval only when needed
- explicit final-action boundary before external submission, upload, push, publish, or sharing

`job_hunting_profile` is the first schema template. It is not the product boundary.

## Completed

- Standalone package directory exists.
- No real `vault.json` is present.
- No image, SQLite, database, backup, or private data file is present.
- No source references to the originating private project path were found.
- README, SECURITY, CONTRIBUTING, LICENSE, AGENT_PROTOCOL, and PUBLICATION_GATE exist.
- CLI supports raw-free `context`.
- CLI supports raw-free `schema`.
- CLI `env` warns before raw-value export.
- Unit tests include raw-free context checks.
- PII scan script exists.
- Release check script exists.
- Makefile exists with `test`, `pii`, `release-check`, and `clean` targets.
- GitHub Actions workflow exists for future repository use.
- Local Git preparation guide exists.
- Prior art review exists and README positioning reflects it.
- Product positioning and MVP boundary document exists.

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
unittest: 10 tests passed
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

This directory is still not a Git repository. Local Git initialization and the first local commit remain approval-gated. See [LOCAL_GIT_PREP.md](LOCAL_GIT_PREP.md).

## Not Done Without Explicit Approval

The following actions remain stopped:

- `git init`
- local commit
- GitHub repository creation
- `git push`
- release creation
- package publish
- public announcement
- external sharing

## Recommended Next Approval

If the user wants to proceed, the next bounded local action is:

```text
Initialize a local Git repository inside agent-personal-vault and create the first local commit after rerunning tests and PII scan.
```

This still does not publish anything externally. Remote creation and push remain separate approvals.
