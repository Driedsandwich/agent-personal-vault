# Local Git Preparation

日本語タイトル: ローカルGit準備手順

status: approval-required
classification: SAFE_CANDIDATE

## Boundary

This project is not initialized as a Git repository yet.

The following are separate approval steps:

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
