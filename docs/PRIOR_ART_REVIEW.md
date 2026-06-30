# Prior Art Review

日本語タイトル: 先行OSS調査

status: reviewed
classification: SAFE_CANDIDATE
updated: 2026-07-01

## Conclusion

There are direct and adjacent prior OSS projects.

The closest direct prior art is:

- `lovincyrus/personal-vault`
- `lovincyrus/personal-context-protocol`

This means Agent Personal Vault should not be positioned as a novel category by itself. A safer positioning is:

```text
A small Python-first, local-only, raw-free-context-first personal data vault for AI agents, with Japan-oriented profile templates as the initial schema.
```

## Direct Prior Art

### Personal Vault

Repository:

```text
https://github.com/lovincyrus/personal-vault
```

Observed positioning:

- encrypted personal context vault
- AI agents can query personal context
- MCP server
- metadata listing without values
- decrypted field access
- audit log
- service tokens
- browser UI
- shopping demo
- MIT license

Impact:

This is highly overlapping. Agent Personal Vault should differentiate by being simpler, Python-first, no-server-required for CLI use, and conservative by default with `context` and `schema` commands that do not expose raw values.

Source note:

- GitHub search result described it as an encrypted vault for personal context with a TypeScript MCP server, `vault_list` metadata without values, and `vault_get` decrypted field access.

### Personal Context Protocol

Repository:

```text
https://github.com/lovincyrus/personal-context-protocol
```

Observed positioning:

- open protocol for AI agents to access personal context
- scoped access requests
- user approval
- expiring tokens
- access logging
- Go reference implementation via Personal Vault

Impact:

This is also highly overlapping at the protocol level. Agent Personal Vault should avoid claiming a unique protocol category unless it deliberately diverges. It may be better to reference this as prior art and focus on a minimal implementation and local agent workflow.

Source note:

- GitHub/specification search result describes it as a single encrypted user-controlled vault of personal context that agents request scoped access to.

## Adjacent Prior Art

### Enclave / slm-vault

Repository:

```text
https://github.com/zd87pl/slm-vault
```

Observed positioning:

- privacy-first AI personal data manager
- local trusted agent
- MCP integration
- encrypted document storage
- local RAG
- activity logging
- per-agent permissions
- desktop GUI

Impact:

Adjacent but broader. It focuses on documents, local RAG, encryption, and MCP-controlled processing. Agent Personal Vault is narrower and field/profile-oriented.

### Infisical Agent Vault

Repository:

```text
https://github.com/Infisical/agent-vault
```

Observed positioning:

- credential vault and proxy for AI agents
- MITM proxy architecture
- injects API credentials into outbound agent requests
- designed so agents do not directly access credentials

Impact:

Adjacent but credential-focused, not personal profile/context-focused. Useful comparison for security boundary language.

Source note:

- Infisical describes Agent Vault as an open-source credential proxy/vault and broker where secrets stay in the vault and are injected via a proxy rather than exposed directly to agents.

### Aegis Vault

Repository:

```text
https://github.com/cbuchele/aegis-vault
```

Observed positioning:

- middleware for LLM prompts
- detects, redacts, encrypts PII before sending to LLM APIs
- restores sensitive data in responses
- focused on LGPD/Brazilian identifiers

Impact:

Adjacent. It is a PII redaction/encryption middleware rather than a user-controlled profile/context vault.

### ClawVault

Repository:

```text
https://github.com/tophant-ai/ClawVault
```

Observed positioning:

- security vault for AI agent interactions
- monitors access to private data, credentials, files
- detects sensitive info, prompt injection, dangerous commands
- dashboard and policy controls

Impact:

Adjacent. It is broader security monitoring and policy enforcement, not primarily a structured personal profile vault.

Source note:

- GitHub search result positions ClawVault around preventing AI agents from leaking personal private data, accessing credentials/private files, and mishandling sensitive files.

### Other Adjacent Secret/Vault Projects

- `botiverse/agent-vault`: placeholder-style secret-aware file I/O for AI agents.
- `ewimsatt/agent-vault`: local encrypted credential manager for AI agents.
- HashiCorp Vault MCP servers: MCP interfaces for existing secret-management infrastructure.

These are relevant to naming and security language, but they are mostly credential/secret-management projects rather than structured user profile/context vaults.

## Recommended Positioning Change

Avoid:

```text
The open-source way for AI agents to manage personal data.
```

Prefer:

```text
A minimal Python local-first vault for AI agents to inspect personal-data metadata safely and retrieve only specific user-approved fields.
```

Potential differentiators:

- Python standard-library-only implementation
- no daemon required for CLI usage
- raw-free `context` as the default agent planning interface
- public `schema` command that does not read the vault
- Japan-oriented profile schema as a practical first template
- explicit final-action boundary for Codex-like coding agents
- small enough to audit and fork

## Product Implications

Before public release:

1. README should acknowledge adjacent prior art or at least avoid category-first novelty claims.
2. Do not name the project too close to `personal-vault`.
3. Consider whether to integrate with or reference Personal Context Protocol later.
4. Consider adding encryption before positioning as a secure vault.
5. Keep current positioning as an alpha, minimal, local-first utility.
