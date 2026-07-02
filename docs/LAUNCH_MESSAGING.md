# Launch Messaging

日本語タイトル: 公開時メッセージ方針

status: draft
classification: SAFE_CANDIDATE

## Purpose

This file prevents reputation and safety issues when presenting Agent Personal Vault publicly.

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

## Avoid

Do not use these claims:

- secure personal-data vault
- encrypted vault
- privacy guaranteed
- enterprise-grade
- compliance-ready
- safe for all personal data
- first of its kind
- replaces password managers, secret managers, or consent systems
- lets agents safely access all user data

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

- The announcement text uses the safe framing in this file.
- The announcement text says alpha/local utility, raw-free first, one-key raw retrieval, and human stop before external actions.
- The text does not ask readers to post real personal data, screenshots, logs, vault files, consent files, audit files, or local paths.
- The text does not include local developer paths, private support details, private screenshots, PyPI tokens, GitHub tokens, or unpublished issue details.
- The current GitHub release, PyPI page, README install path, Actions, Security alerts, and open Issue/PR state have been checked.
- The planned channel, text, target URL, rollback/edit path, and expected support burden are written down before approval.

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

## Issue Response Template

Use this when a report includes or asks for real personal data:

```text
Please remove any real personal data from the issue before we discuss details. This project cannot review raw names, addresses, phone numbers, emails, IDs, photos, screenshots, or vault files in public. A minimal reproduction using dummy values is enough.
```
