# 部品表（BOM）

3Dプリント部品は本リポジトリの `stl/` に印刷用データを収録しています。購入部品と、印刷に必要な材料のみを以下に示します。

## ロボット前腕本体

| 部品 | 仕様・備考 | 数量 |
| --- | --- | ---: |
| サーボモータ（筋アクチュエータ） | Dynamixel XL330-M288-T, Robotis；半径12 mmプーリ | 22 |
| 靭帯 | 鎖編みポリエチレン（PE）ワイヤ φ0.23 mm | - |
| 腱 | ポリエチレン（PE）ワイヤ φ0.3 mm | - |
| 腱鞘 | PTFEチューブ 外径2 mm | - |
| 指先 表層（皮膚相当） | Shore E30シリコーン、厚さ1 mm（ヤング率22.1 kPa） | - |
| 指先 内層（皮下組織相当） | 発泡シリコーン | - |

## 3Dプリント部品と造形材料

印刷用データは `stl/`（STL）および `cad/`（STEP、F3D）を参照してください。

| 部品群 | 造形法・材料 | データ |
| --- | --- | --- |
| 骨（手根骨・中手骨・指節骨・橈骨・尺骨）、爪 | 光造形（SLA）／White Resin, Formlabs | `stl/bone_*.stl` |
| 三角線維軟骨（TFCC） | 熱溶解積層（FDM）／TPU | `stl/soft_tissue_tfcc.stl` |
| ベースプレート・モータタワー | 熱溶解積層（FDM）／PolyLite ASA, Polymaker | `stl/tower_*.stl` |
| 組立治具（靭帯長・手根骨） | 熱溶解積層（FDM）／PolyLite ASA, Polymaker | `stl/jig_*.stl` |
| 実験治具（上腕固定・手部固定・フォースゲージ） | 熱溶解積層（FDM）／PolyLite ASA, Polymaker | `stl/exp_*.stl` |

## 制御系

| 部品 | 仕様・備考 | 数量 |
| --- | --- | ---: |
| マイコンボード | Teensy 4.1（SDIOとI/O数のため必須） | 1 |
| Dynamixel通信インタフェース基板 | TTL2DXIF（BTE094B）, ベストテクノロジー；TTL／RS-485変換。Teensy側はSerial2（ピン7–8）、方向制御ピン2 | 1 |
| microSDカード | 32 GB（Teensy 4.1内蔵SDIOを使用） | 1 |
| DC-DCコンバータ（5 V電源） | AE-MYMGK00506ERSR-5V0（MYMGK00506ERSR使用 5V出力 最大6A 大電流DCDCコンバーターモジュールキット）, 秋月電子通商。XL330-M288-Tの駆動電源。組立キット | 4 |