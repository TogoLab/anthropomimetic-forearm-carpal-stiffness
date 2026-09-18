#ifndef _COOP_GRAPH_H_
#define _COOP_GRAPH_H_

#include <Arduino.h>

// docs/design_philosophy.md の協調筋グラフに対応するヘルパ群。
// coopGraspMotion から呼ばれ、ID ごとの目標電流設定と
// 協調フラグの伝搬を担う。

// 手首筋が駆動されるとき、協調する指筋にもフラグを立てる。
void setWristCoopFlags(uint8_t ID, int8_t *flags);

// 単独駆動時の既定把持電流を筋ごとに割り当てる。
void applyGraspCurrent(uint8_t ID);

// 協調フラグの推移的拡張:
//   伸筋: EIP && EDM → ED + FPL をトルク制御
//   屈筋: IndexFDP && PinkyFDP → MiddleFDP + RingFDP をトルク制御
void propagateCoopFlags(int8_t *flags);

#endif //_COOP_GRAPH_H_
