# Release/Package Dry-Run Plan

日本語タイトル: 配布前dry-run計画

status: draft-plan
classification: SAFE_CANDIDATE
last_updated: 2026-07-04

## Purpose

This document defines the dry-run checklist for a future GitHub release or package distribution of Agent Personal Vault.

It is a planning document only. It does not authorize a GitHub release, package publish, tag creation, public announcement, repository setting change, branch deletion, Claude Desktop app UI operation, or API-billed review path. Each of those actions requires separate explicit approval, or 明示承認.

Current package state:

- Latest GitHub prerelease: `v0.1.11`.
- Latest PyPI package: `0.1.11`.
- Latest Trusted Publisher documentation checkpoint before this status refresh: `3b9207b5b4cb7446342ea3a2b12e1a3249be353b`.
- Trusted Publishing setup was first validated by the `v0.1.5` PyPI publish and used again for the `v0.1.6`, `v0.1.7`, `v0.1.8`, `v0.1.9`, `v0.1.10`, and `v0.1.11` PyPI publishes through the OIDC lane. Package publishes through `v0.1.4` used the manual token fallback lane.
- `v0.1.11` is tagged, published as a GitHub prerelease, and published to PyPI.
- The manual `publish-package` workflow exists and is the approved OIDC publish lane after GitHub environment approval.
- GitHub environment `pypi` exists with required reviewer `Driedsandwich`, `prevent_self_review: false`, protected-branches-only deployment policy, no environment secrets, no stored PyPI token, and `can_admins_bypass: true`.
- PyPI Trusted Publisher is configured according to the PyPI project management UI confirmed by the project owner: GitHub, repository `Driedsandwich/agent-personal-vault`, workflow `pypi-publish.yml`, environment `pypi`.
- The Trusted Publisher was used successfully for the `v0.1.5`, `v0.1.6`, `v0.1.7`, `v0.1.8`, `v0.1.9`, `v0.1.10`, and `v0.1.11` PyPI publishes.
- Manual token publishing is now an emergency fallback only.
- The `v0.1.10` patch release was published after `v0.1.9` for synced or cloud-backed store path warning coverage.
- The `v0.1.11` patch release was published after `v0.1.10` for broader raw-like task and purpose redaction.
- Older sections in this document are historical planning records unless a section explicitly says it is current.

## Trusted Publishing OIDC Publish Plan

Status date: 2026-07-04.

This section records the preflight plan that was used for the first Trusted Publishing OIDC publish and remains the baseline for future OIDC publishes. It does not authorize a version bump, GitHub tag creation, GitHub release creation or publish, PyPI package upload, SNS/blog announcement, repository setting change, branch deletion, Claude Desktop app UI operation, or API-billed validation.

### Current Verified State

- `v0.1.11` is published as a GitHub prerelease and points to `3b9207b5b4cb7446342ea3a2b12e1a3249be353b`.
- PyPI latest is `0.1.11`.
- The `publish-package` workflow is active and manually triggered through `workflow_dispatch`.
- GitHub environment `pypi` exists with required reviewer `Driedsandwich`, `prevent_self_review: false`, protected-branches-only deployment policy, no environment secrets, no stored PyPI token, and `can_admins_bypass: true`.
- PyPI Trusted Publisher is configured in the PyPI project management UI for GitHub repository `Driedsandwich/agent-personal-vault`, workflow `pypi-publish.yml`, and environment `pypi`.
- The `v0.1.11` OIDC publish workflow completed successfully.
- The `v0.1.11` publish logs include DSSE/in-toto attestation generation for the wheel and sdist.
- Open CodeQL, Dependabot, and secret-scanning alerts were 0 during the post-publish check.

### Target Version And Version Bump

Do not use Trusted Publishing to republish an existing PyPI version. PyPI versions are immutable, and the workflow should stop if the target version already exists on PyPI.

For a future OIDC publish, use a new version only after a dedicated Issue/PR updates:

- `pyproject.toml` version;
- `CHANGELOG.md`;
- release/package dry-run evidence;
- any release-note text that must mention the publishing-lane change.

An OIDC publish may be an infrastructure-validation patch release if no runtime change is needed, but it still needs the same version, changelog, artifact, CI, and security checks as any package publish.

### Fresh Artifact Preflight

Before asking to run the OIDC workflow, rebuild artifacts from the approved tag or target commit and record:

- wheel and sdist filenames;
- file sizes;
- archive entry counts;
- SHA-256 hashes;
- `twine check` result;
- Project-URL metadata;
- strict forbidden-file scan result;
- PyPI absence for the exact target version.

Do not reuse previous local artifact hashes as authorization for an OIDC publish.

### Approval Lanes

Keep each OIDC publish split into separate approvals:

1. Version-bump PR, including `CHANGELOG.md` and fresh artifact dry-run evidence.
2. GitHub tag creation for the approved commit.
3. GitHub prerelease draft and publish for the approved tag, if still desired before package upload.
4. OIDC publish workflow dispatch using the approved tag and exact confirmation phrase.
5. Post-publish verification of PyPI page, install, console scripts, Project-URL metadata, Actions logs, security alerts, and open Issue/PR state.
6. Any SNS/blog/community announcement as a separate optional lane.

### Stop Conditions

Stop before an OIDC publish if any of these are true:

- The target version already exists on PyPI.
- The workflow filename, repository, owner, or environment no longer matches the PyPI Trusted Publisher settings.
- The `publish` job lacks `id-token: write` or does not use the protected `pypi` environment.
- The workflow can publish from a branch or unapproved ref instead of the approved tag.
- GitHub environment approval is missing, bypassed unexpectedly, or changed without a separate repository-settings approval.
- CI, CodeQL, Dependabot, secret scanning, local release-check, `twine check`, or strict artifact scan fails.
- Artifacts, docs, workflow logs, Issues, PRs, or release text contain raw personal data, secrets, private local paths, vault files, consent files, audit files, generated databases, or private support details.
- The requested action also includes repository setting changes, branch deletion, SNS/blog announcement, Claude Desktop app UI operation, API-billed validation, or manual token fallback without separate explicit emergency approval.

### Rollback

Trusted Publishing upload rollback cannot rely on deleting an already published package version.

Prepared rollback actions:

- stop announcements and external promotion;
- open a corrective Issue and PR;
- publish a patch release through the approved lane if the package is wrong but not unsafe;
- yank the PyPI release only if the package is unsafe and yanking is separately approved;
- correct GitHub release notes if the release text is wrong;
- disable or revert the publish workflow through PR if workflow behavior is wrong;
- remove or correct the PyPI Trusted Publisher entry only through a separate PyPI account-settings approval;
- keep a short post-incident note without raw personal data, secrets, private paths, or private support details.

## v0.1.11 Raw-Like Task/Purpose Redaction Patch Candidate Dry-Run

Status date: 2026-07-04.

Tracking Issue: #203.

This section records the package dry-run and later approved publish status for the `v0.1.11` raw-like task and purpose redaction patch. The original dry-run did not create a tag, GitHub release, package publish, announcement, repository setting change, branch deletion, Trusted Publishing publish run, PyPI token change/deletion, Claude Desktop app UI operation, or API-billed validation. The later tag, GitHub prerelease publish, and Trusted Publishing OIDC publish were handled through separate approval lanes.

Candidate scope:

- bump package version from `0.1.10` to `0.1.11`;
- move the post-`v0.1.10` Oracle Pro review follow-up into the `0.1.11` changelog entry;
- broaden raw-looking task and purpose redaction for common local/Japanese PII-like shapes, including Japanese name pairs, Japanese address markers, DOB-like dates, ungrouped phone numbers, local path prefixes, postal codes, and long numeric IDs;
- extend MCP consent and audit regression coverage so raw-looking purpose text stays out of agent-facing outputs and audit events;
- refresh README install examples so the package long description points to `agent-personal-vault==0.1.11`.

Local dry-run results:

- Fresh isolated artifact build source: temporary local source copy with `.git`, generated outputs, and local package metadata excluded.
- Temporary build/twine environment: temporary local virtual environment.
- Build command: `python -m build --outdir <temp-dist> <temp-src>`.
- `twine check <temp-dist>/*`: passed for sdist and wheel.
- Wheel metadata reports version `0.1.11`.
- PyPI `0.1.11` absence check returned HTTP 404 before the candidate preparation work.
- Project-URL metadata:
  - `Homepage, https://github.com/Driedsandwich/agent-personal-vault`
  - `Source, https://github.com/Driedsandwich/agent-personal-vault`
  - `Issues, https://github.com/Driedsandwich/agent-personal-vault/issues`
  - `Documentation, https://github.com/Driedsandwich/agent-personal-vault#readme`
- Strict forbidden-file entry and text scan found no bundled `vault.json`, `consents.json`, `audit.jsonl`, `.pypirc`, `.env`, private job profile file, username-specific path fragment, private project path fragment, or `/Users/` path in artifact entries/text.
- PII scan found no obvious private data patterns.

Artifact records:

| Artifact | Size | Entries | SHA-256 |
| --- | ---: | ---: | --- |
| `agent_personal_vault-0.1.11-py3-none-any.whl` | 38,210 bytes | 15 | `db5a3d131e34e80456c5d7d4b0cdec8638d5943d814940d1f3e941480a9b38f1` |
| `agent_personal_vault-0.1.11.tar.gz` | 51,365 bytes | 26 | `9cbe09154e3f39e936561a0cf521278f09ba5c498c5d3bdfb2de27c56db60d50` |

Stop conditions before any later publish lane:

- PyPI `0.1.11` exists before the separately approved package publish;
- any generated artifact includes local vault data, consent state, audit state, `.pypirc`, `.env`, private job profile data, username-specific paths, private project path fragments, or `/Users/` path entries/text;
- the package metadata does not report version `0.1.11`;
- `twine check`, local release-check, CI, CodeQL, Dependabot, or secret scanning fails;
- the requested action also includes release creation, tag creation, package publish, announcement, repository setting change, branch deletion, Trusted Publishing publish run, PyPI token change/deletion, Claude Desktop app UI operation, or API-billed validation without separate explicit approval.

Current post-publish state:

- PyPI latest is `0.1.11`.
- PyPI `0.1.11` is published.
- GitHub release `v0.1.11` is published as a prerelease and points to `3b9207b5b4cb7446342ea3a2b12e1a3249be353b`.
- Trusted Publishing OIDC publish has completed successfully for `v0.1.11`.
- The `publish-package` run for `v0.1.11` completed successfully and produced attestation files for the wheel and sdist.

Uploaded PyPI artifacts from the approved Trusted Publishing OIDC run:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `agent_personal_vault-0.1.11-py3-none-any.whl` | 38,210 bytes | `1e2748d1c385f726cb5924246f355ebe63ec1b1fbee790959c460f298afad0d2` |
| `agent_personal_vault-0.1.11.tar.gz` | 51,130 bytes | `6dfa15741816166bcee0b3dc1df874030bd3d132bbf7c9a0f91bdb97f0692e7c` |

## v0.1.10 Synced Store Path Warning Patch Candidate Dry-Run

Status date: 2026-07-04.

This section records the package dry-run for the `v0.1.10` synced or cloud-backed store path warning patch candidate. It does not create a tag, GitHub release, package publish, announcement, repository setting change, branch deletion, Trusted Publishing publish run, PyPI token change/deletion, Claude Desktop app UI operation, or API-billed validation. Those actions remain separate approval lanes.

Candidate scope:

- bump package version from `0.1.9` to `0.1.10`;
- move the post-`v0.1.9` synced-store warning change into the `0.1.10` changelog entry;
- keep current public-alpha safety boundaries unchanged;
- include CLI `init`, CLI `check`, CLI `set`, and GUI warnings when the vault store path appears to be under a known synced or cloud-backed folder;
- keep warning text advisory and avoid echoing the full local store path in CLI/GUI warning output;
- refresh README install examples so the package long description points to `agent-personal-vault==0.1.10`.

Local dry-run results:

- Isolated build environment: temporary local virtual environment.
- Build command: `python -m build --outdir <temp-dist> .`.
- `twine check <temp-dist>/*`: passed for sdist and wheel.
- Wheel metadata reports version `0.1.10`.
- PyPI `0.1.10` absence check returned HTTP 404.
- Project-URL metadata:
  - `Homepage, https://github.com/Driedsandwich/agent-personal-vault`
  - `Source, https://github.com/Driedsandwich/agent-personal-vault`
  - `Issues, https://github.com/Driedsandwich/agent-personal-vault/issues`
  - `Documentation, https://github.com/Driedsandwich/agent-personal-vault#readme`
- Strict forbidden-file entry scan found no bundled `vault.json`, `consents.json`, `audit.jsonl`, `.pypirc`, `.env`, private job profile file, username-specific path fragment, or `/Users/` path in artifact entries.

Artifact records:

| Artifact | Size | Entries | SHA-256 |
| --- | ---: | ---: | --- |
| `agent_personal_vault-0.1.10-py3-none-any.whl` | 37,110 bytes | 15 | `8fc46acbeadedc796e186d8d43914f87bad9862baed46793caaaa04e5bbec263` |
| `agent_personal_vault-0.1.10.tar.gz` | 50,102 bytes | 26 | `db0e199e3fc1568574d8de7e47b07dbe57e29755982504161d6af2e765bd1a6d` |

Stop conditions before any later publish lane:

- PyPI `0.1.10` exists before the separately approved package publish;
- any generated artifact includes local vault data, consent state, audit state, `.pypirc`, `.env`, private job profile data, username-specific paths, or `/Users/` path entries;
- the package metadata does not report version `0.1.10`;
- `twine check`, local release-check, CI, CodeQL, Dependabot, or secret scanning fails;
- the requested action also includes release creation, tag creation, package publish, announcement, repository setting change, branch deletion, Trusted Publishing publish run, PyPI token change/deletion, Claude Desktop app UI operation, or API-billed validation without separate explicit approval.

## v0.1.9 Consent And Local Trust Boundary Patch Candidate Dry-Run

Status date: 2026-07-04.

This section records the package dry-run and later approved publish status for the `v0.1.9` consent and local-trust boundary patch. The original dry-run did not create a tag, GitHub release, package publish, announcement, repository setting change, branch deletion, Trusted Publishing publish run, PyPI token change/deletion, Claude Desktop app UI operation, or API-billed validation. The later tag, GitHub prerelease publish, and Trusted Publishing OIDC publish were handled through separate approval lanes.

Candidate scope:

- bump package version from `0.1.8` to `0.1.9`;
- move post-`v0.1.8` safety changes into the `0.1.9` changelog entry;
- include invalid consent expiry hardening that returns sanitized consent errors without raw values, private store paths, full consent tokens, or Python tracebacks;
- include MCP consent-token boundary coverage so token-looking MCP inputs are not treated as authentication or authorization and are not echoed;
- clarify the MCP local process/client trust boundary and the absence of built-in MCP authentication;
- document plaintext JSON backup, sync, snapshot, manual-copy, and terminal-history residual risks;
- clarify that audit logs are raw-free metadata but not immutable, signed, append-only, or tamper-evident forensic logs;
- include cross-process one-time consent consume regression coverage;
- refresh README install examples so the package long description points to `agent-personal-vault==0.1.9`.

Local dry-run checks:

- Fresh isolated artifact build source: temporary worktree copy with generated outputs, `.git`, and local metadata excluded.
- `twine check dist/*`: passed.
- Project URL metadata is present in the wheel artifact:
  - `Homepage`: `https://github.com/Driedsandwich/agent-personal-vault`
  - `Source`: `https://github.com/Driedsandwich/agent-personal-vault`
  - `Issues`: `https://github.com/Driedsandwich/agent-personal-vault/issues`
  - `Documentation`: `https://github.com/Driedsandwich/agent-personal-vault#readme`
- Strict forbidden-file scan: passed for both artifacts.
- Wheel metadata reports version `0.1.9`.
- PyPI `0.1.9` absence check returned HTTP 404.

Current post-publish state:

- PyPI latest is `0.1.9`.
- PyPI `0.1.9` is published.
- GitHub release `v0.1.9` is published as a prerelease and points to `88f16fb5b7afb367655208e842e305f858d991fe`.
- Trusted Publishing OIDC publish has completed successfully for `v0.1.9`.
- The `publish-package` Actions run generated DSSE/in-toto attestations for the wheel and sdist.
- GitHub Actions run: `28694525143`.

Artifact evidence:

| Artifact | Size | Entries | SHA-256 |
| --- | ---: | ---: | --- |
| `agent_personal_vault-0.1.9-py3-none-any.whl` | 36,080 bytes | 15 | `2c0c899056cd691fdd17874ea59fdf9881949fa3f5346d250246a00a99f17d04` |
| `agent_personal_vault-0.1.9.tar.gz` | 48,465 bytes | 26 | `b2e6cfb1dcebc2b12b914f92bf1b40570282cc868a4545c9bde952a2258d1971` |

Uploaded PyPI artifacts from the approved Trusted Publishing OIDC run:

| file | size | SHA-256 |
| --- | ---: | --- |
| `agent_personal_vault-0.1.9-py3-none-any.whl` | 36,080 bytes | `f1600d961bebd06b2892c9c5b7cb345ce4697d73b37a569872fe31166a9ed144` |
| `agent_personal_vault-0.1.9.tar.gz` | 48,214 bytes | `fa1d9b4c6394b52ec395d272313c91fa61e238974051493acb052ff2675418ec` |

## v0.1.8 Boundary Hardening Patch Candidate Dry-Run

Status date: 2026-07-04.

This section records the package dry-run and later approved publish status for the `v0.1.8` boundary-hardening patch. The original dry-run did not create a tag, GitHub release, package publish, announcement, repository setting change, branch deletion, Trusted Publishing publish run, PyPI token change/deletion, Claude Desktop app UI operation, or API-billed validation. The later tag, GitHub prerelease publish, and Trusted Publishing OIDC publish were handled through separate approval lanes.

Candidate scope:

- bump package version from `0.1.7` to `0.1.8`;
- move post-`v0.1.7` safety changes into the `0.1.8` changelog entry;
- include raw-looking task redaction for CLI `context --task` and MCP `apv.context` planning hints;
- include CLI negative-path hardening so expected local errors do not emit Python tracebacks, raw values, or local store paths;
- include private-mode temporary file creation before atomic vault and consent state replacement;
- refresh README install examples so the package long description points to `agent-personal-vault==0.1.8`.

Current post-publish state:

- PyPI latest is `0.1.8`.
- PyPI `0.1.8` is published.
- GitHub release `v0.1.8` is published as a prerelease and points to `bb0756ab7afdebe6f09aa827963022ea2872ad45`.
- Trusted Publishing OIDC publish has completed successfully for `v0.1.8`.
- The `publish-package` Actions run generated DSSE/in-toto attestations for the wheel and sdist.

Local dry-run checks:

- Fresh isolated artifact build source: temporary worktree copy with generated outputs, `.git`, and local metadata excluded.
- `twine check dist/*`: passed.
- Project URL metadata is present in the wheel artifact:
  - `Homepage`: `https://github.com/Driedsandwich/agent-personal-vault`
  - `Source`: `https://github.com/Driedsandwich/agent-personal-vault`
  - `Issues`: `https://github.com/Driedsandwich/agent-personal-vault/issues`
  - `Documentation`: `https://github.com/Driedsandwich/agent-personal-vault#readme`
- Strict forbidden-file scan: passed for both artifacts.
- Wheel metadata reports version `0.1.8`.

Artifact evidence:

| Artifact | Size | Entries | SHA-256 |
| --- | ---: | ---: | --- |
| `agent_personal_vault-0.1.8-py3-none-any.whl` | 35,689 bytes | 15 | `4983ad573351fc3ef76c033f76f00105d0009102b565b48c75290225cd52603f` |
| `agent_personal_vault-0.1.8.tar.gz` | 46,997 bytes | 26 | `cc450bbccb96d95959ab553ecaf9a746d6f5e0b1bc6f5991d409150e70108051` |

Uploaded PyPI artifacts from the approved Trusted Publishing OIDC run:

| file | size | SHA-256 |
| --- | ---: | --- |
| `agent_personal_vault-0.1.8-py3-none-any.whl` | 35,689 bytes | `c1f6946f5db5a48e0ba589cc69a7017827b40fa40880f7a581e962049f0e2338` |
| `agent_personal_vault-0.1.8.tar.gz` | 46,770 bytes | `6ccba7aa2784c84257b894cf6312b6068df4465b51e0a9f6a043de04d7bc0e19` |

## v0.1.7 Purpose Redaction Patch Candidate Dry-Run

Status date: 2026-07-04.

This section records the package dry-run for the `v0.1.7` purpose-redaction patch candidate. It does not create a tag, GitHub release, package publish, announcement, repository setting change, branch deletion, Trusted Publishing publish run, PyPI token change/deletion, Claude Desktop app UI operation, or API-billed validation.

Candidate scope:

- bump package version from `0.1.6` to `0.1.7`;
- move post-`v0.1.6` safety and release-hygiene changes into the `0.1.7` changelog entry;
- include raw-looking `purpose` redaction for agent-facing consent and audit outputs;
- include MCP/audit raw-free regression coverage for raw-looking `purpose` text;
- include post-`v0.1.6` release/package status documentation synchronization;
- refresh README install examples so the package long description points to `agent-personal-vault==0.1.7`.

External state during this dry-run:

- PyPI latest is `0.1.7`.
- PyPI `0.1.7` is published.
- GitHub release `v0.1.7` is published as a prerelease.
- Trusted Publishing OIDC publish has completed successfully for `v0.1.7`.

Local dry-run checks:

- Fresh isolated artifact build source: temporary worktree copy with generated outputs, `.git`, and local metadata excluded.
- `twine check dist/*`: passed.
- Project URL metadata is present in the wheel artifact:
  - `Homepage`: `https://github.com/Driedsandwich/agent-personal-vault`
  - `Source`: `https://github.com/Driedsandwich/agent-personal-vault`
  - `Issues`: `https://github.com/Driedsandwich/agent-personal-vault/issues`
  - `Documentation`: `https://github.com/Driedsandwich/agent-personal-vault#readme`
- Strict forbidden-file scan: passed for both artifacts.
- Wheel metadata reports version `0.1.7`.

Artifact evidence:

| Artifact | Size | Entries | SHA-256 |
| --- | ---: | ---: | --- |
| `agent_personal_vault-0.1.7-py3-none-any.whl` | 35,331 bytes | 15 | `926b19c4efefeb579237b674b550245eb15e6b51c5e5b6d4f8813e93d07c5896` |
| `agent_personal_vault-0.1.7.tar.gz` | 45,963 bytes | 26 | `4b0b0002ad2ddfb8ea77253f07fae14421fbe68c0246f7df8ffcae9062e7332b` |

Uploaded artifact evidence:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `agent_personal_vault-0.1.7-py3-none-any.whl` | 35,331 bytes | `faf18a44091f85f28dffab341632fca25b99d80ede4e8eab6a7f8cba54a6dca3` |
| `agent_personal_vault-0.1.7.tar.gz` | 45,757 bytes | `68c025806242bb04d50b538c3fe174fe62f220fe687ddcf31024b9420e04cb6a` |

## v0.1.6 Safety Patch Candidate Dry-Run

Status date: 2026-07-04.

This section records the package dry-run for the `v0.1.6` safety patch candidate. It does not create a tag, GitHub release, package publish, announcement, repository setting change, branch deletion, Trusted Publishing publish run, Claude Desktop app UI operation, PyPI token change/deletion, or API-billed validation.

Candidate scope:

- bump package version from `0.1.5` to `0.1.6`;
- move post-`v0.1.5` safety and release-hygiene changes into the `0.1.6` changelog entry;
- include CLI `set` non-encrypted/local real-data warning and GUI manual-save alpha/non-encrypted/dummy-data warning;
- include README storage location, one-key `unset`, and disposable test-vault deletion lifecycle clarification;
- include prerelease graduation criteria tightening and Trusted Publishing/manual fallback status synchronization;
- refresh README install examples so the package long description points to `agent-personal-vault==0.1.6`.

External state during this dry-run:

- PyPI latest remains `0.1.5`.
- PyPI `0.1.6` is absent.
- GitHub release `v0.1.5` remains the latest GitHub prerelease.
- No `v0.1.6` tag, GitHub release, package publish, or Trusted Publishing publish has been run.

Local dry-run checks:

- Fresh isolated artifact build path: `/tmp/apv-v016-dry-run`.
- Temporary build/twine environment: `/tmp/apv-v016-build-venv`.
- `twine check dist/*`: passed.
- Project URL metadata is present in both artifacts:
  - `Homepage`: `https://github.com/Driedsandwich/agent-personal-vault`
  - `Source`: `https://github.com/Driedsandwich/agent-personal-vault`
  - `Issues`: `https://github.com/Driedsandwich/agent-personal-vault/issues`
  - `Documentation`: `https://github.com/Driedsandwich/agent-personal-vault#readme`
- Strict forbidden-file scan: passed for both artifacts.
- Wheel metadata contains `agent-personal-vault==0.1.6`, contains the storage/deletion lifecycle text, and does not contain the old `agent-personal-vault==0.1.5` install example.

Artifact evidence:

| Artifact | Size | Entries | SHA-256 |
| --- | ---: | ---: | --- |
| `agent_personal_vault-0.1.6-py3-none-any.whl` | 35,045 bytes | 15 | `7956c06d0570fb5eb17d1be2d9355f3af6d98eb55843a084ca3d66fcbf12143f` |
| `agent_personal_vault-0.1.6.tar.gz` | 45,569 bytes | 26 | `2e61571362c42b23c759883f282f227a9f751cf0181ba226b9a5a2028d57ac1a` |

## v0.1.5 Infrastructure Validation Patch Dry-Run

Status date: 2026-07-04.

This section records the package dry-run for the `v0.1.5` infrastructure-validation patch candidate. It does not create a tag, GitHub release, package publish, announcement, repository setting change, branch deletion, Trusted Publishing first publish run, Claude Desktop app UI operation, or API-billed validation.

Candidate scope:

- bump package version from `0.1.4` to `0.1.5`;
- move the post-`v0.1.4` release/package status refresh from `Unreleased` into the `0.1.5` changelog entry;
- include the first Trusted Publishing OIDC publish preflight planning updates;
- refresh README install examples so the package long description points to `agent-personal-vault==0.1.5`.

External state during the original dry-run:

- PyPI latest remains `0.1.4`.
- PyPI `0.1.5` is absent.
- GitHub release `v0.1.4` remains the latest GitHub prerelease.
- No Trusted Publishing OIDC publish has been run yet.

Post-publish status after the separately approved release lanes:

- GitHub release `v0.1.5` is published as a prerelease.
- PyPI latest is `0.1.5`.
- Trusted Publishing OIDC publish succeeded through the `publish-package` workflow.
- Manual token publishing is now an emergency fallback only.

Local dry-run checks:

- Fresh isolated artifact build path: `/tmp/apv-v015-dry-run`.
- `twine check dist/*`: passed.
- Project URL metadata is present in both artifacts:
  - `Homepage`: `https://github.com/Driedsandwich/agent-personal-vault`
  - `Source`: `https://github.com/Driedsandwich/agent-personal-vault`
  - `Issues`: `https://github.com/Driedsandwich/agent-personal-vault/issues`
  - `Documentation`: `https://github.com/Driedsandwich/agent-personal-vault#readme`
- Strict forbidden-file scan: passed for both artifacts.
- README install examples contain `agent-personal-vault==0.1.5` and no `agent-personal-vault==0.1.4` examples.

Artifact evidence:

| Artifact | Size | Entries | SHA-256 |
| --- | ---: | ---: | --- |
| `agent_personal_vault-0.1.5-py3-none-any.whl` | 34,723 bytes | 15 | `59ada157b83e7c93d34687760bc76672c8a76855ae79c48b8dbb91a3cf789bc9` |
| `agent_personal_vault-0.1.5.tar.gz` | 44,831 bytes | 22 | `035346aae2064a17ff1528e1ab57ee032d4adf07ff029df5ba60ec02a4ee16d4` |

Uploaded artifact evidence:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `agent_personal_vault-0.1.5-py3-none-any.whl` | 34,723 bytes | `b8b7709a6ca17ca5413a6e7228e963b5b3a16e8d2b8fbd95fc134eb8c06a6633` |
| `agent_personal_vault-0.1.5.tar.gz` | 44,611 bytes | `990259a0d259355e4b88236170a7a843483e10151ecbea2199376b0d3a96884c` |

Completed approval gates:

1. The `v0.1.5` preparation PR was merged after release-check and CI passed.
2. Tag `v0.1.5` was created for the approved commit.
3. GitHub prerelease `v0.1.5` was published.
4. The first OIDC workflow dispatch for tag `v0.1.5` completed successfully.

Remaining approval gate:

1. Separately approve any public announcement.

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

- the first publish attempt through that workflow.

The GitHub `pypi` environment already exists. Changing its reviewers, admin bypass behavior, self-review setting, branch policy, or secrets remains a separate repository-settings approval.
The PyPI Trusted Publisher already exists according to the PyPI management UI. Changing or deleting it remains a separate PyPI account approval.

Before the first OIDC publish dry-run, confirm:

- workflow identity exactly matches the PyPI publisher settings;
- `id-token: write` is granted only to the publishing job;
- the publish job uses the protected `pypi` environment;
- the workflow dispatch input tag resolves to `refs/tags/<tag>`, not a branch;
- artifacts are built from the approved tag and downloaded into the publish job;
- manual token fallback remains available only for separately approved emergency maintenance and is not the normal publish path after the `v0.1.5` OIDC validation.

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
- `v0.1.4` itself used the manual token fallback lane. Trusted Publishing setup was handled later and was validated by the separately approved `v0.1.5` OIDC publish.

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

Trusted Publishing note:

- `v0.1.4` was published through the manual token fallback lane.
- `v0.1.5` was published through the Trusted Publishing OIDC lane.
- A future OIDC publish must not reuse old artifact hashes as authorization.
- Future Trusted Publishing runs need fresh artifacts, the existing GitHub `pypi` environment to be reviewed as still correct, matching PyPI publisher settings, and a separate publish approval.
