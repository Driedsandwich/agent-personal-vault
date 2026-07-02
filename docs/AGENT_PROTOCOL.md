# Agent Protocol

日本語タイトル: AIエージェント利用プロトコル

classification: SAFE_CANDIDATE
audience: ai-agent

## Purpose

This document defines how an AI agent should use Agent Personal Vault without leaking raw personal data.

The core product is a local-first personal data boundary for AI agents. `job_hunting_profile` is the first bundled schema.

## 5-Minute Agent Path

Use this order for a first public-alpha integration test:

1. Initialize a local store and fill only dummy or user-approved local values.
2. Call `agent-personal-vault context --task "<raw-free task>"`.
3. In MCP, call `apv.context` with the same raw-free task.
4. If a raw value is necessary, call `apv.request_consent` for one key, such as `FULL_NAME`.
5. Wait for a human-operated approval or denial in the GUI or a separate human-operated CLI session. The agent must not run approval commands for itself.
6. After approval, call CLI `get <KEY>` with the matching consent token shown by the human approval step. The MCP request id is not the consent token.
7. Check `audit summary` or `audit tail` and report only key names, never raw values.

Do not use MCP for raw retrieval. MCP exposes planning and consent-request tools only; CLI `get` is the explicit raw-returning step after human approval.

## Default Flow

1. Start with metadata only.

```sh
agent-personal-vault context
```

2. Inspect `required_missing`, `filled_keys`, and `derived_keys`.

3. Ask for or use only the minimum raw key needed for the current local task.

```sh
agent-personal-vault consent request --action get --key FULL_NAME --purpose "prepare local draft for user review"
agent-personal-vault get FULL_NAME --purpose "prepare local draft for user review" --consent-id "<printed-consent-id>"
```

The approval step is intentionally out of band. A human may approve in the GUI or in a separate human-operated CLI session. Agents must not run `consent approve`, `consent deny`, or `consent grant` for themselves.

4. Never include raw values in:

- final answers
- public files
- GitHub issues or pull requests
- remote AI prompts
- Subagent prompts
- logs
- telemetry
- search queries

5. Stop before final actions:

- external upload
- form submission
- account registration
- email sending
- public sharing
- repository push

## Safe Commands

These commands do not print raw personal values:

```sh
agent-personal-vault context
agent-personal-vault schema
agent-personal-vault check
agent-personal-vault list
```

`schema` does not read the vault file. `list` reports filled status and rough length without raw fragments. Use `context` as the safest default for agent planning when a vault exists, and `schema` when the agent only needs field definitions.

When a task is known, use `context --task "<raw-free task>"` to get conservative minimum-key planning hints. The hints list candidate keys and filled status only; they do not include stored raw values.

Consent tokens and audit logs are workflow controls. They are not a hard security boundary against an agent or process that already has shell access as the same OS user.

## Agent-Allowed Commands

In the public-alpha protocol, agents may use these commands for planning, raw-free inspection, or request creation:

```sh
agent-personal-vault context
agent-personal-vault schema
agent-personal-vault check
agent-personal-vault list
agent-personal-vault consent request --action get --key <KEY> --purpose "<raw-free purpose>"
agent-personal-vault audit summary
agent-personal-vault audit tail --limit 10
agent-personal-vault consent requests
agent-personal-vault consent list
```

Agents must not run approval commands for themselves. `consent approve`, `consent deny`, and direct `consent grant` are human-operated commands. Agents also must not use bulk raw export as a normal integration path.

## MCP Raw-Free Tools

The MCP stdio server exposes only raw-free tools:

```sh
apv-mcp --store /path/to/vault.json
```

Tools:

- `apv.schema`
- `apv.context`
- `apv.check`
- `apv.list_masked`
- `apv.request_consent`

The MCP server does not expose raw-value tools, stored-value write tools, external upload, form submission, email sending, or repository operations. `apv.context` accepts an optional raw-free `task` argument and may return conservative minimum-key planning hints. `apv.list_masked` does not return raw value fragments; it returns field status metadata only. `apv.request_consent` can create a raw-free one-key consent request for later human approval, but it still does not return the requested raw value.

## Raw Commands

After a human-operated approval, this command can print one raw personal value:

```sh
agent-personal-vault consent request --action get --key <KEY> --purpose "<raw-free purpose>"
agent-personal-vault get <KEY> --purpose "<raw-free purpose>" --consent-id "<printed-consent-id>"
```

Use it only after the agent has a concrete local purpose and the single key is necessary. The purpose is written to raw-free local consent and audit files, so it must not contain raw personal values. Consent requests can be approved or denied by a human in the GUI or a separate human-operated CLI session. Consent tokens are one-time tokens and must match action, key, and purpose.

`env` is an advanced/manual bulk raw export command. It is not part of the public-alpha agent protocol, MCP integration path, Quickstart, or release validation path. Prefer one-key `get <KEY>` retrieval.

These commands change stored values and also write raw-free audit events:

```sh
agent-personal-vault set <KEY> --purpose "<raw-free purpose>"
agent-personal-vault unset <KEY> --purpose "<raw-free purpose>"
```

GUI profile saves also write raw-free audit events with actor `gui`.

## Audit Commands

These commands inspect audit metadata and do not print raw personal values:

```sh
agent-personal-vault audit summary
agent-personal-vault audit tail --limit 10
agent-personal-vault consent requests
agent-personal-vault consent list
```

Audit events include action, key, consent id, raw-returned flag, purpose, and outcome. Consent requests and grants include action, key, purpose, expiry or resolution state, and used status. They do not include raw stored values.

## Subagents

Do not pass raw values to subagents by default. Parent agents should pass only:

- field labels
- missing field names
- schema names
- high-level task summaries
- redacted examples

## Logging

When reporting work, say which keys were used, not what values they held.

Good:

```text
Used FULL_NAME and EMAIL locally to prepare a draft.
Checked audit summary; raw access was limited to FULL_NAME and EMAIL.
```

Bad:

```text
Prepared the draft for <raw name> using <raw email>.
```
