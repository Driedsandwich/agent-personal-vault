# Announcement Approval Packet

日本語タイトル: 告知文案の最終承認パケット

status: draft
classification: SAFE_CANDIDATE
last_updated: 2026-07-05

## Purpose

This packet prepares a future announcement review for Agent Personal Vault.

It does not authorize SNS, blog, newsletter, community, or other public announcement. It also does not authorize repository setting changes, branch deletion, next-version release/tag/package publish, Trusted Publishing changes or additional publish runs, Claude Desktop app UI operation, or API-billed validation.

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

Use the GitHub README as the primary announcement link. PyPI latest is `0.1.13`, the `v0.1.13` GitHub prerelease is published, and Trusted Publishing OIDC publish has succeeded for `v0.1.5`, `v0.1.6`, `v0.1.7`, `v0.1.8`, `v0.1.9`, `v0.1.10`, `v0.1.11`, `v0.1.12`, and `v0.1.13`. The PyPI long description reflects the current README install examples, but generic announcement text should still avoid quoting a pinned `pip install agent-personal-vault==...` command. If a channel requires install instructions, link to the current README instead of copying a version-pinned command into the post.

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

## Channel-Specific Final Draft Candidates

These drafts are final candidates for per-channel review. They do not authorize posting.

Before using any draft, create a separate approval request with the exact channel, account, final text, timing, target URL, and monitoring owner.

Shared target URL:

```text
https://github.com/Driedsandwich/agent-personal-vault
```

Shared non-removable safety notes:

- alpha local utility
- not encrypted by default
- not a compliance, enterprise-security, password-manager, or secret-manager replacement
- public issues, comments, examples, and screenshots must use dummy data only
- primary link is the GitHub README
- no pinned `pip install agent-personal-vault==...` command in generic announcement text
- human stop before external submission, upload, registration, application, or publication

If these notes do not fit a channel's format, do not post from that channel until a new channel-specific packet is reviewed.

### X/Twitter

Use a short thread so the safety notes are not removed for length. Do not compress this into a single post if that would remove the limitation or dummy-data notice.

English draft:

```text
Post 1/2
I published Agent Personal Vault, an alpha local utility for AI-agent workflows that need repeated personal-data fields.

It starts with raw-free context, supports explicit one-key retrieval, and keeps a human stop before external actions.

https://github.com/Driedsandwich/agent-personal-vault

Post 2/2
Safety boundary: not encrypted by default; not a compliance, enterprise-security, password-manager, or secret-manager replacement. Please use dummy data only in public issues, examples, and screenshots.
```

Japanese draft:

```text
投稿 1/2
Agent Personal Vaultを公開しました。AIエージェント作業で繰り返し必要になる個人情報フィールドをローカルで扱うalpha版ユーティリティです。

rawなしのcontextを先に使い、必要な時だけ1 key単位で取得し、外部送信前に人間確認で止めます。

https://github.com/Driedsandwich/agent-personal-vault

投稿 2/2
安全境界: 既定では暗号化されません。法令対応、企業向けセキュリティ、password/secret managerの代替ではありません。public issue、例、スクショはdummy dataのみでお願いします。
```

Link handling:

- Use the GitHub README URL only.
- Do not include a PyPI URL or pinned install command in the post.
- Review the generated link preview before posting; stop if it implies production readiness, broad security guarantees, or stale install guidance.

24-hour monitoring:

- replies, quote posts, repost comments, and bookmark/share-driven questions if visible
- repeated confusion around encryption, raw retrieval, MCP setup, install path, or whether real data can be posted publicly
- GitHub Issues/PRs opened from the post
- Star/Fork/Watch spikes accompanied by support questions
- any public screenshot or example containing real personal data, local private paths, tokens, vault files, consent files, or audit logs

Correction/withdrawal:

- If the text is merely imprecise and the channel supports edits, edit the post and add a short correction reply.
- If a required safety note is missing, delete or withdraw the thread if possible and repost only after a new approval.
- If readers may already have acted on unsafe wording, add a correction reply that points to the GitHub README and dummy-data-only issue policy.

### GitHub Discussions Or Community Post

Use this for GitHub Discussions, developer communities, or similar forums where a short paragraph plus bullets is acceptable.

English draft:

```text
I published Agent Personal Vault, an alpha local utility for AI-agent workflows that need repeated personal-data fields.

The project is designed around:

- raw-free schema/status/context first
- explicit one-key retrieval only when a raw value is needed
- a human stop before external submission, upload, registration, application, or publication

Important limitations:

- not encrypted by default
- not a compliance, enterprise-security, password-manager, or secret-manager replacement
- public issues, comments, examples, and screenshots must use dummy data only

README:
https://github.com/Driedsandwich/agent-personal-vault
```

Japanese draft:

```text
Agent Personal Vaultを公開しました。AIエージェント作業で繰り返し必要になる個人情報フィールドをローカルで扱うalpha版ユーティリティです。

設計上の中心は以下です。

- raw値なしのschema/status/contextを先に使う
- raw値が必要な場合だけ1 key単位で明示的に取得する
- 外部送信、アップロード、登録、応募、公開の前には人間確認で止める

重要な制限:

- 既定では暗号化されません
- 法令対応、企業向けセキュリティ、password manager、secret managerの代替ではありません
- public issue、コメント、例、スクリーンショットではdummy dataのみを使ってください

README:
https://github.com/Driedsandwich/agent-personal-vault
```

Link handling:

- Prefer the GitHub README URL.
- If the forum allows related links, `SECURITY.md` may be linked in a follow-up comment, but do not replace the README as the primary URL.
- Do not paste local paths, private support instructions, tokens, or unpublished operational details.

24-hour monitoring:

- comments, replies, reactions, and duplicate GitHub Issues/PRs
- requests to review real vault files, screenshots, logs, personal data, or local paths
- confusion around alpha status, encryption, compliance, password-manager/secret-manager boundaries, or public support expectations
- Actions, CodeQL, Dependabot/security alerts, and README/PyPI install consistency if the post drives new traffic

Correction/withdrawal:

- Edit the discussion post if the channel supports edits and the problem is narrow.
- Add a visible correction comment if replies already quote or depend on the incorrect wording.
- Lock or close the discussion only if moderation is needed to stop raw personal-data sharing or repeated unsafe requests.

### Personal Blog Or Longer Note

Use this when the channel allows more context while still keeping the announcement short.

English draft:

```text
I published Agent Personal Vault, an alpha local utility for AI-agent workflows that need repeated personal-data fields.

The project focuses on a narrow boundary: agents can inspect schema, status, and task-oriented context without receiving raw personal data. When a raw value is actually needed, the intended path is explicit one-key retrieval, with a human stop before external submission, upload, registration, application, or publication.

This is not a security product. It is not encrypted by default, and it is not a compliance, enterprise-security, password-manager, or secret-manager replacement. Public issues, examples, and screenshots should use dummy data only.

README:
https://github.com/Driedsandwich/agent-personal-vault
```

Japanese draft:

```text
Agent Personal Vaultを公開しました。AIエージェント作業で繰り返し必要になる個人情報フィールドを、ローカルで扱いやすくするalpha版ユーティリティです。

中心に置いている境界は狭いです。AIエージェントはraw個人情報を受け取らずにschema、status、用途別contextを確認できます。raw値が本当に必要な場合は、1 key単位で明示的に取得し、外部送信、アップロード、登録、応募、公開の前には人間確認で止める設計です。

これはセキュリティ製品ではありません。既定では暗号化されず、法令対応、企業向けセキュリティ、password manager、secret managerの代替でもありません。public issue、例、スクリーンショットでは必ずdummy dataを使ってください。

README:
https://github.com/Driedsandwich/agent-personal-vault
```

Link handling:

- Primary link: GitHub README.
- Optional secondary link after the main text: GitHub release `v0.1.13` if the post is explicitly about the current alpha release.
- Avoid PyPI-first routing unless the post is specifically about installation and the PyPI page has been rechecked immediately before publishing.

24-hour monitoring:

- comments, backlinks, referrers if available, and social reposts
- GitHub Issues/PRs created after the post
- install or onboarding confusion caused by the article
- any use of real personal data, screenshots, paths, tokens, vault files, consent files, or audit logs in public responses
- Actions, CodeQL, Dependabot/security alerts, and README/PyPI consistency

Correction/withdrawal:

- Prefer an inline correction note at the top or bottom when the issue is limited.
- If the article creates unsafe expectations around security, encryption, compliance, or automated data access, unpublish or withdraw until a corrected version is approved.
- If the article sends users to stale install guidance, update the article and add a visible correction note with the current README link.

## Per-Channel Approval Checklist

Before any channel-specific post, confirm:

- exact channel and account
- exact final text
- exact target URL
- intended timing
- link preview or rendered preview
- non-removable safety notes are present
- no pinned `pip install agent-personal-vault==...` command in generic announcement text
- no local private path, token, raw personal data, vault file, consent file, audit file, or unpublished operational detail
- 24-hour monitoring owner and check schedule
- edit, deletion, withdrawal, or correction procedure for that channel
- GitHub Issues/PRs, Actions, CodeQL, Dependabot/security alerts, README, PyPI description, and GitHub release state checked immediately before posting

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

Issue #108 is closed. It previously tracked that the PyPI project description could lag the README install examples after the `v0.1.2` cleanup. The `v0.1.3` PyPI publish refreshed the long description at that time.

Issue #132 is closed. It tracked the post-`v0.1.4` cleanup of stale release/package status text.

Issue #146 is closed. It tracked the post-`v0.1.5` status sync after the first Trusted Publishing OIDC publish.

Issue #149 tracked the announcement packet refresh after the `v0.1.5` GitHub prerelease and PyPI `0.1.5` package were published.

Issue #161 tracked the post-`v0.1.6` status sync after the `v0.1.6` GitHub prerelease and PyPI `0.1.6` package were published through the Trusted Publishing OIDC lane. Issue #167 tracked the post-`v0.1.7` status sync after the `v0.1.7` GitHub prerelease and PyPI `0.1.7` package were published through the Trusted Publishing OIDC lane. Issue #173 tracked the post-`v0.1.8` status sync after the `v0.1.8` GitHub prerelease and PyPI `0.1.8` package were published through the Trusted Publishing OIDC lane. Issue #191 tracked the post-`v0.1.9` status sync after the `v0.1.9` GitHub prerelease and PyPI `0.1.9` package were published through the Trusted Publishing OIDC lane. Issue #199 tracked the post-`v0.1.10` status sync after the `v0.1.10` GitHub prerelease and PyPI `0.1.10` package were published through the Trusted Publishing OIDC lane. Issue #205 tracked the post-`v0.1.11` status sync after the `v0.1.11` GitHub prerelease and PyPI `0.1.11` package were published through the Trusted Publishing OIDC lane. Issue #217 tracked the post-`v0.1.12` status sync after the `v0.1.12` GitHub prerelease and PyPI `0.1.12` package were published through the Trusted Publishing OIDC lane. Issue #225 tracks the post-`v0.1.13` status sync after the `v0.1.13` GitHub prerelease and PyPI `0.1.13` package were published through the Trusted Publishing OIDC lane. Announcements should continue to point readers to the GitHub README for the current installation path.

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
