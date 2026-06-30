# Agent Protocol

日本語タイトル: AIエージェント利用プロトコル

classification: SAFE_CANDIDATE

## Purpose

This document defines how an AI agent should use Agent Personal Vault without leaking raw personal data.

The core product is not a job-hunting form helper. It is a local-first personal data boundary for AI agents. `job_hunting_profile` is the first schema template.

## Default Flow

1. Start with metadata only.

```sh
agent-personal-vault context
```

2. Inspect `required_missing`, `filled_keys`, and `derived_keys`.

3. Ask for or use only the minimum raw key needed for the current local task.

```sh
agent-personal-vault get FULL_NAME
```

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

`schema` does not read the vault file. `list` masks values but still reveals rough length. Use `context` as the safest default for agent planning when a vault exists, and `schema` when the agent only needs field definitions.

## Raw Commands

These commands can print raw personal values:

```sh
agent-personal-vault get <KEY>
agent-personal-vault env
```

Use them only after the agent has a concrete local purpose and the key is necessary.

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
```

Bad:

```text
Prepared the draft for <raw name> using <raw email>.
```
