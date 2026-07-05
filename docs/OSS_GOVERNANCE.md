# OSS Governance

日本語タイトル: OSS運用方針

status: active
classification: SAFE_CANDIDATE
last_updated: 2026-07-05

## 結論

Agent Personal Vault は、public alpha公開後も Issue / PR 前提で運用する。

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

## Merge運用

- PR mergeは原則として `gh pr merge <PR_NUMBER> --squash` を使う。
- GitHub REST merge endpointを直接叩く運用は標準にしない。PR #2で、mainには同一treeのsquash commitが入った一方、PR表示が`merged`にならず`closed`で残る不整合が発生したため。
- merge前に次を確認する。
  - PR state: `OPEN`
  - mergeable: `MERGEABLE`
  - required checks: all success
  - branch is up to date with `main`
- merge後に次を確認する。
  - PR stateが`MERGED`になっている
  - `main`のHEADが意図したcommitへ進んでいる
  - `git checkout main && git pull --ff-only origin main` が成功する
  - `python3 scripts/check_release.py` と `make release-check` がローカルmainで成功する
- main反映後のGitHub Actions確認は、push eventのCIが発火していればその結果を見る。発火しない、または再確認が必要な場合は、`workflow_dispatch`で`test` workflowを手動実行して確認する。

## Merged / Closed 判定

- `mergedAt`またはGitHub UIがmergedを示すPRだけを、通常のmerged扱いにする。
- PR headとmainのtreeが一致していても、PR stateが`CLOSED`かつ`mergedAt`が空なら、merged済みとは表現しない。
- その場合は、重複mergeを避けるため次を確認する。
  - `git rev-parse origin/main^{tree} origin/<branch>^{tree}`
  - `git diff --exit-code origin/main origin/<branch>`
  - PRに経緯コメントが残っていること
- 内容がmainへ反映済みでPR表示だけが`OPEN`に残った場合は、経緯コメントを残してcloseする。final reportでは「main反映済み、PR表示はclosed」と分けて報告する。

## Branch Cleanup

- merge済みまたはmainと同一treeの作業branchでも、remote branch削除は別操作として扱う。
- branch削除は外部状態変更なので、削除対象branch、戻し方、影響範囲を示して明示承認を取ってから行う。
- 承認がない場合は、不要branchとして報告に残すだけにする。

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

## Public Alpha Repository Check

public alpha運用中に、repo設定や公開状態を確認する場合は読み取り専用で確認する。

```sh
gh repo view Driedsandwich/agent-personal-vault --json visibility,isPrivate,hasIssuesEnabled,hasWikiEnabled,description
gh api repos/Driedsandwich/agent-personal-vault/branches/main/protection
gh run list --repo Driedsandwich/agent-personal-vault --limit 3
```

Manual workflow dispatch such as `gh workflow run ...` is a write action. Keep it in a separate explicit approval lane.

期待値:

- visibility: `PUBLIC`
- issues: enabled
- wiki: disabled
- description: set
- `main` protected
- latest CI: success

## 禁止事項

別途明示承認があるまで、次は実行しない。

- repository visibilityやsettingsの変更
- GitHub release creation
- package publish
- SNS/blog等の告知
- 追加外部共有
