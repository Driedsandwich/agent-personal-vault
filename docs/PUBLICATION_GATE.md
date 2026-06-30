# Publication Gate

日本語タイトル: 公開前承認ゲート

status: draft
classification: SAFE_CANDIDATE

## Current Position

This directory is an OSS candidate extracted from a private local project. It must not be pushed, published, deployed, or shared externally until a human explicitly approves that final action.

## Scope

Project name:

```text
agent-personal-vault
```

Core purpose:

```text
Local-first personal data vault for AI agents. Job hunting profile is the first template, not the core product boundary.
```

## Must Pass Before Publication

- No real `vault.json` exists in this tree.
- No `private/`, backup, screenshot, local log, or machine-specific absolute path is included.
- `python3 -m unittest discover -s tests` passes.
- `python3 scripts/pii_scan.py .` passes.
- `python3 -m py_compile agent_personal_vault/*.py scripts/pii_scan.py` passes.
- `python3 scripts/check_release.py` passes.
- `make release-check` passes when `make` is available.
- `.github/workflows/test.yml` exists and runs `python scripts/check_release.py`.
- README explains data handling, final-action boundary, and no-at-rest-encryption limitation.
- README acknowledges prior art and avoids novelty overclaiming.
- `docs/PRIOR_ART_REVIEW.md` exists.
- `docs/PRODUCT_POSITIONING.md` exists and defines differentiation, MVP scope, and messaging rules.
- `docs/AGENT_PROTOCOL.md` explains the safe AI-agent flow and raw access boundary.
- SECURITY.md exists.
- CONTRIBUTING.md exists.
- LICENSE exists.
- `.gitignore` excludes real vault data, images, local secrets, and build artifacts.
- GitHub repository creation, `git push`, release creation, package publish, and public announcement remain stopped until separately approved.

## Current Verification Commands

Run from this directory:

```sh
python3 -m py_compile agent_personal_vault/*.py scripts/pii_scan.py
python3 -m unittest discover -s tests
python3 scripts/pii_scan.py .
python3 scripts/check_release.py
make release-check
```

Optional CLI smoke test:

```sh
tmpdir=$(mktemp -d)
python3 -m agent_personal_vault.cli --store "$tmpdir/vault.json" init
python3 -m agent_personal_vault.cli --store "$tmpdir/vault.json" check
ls -l "$tmpdir/vault.json"
```

Optional GUI smoke test:

```sh
tmpdir=$(mktemp -d)
python3 -m agent_personal_vault.gui --port 0 --store "$tmpdir/vault.json"
```

Confirm the printed URL binds to `127.0.0.1`, then stop with `Ctrl-C`.

## Release Decision

Recommended next step:

1. Review this directory as a standalone OSS candidate.
2. Decide whether to initialize a new Git repository here.
3. If approved, run local tests again.
4. Stop before remote creation or push and request explicit approval.

See [LOCAL_GIT_PREP.md](LOCAL_GIT_PREP.md) before any Git initialization.
