# PyPI Trusted Publishing Plan

日本語タイトル: PyPI Trusted Publishing 導入検討

status: active-plan
classification: SAFE_CANDIDATE
last_updated: 2026-07-07

## Purpose

This document records the Trusted Publishing setup and operating boundary for the Agent Personal Vault package publish lane.

This is a planning and status document only. It does not authorize PyPI publisher configuration changes, GitHub repository setting changes, GitHub environment changes, workflow activation, package publishing, tag creation, release creation, branch deletion, announcement, Claude Desktop app UI operation, or API-billed validation.

## Recommendation

Use PyPI Trusted Publishing as the normal package publish path after successful OIDC publishes from `v0.1.5` through `v0.1.15`.

Reason:

- It removes long-lived PyPI API tokens from the normal publish path.
- It uses GitHub Actions OIDC and PyPI-minted short-lived publish credentials.
- It can be paired with a protected GitHub environment for human approval before upload.
- It adds operational complexity and repository/PyPI settings that must be approved separately.

Manual token publishing remains an emergency fallback only. It should not be the preferred recurring path now that the protected Trusted Publishing workflow has been validated.

## Current Repository State

- Latest GitHub prerelease: `v0.1.15`.
- Latest PyPI package: `0.1.15`.
- Package publishes through `v0.1.4` used the manual token fallback lane.
- `v0.1.5` through `v0.1.15` were published to PyPI through the Trusted Publishing OIDC lane.
- The repository currently has `test`, `Dependency Graph`, `CodeQL`, and manual `publish-package` workflows.
- `.github/workflows/pypi-publish.yml` is a manual `workflow_dispatch` workflow for the OIDC publish lane. It does not authorize a publish by itself.
- GitHub environment `pypi` exists. It requires reviewer `Driedsandwich`, has `prevent_self_review: false`, uses protected-branches-only deployment policy, stores no environment secrets or PyPI token, and currently has `can_admins_bypass: true`.
- PyPI Trusted Publisher setup is complete according to the PyPI project management UI confirmed by the project owner. The configured publisher is GitHub, repository `Driedsandwich/agent-personal-vault`, workflow `pypi-publish.yml`, environment `pypi`.
- The first OIDC workflow result confirms the PyPI Trusted Publisher identity through the `v0.1.5` publish, and the lane was reused successfully through `v0.1.15`.
- Package publish has already been performed manually for `v0.1.0`, `v0.1.1`, `v0.1.2`, `v0.1.3`, and `v0.1.4`.
- Trusted Publishing has been used successfully for `v0.1.5` through `v0.1.15`.
- First OIDC publish preflight planning and follow-up evidence are tracked in Issue #142, Issue #146, and `docs/RELEASE_PACKAGE_DRY_RUN_PLAN.md`. Post-`v0.1.6` through post-`v0.1.15` status synchronization is tracked in Issues #161, #167, #173, #191, #199, #205, #217, #225, #231, and #239.
- Future publish actions remain separately approval-gated.

## PyPI Publisher Settings

For the existing PyPI project `agent-personal-vault`, the PyPI trusted publisher has been configured after separate explicit approval. Changing or deleting it remains a separate PyPI account-settings approval.

Configured settings:

- Owner: `Driedsandwich`
- Repository name: `agent-personal-vault`
- Workflow name: `pypi-publish.yml`
- Environment name: `pypi`

The PyPI project setting must match the GitHub Actions workflow identity exactly. If the workflow filename or environment name changes, the PyPI publisher configuration must be reviewed again.

PyPI-side setup is a separate external account action. Before changing it, confirm:

- the logged-in PyPI account owns or administers `agent-personal-vault`;
- the publisher form is for the existing PyPI project, not a new project;
- owner, repository, workflow name, and environment name match the workflow candidate exactly;
- no broad API token or account-wide credential is added as a workaround;
- a rollback path is known: remove the Trusted Publisher entry and return to manual project-scoped token fallback for the next approved publish.

## GitHub Actions Workflow

The workflow file exists and OIDC publishes succeeded for `v0.1.5` through `v0.1.15`. Do not run it for another real publish until the next version, tag, release, package availability, artifact, CI, security, and human approval gates are complete.

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
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5
        with:
          ref: ${{ inputs.tag }}
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
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
        uses: actions/upload-artifact@330a01c490aca151604b8cf639adc76d48f6c5d4 # v5
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
        uses: actions/download-artifact@018cc2cf5baa6db3ef3c5f8a56943fffe632ef53 # v6
        with:
          name: dist
          path: dist
      - name: Publish distributions to PyPI
        uses: pypa/gh-action-pypi-publish@cef221092ed1bacb1cc03d23a2d87d1d172e277b # release/v1
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
- Action references are pinned to full commit SHAs. Updating those actions is a normal dependency-maintenance PR, not an implicit publish approval.

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

- Review whether admin bypass should be disabled before a future publish as a separate repository-settings lane.
- If a trusted second reviewer is available, reconsider `prevent_self_review: true`.
- Do not change those settings without a separate repository-settings approval.

Rollback if the environment is wrong:

- remove or tighten the `pypi` environment protection rules;
- disable the package-publish workflow until the environment is corrected;
- do not bypass environment approval for the first OIDC publish.

## Manual Token Fallback

Manual token publish can remain available only as an emergency fallback after the successful Trusted Publishing OIDC publishes. It is not the normal package publish path.

Use Trusted Publishing OIDC for normal package publishes. Do not switch back to token-based upload for convenience, speed, local debugging, or routine maintenance.

Manual fallback requires a separate explicit approval that names:

- the target package version and tag;
- why the OIDC path cannot be used or must be avoided for that specific publish;
- the token scope and account ownership checks;
- the artifact rebuild, `twine check`, strict forbidden-file scan, and hash-recording steps;
- the rollback or corrective-release path.

Fallback rules:

- Use project-scoped PyPI tokens only.
- Do not store tokens in repository files, PR text, Issues, docs, shell history examples, terminal transcripts, screenshots, CI logs, or package artifacts.
- Prefer local one-time environment variables for the upload session; do not persist token values in checked-in config or GitHub environment secrets.
- Keep `.pypirc` and any local token material out of the repository and out of public support artifacts.
- Do not paste token values into Codex, GitHub, PyPI support messages, Issues, PRs, release notes, or announcement drafts.
- Rebuild artifacts from the approved tag immediately before upload.
- Run `twine check`, strict forbidden-file scan, and hash recording before upload.
- Stop if there is any uncertainty about token scope, account ownership, artifact contents, or PyPI project ownership.
- After an emergency fallback upload, immediately open a follow-up Issue to record the reason, public-safe outcome, and whether the OIDC path needs repair. Do not include token values, private paths, local shell history, or private support details.

## OIDC Publish Stop Conditions

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

The first OIDC publish was completed for `v0.1.5`, and the same lane was reused successfully through `v0.1.15`. Future OIDC publishes should remain separate release lanes for approved versions, not background migration steps.

Required preflight before any future OIDC publish:

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

Trusted Publishing is the validated normal publish lane for Agent Personal Vault, with manual token publishing retained only as an emergency fallback.

Next safe steps, if approved later:

1. Use Trusted Publishing for future approved package publishes by default.
2. Keep manual project-scoped token publishing as a documented emergency fallback only.
3. Consider admin-bypass hardening as a separate repository-settings lane.
