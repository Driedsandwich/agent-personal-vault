# External Publication Decision

日本語タイトル: 外部公開判断パケット

status: superseded-by-public-release-review
classification: SAFE_CANDIDATE
last_updated: 2026-07-01

## 結論

現時点の推奨は、`Agent Personal Vault` / `agent-personal-vault` の名称を維持すること。

Private GitHub dry-runは完了済み。public化、release creation、package publish、public announcement は、まだ実行しない。これらはそれぞれ別の明示承認が必要。

## 現在状態

```text
Local publication gate: pass
Latest local commit: see `git log --oneline -1`
Private GitHub dry-run: completed
Public visibility: not executed
```

ローカルでは、README、SECURITY、CONTRIBUTING、LICENSE、Issue templates、release check、PII scan、audit/consent、optional encryption、read-only MCP が揃っている。

## 公開名

推奨:

```text
Project name: Agent Personal Vault
Repository slug: agent-personal-vault
Package/import name: agent_personal_vault
```

公開Webの簡易確認では、`Agent Personal Vault` の完全一致で大きな既存OSS名衝突は確認できなかった。一方で、AI agent の personal vault、agent vault、memory vault、agent向けcredential/vault という近接表現やサービスは存在する。

したがって、名前は維持してよい。ただし、次の表現は避ける。

- 世界初
- 新カテゴリの発明
- AI個人情報管理の標準
- 既存vault/secret managerの代替

この確認は商標調査ではない。正式な商標・法務確認は未実施。

参考にした近接例:

- `ctxvault`: agentをvaultへattachする概念があるPyPI package
- `mantle-ai`: personal vaultをAI context/skill knowledgeとして扱うPyPI package
- `deepsecure`: AI agent向けcredential/security control planeを掲げるPyPI package
- `angel-claw`: encrypted vaultを含むagent OS系PyPI package

## 公開方式

推奨は `private dry-run -> public`。

| 選択肢 | 推奨 | 理由 |
|---|---:|---|
| private GitHub repoを作り、CIとREADME表示を確認してからpublic化 | yes | PII漏れ、Issue template、Actions、表示崩れ、表現リスクを公開前に確認できる |
| public repoへ直行 | no | 今の品質なら可能だが、個人情報ツールなので初回の公開事故リスクを下げる価値が大きい |
| まだ公開しない | acceptable | OSS候補としてはlocal-readyだが、告知や保守方針を詰めたいなら保留可能 |

## 初回告知

推奨はREADME中心。SNSやblogは後回し。

安全な短文:

```text
Agent Personal Vault is an alpha local utility for managing personal-data fields that AI agents may need during local workflows. It favors raw-free metadata, explicit one-key retrieval, and a human stop before external actions. It is not encrypted by default and is not a compliance or enterprise security product.
```

告知で避ける表現:

- secure personal-data vault
- encrypted vault
- privacy guaranteed
- compliance-ready
- enterprise-grade
- safe for all personal data

## CI確認

private dry-runで確認する項目:

1. GitHub Actionsで `python scripts/check_release.py` が通る。
2. README、SECURITY、CONTRIBUTING、Issue templates がGitHub上で意図通り表示される。
3. Issue templatesが実データ投稿を止める文言になっている。
4. repositoryに `vault.json`、`audit.jsonl`、`consents.json`、画像、DB、backup、private directory が含まれていない。
5. public化前に `python3 scripts/check_release.py` と `make release-check` を再実行する。

## ライセンスとセキュリティ表現

現在の表現は公開候補として許容範囲。

維持する境界:

- alpha
- local utility
- optional encryption is off by default
- no compliance claim
- no enterprise security claim
- no password-manager or secret-manager replacement claim
- public issues must not contain real personal data

## 次に設定すべきゴール

推奨ゴール:

```text
Agent Personal Vaultのpublic公開可否をprivate repo上で最終判断する。README/SECURITY/Issue template/docs/CI結果を人間レビューし、公開時の説明文と禁止表現を確定する。ただし、public化、release、package publish、告知はそれぞれ別途明示承認まで実行しない。
```

完了条件:

- private repository creation policy is approved
- first push target and visibility are confirmed
- CI result is checked
- rendered README/SECURITY/Issue templates are reviewed
- final publicization decision is documented

停止条件:

- GitHub repository creation approvalがない
- push approvalがない
- PII、secret、private path、raw vault fileの混入疑いが出る
- READMEや告知文が安全性を過大主張している
