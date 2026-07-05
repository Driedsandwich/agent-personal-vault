# Local Git Preparation

日本語タイトル: ローカルGit準備手順

status: historical-snapshot
classification: SAFE_CANDIDATE

## Boundary

This is a historical pre-initialization checklist. The project is now an initialized public Git repository with published public-alpha releases. Do not treat the commands below as current-state instructions unless this directory is recreated from scratch or moved outside Git.

The following were separate approval steps at the historical pre-initialization checkpoint:

1. `git init`
2. first local commit
3. remote repository creation
4. `git push`
5. release creation
6. package publish

Remote creation, push, release, publish, and public sharing must not happen without explicit approval.

## Preflight Before `git init`

Run:

```sh
python3 scripts/check_release.py
make clean
find . -maxdepth 4 -type f | sort
```

Confirm:

- no `vault.json`
- no `private/`
- no screenshots or photos
- no local absolute paths
- no real personal values
- no generated `__pycache__`

## Suggested Local Commands After Approval

```sh
git init
git add .
git status --short
git diff --cached --stat
```

Only after reviewing staged files:

```sh
git commit -m "Initial OSS candidate for Agent Personal Vault"
```

Stop before:

```sh
git remote add ...
git push ...
```
