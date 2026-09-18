#include "muscle_specs.h"
#include "DXLSetup.h"

// MuscleID 順。各行が筋1本の静的属性を保持する。
//   currentLimit:          既定の電流リミット（mA 相当の raw 値）
//   forwardLimit:          緊張方向の位置上限
//   backwardLimit:         弛緩方向の位置下限
//   lowContraction:        低収縮姿勢目標
//   highContraction:       高収縮姿勢目標
//   highContractionFinger: 指を付けた高収縮姿勢目標
//   initialPos:            初期姿勢
//   graspPos:              把持姿勢
const MuscleSpec muscle_specs[SERVO_NUM] = {
    // IndexFDP
    { MAX_FLEX_CURRENT,     5084, 1550,  200,  200, 3572,  400, 1690 },
    // MiddleFDP
    { MAX_FLEX_CURRENT,     5852, 2120,  200,  200, 4524,  400, 2827 },
    // RingFDP
    { MAX_FLEX_CURRENT,     5013, 1160,  200,  200, 2424,  400, 1350 },
    // PinkyFDP
    { MAX_FLEX_CURRENT,     4840, 1380,  200,  200, 3345,  400,  941 },
    // FPL
    { MAX_FLEX_CURRENT,     4700, 2660,  200,  200,  400,  400,  731 },
    // APM
    { MAX_FLEX_CURRENT,     3000, 1080,  200,  200,  400,  400,  752 },
    // OPM
    { MAX_FLEX_CURRENT,     2000,    0,  200,  200,  400,  208,    0 },
    // APB
    { MAX_FLEX_CURRENT,     5500,    0,  500,  200,  400,  400, 5064 },
    // EIP
    { MAX_EXTENS_CURRENT,   6100,    0,  500,  200, 1788,  400,  820 },
    // EDM
    { MAX_EXTENS_CURRENT,   3000,   36,  200,  200, 3690, 3690, 2570 },
    // ED
    { MAX_EXTENS_ED_CURRENT,2800, 1628,  200,  200, 2524, 2081, 2769 },
    // EPB
    { MAX_EXTENS_CURRENT,   3000,  202,  200,  200,  200,  400, 2590 },
    // EPL
    { MAX_EXTENS_CURRENT,   2500,  100,  200,  200,  200, 2014, 1433 },
    // APL
    { MAX_EXTENS_CURRENT,   5310,  100,  200,  200, 3759, 4043, 1730 },
    // FCR
    { CARPAL_CURRENT,       4000,  100,  200,  200, 1360, 4362, 1063 },
    // FCU
    { CARPAL_CURRENT,       2700,  700,  400, 4784, 1496, 4784,  777 },
    // ECRL
    { CARPAL_CURRENT,       2700,  850,  400, 1896, 1644, 1896,  643 },
    // ECU
    { CARPAL_CURRENT,       2700, 1200, 1700, 1182, 1926, 1182, 2088 },
    // SPN
    { SP_CURRENT,           2710, 1770, 1700,  308, 2926,  308, 1923 },
    // BPB
    { SP_CURRENT,            240,    0,  243, 1800, 1591, 1800,  251 },
    // PQ
    { PR_CURRENT,           1700,    0, 1632, 1591, 1500, 1627, 1625 },
    // PT
    { PR_CURRENT,           1500,    0, 1453, 1500,    0, 1250, 1072 },
};
