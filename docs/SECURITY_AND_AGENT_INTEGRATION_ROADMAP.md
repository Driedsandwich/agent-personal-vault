# Security And Agent Integration Roadmap

日本語タイトル: セキュリティ機能とAIエージェント連携ロードマップ

status: draft
classification: SAFE_CANDIDATE

## 結論

Agent Personal Vault は、今のCLI/GUIだけなら「alpha版のローカル実験ユーティリティ」として成立する。ただし、実個人情報を継続的に扱い、CodexなどのAIエージェントが日常的に参照する前提では、次の順に強化するべき。

1. 監査ログ
2. 同意UI
3. 暗号化
4. MCP連携と権限管理

理由は、MCPだけ先に入れると「AIが個人情報へアクセスしやすくなる」効果が先に出て、説明責任・同意・追跡・保管安全性が追いつかないため。

## Public Alpha Checkpoint

2026-07-02時点では、releaseやpackage publishをまだ行わない前提で、既知のP0実装ブロッカーはない。

確認済み:

- dummy dataによるonboarding正常系は、CLI `context`、MCP `apv.context`、MCP `apv.request_consent`、GUI承認、CLI `get`、`audit tail` まで通過した。
- consent拒否、key不一致、期限切れtoken、MCP unknown key、invalid action、unknown tool、invalid arguments の否定系は、raw値、store path、secret風文字列を出さずに失敗した。
- GUIは承認後にCLI `get --consent-id` へ渡すconsent idを表示する。
- generic stdio、Codex `mcp add/list/get`、Claude Code `mcp add/list/get`、Claude Code project `.mcp.json` の設定差分をdummy dataで確認した。
- Claude Codeの非対話/制限モードでは、server承認だけでなく `mcp__agent-personal-vault__apv_context` と `mcp__agent-personal-vault__apv_request_consent` のtool許可が必要。この点は `docs/MCP_CLIENT_SETUP.md` に反映済み。

残るP1:

- Claude Desktopは設定JSON形、generic stdio互換、terminal-only/Desktop-likeなconsent handoffまで確認済み。ユーザーlevelのDesktop設定を編集してClaude Desktopを再起動し、実UIでtool-callするUXは未検証であり、明示承認と人間作業を邪魔しない環境がない限り実施しない。
- MCP host/clientごとの権限UI、tool名表示、エラー表示は差があるため、利用報告が出たclientから順に追加確認する。
- raw-value MCP toolは引き続き未実装にする。追加する場合は、host/client表示差、consent token受け渡し、監査ログ、max 1 key制限、bulk raw export禁止を別Issueでレビューする。
- release/package publishは、配布artifact、依存関係、インストール手順、サポート負荷を別途確認するまで実行しない。

## Post-v0.1.6 Opus Product Review Checkpoint

2026-07-04時点では、`v0.1.6` のGitHub prerelease、PyPI package、Trusted Publishing OIDC publish、post-publish docs sync、branch cleanupは完了している。Opusによる製品レビューでは、公開alpha継続は妥当で、緊急patch releaseは不要という助言だった。

ただし、P1として次を継続監視する:

- 既定で非暗号化の平文保存であるため、保存場所、ファイル権限、OSユーザー境界、バックアップ/同期フォルダ混入は利用者に明示し続ける。
- raw値がstderr、例外、MCP error、audit、consent、GUI/CLIログ、workflow log、public issueへ混入しないことを回帰テストで確認する。
- `purpose` はraw-free前提だが、利用者がraw値を書いてしまう可能性がある。agent-facing outputではraw-lookingなpurposeを返さない方針を維持する。
- consent tokenとauditはworkflow制御と説明責任の仕組みであり、同じOSユーザーとしてshell実行できるagentを強制的に隔離する権限境界ではない。

停止条件:

- raw値、token、private local path、vault file、consent file、audit fileが意図せずstderr、例外、MCP response、audit view、public artifact、public issueに出た場合。
- consent gate、human approval、one-time token、audit redactionの回避が確認された場合。
- Trusted Publishingの設定不一致、package publish経路の破綻、高severity security alertが発生した場合。

## 機能別判断

| 機能 | 実装是非 | 優先度 | 判断 |
|---|---:|---:|---|
| 監査ログ | 実装する | P0 | rawアクセスの説明責任に必須。MCPより先に必要。 |
| 同意UI | 実装する | P0 | AIエージェント経由のraw取得には人間確認が必要。 |
| 暗号化 | 初期版を実装済み | P1 | optional backendを追加済み。OS key store連携は未実装。 |
| MCP権限管理 | raw-free版を実装済み | P1 | 汎用AIエージェント連携には有効。raw-value toolはまだ公開しない。 |

## 監査ログ

入れるべき理由:

- raw値をいつ、どのkeyで、何の目的で取得したかを後から確認できる。
- AIエージェント連携で「知らないうちに取られた」不安を下げる。
- 公開OSSとして、セキュリティ限界を補う透明性になる。

記録する情報:

```json
{
  "timestamp": "UTC ISO-8601",
  "actor": "cli|gui|mcp",
  "action": "context|get|env|set|unset|consent_grant|consent_deny",
  "key": "EMAIL",
  "raw_returned": true,
  "purpose": "draft local application form",
  "consent_id": "local random id",
  "outcome": "allowed|denied|error"
}
```

記録しない情報:

- raw値
- 氏名、住所、電話番号、メールなどの実値
- 顔写真パス
- 外部送信先URL
- ローカル絶対パス

実装方針:

- `~/.local/share/agent-personal-vault/audit.jsonl` にappend-onlyで保存する。
- file modeは `0600`。新規作成する保存ディレクトリは `0700`。既存のcustom親ディレクトリを指定した場合は、その親ディレクトリの権限を自動変更しない前提で扱う。
- CLIは `audit tail` と `audit summary` を提供する。
- 公開レポート用にはkey名と件数だけを出す。

## 同意UI

入れるべき理由:

- raw取得はユーザーの認識が必要。
- MCPや将来のエージェント接続では、モデルが自律的にtool callを試みる可能性がある。
- 「AIが勝手に個人情報を取った」と見えることが最大の炎上要因になる。

最小仕様:

- raw取得系コマンドには `--purpose` を必須にする。
- 非対話環境では、同意なしraw取得を拒否する。
- GUIには「要求中のkey」「目的」「呼び出し元」「許可時間」「一回限り/セッション中」を表示する。
- 同意結果は監査ログへ記録する。

例:

```sh
agent-personal-vault get EMAIL --purpose "prepare local draft for user review"
```

MCPの場合:

1. agentが `request_value` を呼ぶ。
2. serverは `consent_required` を返す。
3. GUIまたはCLIで人間が許可する。
4. agentが同じ `consent_id` で再試行する。

## 暗号化

入れるべき理由:

- 実個人情報を長期保存するなら、平文JSONは説明が弱い。
- 「vault」という名前との期待差を縮められる。
- 公開後の批判点を明確に減らせる。

やってはいけないこと:

- 自作暗号。
- 独自難読化を暗号化と呼ぶ。
- 「暗号化したから安全」と言い切る。
- 鍵、復旧コード、パスフレーズをログや設定ファイルに保存する。

推奨実装順:

1. store backend interfaceを作る。
   - `PlainJsonStore`
   - `EncryptedJsonStore`
2. 既存ユーザー向けに明示的な移行コマンドを作る。
   - `agent-personal-vault migrate-encrypt`
   - `agent-personal-vault migrate-decrypt`
3. 暗号化backendでは標準ライブラリだけに固執しない。
   - robustなAEAD実装を使う。
   - optional extraとして提供する。
4. macOS KeychainなどOS key store連携は追加backendとして扱う。

Status: optional encrypted backend is implemented using `cryptography` when installed. It is off by default, uses AES-256-GCM with PBKDF2-HMAC-SHA256 key derivation, and depends on a user-managed passphrase. OS key store integration remains pending.

推奨しない初手:

最初からMCPサーバーと暗号化を同時に入れない。保存形式、鍵管理、同意、監査、エージェントtool surfaceが同時に変わり、レビュー不能になる。

## MCP権限管理

入れるべき理由:

- Codex以外のAIエージェントからも使いやすくなる。
- CLI標準出力をAIが読むより、tool schemaで意図を制約しやすい。
- raw-freeとraw-returning toolを分けられる。

MCP tool設計:

raw-free:

- `apv.schema`
- `apv.context`
- `apv.check`
- `apv.list_masked`

raw-returning:

- `apv.request_value`
- `apv.request_derived_value`

write:

- `apv.set_value`
- `apv.unset_value`

raw-returning toolは、必ず次を要求する。

- `key`
- `purpose`
- `consent_id`
- `max_age_seconds`

権限manifest:

```json
{
  "default_allow": ["schema", "context", "check"],
  "require_consent": ["get", "set", "unset"],
  "human_only_bulk_raw": ["env"],
  "deny": ["bulk_export_raw"],
  "max_raw_keys_per_request": 1
}
```

明示的に作らないtool:

- 全raw値一括取得
- 顔写真ファイル本文取得
- 外部フォーム自動送信
- メール送信
- GitHub投稿
- remote AI prompt送信

## AIエージェント連携性能

ここでの「性能」は速度だけではなく、実運用でエージェントが迷わず、漏らさず、過剰取得せずに使える性能を指す。

| 軸 | 目標 | 確認方法 |
|---|---|---|
| 発見性 | agentが最初にraw-free commandへ到達できる | README、AGENT_PROTOCOL、MCP tool descriptionsを確認 |
| 最小取得 | 必要keyだけを取りに行く | tool schemaで1 key制限、監査ログ確認 |
| 低漏洩 | raw値がログ・最終報告・Subagentへ出ない | tests、manual smoke、PII scan |
| 低摩擦 | context取得は高速・daemon不要 | CLI smoke、MCP smoke |
| 人間制御 | raw取得時に目的と同意が残る | consent UI、audit log |
| 回復性 | 同意拒否・空値・未設定でもagentが破綻しない | error schema、tests |

### CLI連携

現状のCLIは、Codexのようなローカル作業エージェントに向いている。

利点:

- daemon不要。
- 標準ライブラリのみ。
- `context` と `schema` がraw-free。
- shell commandとして監査しやすい。

弱点:

- `get` のstdoutはraw値なので、エージェントの会話ログやツールログに残りやすい。
- purpose、one-time consent token、監査ログは構造化済み。ただし、同じOSユーザー権限の別プロセスによるCLI実行を完全に分離する権限モデルではない。
- 複数エージェント間の権限差を表現しにくい。

改善:

- raw取得結果をエージェントの会話ログ、Subagent指示、公開成果物へ残さない運用をREADME/AGENT_PROTOCOLとテストで維持する。
- consent tokenの期限、使用済み状態、拒否履歴をGUIでさらに見やすくする。
- 複数エージェントや複数clientを明確に分ける必要が出たら、actor/client識別と権限manifestを拡張する。

### MCP連携

MCPは汎用エージェント連携に向くが、raw取得toolを公開する時点でリスクが上がる。

利点:

- tool descriptionで安全な使い方を明示できる。
- raw-free toolとraw-returning toolを分けられる。
- エージェント側がstructured errorを扱いやすい。

弱点:

- エージェントがtoolを自律選択するため、同意UIなしでは危険。
- host/clientごとの確認UI差に依存する。
- STDIO型のローカルMCPでは、OAuthのような外部認可モデルをそのまま使えない場面がある。

改善:

- 現行MCP版はraw-free planning/status toolsとraw-free consent request toolだけに限定する。
- Clientごとの権限UI差を前提にし、docsには確認済みclient固有の注意点を追記する。Claude Codeでは `mcp__agent-personal-vault__apv_context` と `mcp__agent-personal-vault__apv_request_consent` の明示許可が必要になる場合がある。
- raw-returning toolsは、host/clientの確認UI差、consent tokenの受け渡し、監査ログ、テスト、ドキュメントを別Issueでレビューしてから検討する。
- raw-value toolを追加する場合も、既定値は無効、max 1 key、bulk raw exportなしを維持する。

### GUI連携

GUIはagent向けというより、人間の入力・同意・確認に向く。

改善:

- 「入力画面」「同意画面」「監査確認」を分けたまま、5分導線で迷わない配置を維持する。
- consent tokenの期限、使用済み状態、拒否履歴の表示を必要に応じて改善する。
- GUI audit表示はraw-free summary/tailに限定し、raw値やローカル絶対パスを出さない。

## 推奨ロードマップ

### Phase 1: Audit And Consent CLI

- `audit.py` を追加する。
- raw取得とset/unsetの監査を入れる。
- `get` に `--purpose` を追加する。
- testsで「raw値はauditに入らない」ことを確認する。

Status: audit logging, required `--purpose`, one-time consent tokens, consent request queue, CLI approve/deny, and GUI approve/deny are implemented for raw-returning `get` and `env`.

### Phase 2: Consent GUI

- GUIにconsent request queueを追加する。
- GUI/CLIで承認・拒否できるようにする。
- 一回限りのconsent tokenを発行する。
- audit viewerを追加する。

Status: consent request queue, approve/deny, and a dedicated raw-free audit viewer are implemented. Consent token expiry, used, and denied-state visibility can be polished if public-alpha users find it unclear.

### Phase 3: Encryption Backend

- store backend interfaceを導入する。
- optional encrypted backendを追加する。
- migration commandを追加する。
- READMEのsecurity limitationを更新する。

Status: initial optional encrypted backend and migration commands are implemented. OS key store integration and recovery UX remain pending.

### Phase 4: MCP Raw-Free Server

- `apv.schema`
- `apv.context`
- `apv.check`
- `apv.list_masked`
- `apv.request_consent`

ここではraw-returning toolをまだ出さない。

Status: raw-free MCP stdio server is implemented. It exposes raw-free planning/status tools and a raw-free consent request tool. It does not expose raw retrieval, stored-value write, or external action tools.

### Phase 5: MCP Raw Access With Consent

- `apv.request_value`
- consent token必須。
- max 1 key per request。
- audit必須。
- bulk raw exportなし。

## First Implementation Target

現時点でreleaseやpackage publishをまだ行わない前提では、既知のP0実装ブロッカーはない。次に実装するなら、P1として最小で次を検討する。

1. consent tokenの有効期限、使用済み状態、拒否履歴をGUIで表示する。
2. OS key store integrationとpassphrase recovery UXを検討する。
3. MCP raw-value toolsを追加する場合のconsent token設計、client表示差、監査ログ、test fixtureをレビューする。
4. 複数エージェント/複数client識別が必要になった場合のactor permission manifestを設計する。

当面は、GitHub Issues/PRs、Actions、Security alerts、README表示、release/tag absence、外部フィードバックを軽量観測し、実利用で迷いが出た箇所だけIssue化する。監査ログ、purpose記録、CLI consent token、consent request queue、GUI承認/拒否、GUI audit viewer、optional encryption backend、raw-free MCP serverは実装済み。

## References

- Model Context Protocol specification: https://modelcontextprotocol.io/specification/2025-06-18
- MCP server tools specification: https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- MCP authorization specification: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
