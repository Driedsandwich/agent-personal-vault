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
- Plaintext vault files can be copied outside their file-permission boundary by backups, cloud sync, snapshots, archives, or manual copies. Keep real vaults out of shared/synced/public paths, and consider optional encryption when those copies cannot be controlled.
- Consent tokens and audit logs are workflow controls, not a hard security boundary against an agent or process that already has shell access as the same OS user.
- Audit metadata such as `human_operated` records the local approval path, for example CLI or GUI, and is not proof that a physical human rather than same-user automation performed the action.
- The MCP stdio server has no built-in authentication layer. It trusts the local process and MCP client connected to its stdin/stdout; do not expose it to untrusted agents, shared-user sessions, or unintended local processes.
- Localhost GUI returns all fields to a browser tab with the valid token.
- CLI `get` intentionally prints one raw value only after a matching one-time consent token is supplied and raw-free audit metadata is written. CLI `env` is a human-only bulk raw export escape hatch and is not part of the public-alpha agent or MCP path. Recommended agent flow is request, human approve or deny, then one-key raw retrieval with the approved token.
- Audit logs record action, key, purpose, outcome, and whether raw data was returned. They do not intentionally record raw values, but user-provided purpose text must still be kept raw-free. They are not immutable, append-only, signed, or tamper-evident forensic logs.
- Consent files record action, key, purpose, expiry, request resolution, and used status. They do not intentionally record raw values, but they are still local private metadata.
- On Windows, Unix-style `0600` permissions and `fcntl` locks do not apply as-is. A Windows locking fallback exists, but live Windows concurrency and permission behavior are not yet covered by this project's test suite.
- This tool cannot protect data on an already compromised machine.
- This project does not claim GDPR, APPI, HIPAA, SOC 2, or enterprise compliance.
- Treat it as an alpha local utility, not as a complete secure personal-data platform.

## Public Communication

Use [docs/LAUNCH_MESSAGING.md](docs/LAUNCH_MESSAGING.md) before public announcements, README rewrites, social posts, or release notes. The default posture is conservative: alpha, local utility, optional at-rest encryption off by default, no compliance claim, no enterprise-security claim, and no request for users to post real personal data.
