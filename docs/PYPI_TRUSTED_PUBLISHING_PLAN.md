# PyPI Trusted Publishing Plan

日本語タイトル: PyPI Trusted Publishing 導入検討

status: draft-plan
classification: SAFE_CANDIDATE
last_updated: 2026-07-04

## Purpose

This document evaluates PyPI Trusted Publishing for a future Agent Personal Vault package publish lane.

This is a planning document only. It does not authorize PyPI publisher configuration, GitHub repository setting changes, GitHub environment changes, workflow activation, package publishing, tag creation, release creation, branch deletion, announcement, Claude Desktop app UI operation, or API-billed validation.

## Recommendation

Adopt PyPI Trusted Publishing before repeated package publishes, but not as an immediate background change.

Reason:

- It removes long-lived PyPI API tokens from the normal publish path.
- It uses GitHub Actions OIDC and PyPI-minted short-lived publish credentials.
- It can be paired with a protected GitHub environment for human approval before upload.
- It adds operational complexity and repository/PyPI settings that must be approved separately.

Manual token publishing can remain an emergency fallback, but it should not be the preferred recurring path once a protected Trusted Publishing workflow is reviewed.

## Current Repository State

- Latest GitHub prerelease: `v0.1.4`.
- Latest PyPI package: `0.1.4`.
- Package publishes through `v0.1.4` used the manual token fallback lane.
- The repository currently has `test`, `Dependency Graph`, `CodeQL`, and manual `publish-package` workflows.
- `.github/workflows/pypi-publish.yml` is a manual `workflow_dispatch` workflow for a future OIDC publish lane. It does not authorize a publish by itself.
- GitHub environment `pypi` exists. It requires reviewer `Driedsandwich`, has `prevent_self_review: false`, uses protected-branches-only deployment policy, stores no environment secrets or PyPI token, and currently has `can_admins_bypass: true`.
- PyPI Trusted Publisher setup is complete according to the PyPI project management UI confirmed by the project owner. The configured publisher is GitHub, repository `Driedsandwich/agent-personal-vault`, workflow `pypi-publish.yml`, environment `pypi`.
- PyPI public JSON does not expose Trusted Publisher configuration, so re-check the PyPI management UI or first OIDC workflow result before treating the lane as operational.
- Package publish has already been performed manually for `v0.1.0`, `v0.1.1`, `v0.1.2`, `v0.1.3`, and `v0.1.4`.
- No package publish has used Trusted Publishing yet.
- First OIDC publish preflight planning is tracked in Issue #142 and `docs/RELEASE_PACKAGE_DRY_RUN_PLAN.md`.
- Future publish actions remain separately approval-gated.

## PyPI Publisher Settings

For the existing PyPI project `agent-personal-vault`, the PyPI trusted publisher has been configured after separate explicit approval. Changing or deleting it remains a separate PyPI account-settings approval.

Configured settings:

- Owner: `Driedsandwich`
- Repository name: `agent-personal-vault`
- Workflow name: `pypi-publish.yml`
- Environment name: `pypi`

The PyPI project setting must match the future GitHub Actions workflow identity exactly. If the workflow filename or environment name changes, the PyPI publisher configuration must be reviewed again.

PyPI-side setup is a separate external account action. Before changing it, confirm:

- the logged-in PyPI account owns or administers `agent-personal-vault`;
- the publisher form is for the existing PyPI project, not a new project;
- owner, repository, workflow name, and environment name match the workflow candidate exactly;
- no broad API token or account-wide credential is added as a workaround;
- a rollback path is known: remove the Trusted Publisher entry and return to manual project-scoped token fallback for the next approved publish.

## GitHub Actions Workflow

The workflow file exists as the Lane 1 code preparation step. Do not run it for a real publish until GitHub environment setup, PyPI publisher setup, and first OIDC publish are separately approved.

Workflow shape:

```yaml
name: publish-package

on:
  workflow_dispatch:
    inputs:
      tag:
        description: "Approved tag to publish, for example v0.1.5"
        required: true
        type: string
      confirm_publish:
        description: "Type exactly: publish <tag>"
        required: true
        type: string

permissions:
  contents: read

jobs:
  build:
    if: startsWith(inputs.tag, 'v') && inputs.confirm_publish == format('publish {0}', inputs.tag)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          ref: ${{ inputs.tag }}
      - uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - name: Verify checkout is the approved tag
        run: |
          head_sha="$(git rev-parse HEAD)"
          tag_sha="$(git rev-parse "refs/tags/${APV_TAG}^{commit}")"
          test "$head_sha" = "$tag_sha"
      - name: Build distributions
        run: |
          python -m pip install --upgrade pip build twine
          python -m build
          twine check dist/*
      - name: Strict forbidden-file scan
        run: python <inline artifact scan>
      - name: Upload distributions for approval
        uses: actions/upload-artifact@v5
        with:
          name: dist
          path: dist/*

  publish:
    needs: build
    if: startsWith(inputs.tag, 'v') && inputs.confirm_publish == format('publish {0}', inputs.tag)
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/project/agent-personal-vault/
    permissions:
      contents: read
      id-token: write
    steps:
      - name: Download distributions
        uses: actions/download-artifact@v6
        with:
          name: dist
          path: dist
      - name: Publish distributions to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

Design notes:

- `id-token: write` belongs on the publishing job, not globally.
- The publishing job should use a protected environment named `pypi`.
- The workflow should be manual by default for alpha releases.
- The workflow verifies that the checkout matches `refs/tags/<tag>`, so a branch with a matching name is not enough.
- The workflow requires a confirmation input matching `publish <tag>` to reduce accidental dispatch risk.
- The workflow checks that the package version is not already present on PyPI before building.
- The build job uploads artifacts for the protected publish job to consume.
- The build job runs `twine check` and a strict artifact forbidden-file scan before upload.

Workflow addition is a repository code change, not a publish by itself. It still needs a dedicated Issue/PR because it introduces a path that can publish once the external settings exist.

Stop before merging the workflow PR if:

- the workflow can publish from an unreviewed branch or unapproved tag;
- `id-token: write` is granted globally instead of only on the publish job;
- the publish job omits the `pypi` environment;
- artifacts are built and published in the same privileged job;
- the workflow uses PyPI username/password/token secrets as the normal path;
- local `scripts/check_release.py`, PR CI, or CodeQL fails.

Rollback if the workflow is wrong:

- revert or amend the workflow PR before merge;
- if already merged but unused, open a rollback PR removing or disabling the workflow;
- if the workflow has been used to publish, stop announcements and prepare a corrective patch/yank decision through the package-publish rollback lane.

## GitHub Environment Protection

Candidate environment: `pypi`.

Recommended protection before any active publish workflow:

- require at least one human reviewer;
- restrict who can approve deployments to trusted maintainers;
- keep deployment branch/tag policy narrow;
- require the release/tag approval packet to be checked before approving the environment;
- do not store PyPI API tokens in the environment unless using the manual fallback lane.

Creating or changing this environment is a repository setting change and requires separate explicit approval.

GitHub environment setup is separate from the workflow PR.

Current approved setup:

- environment name: `pypi`;
- required reviewer: `Driedsandwich`;
- `prevent_self_review: false`;
- deployment branch policy: protected branches only;
- environment secrets: none;
- PyPI token: not stored;
- `can_admins_bypass: true`.

Optional later hardening:

- Review whether admin bypass should be disabled before the first OIDC publish.
- If a trusted second reviewer is available, reconsider `prevent_self_review: true`.
- Do not change those settings without a separate repository-settings approval.

Rollback if the environment is wrong:

- remove or tighten the `pypi` environment protection rules;
- disable the package-publish workflow until the environment is corrected;
- do not bypass environment approval for the first OIDC publish.

## Manual Token Fallback

Manual token publish can remain available for emergency or one-off maintenance, but it has higher secret-handling burden.

Fallback rules:

- Use project-scoped PyPI tokens only.
- Do not store tokens in repository files, PR text, Issues, docs, shell history examples, or logs.
- Prefer local one-time environment variables for the upload session.
- Rebuild artifacts from the approved tag immediately before upload.
- Run `twine check`, strict forbidden-file scan, and hash recording before upload.
- Stop if there is any uncertainty about token scope, account ownership, artifact contents, or PyPI project ownership.

## First OIDC Publish Stop Conditions

Stop before upload if any of these occur:

- PyPI publisher settings do not exactly match owner, repo, workflow, and environment.
- GitHub environment protection is absent, misconfigured, or bypassed.
- The workflow is triggered from a branch or commit that is not the approved tag.
- CI, CodeQL, Dependabot, secret scanning, or local release checks are failing.
- Artifacts contain vault, consent, audit, private config, database, image, backup, token, or local developer files.
- `twine check` fails.
- The package version is already present on PyPI.
- The release note, approval packet, or tag target does not match the publish target.
- Any real personal data, secrets, private paths, or private support details appear in workflow logs, artifacts, Issues, PRs, or release text.

First OIDC publish approval should be a separate release lane for a future version, not a background migration step.

Required preflight before the first OIDC publish:

- latest `main` is clean and matches `origin/main`;
- target tag, package version, CHANGELOG, GitHub release state, and PyPI availability all agree;
- the GitHub `pypi` environment is protected and pending human approval before publish;
- PyPI publisher settings exactly match owner `Driedsandwich`, repository `agent-personal-vault`, workflow `pypi-publish.yml`, and environment `pypi`;
- workflow run builds fresh artifacts from the approved tag;
- artifact filenames, sizes, entry counts, SHA-256 hashes, Project-URL metadata, and forbidden-file scan are recorded;
- no SNS/blog/community announcement is bundled into the publish approval.

Rollback after a bad OIDC publish:

- stop or cancel any announcement lane;
- open an Issue documenting the package impact without raw personal data or secrets;
- prepare a corrective patch release through normal Issue/PR/release lanes;
- yank the PyPI release only if the package is unsafe and yanking is separately approved;
- remove or disable the Trusted Publisher and workflow only if the failure came from the publishing path itself.

## Decision

Trusted Publishing is suitable for Agent Personal Vault, but only as a future explicitly approved publish-lane hardening step.

Next safe step, if approved later:

1. Separately approve the first OIDC publish attempt for a future version.
2. Keep manual project-scoped token publishing as a documented emergency fallback until the first OIDC publish succeeds.
3. Consider admin-bypass hardening as a separate repository-settings lane before the first OIDC publish.
