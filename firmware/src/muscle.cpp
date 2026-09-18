#include "muscle.h"

void Muscle::changeVerocity(uint32_t profile_v){
    dxl.writeControlTableItem(ControlTableItem::PROFILE_VELOCITY, motorId, profile_v);
}

void Muscle::moveToWithDuration(float pos_e, uint16_t time, bool sync){
    checkPosition();
    int32_t angle = pos_e - position;
    uint32_t v = abs(angle / time / VELOCITY_UNIT_SCALE);
    uint32_t ret = pos_e;

    changeVerocity(v);
    dxl.write(motorId, GOAL_POSITION_ADDR, (uint8_t*)&ret, GOAL_POSITION_ADDR_LEN, TIMEOUT);
    if (sync) delay(time * 1000);
}

void Muscle::checkCurrent(){
    current = dxl.getPresentCurrent(motorId, UNIT_MILLI_AMPERE);
}

void Muscle::checkPosition(){
    position = dxl.getPresentPosition(motorId, UNIT_RAW);
}

Muscle
  IndexFDP,   // 1:示指屈筋
  MiddleFDP,  // 2:中指深指屈筋
  RingFDP,    // 4:薬指屈筋
  PinkyFDP,   // 5:小指屈筋
  FPL,        // 6:長母指屈筋
  APM,        // 7:母指内転筋
  OPM,        // 8:母指対立筋
  APB,        // 9:短母指外転筋
  EIP,        // 10:示指伸筋
  EDM,        // 11:小指伸筋
  ED,         // 12:総指伸筋
  EPB,        // 13:短母指伸筋
  EPL,        // 14:長母指伸筋
  APL;        // 15:長母指外転筋

Muscle
  FCR,        // 16:橈側手根屈筋
  FCU,        // 17:尺側手根屈筋
  ECRL,       // 18:長橈側手根伸筋
  ECU;        // 19:尺側手根伸筋

Muscle
  SPN,        // 20:回外筋
  BPB,        // 21:上腕二頭筋
  PT,         // 22:円回内筋
  PQ;         // 23:方形回内筋

Muscle *fingers[14] = {
  &IndexFDP,   // 1:示指屈筋
  &MiddleFDP,  // 2:中指深指屈筋
  &RingFDP,    // 3:薬指屈筋
  &PinkyFDP,   // 4:小指屈筋
  &FPL,        // 5:長母指屈筋
  &APM,        // 6:母指内転筋
  &OPM,        // 7:母指対立筋
  &APB,        // 8:短母指外転筋
  &EIP,        // 9:示指伸筋
  &EDM,        // 10:小指伸筋
  &ED,         // 11:総指伸筋
  &EPB,        // 12:短母指伸筋
  &EPL,        // 13:長母指伸筋
  &APL        // 14:長母指外転筋
};
Muscle *wrists[4] = {
  &FCR,        // 16:橈側手根屈筋
  &FCU,        // 17:尺側手根屈筋
  &ECRL,       // 18:長橈側手根伸筋
  &ECU        // 19:尺側手根伸筋
};
Muscle *forearms[4] = {
  &SPN,        // 20:回外筋
  &BPB,        // 21:上腕二頭筋
  &PT,         // 22:円回内筋
  &PQ          // 23:方形回内筋
};

Muscle *muscles[SERVO_NUM] = {
  &IndexFDP,   // 1:示指屈筋
  &MiddleFDP,  // 2:中指深指屈筋
  &RingFDP,    // 3:薬指屈筋
  &PinkyFDP,   // 4:小指屈筋
  &FPL,        // 5:長母指屈筋
  &APM,        // 6:母指内転筋
  &OPM,        // 7:母指対立筋
  &APB,        // 8:短母指外転筋
  &EIP,        // 9:示指伸筋
  &EDM,        // 10:小指伸筋
  &ED,         // 11:総指伸筋
  &EPB,        // 12:短母指伸筋
  &EPL,        // 13:長母指伸筋
  &APL,        // 14:長母指外転筋
  &FCR,        // 15:橈側手根屈筋
  &FCU,        // 16:尺側手根屈筋
  &ECRL,       // 17:長橈側手根伸筋
  &ECU,        // 18:尺側手根伸筋
  &SPN,        // 19:回外筋
  &BPB,        // 20:上腕二頭筋
  &PT,         // 21:円回内筋
  &PQ         // 22:方形回内筋
};

void setMotorID(){
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
        muscles[i]->setId(i);
        muscles[i]->bindSpec(&muscle_specs[i]);
    }

    SPN.setEndlessWinding(true);
    PQ.setEndlessWinding(true);
}

void initCurrentLimit(){
    for (uint8_t i = 0; i < SERVO_NUM; i++) {
        muscles[i]->resetCurrentLimit();
    }
}

void fillInitialPositions(int32_t *out){
    for (uint8_t i = 0; i < SERVO_NUM; i++) out[i] = muscle_specs[i].initialPos;
}

void fillLowContractionPos(int32_t *out){
    for (uint8_t i = 0; i < SERVO_NUM; i++) out[i] = muscle_specs[i].lowContraction;
}

void fillHighContractionPos(int32_t *out){
    for (uint8_t i = 0; i < SERVO_NUM; i++) out[i] = muscle_specs[i].highContraction;
}

void fillHighContractionFingerPos(int32_t *out){
    for (uint8_t i = 0; i < SERVO_NUM; i++) out[i] = muscle_specs[i].highContractionFinger;
}

void fillGraspPositions(int32_t *out){
    for (uint8_t i = 0; i < SERVO_NUM; i++) out[i] = muscle_specs[i].graspPos;
}
