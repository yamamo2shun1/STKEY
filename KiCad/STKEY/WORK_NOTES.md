# STKEY KiCad 作業メモ

開始: 2026-11-25（ブランチ `muse/kicad-schematic-v1`）
設計の正: `docs/circuit-design-v1.md`（main マージ済み）

## プロジェクト構成（雛形を作成済み）

C4NDY の KVL_STK プロジェクトをコピーして改名したもの。

| ファイル | 由来 | 状態 |
|---|---|---|
| STKEY.kicad_pro | KVL_STK.kicad_pro | 改名のみ |
| STKEY.kicad_sch（ルート） | KVL_STK.kicad_sch | キーマトリクスそのまま。MCU シートのブロックを追加済み（ピンなし） |
| ICs.kicad_sch | KVL_STK ICs シート | 未編集（次段階で編集） |
| LEDs.kicad_sch | KVL_STK LEDs シート | そのまま使う（編集不要の見込み） |
| MCU.kicad_sch | C4NDY_mainboard の C4NDY.kicad_sch | 未編集（次段階で編集） |

## 接続方式の調査結果（2026-11-25）

- KVL_STK 側のシート間接続は **グローバルラベル**（Q0〜Q7、PA15 等）と、ICs シート内のローカルラベル（164_A / 165_SL / POT0 / SCL / SDA / BCLK 等。モジュールフットプリントのピンに接続）
- メインボード側は全てローカルラベル（SAI_*、QSPI_*、I2C_*、ADC*_IN* 等）
- 統合方針: 両シートの受け渡しネットを **グローバルラベルに統一** して接続する

## 次段階の編集内容

### MCU シート
1. TPS2116、外部電源入力コネクタ、QSPI 引き出しコネクタを削除
2. 旧コネクタ向けスタブのうち再利用するものを改名: SAI 系 5 本＋ I2C 系 2 本＋ POT0 の配線を ENC1〜4 の A/B としてグローバルラベル化（ピン対応は設計書の割り当て表どおり: PB3/PB4/PB5/PB6/PA8/PA9/PB0/PB1。PB0/PB1 は旧 QSPI 側）
3. スキャン系（165_SL / 165_QH / 165_CLK / 164_CLK / 164_A）、PA15、スティック ADC 4 本、USER_SW / USER_LED / LP_LED をグローバルラベル化
4. QSPI の MCU ピン（PA3 / PA6 / PA7 / PB11）は NC として残す

### ICs シート
1. ADAU1761 と周辺受動部品、オーディオジャック ×2、RV1 ポット、RV2/RV3 スティック、C4NDY モジュール受け、MIC2005A を削除
2. ローカルラベルをグローバルラベルに変換（MCU シートと対になるもの）
3. PEC11R-4220F-S0024 ×4 を追加（A/B はグローバルラベル ENC*、押し込みは新規 74HC165 の入力へ）。KiCad 標準に PEC11R のシンボル／フットプリントがなければ My_Parts 側に作成が必要
4. 74HC165 を 1 個追加し、スキャンチェーンを延長（QH→SI のカスケードを組み替え）
5. スティックコネクタ ×2（4 ピン: 3.3V / GND / X / Y）を追加し、ADC グローバルラベルへ

## 制約

- Muse の環境では KiCad を実行できないため、編集は .kicad_sch のテキスト操作で行う。**各段階のあとに KiCad で開いて表示と ERC を確認してもらう必要がある**（JUMBLEQ rev.D と同じ制約）
- 編集後はテキストベースのネット監査（ラベル一覧の突き合わせ）で受け渡しネットの対応を検証する
