# MCP Client Setup

日本語タイトル: MCPクライアント接続例

classification: SAFE_CANDIDATE
audience: public-alpha-user

## 目的

このページは、Agent Personal Vault のraw-free MCP stdio serverを、Codex、Claude Desktop、Claude Code、その他のMCPクライアントから試すための最小設定例です。

ここではdummy dataか、ローカルで扱ってよい値だけを使ってください。MCP serverはraw値を返すtoolを公開しません。raw値が必要な場合は、MCPでconsent requestを作り、人間がGUIまたはCLIで承認したあと、CLI `get` で1 keyだけ取得します。

## 前提

ローカルでCLIを使える状態にします。

```sh
python3 -m pip install -e .
export APV_STORE="$(mktemp -d)/vault.json"

agent-personal-vault --store "$APV_STORE" init
printf 'Example\n' | agent-personal-vault --store "$APV_STORE" set FAMILY_NAME --stdin --purpose "dummy local mcp setup"
printf 'Taro\n' | agent-personal-vault --store "$APV_STORE" set GIVEN_NAME --stdin --purpose "dummy local mcp setup"
printf 'taro@example.test\n' | agent-personal-vault --store "$APV_STORE" set EMAIL --stdin --purpose "dummy local mcp setup"
agent-personal-vault --store "$APV_STORE" context --task "応募フォームの氏名とメール連絡先を下書きする"
```

MCPクライアント設定では、`$APV_STORE` ではなく実際の絶対パスを使うのが確実です。editable installのconsole scriptが見つからない場合は、`apv-mcp` ではなく `/absolute/path/to/venv/bin/apv-mcp` のように絶対パスを指定してください。

## Codex

CodexはMCP設定を `~/.codex/config.toml` または信頼済みprojectの `.codex/config.toml` に置けます。CLIで追加する場合:

```sh
codex mcp add agent-personal-vault -- apv-mcp --store /absolute/path/to/vault.json
```

TOMLで書く場合:

```toml
[mcp_servers.agent-personal-vault]
command = "apv-mcp"
args = ["--store", "/absolute/path/to/vault.json"]
```

Codex内では `/mcp` で接続状態を確認します。

## Claude Desktop

Claude Desktopの設定ファイルに `mcpServers` を追加します。macOSでは通常 `~/Library/Application Support/Claude/claude_desktop_config.json`、Windowsでは通常 `%APPDATA%\Claude\claude_desktop_config.json` です。

```json
{
  "mcpServers": {
    "agent-personal-vault": {
      "command": "apv-mcp",
      "args": ["--store", "/absolute/path/to/vault.json"]
    }
  }
}
```

保存後、Claude Desktopを完全に終了して再起動します。表示されない場合は、設定JSONの構文、`apv-mcp` のパス、storeの絶対パス、Claude DesktopのMCPログを確認してください。

## Claude Code Project Config

Claude Codeでproject-localに置く場合は、project rootの `.mcp.json` にstdio serverとして追加します。

```json
{
  "mcpServers": {
    "agent-personal-vault": {
      "type": "stdio",
      "command": "apv-mcp",
      "args": ["--store", "/absolute/path/to/vault.json"]
    }
  }
}
```

新しいClaude Code sessionを起動し、初回promptでproject-scoped serverを承認します。接続状態は `/mcp` で確認します。

## Generic Stdio MCP Client

stdio serverとして次を起動する設定にします。

```text
command: apv-mcp
args:
  - --store
  - /absolute/path/to/vault.json
```

クライアントが `env` や `cwd` を指定できる場合でも、最初はstore pathを明示するほうが安全です。

## Raw-Free Tool Order

初回利用では、この順番にします。

1. `apv.context` を呼ぶ。`task` にはraw値を含めない。
2. `planning_hints.matched_hints[].candidate_keys` で必要候補keyを見る。
3. raw値が必要な場合だけ、`apv.request_consent` で1 keyを要求する。
4. 人間が `apv-gui --store /absolute/path/to/vault.json --open` またはCLIで承認/拒否する。
5. 承認後、GUIまたはCLI `consent approve` が表示したconsent idを使い、CLIで `agent-personal-vault --store /absolute/path/to/vault.json get <KEY> --purpose "<raw-free purpose>" --consent-id "<token>"` を実行する。GUIを閉じた場合は `agent-personal-vault --store /absolute/path/to/vault.json consent list` で未使用tokenを確認する。
6. `agent-personal-vault --store /absolute/path/to/vault.json audit summary` または `audit tail` でrawなしの利用履歴を確認する。

MCPには `get`、`env`、`set`、`unset`、外部送信、フォーム送信、メール送信、repository操作のtoolはありません。`apv.request_consent` もraw値を返しません。

## Troubleshooting

| Symptom | Check |
|---|---|
| MCP serverが起動しない | `apv-mcp --store /absolute/path/to/vault.json` をterminalで直接実行し、command not foundやPython import errorを確認する |
| clientにserverが出ない | clientを完全に再起動し、設定ファイルの場所とJSON/TOML構文を確認する |
| `apv.context` がstoreを読めない | store pathが絶対パスか、CLIで `agent-personal-vault --store /absolute/path/to/vault.json check` が通るか確認する |
| `apv.request_consent` がkeyを拒否する | `apv.context` の候補keyか、`agent-personal-vault schema` のkeyを使う。`FULL_NAME` などのderived keyも利用可能 |
| raw値が返らない | 正常です。MCPはraw値を返しません。GUI/CLIで承認後、CLI `get` を使います |
| GUIにpending requestがない | MCP clientとGUIが同じstore pathを見ているか確認する |
| auditにraw値が出るのが心配 | `audit summary` と `audit tail` はraw値を意図的に記録しません。ただし `--purpose` にはraw値を書かないでください |

## References

- Codex MCP configuration: <https://developers.openai.com/codex/mcp>
- Codex config reference: <https://developers.openai.com/codex/config-reference>
- MCP local server connection guide: <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
- Claude Code MCP setup: <https://code.claude.com/docs/en/mcp-quickstart>
