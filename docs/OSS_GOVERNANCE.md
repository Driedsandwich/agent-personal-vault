# OSS Governance

日本語タイトル: OSS運用方針

status: active
classification: SAFE_CANDIDATE
last_updated: 2026-07-01

## 結論

Agent Personal Vault は、public化前から Issue / PR 前提で運用する。

`main` への直pushは使わない。変更はbranchを作り、Pull Requestを通し、GitHub Actionsのrelease-checkが通ってからmergeする。

## Issue運用

- GitHub Issuesは有効にする。
- blank issueは無効にする。
- bug reportとsecurity concernのtemplateを使う。
- 実データ、スクリーンショット、vault file、raw log、ローカル絶対パス、tokenは投稿しない。
- 実データが必要な脆弱性報告はpublic issueに書かず、private advisoryまたはprivate連絡に回す。

## PR運用

- すべての変更はPull Requestで扱う。
- `main` への直pushは禁止する。
- PRでは `.github/pull_request_template.md` のSafety Checklistを埋める。
- 必須CIはGitHub Actions `test` workflowの次の3つ。
  - `release-check (3.11)`
  - `release-check (3.12)`
  - `release-check (3.13)`
- PR branchは最新の`main`から作る。
- raw-value output、GUI token、MCP、consent、audit、file permission、encryptionに触る変更はsecurity review扱いにする。

## Branch Protection

`main` branchは次を要求する。

- Pull Request経由の変更
- required status checks
- stale review dismissal
- branch up-to-date before merge
- direct push restriction
- force push禁止
- deletion禁止

Solo maintainer運用では、review approval数は公開初期に0または最小構成でもよい。ただしCI必須とPR経由は維持する。

## Public化前チェック

public化直前に確認する。

```sh
gh repo view Driedsandwich/agent-personal-vault --json visibility,isPrivate,hasIssuesEnabled,hasWikiEnabled,description
gh api repos/Driedsandwich/agent-personal-vault/branches/main/protection
gh run list --repo Driedsandwich/agent-personal-vault --limit 3
```

期待値:

- visibility: `PRIVATE` before public approval
- issues: enabled
- wiki: disabled
- description: set
- `main` protected
- latest CI: success

## 禁止事項

別途明示承認があるまで、次は実行しない。

- repository visibilityのpublic化
- GitHub release creation
- package publish
- SNS/blog等の告知
- 追加外部共有
