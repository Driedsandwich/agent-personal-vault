# Agent Personal Vault

日本語タイトル: AIエージェント向け個人情報ローカルVault

`Agent Personal Vault` は、Codex などのAIエージェントがユーザーの個人情報を安全に保管し、必要な時だけ最小限に参照するためのローカルファーストな管理レイヤーです。

これは「就活フォーム入力ツール」ではありません。就活プロフィールは、個人情報をAIエージェントが扱う最初の実用テンプレートです。

## 位置づけ

この領域には、暗号化された個人コンテキストVault、MCPサーバー、資格情報Vault、PII redaction middleware などの先行OSSがあります。

`Agent Personal Vault` は新しいカテゴリを独占的に主張するものではありません。現時点の狙いは、次のような小さく監査しやすい実装です。

- Python標準ライブラリのみ
- CLIはdaemonなしで利用可能
- AIエージェント計画用の既定入口はraw値なしの `context`
- 保存値を読まない公開可能な `schema`
- 必要keyだけを `get` する最小raw取得
- Codexのようなローカル作業エージェント向けのfinal action境界
- 日本向けプロフィールを最初の実用スキーマとして提供

先行OSSとの比較メモは [docs/PRIOR_ART_REVIEW.md](docs/PRIOR_ART_REVIEW.md) にあります。
差別化方針とMVP境界は [docs/PRODUCT_POSITIONING.md](docs/PRODUCT_POSITIONING.md) にまとめています。

## 目的

- ユーザーに同じ個人情報を何度も入力させない。
- AIエージェントが必要な項目だけを安全に取得できるようにする。
- raw個人情報をチャットログ、README、GitHub、外部API、Subagent指示へ不用意に流さない。
- 外部送信や応募などの final action は人間確認で止める。

## 現在のテンプレート

- `job_hunting_profile`
  - 氏名、ふりがな、生年月日
  - 住所、電話、メール
  - 大学、大学院、追加学歴
  - 資格
  - 顔写真ファイルパス

今後、契約、金融、本人確認書類、医療、家族情報などのテンプレートを足す場合も、raw値を外へ出さない設計を維持します。

## インストール

開発版:

```sh
python3 -m pip install -e .
```

依存関係は標準ライブラリのみです。

## 保存先

既定では次に保存します。

```text
~/.local/share/agent-personal-vault/vault.json
```

変更したい場合:

```sh
export AGENT_PERSONAL_VAULT_HOME="$HOME/.local/share/agent-personal-vault"
```

またはコマンドごとに:

```sh
agent-personal-vault --store /path/to/vault.json check
```

保存ファイルは `0600`、保存ディレクトリは `0700` に設定されます。

## CLI

初期化:

```sh
agent-personal-vault init
```

raw値を出さずに状態確認:

```sh
agent-personal-vault check
```

AIエージェント向けに、raw値なしのJSONコンテキストを取得:

```sh
agent-personal-vault context
```

保存値を読まず、公開可能なスキーマ定義だけ確認:

```sh
agent-personal-vault schema
```

マスク表示:

```sh
agent-personal-vault list
```

値を保存する。値はコマンド履歴に残さないため、実行後に入力します。

```sh
agent-personal-vault set FAMILY_NAME
```

必要なkeyだけ取得:

```sh
agent-personal-vault get FULL_NAME
```

`get` と `env` はraw値を出します。ログ、公開Issue、外部AI、Subagent指示へ貼らないでください。

## GUI

```sh
apv-gui --open
```

GUIは `127.0.0.1` にだけbindし、起動ごとにtoken付きURLを発行します。必要な時だけ起動し、作業後は `Ctrl-C` で停止してください。

## AIエージェント向け安全手順

1. まず `check` を使い、入力済み件数と不足項目だけを見る。
2. エージェントの計画には、まず `context` のraw値なしJSONを使う。
3. raw値が必要な場合は、対象keyを1つずつ `get <KEY>` で取得する。
4. raw値を最終報告、公開成果物、外部API、検索クエリ、GitHub、メール、SNS、応募サイトへ無断で送らない。
5. 外部送信、応募、登録、アップロード、メール送信は final action として止める。
6. Subagentやworkerへraw値を渡さない。必要なら親エージェントが最小限の取得と貼り付けを担当する。

詳しいプロトコルは [docs/AGENT_PROTOCOL.md](docs/AGENT_PROTOCOL.md) を参照してください。

## セキュリティ上の限界

- このツールはローカルの秘密メモに近いです。
- OSのユーザー権限を越えた攻撃者、マルウェア、侵害済み端末からは守れません。
- 既定では暗号化しません。macOS Keychain、Windows Credential Manager、libsecret対応は今後の候補です。
- ブラウザ履歴やターミナルログにtokenやraw値を残さない運用が必要です。
- 暗号化、MCP連携、監査ログ、権限委譲が必要な用途では、既存のpersonal context vaultやsecret manager系OSSも比較してください。

## OSS公開時の注意

このリポジトリには実データを入れないでください。

- `vault.json`
- `private/`
- 顔写真
- バックアップ
- スクリーンショット
- ローカル絶対パス入り設定

公開前に次を実行してください。

```sh
make release-check
```

`make` を使わない場合:

```sh
python3 scripts/check_release.py
```

公開前の停止条件は [docs/PUBLICATION_GATE.md](docs/PUBLICATION_GATE.md) にまとめています。
ローカルGit初期化へ進む場合は [docs/LOCAL_GIT_PREP.md](docs/LOCAL_GIT_PREP.md) を確認してください。

## ライセンス

MIT License。
