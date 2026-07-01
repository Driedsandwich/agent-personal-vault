# Product Positioning

日本語タイトル: プロダクト位置づけとMVP方針

status: draft
classification: SAFE_CANDIDATE

## One Sentence

Agent Personal Vault is a small Python-first local vault that lets AI agents inspect personal-data metadata without raw values by default and retrieve only specific fields when a local task truly needs them.

## What This Is

- A local-first personal data boundary for AI agents.
- A structured profile vault, not a general document vault.
- A raw-free planning interface via `context`.
- A public schema inspection interface via `schema`.
- A conservative tool for Codex-like local agents that need clear final-action boundaries.

## What This Is Not

- Not a claim to invent the AI personal context vault category.
- Not a replacement for encrypted personal context vaults such as Personal Vault.
- Not a broad MCP protocol implementation; it exposes only read-only raw-free MCP tools.
- Not a credential broker like Infisical Agent Vault.
- Not a PII redaction middleware like Aegis Vault.
- Not a full agent security monitor like ClawVault.
- Not secure against malware, compromised OS users, or hostile local processes.

## Prior Art-Aware Differentiation

| Dimension | Prior-art-heavy direction | Agent Personal Vault direction |
|---|---|---|
| Runtime | MCP server, daemon, browser app | Python CLI first; GUI optional |
| Storage | encrypted context vaults, document stores | small structured field vault |
| Agent planning | often protocol/API dependent | `context` returns raw-free JSON |
| Schema discovery | product-specific APIs | `schema` does not read vault data |
| Security depth | tokens, audit logs, encryption, policy engines | audit, consent tokens, optional encryption, read-only raw-free MCP, and explicit limitations |
| Initial use case | shopping, documents, credentials, redaction | Japanese profile/job-hunting schema as first template |
| Audience | infra/security teams or agent platform builders | local AI/Codex users who want a simple auditable utility |

## MVP Boundary

MVP includes:

1. Local private JSON storage with `0600` file mode and `0700` parent directory mode.
2. Standard-library-only Python package.
3. `init`, `check`, `context`, `schema`, `list`, `set`, `get`, `unset`, and `env` CLI commands.
4. Localhost GUI with token URL for human editing.
5. Raw-free agent planning path.
6. Japan-oriented `job_hunting_profile` schema.
7. Explicit final-action boundary in docs.
8. PII/secret pre-publication scanner.
9. Release check script and CI workflow.
10. Raw-free audit log for `get`, `env`, `set`, and `unset`.
11. Required raw-free `--purpose` text for raw access and changes.
12. One-time consent tokens for raw-returning `get` and `env`.
13. Consent request queue with CLI and GUI approve/deny.
14. Optional encrypted store backend using `cryptography` when installed.
15. Raw-free MCP stdio server exposing planning/status tools and raw-free consent request only.

MVP does not include:

1. MCP raw-value tools.
2. Multi-user permissions.
3. Remote sync.
4. Browser extension.
5. Enterprise policy engine.
6. Automatic form submission.

## Feature Priority

### P0: Before First Public Release

- Keep no-real-data invariant.
- Keep `context` and `schema` raw-free.
- Keep release checks passing.
- Keep prior-art-aware README language.
- Complete private GitHub dry-run.
- Complete public release review.

### P1: After Public Visibility, Before Announcement

- Add more CLI docs and examples.
- Add a small architecture diagram or data-flow section.
- Add a `CHANGELOG.md`.
- Re-run prior-art review before public announcement.
- Add GUI audit viewer before any MCP raw-value tool is exposed.

### P2: After Initial Public Release

- Add additional schema templates.
- Add import/export with redaction checks.

### P3: After Audit, Consent, And Encryption Design

- Add MCP raw-value tools with consent tokens.
- Add GUI audit viewer.
- Add stricter permission manifests for agent integrations.

## Messaging Rules

Use:

```text
small
local-first
Python-first
raw-free context
specific-field retrieval
Codex/local-agent workflow
Japan-oriented first schema
```

Avoid:

```text
first
unique
complete security
encrypted vault
enterprise-grade
solves personal data for all agents
```

## Next Decision

The next bounded decision is whether to change the private GitHub repository visibility to public.

```text
Public visibility: approval required
Release creation: separate approval required
Package publish: separate approval required
Announcement: separate approval required
```

See [SECURITY_AND_AGENT_INTEGRATION_ROADMAP.md](SECURITY_AND_AGENT_INTEGRATION_ROADMAP.md) for the security and agent-integration roadmap.
