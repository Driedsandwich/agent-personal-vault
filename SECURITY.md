# Security Policy

日本語タイトル: セキュリティ方針

## Supported Versions

This project is an early alpha. Treat all versions as experimental until a stable release is published.

## Data Handling

Agent Personal Vault stores sensitive personal data locally. It is designed for local agent assistance, not for remote hosting.

Rules:

- Do not commit real `vault.json` files.
- Do not paste raw values into issues, pull requests, logs, screenshots, or public examples.
- Do not send raw values to external AI services or agents without explicit user approval.
- Do not include raw personal values in `--purpose`; purpose text is stored in the local audit log.
- Do not commit `audit.jsonl` or `consents.json`; they are raw-free by design but still describe private usage patterns.
- Treat form submission, registration, email sending, and upload as separate final actions that require human confirmation.

## Reporting Vulnerabilities

Open a private advisory or contact the maintainer privately if the issue involves a real user's personal data.

Public issues are acceptable only when they contain no personal data, credentials, screenshots with raw values, or local private paths.

If GitHub Issues are enabled, use the issue templates and keep the report raw-free. If a report would require real personal data, screenshots, vault files, tokens, or exploit output that exposes another person, do not post it publicly.

## Current Limitations

- At-rest encryption is optional and off by default. It requires the optional `cryptography` dependency and a user-managed passphrase.
- Do not store the encryption passphrase in logs, public issues, shell history, or repository files.
- Localhost GUI returns all fields to a browser tab with the valid token.
- CLI `get` and `env` intentionally print raw values only after a matching one-time consent token is supplied and raw-free audit metadata is written. Recommended agent flow is request, human approve or deny, then raw retrieval with the approved token.
- Audit logs record action, key, purpose, outcome, and whether raw data was returned. They do not intentionally record raw values, but user-provided purpose text must still be kept raw-free.
- Consent files record action, key, purpose, expiry, request resolution, and used status. They do not intentionally record raw values, but they are still local private metadata.
- This tool cannot protect data on an already compromised machine.
- This project does not claim GDPR, APPI, HIPAA, SOC 2, or enterprise compliance.
- Treat it as an alpha local utility, not as a complete secure personal-data platform.

## Public Communication

Use [docs/LAUNCH_MESSAGING.md](docs/LAUNCH_MESSAGING.md) before public announcements, README rewrites, social posts, or release notes. The default posture is conservative: alpha, local utility, optional at-rest encryption off by default, no compliance claim, no enterprise-security claim, and no request for users to post real personal data.
