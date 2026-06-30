# Pre-Public Objective Review

日本語タイトル: Public公開前の客観レビュー

status: reviewed-with-fix
classification: SAFE_CANDIDATE
last_updated: 2026-07-01

## 結論

public化を止める致命的な問題は見つからなかった。

ただし、レビュー中に1件、公開前に直すべき問題を確認したため修正済み。

## 修正済みの問題

### CLI `list` がraw断片を表示していた

Before:

```text
EMAIL  メール  pr...st (27 chars)
```

これは、同意なしでraw個人情報の一部を出すため、`raw-free first` の設計と弱く矛盾していた。

After:

```text
EMAIL  メール  (filled, 27 chars)
```

現在は、入力済みかどうかと文字数だけを表示する。raw断片は出さない。テスト `test_cli_list_does_not_return_raw_fragments` を追加済み。

## 多角レビュー結果

| 観点 | 判定 | コメント |
|---|---|---|
| 実データ混入 | pass | release check、PII scan、forbidden-file checkが通過 |
| README第一印象 | pass | 就活フォーム入力ツールに見える防御的文言を削除し、説明図を追加 |
| セキュリティ表現 | pass-with-boundary | alpha、local utility、optional encryption off by default、no compliance claimを維持 |
| raw-free agent path | pass | `schema`、`context`、`check`、MCP read-only toolsはraw値を返さない |
| raw access control | pass-with-boundary | `get` / `env` はconsent token必須。ただし同一OSユーザーのshell accessに対する強制的な防壁ではない |
| CLI masked output | fixed | `list` のraw断片表示を修正済み |
| GUI | pass-with-boundary | `127.0.0.1` bind、token付きURL。ただし有効tokenを持つブラウザには全fieldを返す |
| audit / consent logs | pass-with-boundary | raw値は意図的に記録しない。ただしpurposeにはユーザーがraw値を書けてしまうため注意書きが必要 |
| encryption | pass-with-boundary | optional backendあり。既定off。OS key storeは未実装 |
| MCP | pass | raw取得、write、consent mutation、external action toolなし |
| GitHub readiness | pass | private repo、latest CI success、README/SVG/Issue template反映済み |
| GitHub repository settings | pass | repository description設定済み、Wiki無効化済み、Issues有効をprivate repo上で確認 |
| Issue / PR governance | pass | Issue templates、PR template、main branch protection、CI必須化をprivate repo上で確認 |
| OSS reputation | pass-with-boundary | 先行OSSへの配慮、禁止表現、Issue templateあり。過大な独自性主張は避ける |

## 残るリスク

public化してよいが、次は残る限界として明示したまま扱う。

1. Consent tokenはworkflow/audit制御であり、同じOSユーザーとしてshell実行できるagentを強制的に止めるものではない。
2. GUIはtoken付きURLで保護されるが、tokenを持つブラウザタブにはraw fieldを返す。
3. 既定では暗号化しない。暗号化を使う場合もpassphrase管理はユーザー責任。
4. audit/consentのpurpose欄はraw-free前提だが、機械的にPIIを完全排除する仕組みではない。
5. concurrentな同時CLI実行に対する厳密なトランザクション保証はない。
6. package publishは未検証。PyPI等へ出す場合は、sdist/wheel内容とREADME asset表示を別途確認する。
7. Branch protectionはAPI上で確認済み。ただし、direct push拒否の実押下テストは行っていない。
8. Required approving review countは0。solo-maintainer運用としては許容可能だが、共同管理者を置く段階では1以上へ上げる余地がある。

## Public化前に推奨するGitHub設定

repository description:

```text
Alpha local utility for AI-agent workflows that need raw-free personal-data metadata and explicit one-key retrieval.
```

current recommended settings:

- Repository description: configured
- Wiki: disabled
- Issues: enabled
- Blank issues: disabled through `.github/ISSUE_TEMPLATE/config.yml`
- Main branch protection: PR-based changes and required CI checks enabled
- Discussions: do not enable until moderation policy is ready

## 判断

GitHub repository visibilityをpublicへ変更する判断は可能。直前には、repository description、Wiki無効化、Issues、blank issue disabled、main branch protection、latest CIを再確認する。

ただし、release、package publish、SNS/blog告知、追加外部共有は、別の承認と別のチェックを要求する。
