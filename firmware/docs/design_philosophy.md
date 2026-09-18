# 設計思想: 手首優位の協調筋制御による把持

## 課題

センサレスロボットハンドで物体を把持するため、完全に指を屈曲させ握りこぶしを作った状態のサーボ角度位置を目標角度とし、物体を把持させる方法を取っている。握りこぶしの状態では指伸筋腱が伸びきった状態で固定される。物体を把持した状態では指関節角度が小さくなり、指伸筋腱が完全に緩み、背屈ができない状態になる。手首が物理的に固定されているロボットアームではこのような問題は起こらない。

解決策としては、腱にバネなどの弾性体を繋げ張力を一定に保つ方法、屈曲側と伸筋側のサーボ回転角度を把持物体に合わせて調節する方法などがある。

## 解決方法

本研究では、機械的アプローチを取らず、**筋肉同士の協調動作**をソフトウェアで実装する。手首を優位として、指の筋肉を連動させる。

- 緊張する指の筋はトルクが能動的に与えられる（トルク制御）
- 弛緩する筋は低トルク（電流位置制御モード）
- 把持時、伸筋側は受動的な腱の伸長が起こると仮定
- 緊張する筋 → トルク制御、弛緩する筋 → 電流位置制御

## 協調ルール

### 手首筋から指筋への伝播（直接協調）

| 手首筋が緊張 | 協調して駆動される指筋 |
|---|---|
| FCR（橈側手根屈筋） | IndexFDP + FPL |
| FCU（尺側手根屈筋） | PinkyFDP |
| ECRL（長橈側手根伸筋） | EIP |
| ECU（尺側手根伸筋） | EDM |

これがコードの `setWristCoopFlags` に対応する。

### 伸筋ノード（背屈時のみ緊張）

```
EIP AND EDM が緊張 → ED + FPL もトルク制御で緊張
```

FPL（長母指屈筋）が背屈時の指伸筋群と協調するのは、指背屈時に母指を屈曲させて指の背側に母指を重ねる動作（握り拳を作る際の自然な母指位置）のため。

### 屈筋ノード（掌屈時のみ緊張）

```
IndexFDP AND PinkyFDP が緊張 → MiddleFDP + RingFDP もトルク制御で緊張
```

示指と小指の深指屈筋が両方緊張したとき、中指と薬指の屈筋も波及的に緊張する。

これがコードの `propagateCoopFlags` に対応する。

## コード実装

- `setWristCoopFlags(ID, flags)`: 手首筋 ID が与えられたとき対応する指筋フラグを立てる
- `applyGraspCurrent(ID)`: 協調フラグが立っていない筋に、筋種別の目標電流を割り当て
- `propagateCoopFlags(flags)`: 伸筋・屈筋ノードの AND 論理で MiddleFDP/RingFDP/ED/FPL に伝播
- `graspMotion` (`coopGraspMotion`): 上記を束ねて制御モードを決定

## 目標電流一覧（`DXLSetup.h`）

| 定数 | 値 | 用途 |
|---|---|---|
| `MAX_FLEX_CURRENT` | 20 | 4指深指屈筋の把持電流 |
| `THUMB_FLEX_CURRENT` | 30 | FPL（長母指屈筋）の把持電流。4指に対向するため少し高め |
| `MAX_EXTENS_CURRENT` | 20 | 指伸筋の把持電流 |
| `MAX_EXTENS_ED_CURRENT` | 40 | 総指伸筋 ED の CurrentLimit |
| `MIN_CURRENT` | 30 | 弛緩時の最小電流 |
| `GENERAL_CURRENT` | 100 | 母指系（APM/APB/OPM/EPB/EPL/APL）の位置制御電流 |
| `CARPAL_CURRENT` | 200 | 手首筋 FCR/FCU/ECRL/ECU の位置制御電流 |
| `SP_CURRENT` | 150 | BPB/PT |
| `PR_CURRENT` | 200 | PQ |
| `TEACHING_FINGER_CURRENT` | 30 | 教示モードの指の目標電流 |
| `TEACHING_WRIST_CURRENT` | 60 | 教示モードの手首関節の目標電流 |
| `TEACHING_FOREARM_CURRENT` | 60 | 教示モードの前腕関節の目標電流 |

## 再生フロー

1. 現在の各サーボ回転角度を取得
2. 目標回転角度を取得
3. 角度差からサーボ回転速度を算出
4. 緊張する筋の種類から制御手法決定（`coopGraspMotion` / `relaxMotion`）
5. サーボを回転
6. 100Hz 間隔で電流トルクを徐々に上昇（`sweepRunGoalPosition` 内のランプ）

## 参考: 手首動作別の協調パターン（PlantUML 図は別途）

- **背屈**: ECRL/ECU 緊張、FCR/FCU 弛緩。伸筋ノード発火 → ED + FPL 緊張
- **掌屈**: FCR/FCU 緊張、ECRL/ECU 弛緩。屈筋ノード発火 → Middle/Ring 緊張
- **撓屈**: ECRL/FCR 緊張、ECU/FCU 弛緩。FCR → FPL + IndexFDP、ECRL → EIP
