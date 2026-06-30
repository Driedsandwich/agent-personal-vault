# Contributing

日本語タイトル: コントリビューション方針

## Principle

This project handles personal data. Contributions must preserve the local-first privacy boundary.

## Before Opening a Pull Request

Run:

```sh
make release-check
```

If `make` is unavailable, run `python3 scripts/check_release.py`.

Do not include:

- real `vault.json`
- screenshots containing real values
- local private paths
- backups
- real names, addresses, phone numbers, emails, school names, or IDs

## Examples

Use only dummy data from reserved/example domains and obviously fake institutions.

Good:

```text
taro@example.test
サンプル大学
2099年12月
```

Bad:

```text
real personal email addresses
actual school names from a user profile
actual addresses or phone numbers
```

## Security Changes

Changes that affect raw value output, GUI token handling, storage location, file permissions, or external transmission behavior need explicit security review.
