# Announcement Approval Packet

日本語タイトル: 告知文案の最終承認パケット

status: draft
classification: SAFE_CANDIDATE
last_updated: 2026-07-03

## Purpose

This packet prepares a future announcement review for Agent Personal Vault.

It does not authorize SNS, blog, newsletter, community, or other public announcement. It also does not authorize repository setting changes, branch deletion, next-version release/tag/package publish, Trusted Publishing activation, Claude Desktop app UI operation, or API-billed validation.

Before posting anywhere, create a channel-specific approval request with the exact channel, account, text, timing, and target URL.

## Non-Removable Disclaimer

Every channel-specific announcement must keep the following points visible in the final text. Do not remove them to fit a short channel format.

- Agent Personal Vault is an alpha local utility.
- It is not encrypted by default.
- It is not a compliance, enterprise-security, password-manager, or secret-manager replacement.
- Public issues, comments, examples, and screenshots must use dummy data only.
- The primary link must be the GitHub README:

```text
https://github.com/Driedsandwich/agent-personal-vault
```

- Do not quote a pinned `pip install agent-personal-vault==...` command in generic announcement text.

If these points do not fit in a channel's short format, do not post there until a channel-specific approval packet is prepared.

## Current Routing Decision

Use the GitHub README as the primary link:

```text
https://github.com/Driedsandwich/agent-personal-vault
```

Use the GitHub README as the primary announcement link. PyPI latest is `0.1.3` and Issue #108 has been closed after the PyPI long description was refreshed, but generic announcement text should still avoid quoting a pinned `pip install agent-personal-vault==...` command. If a channel requires install instructions, link to the current README instead of copying a version-pinned command into the post.

## English Short Draft

```text
I published Agent Personal Vault, an early alpha local utility for AI-agent workflows that need repeated personal-data fields.

It is designed around raw-free schema/status/context first, explicit one-key retrieval only when needed, and a human stop before external submission, upload, registration, application, or publication.

Important limitation: it is not encrypted by default and is not a compliance, enterprise-security, password-manager, or secret-manager replacement. Please use dummy data in public issues.

README:
https://github.com/Driedsandwich/agent-personal-vault
```

## Japanese Short Draft

```text
Agent Personal Vaultを公開しました。AIエージェント作業で繰り返し必要になる個人情報フィールドを、ローカルで扱いやすくするalpha版ユーティリティです。

raw値を見せずにschema/status/contextを先に確認し、必要なときだけ1 key単位で明示的に取得し、外部送信・登録・応募・公開などの前には人間確認で止める設計です。

重要な制限として、既定では暗号化されません。法令対応、企業向けセキュリティ、password manager、secret managerの代替ではありません。public issueでは必ずdummy dataを使ってください。

README:
https://github.com/Driedsandwich/agent-personal-vault
```

## Safe Wording Check

Checked against `docs/LAUNCH_MESSAGING.md`.

Allowed framing present:

- alpha local utility
- AI-agent workflows
- raw-free metadata/context first
- explicit one-key retrieval only when needed
- human stop before external actions
- not encrypted by default
- not a compliance, enterprise-security, password-manager, or secret-manager replacement
- dummy data in public issues
- GitHub README as the primary link
- no pinned `pip install` command in generic announcement text

Forbidden wording not used:

- secure vault
- encrypted by default
- privacy guaranteed
- compliance-ready
- enterprise-ready
- production-ready
- safe for all personal data
- password-manager replacement
- secret-manager replacement
- consent-system replacement
- fully automated personal-data access
- world-first or first-of-kind claims
- supports every MCP client
- Claude Desktop live UX fully validated

## PyPI Routing Handling

Issue #108 is closed. It previously tracked that the PyPI project description could lag the README install examples after the `v0.1.2` cleanup. The `v0.1.3` PyPI publish refreshed the long description.

Announcement handling:

- Link to the GitHub README instead of the PyPI project page.
- Do not include a pinned `pip install` command in generic announcement copy.
- If a channel requires installation instructions, use the README link and ask readers to follow the current README.
- If a channel preview or auto-card emphasizes the PyPI project page or a pinned install command, review the preview before posting and stop if it shows stale install guidance.
- Do not create a new patch release solely from this packet. Version bump, tag, GitHub release, and PyPI publish remain separate approval lanes.

## Post-Announcement Monitoring

For the first 24 hours and the first week after any approved announcement, check:

- GitHub Issues and PRs
- GitHub Actions and CodeQL
- Dependabot, vulnerability, and secret-scanning alerts
- Star, Fork, and Watch counts
- replies, reposts, comments, quotes, or external mentions on the posted channel
- support-load signals, especially repeated confusion around consent, raw retrieval, MCP setup, install commands, or PyPI-vs-README instructions
- any public post that includes raw personal data, screenshots with real values, local private paths, vault files, consent files, audit logs, tokens, or secrets

Pause further announcements if:

- the non-removable disclaimer is missing or weakened in the final channel text;
- two or more independent users report the same consent, raw retrieval, MCP setup, install, or safety-boundary confusion;
- any report suggests raw personal data, token, local private path, vault file, consent file, or audit file exposure;
- CodeQL, Dependabot, secret scanning, or release-check state becomes red;
- README or PyPI install instructions are found to be misleading;
- support volume cannot be handled without weakening safety boundaries.

## Withdrawal And Correction

If a public announcement is wrong, misleading, or unsafe:

1. Stop further announcements immediately.
2. Preserve the original text and URL for internal review without copying raw personal data into public Issues.
3. Edit the post if the channel supports editing and a narrow correction is enough.
4. Withdraw or delete the post if the issue is material and the channel supports it.
5. Publish a short correction on the same channel if readers may already have acted on incorrect text.
6. Open a GitHub Issue only for product-facing or docs-facing problems. Do not include raw personal data, tokens, local paths, screenshots with raw values, vault files, consent files, or audit logs.
7. If user safety, raw leakage, or consent bypass is involved, stop announcement work and use the security reporting path.

## Approval Text Template

Use this only after selecting the exact channel, account, timing, and final text:

```text
Approve publishing the reviewed Agent Personal Vault announcement text to <channel/account> at <time or timing>. Target URL: https://github.com/Driedsandwich/agent-personal-vault. The final text must keep the non-removable disclaimer: alpha local utility, not encrypted by default, not a compliance/enterprise-security/password-manager/secret-manager replacement, public issues use dummy data only, GitHub README link only, and no pinned pip install command. Do not create releases, tags, package publishes, repository setting changes, branch deletions, Trusted Publishing changes, Claude Desktop UI operations, API-billed validation, or additional announcements.
```

Approval for one channel does not authorize any other channel.
