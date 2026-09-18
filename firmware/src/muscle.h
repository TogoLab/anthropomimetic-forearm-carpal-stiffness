#ifndef _MUSCLE_H_
#define _MUSCLE_H_
#include "config.h"
#include "DXLSetup.h"
#include "muscle_specs.h"

enum class MuscleID{
    IndexFDP,   // 1:示指屈筋
    MiddleFDP,  // 2:中指深指屈筋
    RingFDP,    // 3:薬指屈筋
    PinkyFDP,   // 4:小指屈筋
    FPL,        // 5:長母指屈筋
    APM,        // 6:母指内転筋
    OPM,        // 7:母指対立筋
    APB,        // 8:短母指外転筋
    EIP,        // 9:示指伸筋
    EDM,        // 10:小指伸筋
    ED,         // 11:総指伸筋
    EPB,        // 12:短母指伸筋
    EPL,        // 13:長母指伸筋
    APL,        // 14:長母指外転筋
    FCR,        // 15:橈側手根屈筋
    FCU,        // 16:尺側手根屈筋
    ECRL,       // 17:長橈側手根伸筋
    ECU,        // 18:尺側手根伸筋
    SPN,        // 19:回外筋 // 無限巻取り機構
    BPB,        // 20:上腕二頭筋
    PQ,         // 21:方形回内筋 // 無限巻取り機構
    PT,         // 22:円回内筋
};

class Muscle
{
protected:
    uint8_t motorId;
    int16_t current = 0;
    int32_t position = 0;
    uint16_t currentLimit = 0;
    bool endlessWinding = false;
    const MuscleSpec *spec = nullptr;

    void changeVerocity(uint32_t profile_v);

public:
    void moveToWithDuration(float pos_e, uint16_t time, bool sync);
    void checkCurrent();
    void checkPosition();

    void bindSpec(const MuscleSpec *s) { spec = s; currentLimit = s->currentLimit; }
    void resetCurrentLimit() { if (spec) currentLimit = spec->currentLimit; }
    void setCurrentLimit(uint16_t limit) { currentLimit = limit; }
    void setPosition(float recv_position) { position = recv_position; }
    void setId(uint8_t id) { motorId = id; }
    void setEndlessWinding(bool v) { endlessWinding = v; }
    float getCurrent() { return current; }
    uint16_t getCurrentLimit() { return currentLimit; }
    int32_t getPosition() { return position; }
    uint8_t getId() { return motorId; }
    bool isEndlessWinding() { return endlessWinding; }

    int32_t getForwardLimit()             const { return spec->forwardLimit; }
    int32_t getBackwardLimit()            const { return spec->backwardLimit; }
    int32_t getLowContractionPos()        const { return spec->lowContraction; }
    int32_t getHighContractionPos()       const { return spec->highContraction; }
    int32_t getHighContractionFingerPos() const { return spec->highContractionFinger; }
    int32_t getInitialPos()               const { return spec->initialPos; }
    int32_t getGraspPos()                 const { return spec->graspPos; }
};

extern Muscle IndexFDP, MiddleFDP, RingFDP, PinkyFDP, FPL, APM, OPM, APB,
              EIP, EDM, ED, EPB, EPL, APL;

extern Muscle FCR, FCU, ECRL, ECU;
extern Muscle SPN, BPB, PT, PQ;

// カテゴリ別の走査用ポインタ配列。中身の型差はなく走査ターゲットを限定するだけ。
extern Muscle *fingers[14];
extern Muscle *wrists[4];
extern Muscle *forearms[4];
extern Muscle *muscles[SERVO_NUM];

void setMotorID();
void initCurrentLimit();

// MuscleSpec から SERVO_NUM 長の配列を埋める補助。
void fillInitialPositions(int32_t *out);
void fillLowContractionPos(int32_t *out);
void fillHighContractionPos(int32_t *out);
void fillHighContractionFingerPos(int32_t *out);
void fillGraspPositions(int32_t *out);

#endif //_MUSCLE_H_
