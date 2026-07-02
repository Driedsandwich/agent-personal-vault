# Launch Messaging

日本語タイトル: 公開時メッセージ方針

status: draft
classification: SAFE_CANDIDATE
last_updated: 2026-07-02

## Purpose

This file prevents reputation and safety issues when presenting Agent Personal Vault publicly.

This document does not authorize any SNS, blog, newsletter, community, or other public announcement. Every channel still requires separate explicit approval with the exact text and target URL.

## 日本語要約

公開時は「安全な個人情報Vault」ではなく、「AIエージェント作業で繰り返し必要になる個人情報フィールドを、ローカルで扱いやすくするalpha版ユーティリティ」と説明する。

強調してよい点:

- raw値なしの `schema`、`check`、`context` を先に使う設計
- raw値は必要なkeyだけ明示的に取り出す設計
- 外部送信、応募、登録、アップロード、公開は人間確認で止める設計
- 現在はプロフィール情報のスキーマを同梱している

避けるべき点:

- 暗号化済み、完全安全、プライバシー保証、法令対応済み、企業利用可能、世界初、既存のsecret manager代替などの表現
- ユーザーに実データ、スクリーンショット、vaultファイルをIssueへ投稿させる導線

## Required Framing

Use this framing:

- alpha local utility
- local-first personal-data management for AI agent workflows
- raw-free `schema`, `check`, and `context` first
- one-key raw retrieval only when explicitly needed
- final-action boundary before external sending, upload, application, registration, or publication
- bundled profile schema for initial local workflows
- best-effort public alpha support only

## Approved Wording Building Blocks

These phrases are acceptable when they remain accurate for the current release:

- "alpha local utility"
- "local-first utility for AI-agent workflows"
- "raw-free metadata and context first"
- "explicit one-key retrieval for raw values"
- "human stop before external submission, upload, registration, application, or publication"
- "not encrypted by default"
- "not a compliance, enterprise-security, password-manager, or secret-manager replacement"
- "please use dummy data in public Issues"
- "best-effort public alpha support"

## Avoid

Do not use these claims:

- secure personal-data vault
- encrypted vault
- encrypted by default
- privacy guaranteed
- enterprise-grade
- enterprise-ready
- compliance-ready
- production-ready
- safe for all personal data
- first of its kind
- world-first
- replaces password managers, secret managers, or consent systems
- lets agents safely access all user data
- fully automated personal-data access
- supports every MCP client
- Claude Desktop live UX fully validated

## Safe Short Description

```text
Agent Personal Vault is an alpha local utility for managing personal-data fields that AI agents may need during local workflows. It favors raw-free metadata, explicit one-key retrieval, and a human stop before external actions. It is not encrypted by default and is not a compliance or enterprise security product.
```

## Safe Launch Post

```text
I am publishing an early alpha of Agent Personal Vault, a local-first utility for AI-agent workflows that need repeated personal-data fields.

The project is intentionally small: agents can inspect schema/status/context without raw values, and raw access is limited to explicit one-key retrieval. External submission, upload, application, registration, and publication remain human-confirmed final actions.

Important limitation: it is not encrypted by default and is not a compliance, enterprise-security, or password-manager replacement. Please do not post real personal data, screenshots, or vault files in issues.
```

## Pre-Announcement Checklist

Before any SNS, blog, newsletter, community post, or other public announcement, confirm all items below. This checklist does not authorize announcement by itself; each channel still requires separate explicit approval.

Approval packet:

- Exact channel and account.
- Exact announcement text.
- Target URL.
- Intended timing.
- Edit, withdrawal, or correction path for that channel.
- Expected support-load window.
- Person responsible for checking early replies, Issues, and PRs.

Repository and distribution state:

- Current GitHub release, prerelease status, and target commit are checked.
- PyPI project page and install command are checked if the announcement mentions PyPI.
- README install path and safety notice are visible.
- Actions, CodeQL, Dependabot/security alerts, and open Issue/PR state are checked.
- No release/tag/package publish is implied unless already separately approved and verified.

Text review:

- The announcement text uses the safe framing in this file.
- The announcement text says alpha/local utility, raw-free first, one-key raw retrieval, and human stop before external actions.
- The text does not ask readers to post real personal data, screenshots, logs, vault files, consent files, audit files, or local paths.
- The text does not include local developer paths, private support details, private screenshots, PyPI tokens, GitHub tokens, or unpublished issue details.
- The text does not claim production readiness, compliance, enterprise security, data recovery, or broad MCP/client compatibility.
- The text does not claim full Claude Desktop app live UX unless that exact UX has been separately approved, tested, and documented.
- The text says public support is best-effort when support expectations are mentioned.
- Links point to README, SECURITY, and issue-reporting guidance when the channel allows more than one link.

Forbidden wording:

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

## Announcement Approval Text

Use this template when asking for approval to publish a prepared announcement:

```text
Approve publishing the reviewed Agent Personal Vault announcement text to <channel/account> at <time or timing>. Target URL: <url>. Do not create releases, tags, package publishes, repository setting changes, branch deletions, or additional announcements.
```

Approval for one channel does not authorize any other channel.

## Withdrawal And Correction Procedure

If a public announcement is wrong, misleading, or unsafe:

1. Stop further announcements immediately.
2. Preserve the original text and URL for internal review without copying raw personal data into public Issues.
3. If the channel supports editing, edit the post to remove unsafe wording or broken links.
4. If the channel supports deletion or withdrawal and the issue is material, withdraw the post and record that action internally.
5. If readers may already have acted on the incorrect text, publish a short correction on the same channel.
6. Open a GitHub Issue only when the problem is product-facing or docs-facing; do not include real personal data, tokens, local paths, screenshots with raw values, vault files, consent files, or audit logs.
7. If user safety, raw leakage, or consent bypass is involved, stop announcement work and use the security reporting path.

Correction wording should be factual and narrow. Do not over-explain private operational details.

## Support Load Expectation

Public alpha support is best-effort only.

Do not promise:

- response times;
- production support;
- data recovery;
- compatibility with every MCP client;
- review of real personal data;
- security/compliance assurance.

Expected first-response approach:

- For installation or onboarding confusion, prefer docs clarification through Issue/PR.
- For bug reports, ask for dummy-data reproduction steps.
- For security-sensitive reports, redirect to the security policy and remove raw personal data from public discussion.
- For feature requests, keep scope narrow and avoid roadmap promises.

Stop or pause further announcements if any of these occur:

- two or more independent users report the same consent, raw retrieval, MCP setup, install, or safety-boundary confusion;
- any report suggests raw personal data, token, local private path, vault file, consent file, or audit file exposure;
- CodeQL, Dependabot, secret scanning, or release-check state becomes red;
- README or PyPI install instructions are found to be misleading;
- the announcement attracts support volume that cannot be handled without weakening safety boundaries.

## Issue Response Template

Use this when a report includes or asks for real personal data:

```text
Please remove any real personal data from the issue before we discuss details. This project cannot review raw names, addresses, phone numbers, emails, IDs, photos, screenshots, or vault files in public. A minimal reproduction using dummy values is enough.
```
