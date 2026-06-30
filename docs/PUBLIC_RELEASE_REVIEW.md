# Public Release Review

日本語タイトル: Public公開可否レビュー

status: public-ready-with-boundaries
classification: SAFE_CANDIDATE
last_updated: 2026-07-01

## 結論

Agent Personal Vault は、public GitHub repositoryとして公開してよい状態。

ただし、承認済みとみなす範囲は repository visibility の public化までに限定する。次の操作は、引き続き別途明示承認が必要。

- GitHub release creation
- package publish
- public announcement
- SNS/blog投稿
- 外部サービスへの追加共有

## 現在の確認対象

```text
Repository: Driedsandwich/agent-personal-vault
Current visibility: PRIVATE
Default branch: main
Latest commit: see `git log --oneline -1`
Latest CI: GitHub Actions test workflow success
```

## 人間レビュー観点

| 項目 | 判定 | 根拠 |
|---|---|---|
| README | pass | Alpha Safety Notice、raw-free first、optional encryption off by default、Issue/外部AIへのraw貼付禁止が明記されている |
| SECURITY | pass | alpha、local-only、no compliance claim、public issueへ実データ投稿禁止、optional encryption境界が明記されている |
| Issue templates | pass | bug/security templateが実データ、screenshots、vault files、raw logsの投稿を止めている |
| Docs | pass | publication gate、launch messaging、reputation risk、prior art、agent protocol、dry-run reportが揃っている |
| CI | pass | Python 3.11、3.12、3.13で `python scripts/check_release.py` が成功 |
| PII/forbidden-file check | pass | `vault.json`、`audit.jsonl`、`consents.json`、画像、DB、backup、private directoryの混入なし |
| CLI masked output | pass | `list` はraw断片を出さず、入力済み状態と文字数のみを表示する |
| GitHub repository settings | needs-action-before-public | description設定とWiki無効化をpublic化直前に推奨 |
| Issue / PR governance | needs-action-before-public | Issue templates、PR template、main branch protection、CI必須化をpublic化前に確認する |
| Public messaging | pass-with-boundary | README中心なら可。SNS/blog同時告知は別判断 |

## 公開時の説明文

推奨する短い説明:

```text
Agent Personal Vault is an alpha local utility for managing personal-data fields that AI agents may need during local workflows. It favors raw-free metadata, explicit one-key retrieval, and a human stop before external actions. Optional at-rest encryption is off by default, and this is not a compliance or enterprise security product.
```

README冒頭やGitHub descriptionで使う場合は、より短くする。

```text
Alpha local utility for AI-agent workflows that need raw-free personal-data metadata and explicit one-key retrieval.
```

## 禁止表現

public化後も、次の表現は禁止。

- secure personal-data vault
- encrypted vault
- privacy guaranteed
- compliance-ready
- enterprise-grade
- safe for all personal data
- first of its kind
- standard for AI personal data
- replaces password managers or secret managers
- lets agents safely access all user data

## Public化直前チェック

Public化直前に実行する。

```sh
python3 scripts/check_release.py
make release-check
git status --short
gh repo view Driedsandwich/agent-personal-vault --json visibility,isPrivate,defaultBranchRef
gh run list --repo Driedsandwich/agent-personal-vault --limit 3
```

Public化直前に推奨するGitHub設定:

- repository descriptionを設定する
- Wikiを無効化する
- Issuesは有効のままにし、blank issue disabledを維持する

Public化後に確認する。

```sh
gh repo view Driedsandwich/agent-personal-vault --json visibility,isPrivate,url
gh api repos/Driedsandwich/agent-personal-vault/readme --jq '{name: .name, path: .path, size: .size, html_url: .html_url}'
gh api repos/Driedsandwich/agent-personal-vault/contents/.github/ISSUE_TEMPLATE --jq '.[] | {name: .name, path: .path, size: .size}'
```

## 停止条件

次のどれかが出たらpublic化しない。

- release check失敗
- CI失敗
- 実データ、secret、private path、raw vault file、画像、DB、backupの混入疑い
- README/SECURITY/Issue templateの表示確認ができない
- 公開説明文が安全性・暗号化・法令対応を過大主張している

## 次の推奨判断

次の一手は、repository visibilityをpublicへ変更するかどうかの明示承認。

推奨は public化してよい。ただしrelease、package publish、告知は同時に行わない。
