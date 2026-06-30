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
- Treat form submission, registration, email sending, and upload as separate final actions that require human confirmation.

## Reporting Vulnerabilities

Open a private advisory or contact the maintainer privately if the issue involves a real user's personal data.

Public issues are acceptable only when they contain no personal data, credentials, screenshots with raw values, or local private paths.

## Current Limitations

- No at-rest encryption yet.
- Localhost GUI returns all fields to a browser tab with the valid token.
- CLI `get` and `env` intentionally print raw values.
- This tool cannot protect data on an already compromised machine.
