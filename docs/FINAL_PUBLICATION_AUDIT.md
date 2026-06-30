# Final Publication Audit

日本語タイトル: 最終公開前監査

status: local-pass-with-boundaries
classification: SAFE_CANDIDATE
last_updated: 2026-07-01

## 結論

このリポジトリは、ローカルOSS候補としての公開判断に必要な主要ゲートを満たしている。

ただし、次の操作はまだ実行していない。これらは別途、人間の明示承認が必要。

- remote repository creation
- `git push`
- release creation
- package publish
- public announcement
- external sharing

## 監査対象

Project:

```text
agent-personal-vault
```

Product boundary:

```text
AIエージェントが個人情報を安全に扱うためのローカル管理レイヤー。
就活プロフィールは最初の実用スキーマであり、製品の本質ではない。
```

## 要件別確認

| 要件 | 判定 | 現在の証拠 |
|---|---|---|
| 実データ混入なし | pass | release check、PII scan、forbidden files checkが通過 |
| raw-free計画入口 | pass | `context`、`schema`、MCP `apv.context`、`apv.schema` |
| raw取得の最小化 | pass | `get/env` はconsent token必須、MCPにはraw toolなし |
| rawアクセス目的記録 | pass | `--purpose` 必須、auditに記録 |
| 監査ログ | pass | `audit summary` / `audit tail`、raw値なし |
| 同意導線 | pass | `consent request`、approve/deny、GUI承認/拒否 |
| 保存時暗号化 | pass-with-boundary | optional encrypted backendあり。既定off。passphrase管理はユーザー責任 |
| MCP連携 | pass-with-boundary | read-only/raw-free MCPのみ。raw-value MCP toolは未公開 |
| 炎上対策 | pass | Alpha Safety Notice、launch messaging、reputation risk review、Issue templates |
| 先行OSSへの配慮 | pass | prior art reviewとpositioning documentあり |
| 公開前検証 | pass | `check_release.py` と `make release-check` が通過 |
| 公開操作停止 | pass | push、release、package publish、告知は未実行 |

## 実装済み安全機能

- raw-free `schema`
- raw-free `context`
- raw-free `check`
- CLI consent request queue
- GUI consent approve/deny
- one-time consent token
- raw-free audit log
- optional encrypted store backend
- read-only MCP stdio server
- PII and forbidden-file release check
- GitHub Issue templates that reject personal data

## 明示的に未実装

以下は未実装だが、現段階の公開候補では明示的な境界として扱う。

- MCP raw-value tools
- automatic form submission
- external upload
- email sending
- remote sync
- multi-user permission system
- OS key store integration
- compliance certification
- enterprise security claim

## 最新検証

Commands:

```sh
python3 scripts/check_release.py
make release-check
```

Observed result:

```text
22 tests passed
No obvious private data patterns found
no forbidden files found
no forbidden text found
release checks passed
```

Additional smoke checks completed in the current work:

- CLI consent request, approve, and raw retrieval
- GUI API approve for pending consent request
- optional encryption status and missing-dependency failure path
- MCP tools/list and raw-free `apv.context`

## 残る公開前判断

公開前に人間が判断するべき点:

1. 名前を `Agent Personal Vault` のままにするか。
2. optional encryptionを「十分」と説明するか、「初期版」と強く限定するか。
3. 初回公開をREADME中心にするか、blog/social postも同時に出すか。
4. GitHub remoteをpublicで作るか、privateで一度CI確認してからpublic化するか。

## 推奨判断

現時点の推奨は次の通り。

```text
Local publication gate: pass
Local commit: completed
External publication: approval required
Recommended next action: review the external publication decision packet, then approve or reject private GitHub dry-run repository creation
```

外部公開はまだ行わない。次は [EXTERNAL_PUBLICATION_DECISION.md](EXTERNAL_PUBLICATION_DECISION.md) を正本に、公開名、公開方式、告知文、CI確認、ライセンス/セキュリティ表現を人間が判断するのがよい。
