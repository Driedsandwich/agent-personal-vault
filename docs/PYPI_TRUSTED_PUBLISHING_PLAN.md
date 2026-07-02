# PyPI Trusted Publishing Plan

日本語タイトル: PyPI Trusted Publishing 導入検討

status: draft-plan
classification: SAFE_CANDIDATE
last_updated: 2026-07-02

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

- The repository currently has a test workflow only.
- There is no active package-publishing GitHub Actions workflow.
- Package publish has already been performed manually for `v0.1.0`.
- Future publish actions remain separately approval-gated.

## PyPI Publisher Settings

For the existing PyPI project `agent-personal-vault`, the PyPI trusted publisher should be configured only after separate explicit approval.

Candidate settings:

- Owner: `Driedsandwich`
- Repository name: `agent-personal-vault`
- Workflow name: `pypi-publish.yml`
- Environment name: `pypi`

The PyPI project setting must match the future GitHub Actions workflow identity exactly. If the workflow filename or environment name changes, the PyPI publisher configuration must be reviewed again.

## GitHub Actions Workflow Candidate

Do not add this workflow until the repository setting and PyPI publisher lanes are separately approved.

Candidate workflow shape:

```yaml
name: publish-package

on:
  workflow_dispatch:
    inputs:
      tag:
        description: "Tag to publish, for example v0.1.1"
        required: true
        type: string

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          ref: ${{ inputs.tag }}
      - uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - name: Build distributions
        run: |
          python -m pip install --upgrade pip build twine
          python -m build
          twine check dist/*
      - name: Upload distributions for approval
        uses: actions/upload-artifact@v5
        with:
          name: dist
          path: dist/*

  publish:
    needs: build
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
- The workflow should publish from an approved tag, not from arbitrary branch state.
- The build job uploads artifacts for the protected publish job to consume.
- A future implementation PR should pin action versions or record the accepted tag policy before activation.

## GitHub Environment Protection

Candidate environment: `pypi`.

Recommended protection before any active publish workflow:

- require at least one human reviewer;
- restrict who can approve deployments to trusted maintainers;
- keep deployment branch/tag policy narrow;
- require the release/tag approval packet to be checked before approving the environment;
- do not store PyPI API tokens in the environment unless using the manual fallback lane.

Creating or changing this environment is a repository setting change and requires separate explicit approval.

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

## Decision

Trusted Publishing is suitable for Agent Personal Vault, but only as a future explicitly approved publish-lane hardening step.

Next safe step, if approved later:

1. Create a dedicated Issue for the inactive workflow implementation.
2. Add the workflow only if it cannot publish without a separately configured PyPI publisher and protected environment.
3. Separately approve PyPI publisher configuration.
4. Separately approve GitHub environment protection.
5. Separately approve the first OIDC publish attempt.
