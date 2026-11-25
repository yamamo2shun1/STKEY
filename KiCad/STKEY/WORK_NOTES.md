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
| MCU.kicad_sch | C4NDY_mainboard の C4NDY.kicad_sch | **編集済み（2026-11-25）**: 下記参照 |

## MCU シート編集結果（2026-11-25、tools/sch_audit.py で検証済み）

- 削除: U4 TPS2116、J9 外部電源コネクタ、J1 QSPI 引き出しコネクタ、QSPI ラベル 12 個
- グローバルラベル化＋改名: SAI_BCLK→ENC1_A(PB3)、SAI_MCLK→ENC1_B(PB4)、SAI_DOUT→ENC2_A(PB5)、SAI_LRCLK→ENC2_B(PB6)、I2C_SDA→ENC3_A(PA8)、I2C_SCL→ENC3_B(PA9)、SAI_DIN→ENC4_A(PA10)、ADC1_IN2→ENC4_B(PA1=旧ポット)
- グローバルラベル化（改名）: UART_RX→PA15、UART_TX→PA2、ADC3_IN5→PB13、SPI_SCK→PF1、SPI_MISO→PB14、SPI_MOSI→PB15
- グローバルラベル化（同名）: ADC2_IN1(PA0)、ADC2_IN12(PB2)、ADC2_IN13(PA5)、ADC2_IN17(PA4) = スティック ADC
- 新設: スキャン 5 ピン（PC13=164_CLK、PC14=164_A、PC15=165_CLK、PB7=165_SL、PB9=165_QH）は現行メインボード回路図で no_connect だったため、no_connect を外しスタブ配線＋グローバルラベルを追加
- 残置（GUI 整理時に判断）: J2/J3/J5/J6 コネクタシンボルとその先のスタブ（ネットはグローバル化済みなので電気的には無害）、QSPI ピンのスタブ配線
- 監査で確定した実配線（.ioc の要約と一部相違）: スティックは RV2: X=PB2 / Y=PA0、RV3: X=PA4 / Y=PA5。ポットは PA1。USER_SW=PB10(SW2)、LED0=PB12
- 相違の理由（ユーザー説明 2026-11-25）: **STK が使っているメインボードは 1 つ前のリビジョン**で、リポジトリのメインボード回路図は最新リビジョン（TPS2116 等の外部電源まわりはこちらで追加された）。スキャンピンの未接続やネット名の対応のずれはこのリビジョン差による。STKEY は新規の一体基板なので、キーボード基板側の信号の行き先を正としてピン割り当てを自己完結させている

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
