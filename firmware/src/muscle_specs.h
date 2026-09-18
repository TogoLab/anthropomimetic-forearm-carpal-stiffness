#ifndef _MUSCLE_SPECS_H_
#define _MUSCLE_SPECS_H_

#include <Arduino.h>
#include "config.h"

// 筋（サーボ）ごとの静的属性を単一テーブルに集約。
// 行順は MuscleID / muscles[] と一致させる。
struct MuscleSpec {
    uint16_t currentLimit;
    int32_t  forwardLimit;
    int32_t  backwardLimit;
    int32_t  lowContraction;
    int32_t  highContraction;
    int32_t  highContractionFinger;
    int32_t  initialPos;
    int32_t  graspPos;
};

extern const MuscleSpec muscle_specs[SERVO_NUM];

#endif //_MUSCLE_SPECS_H_
