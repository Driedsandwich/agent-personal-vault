# Versioned KDF移行設計とbenchmark記録

status: implemented-candidate
classification: SAFE_CANDIDATE
last_updated: 2026-08-14
issue: https://github.com/Driedsandwich/agent-personal-vault/issues/309

## 結論

新規暗号化のversion 2 profileはArgon2id、memory 19 MiB、iterations 2、parallelism 1とする。既存version 1 profile（PBKDF2-HMAC-SHA256、390,000 iterations）は読込み可能な互換形式として維持し、通常保存では暗黙にversion 2へ変更しない。

## Synthetic benchmark

実行command:

```sh
python scripts/benchmark_kdf.py
```

実測環境はDarwin arm64、Python 3.14.6、cryptography 45.0.7、logical CPU 10。値は2026-08-14にsynthetic passphrase/saltだけで取得した。`constrained proxy`は4 workerが同時にKDF処理する競合負荷であり、物理的な低性能端末の実測ではない。時間をCIのpass/fail thresholdには使わない。

| Candidate | single-process median（7回） | 4-worker contention median（12操作） |
|---|---:|---:|
| Argon2id 19 MiB / t=2 / p=1 | 195.951 ms | 237.360 ms |
| Argon2id 32 MiB / t=2 / p=1 | 240.489 ms | 583.011 ms |
| Argon2id 64 MiB / t=2 / p=1 | 532.069 ms | 1,038.297 ms |
| PBKDF2-SHA256 600,000 | 247.867 ms | 420.526 ms |
| PBKDF2-SHA256 1,200,000 | 349.241 ms | 758.960 ms |

19 MiB profileはこの環境でPBKDF2 600,000と同程度以下の遅延に収まり、memory-hard KDFへの移行候補として採用した。将来のparameter変更は既存version 2 tupleを上書きせず、新しいversion/profileとして追加する。

## Format contract

- version 1はstorage、KDF、390,000 iterations、salt、nonce、ciphertextの既存tupleだけを受理する。
- version 2はArgon2id、19 MiB、2 iterations、parallelism 1の完全一致だけを受理する。
- bool、負数、過大値、未知field、未知version、未知KDFはkey derivation前に拒否する。
- version 2はvault/sidecar storage、version、sidecar kindをAES-GCM additional authenticated dataへ束縛する。
- 新規暗号化はversion 2、既存version 1の通常保存はversion 1を維持する。読込みによる移行は行わない。

## Migration and recovery contract

1. CLIだけが明示的なupgrade/resume/rollbackを公開する。GUI/MCPへmigration toolを追加しない。
2. vaultと存在するconsent/audit sidecarを先に完全読込みし、形式・size・passphrase・内容を検証する。
3. 全targetをversion 2へ再暗号化し、vaultとsidecarを独立に再復号・構造検証してから原本へ触れる。
4. owner-only journalを作り、各原本の暗号化済みbackupと検証済みnext fileをowner-only storageへ書く。legacy plaintext sidecarのbackupもcurrent profileで独立に暗号化し、平文をrecovery fileへ複製しない。
5. 各targetを既存のfd起点atomic replaceで置換し、hashを再確認する。multi-file全体はglobal atomic transactionとは表現しない。
6. crashやwrite/fsync/replace失敗後はjournalを残し、通常のvault・consent・audit writeを拒否する。
7. resumeはcurrent/original/target hashを照合して未適用memberだけを進める。rollbackはbackupを復号可能なpassphraseで確認して全memberをversion 1へ戻す。
8. 完了後にstaging、backup、journalの順で消去する。外部backup、sync replica、snapshot、manual copyは対象外とする。
9. 完了後のresume/upgradeとrollback完了後のrollbackは、passphrase・全member・profileを再検証して変更なしの状態を返す。異なるprofileや誤ったpassphraseを成功扱いしない。
10. lock順序はKDF migration guardを先、consent/audit固有lockを後に固定し、writerとmigrationの相互待ちを防ぐ。

## 検証範囲

- encrypted extraのsupport floorは`cryptography>=50.0.0`とし、package metadataとinstalled-artifact testでexact lower boundを検証する
- fixed version 1 compatibility and profile-preserving ordinary writes
- version 2 round-trip and strict parameter rejection before KDF work
- vault、consent、auditの明示移行
- preparing段階とpartial replace後のresume/rollback
- write、fsync、replace失敗後のresume/rollbackと完了後の冪等な再実行
- malformed、oversize、wrong-passphrase、unsupported parameterの移行前拒否
- incomplete journal中のCLI/GUI/MCP共通write境界
- passphrase、raw値、token、local pathを公開error/auditへ混入させないこと
- `cryptography==50.0.0`を明示導入したencrypted extraのinstalled-artifact testとPython 3.11-3.13 CI
