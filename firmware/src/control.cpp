#include "control.h"

// Dynamixelモーターのモード設定関数
void dxlModeSetup(uint8_t mode){
    // Turn off torque when configuring items in EEPROM area
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
        dxl.torqueOff(i);
    }
    // Set Operating Mode
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
        sw_op_mode.data[i].mode = mode;
    }
    sw_op_mode.markChanged();
    sw_op_mode.write("Operating Mode");
}

void initGoalCurrent(int8_t *torque_control_flags){
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
        if (torque_control_flags[i] != 0)
        {
            sw_current_velocity.data[i].goal_current = 0;
            sw_current_velocity.data[i].goal_velocity = 0;
        }
        // sw_position.data[i].goal_position = 0;
    }
    sw_current_velocity.markChanged();
}

void computeEAngles(int32_t *e_angles, const int32_t *goal_row){
    for (uint8_t ID = 0; ID < SERVO_NUM; ID++)
    {
        e_angles[ID] = goal_row[ID] - muscles[ID]->getPosition();
    }
}

static void captureAndTorqueOn(int32_t *now_angle){
    for (uint8_t i = 0; i < SERVO_NUM; i++) now_angle[i] = muscles[i]->getPosition();
    for (uint8_t i = 0; i < SERVO_NUM; i++) dxl.torqueOn(i);
}

// flag > 0: モーター正転で筋を緊張させる。
// muscles[i]->getForwardLimit() は緊張方向の位置上限。
static void rampTension(uint8_t i, float chunk, float cnt){
    if (muscles[i]->getPosition() > muscles[i]->getForwardLimit()){
        dxl.torqueOff(i);
        return;
    }
    const uint16_t lim = muscles[i]->getCurrentLimit();
    if (muscles[i]->getCurrent() < lim
        && sw_current_velocity.data[i].goal_current < lim){
        sw_current_velocity.data[i].goal_current += lim * chunk * cnt;
    } else {
        sw_current_velocity.data[i].goal_current = lim;
    }
}

// flag < 0: モーター逆転で筋を弛緩させる。
// muscles[i]->getBackwardLimit() は弛緩方向の位置下限。
// Goal Current(102) は符号付き int16_t で負値が逆転を生む。Current Limit(38) は
// 符号なし uint16_t の magnitude で |goal_current| <= current_limit。
// directionTest(Motor 3, DriveMode bit0=0 Normal) により，+電流=正転/位置増，
// −電流=逆転/位置減 を実機確認済。したがって弛緩には負値を書き込む必要がある。
// 前提: 本ループが扱う各サーボの DriveMode bit0 = Normal であること。
// Reverse に設定されたサーボが混在する場合、当該サーボのみ弛緩方向が反転する。
static void rampRelaxation(uint8_t i, float chunk, float cnt){
    if (muscles[i]->getPosition() < muscles[i]->getBackwardLimit()){
        dxl.torqueOff(i);
        return;
    }
    const uint16_t lim = muscles[i]->getCurrentLimit();
    const int16_t target = -static_cast<int16_t>(lim);
    if (muscles[i]->getCurrent() > target
        && sw_current_velocity.data[i].goal_current > target){
        sw_current_velocity.data[i].goal_current -= lim * chunk * cnt;
    } else {
        sw_current_velocity.data[i].goal_current = target;
    }
}

// 位置制御の場合は目標位置を徐々に上昇させる
static void rampPosition(uint8_t i, const int32_t *goal_pos, const int32_t *e_angles,
                         const int32_t *now_angle, float chunk, float cnt){
    if (e_angles[i] > 0 && sw_position.data[i].goal_position < goal_pos[i]){
        sw_position.data[i].goal_position = float(now_angle[i]) + (float(e_angles[i]) * chunk * float(cnt));
    } else if (e_angles[i] <= 0 && sw_position.data[i].goal_position > goal_pos[i]){
        sw_position.data[i].goal_position = float(now_angle[i]) + (float(e_angles[i]) * chunk * float(cnt) * 1.5);
    } else {
        sw_position.data[i].goal_position = goal_pos[i];
    }
}

bool sweepRunGoalPosition(const int32_t *goal_pos, int32_t *e_angles, int8_t *torque_control_flags, uint16_t time, uint32_t start) {
    int32_t now_angle[SERVO_NUM] = {};
    captureAndTorqueOn(now_angle);

    const float sampling_period = READ_PERIOD;
    const float period_offset = 40.0;
    // 電流値をスイープさせるためのチャンクサイズ
    const float chunk = (sampling_period + period_offset) / (time * 1000);
    float cnt = 1.0;

    currentAndPositionCheck();
    initGoalCurrent(torque_control_flags);
    while (time * 1000 > (millis() - start)){
        for (uint8_t i = 0; i < SERVO_NUM; i++){
            if      (torque_control_flags[i] > 0) rampTension(i, chunk, cnt);
            else if (torque_control_flags[i] < 0) rampRelaxation(i, chunk, cnt);
            else                                  rampPosition(i, goal_pos, e_angles, now_angle, chunk, cnt);
        }
        sw_position.markChanged();
        sw_current_velocity.markChanged();
        if (!sw_position.write("Position")) return false;
        sw_current_velocity.write("Current and Velocity");
        cnt++;
        delay(sampling_period);
        currentAndPositionCheck();
        DEBUG_SERIAL.println(getCurrentAndPositionArray(start));
    }
    return true;
}

/**
 * @brief
 *
 * @param start 開始時刻
 */
String getCurrentAndPositionArray(uint32_t start){
    String sendStringData = "";
    unsigned long time = millis();
    sendStringData += String(time - start) + ",";
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
        sendStringData += String(muscles[i]->getCurrent()) + "," + String(muscles[i]->getPosition()) + ",";
    }
    return sendStringData;
}


/**
 * @brief 電流と角度を定期実行する関数
 *
 */
void currentAndPositionCheck (){
    for (uint8_t i=0; i < SERVO_NUM; i++){
        muscles[i]->checkCurrent();
    }
    for (uint8_t i=0; i < SERVO_NUM; i++){
        muscles[i]->checkPosition();
    }
}

void torqueOnExceptEndless(bool useEndlessMecha){
    for (uint8_t i = 0; i < SERVO_NUM; i++){
        if (!useEndlessMecha && muscles[i]->isEndlessWinding()) continue;
        dxl.torqueOn(i);
    }
}

void servoStop(){
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
        dxl.torqueOff(i);
    }
}

bool fix(){
      dxlModeSetup(OP_CURRENT);
      torqueOnExceptEndless(false);
      for (uint8_t i = 0; i < SERVO_NUM; i++)
      {
        sw_current_velocity.data[i].goal_current = 20;
      }
      sw_current_velocity.markChanged();
      return sw_current_velocity.write("Current and Velocity");
}
