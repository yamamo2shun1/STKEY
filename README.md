# STKEY

C4NDY STK をベースにした、ジョイスティック付きキーボードの新プロジェクト。

## コンセプト

- キー配列は STK と同じ横10列 × 縦4行のオーソリニア
- ジョイスティックをメイン基板から分離し、親指の自然な向きに合わせて、手前＋中央方向へ傾けて設置する
- 中央にロータリーエンコーダーを 2×2 ブロックで4個搭載
- USB HID + MIDI の複合デバイス（オーディオ機能は搭載しない）
- MCU は STM32G491、ファームウェアは TinyUSB ベース。キーマップの書き換えは Confiseur で行う想定

## ドキュメント

- [仕様整理 v0.1](docs/spec-v0.1.md) — 決定事項と未決定事項の集約
- [回路設計スタートメモ](docs/circuit-design-start.md) — 現行STKのピン割り当てと新仕様での設計開始点

## ベースプロジェクト

- [C4NDY](https://github.com/yamamo2shun1/C4NDY) — STK / KeyVLM（STM32G491 + TinyUSB、USB Audio + HID）
