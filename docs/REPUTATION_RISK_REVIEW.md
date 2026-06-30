# Reputation Risk Review

日本語タイトル: 炎上リスク検討

status: reviewed
classification: SAFE_CANDIDATE

## Summary

Agent Personal Vault has a meaningful reputation risk because it combines:

- AI agents
- personal data
- the word `vault`
- optional at-rest encryption that is off by default
- prior OSS projects in the same broad category

The project can still be published, but it should be positioned as an early alpha, local-only, minimal, auditable utility. Avoid security overclaims.

## Risk Register

| Level | Risk | Why It Could Escalate | Mitigation |
|---|---|---|---|
| High | Security overclaim | `vault`, `safe`, or `secure` language can imply encryption or strong protection | Say "local boundary", "raw-free metadata", and "optional encryption is off by default" prominently |
| High | AI agent personal-data anxiety | Users may assume the tool encourages agents to access sensitive data too freely | Lead with `context`/`schema` raw-free flow and final-action boundaries |
| High | Real-data leak during launch | A screenshot, sample, or commit could accidentally include real values | Keep release checks mandatory; no screenshots with real data; run PII scan before push |
| Medium | Prior-art criticism | Similar projects exist, especially `personal-vault` and Personal Context Protocol | Acknowledge prior art and avoid category-first novelty claims |
| Medium | "Toy security" criticism | Local JSON with file permissions may be criticized as insufficient for a vault | Frame as alpha/local utility; compare with encrypted alternatives for higher-risk use |
| Medium | Misuse by less technical users | Users may store data without understanding local malware/OS-user limitations | Add warnings and default to metadata commands in docs |
| Medium | Regulatory/privacy misunderstanding | People may assume GDPR/APPI compliance claims | Make no compliance claims |
| Low | Japan-specific schema criticism | Job-hunting schema may look narrow or culturally specific | Present it as first template, not product boundary |

## Messaging Guidance

Use:

```text
local-first
raw-free metadata
minimal field vault
alpha
not encrypted by default
for local AI/Codex workflows
human approval before external actions
```

Avoid:

```text
secure vault
privacy guaranteed
enterprise-grade
compliance-ready
encrypted
first of its kind
agent can safely access all your personal data
```

## Launch Guidance

Do not launch with:

- real screenshots
- personal anecdotes containing private facts
- claims of strong security
- comparisons that dismiss prior OSS
- "just let agents use your personal data" framing

Safer launch framing:

```text
I built a small local-first Python utility that lets AI coding agents inspect which personal profile fields exist without seeing the raw values, and retrieve only specific fields when a local task needs them. It is alpha, not encrypted by default, and stops before external actions.
```

## README/Docs Requirements

Before public release:

- README must mention optional at-rest encryption is off by default.
- README must acknowledge prior art.
- README must describe `context` and `schema` before raw `get`.
- SECURITY must state what this project does not protect against.
- PUBLICATION_GATE must include reputation-risk review.

## Decision

Publication risk is manageable if the project is framed as:

```text
small alpha local utility, not a complete secure personal-data platform
```

The riskiest path is publicizing it as:

```text
the safe way for AI agents to store and use your personal information
```
