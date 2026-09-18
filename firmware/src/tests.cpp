#include "tests.h"
#include "control.h"
#include "motion.h"
#include "muscle.h"

int16_t randomize(bool bias){
    int bias_val = 3;
    int under = 60;
    int upper = 100;
    if (bias)
    {
        under = under * bias_val;
        upper = upper * bias_val;
    }
    int16_t _random_val = random(under + bias_val, upper);
    // DEBUG_SERIAL.println(_random_val);
    return _random_val;

}
// symbol: -1 or 1
void testRandomFE(int8_t symbol, const int32_t *target){
    currentAndPositionCheck();
    if (symbol == 1 || symbol == -1)
    {

        int8_t torque_control_flags[SERVO_NUM] = {};

        torque_control_flags[IndexFDP.getId()] = symbol;
        torque_control_flags[MiddleFDP.getId()] = symbol;
        torque_control_flags[RingFDP.getId()] = symbol;
        torque_control_flags[PinkyFDP.getId()] = symbol;
        torque_control_flags[FPL.getId()] = symbol;
        torque_control_flags[APB.getId()] = -1 * symbol;
        torque_control_flags[EIP.getId()] = -1 * symbol;
        torque_control_flags[EDM.getId()] = -1 * symbol;
        torque_control_flags[ED.getId()] = -1 * symbol;
        torque_control_flags[EPB.getId()] = -1 * symbol;
        torque_control_flags[EPL.getId()] = -1 * symbol;
        torque_control_flags[APL.getId()] = -1 * symbol;
        torque_control_flags[FCR.getId()] = symbol;
        torque_control_flags[FCU.getId()] = symbol;
        torque_control_flags[ECRL.getId()] = -1 * symbol;
        torque_control_flags[ECU.getId()] = -1 * symbol;

        // 電流設定
        for (uint8_t i = 0; i < SERVO_NUM; i++)
        {
            if (torque_control_flags[i] != 0)
            {
                if (i == (uint8_t)MuscleID::ED ||
                    // i == (uint8_t)MuscleID::EDM ||
                    i == (uint8_t)MuscleID::EIP)
                {
                    uint16_t val = randomize(true);
                    DEBUG_SERIAL.print("ED or EDM or EIP: ");
                    DEBUG_SERIAL.println(val);
                    muscles[i]->setCurrentLimit(val);
                }else{
                    muscles[i]->setCurrentLimit(randomize());
                }
            }
        }
        setControlMode(torque_control_flags);
        int32_t e_angles[SERVO_NUM] = {};
        computeEAngles(e_angles, target);
        sweepRunGoalPosition(target, e_angles, torque_control_flags, 6, millis());
    }else{
        DEBUG_SERIAL.print(symbol);
        DEBUG_SERIAL.println("WRONG SYMBOL. Please input -1 or 1");
    }
    DEBUG_SERIAL.println("Finish FE random test");

}

void testRandomRU(int8_t symbol, const int32_t *target){
    currentAndPositionCheck();
    if (symbol == 1 || symbol == -1)
    {
        int8_t torque_control_flags[SERVO_NUM] = {};

        // torque_control_flags[IndexFDP.getId()] = symbol;
        // torque_control_flags[MiddleFDP.getId()] = symbol;
        // torque_control_flags[MiddleFDS.getId()] = symbol;
        // torque_control_flags[RingFDP.getId()] = symbol;
        // torque_control_flags[PinkyFDP.getId()] = symbol;
        torque_control_flags[APB.getId()] = symbol;
        // torque_control_flags[EIP.getId()] = symbol;
        torque_control_flags[EDM.getId()] = -1 * symbol;
        // torque_control_flags[ED.getId()] = -1 * symbol;
        torque_control_flags[EPB.getId()] = symbol;
        torque_control_flags[EPL.getId()] = -1 * symbol;
        torque_control_flags[APL.getId()] = symbol;
        torque_control_flags[FCR.getId()] = symbol;
        torque_control_flags[FCU.getId()] = -1 * symbol;
        torque_control_flags[ECRL.getId()] = symbol;
        torque_control_flags[ECU.getId()] = -1 * symbol;

        // 電流設定
        for (uint8_t i = 0; i < SERVO_NUM; i++)
        {
            if (torque_control_flags[i] != 0)
            {
                muscles[i]->setCurrentLimit(randomize());
            }
        }
        setControlMode(torque_control_flags);
        int32_t e_angles[SERVO_NUM] = {};
        computeEAngles(e_angles, target);
        sweepRunGoalPosition(target, e_angles, torque_control_flags, 3, millis());
    }else{
        DEBUG_SERIAL.print(symbol);
        DEBUG_SERIAL.println("WRONG SYMBOL. Please input -1 or 1");
    }
}

bool esyncRead(){
    DEBUG_SERIAL.println("esyncからの信号を待ちます");

  while (1)
  {
    if (digitalRead(ESYNC_PIN))
    {
      uint32_t start_time = millis();
      while (1)
      {
        currentAndPositionCheck();
        String result = getCurrentAndPositionArray(start_time) + String(float(analogRead(FORCE_GAGE_PIN))/1023.0*82.5);
        DEBUG_SERIAL.println(result);
      if ((digitalRead(ESYNC_PIN) && (millis() - start_time) > 100) || (millis() - start_time) > 5000)
      {
        DEBUG_SERIAL.println("FINISH");
        return true;
      }
      }
    }
  }

}

static void setWristCurrentLimit20(){
  FCR.setCurrentLimit(20);
  FCU.setCurrentLimit(20);
  ECRL.setCurrentLimit(20);
  ECU.setCurrentLimit(20);
}

static void enableFingerTorqueControl(int8_t* flags){
  flags[IndexFDP.getId()] = 1;
  flags[MiddleFDP.getId()] = 1;
  flags[RingFDP.getId()] = 1;
  flags[PinkyFDP.getId()] = 1;
  flags[EIP.getId()] = 1;
  flags[EDM.getId()] = 1;
  flags[ED.getId()] = 1;
}

bool contractionTest(int mode){
  currentAndPositionCheck();
  // トルク制御するモーターのインデックス
  int8_t torque_control_flags[SERVO_NUM] = {};
  int32_t target[SERVO_NUM] = {};

  switch (mode)
  {
  case 1:
    setWristCurrentLimit20();
    fillLowContractionPos(target);
    break;
  case 2:
    setWristCurrentLimit20();
    fillHighContractionPos(target);
    break;
  case 3:
    setWristCurrentLimit20();
    enableFingerTorqueControl(torque_control_flags);
    fillHighContractionFingerPos(target);
    break;
  case 4:
    enableFingerTorqueControl(torque_control_flags);
    fillHighContractionFingerPos(target);
    break;
  default:
    DEBUG_SERIAL.println("不明なコマンド");
    return false;
  }
  torque_control_flags[FCR.getId()] = 1;
  torque_control_flags[FCU.getId()] = 1;
  torque_control_flags[ECRL.getId()] = 1;
  torque_control_flags[ECU.getId()] = 1;

  setControlMode(torque_control_flags);

  int32_t e_angles[SERVO_NUM] = {};
  computeEAngles(e_angles, target);
  sweepRunGoalPosition(target, e_angles, torque_control_flags, MOVING_TIME, millis());
  delay(1000);
  if(mode == 1 || mode == 4){
    for (uint8_t i = (uint8_t)MuscleID::FCR; i <= (uint8_t)MuscleID::SPN; i++)
    {
      dxl.torqueOff(i);
    }

  }
  return esyncRead();
}

bool fingerDriveTest(uint8_t finger_id){
  currentAndPositionCheck();
  int32_t target[SERVO_NUM] = {};
  fillGraspPositions(target);
  int8_t torque_control_flags[SERVO_NUM] = {};
  int32_t e_angles[SERVO_NUM] = {};
  computeEAngles(e_angles, target);
  sweepRunGoalPosition(target, e_angles, torque_control_flags, MOVING_TIME, millis());
  DEBUG_SERIAL.println("Wait set position");
  delay(1000);

  if (finger_id < 1 || finger_id > 4) {
    DEBUG_SERIAL.println("不明なコマンド");
    return false;
  }
  Muscle* finger = fingers[finger_id - 1];
  finger->setCurrentLimit(60);
  uint8_t motor_id = finger->getId();
  FPL.setCurrentLimit(60);
  APM.setCurrentLimit(20);
  OPM.setCurrentLimit(60);
  APB.setCurrentLimit(60);
  currentAndPositionCheck();

  // 目標位置を設定
  target[motor_id]      = finger->getForwardLimit();
  target[EIP.getId()]   = EIP.getBackwardLimit();
  target[EDM.getId()]   = EDM.getBackwardLimit();
  target[ED.getId()]    = ED.getBackwardLimit();
  target[EPB.getId()]   = EPB.getBackwardLimit();
  target[EPL.getId()]   = EPL.getBackwardLimit();
  target[APL.getId()]   = APL.getBackwardLimit();
  target[FPL.getId()]   = FPL.getForwardLimit();
  target[APM.getId()]   = APM.getForwardLimit();
  target[OPM.getId()]   = OPM.getForwardLimit();
  target[APB.getId()]   = APB.getForwardLimit();

  computeEAngles(e_angles, target);
  // 目標位置に移動
  DEBUG_SERIAL.print("目標位置に移動します．ID: ");
  DEBUG_SERIAL.println(motor_id);
  sweepRunGoalPosition(target, e_angles, torque_control_flags, MOVING_TIME, millis());

  delay(2 * 1000);
  DEBUG_SERIAL.print("拮抗させます");
  target[EIP.getId()] = EIP.getForwardLimit();
  target[EDM.getId()] = EDM.getForwardLimit();
  target[ED.getId()]  = ED.getForwardLimit();
  computeEAngles(e_angles, target);
  sweepRunGoalPosition(target, e_angles, torque_control_flags, MOVING_TIME, millis());

  // 指定されたモーター以外のトルクをオフにする
  for (uint8_t i = (uint8_t)MuscleID::FCU; i <= (uint8_t)MuscleID::SPN; i++)
  {
    dxl.torqueOff(i);
  }

  delay(4 * 1000);
  return esyncRead();
  // return true;

}

bool randomTest(int mode){
  currentAndPositionCheck();
  int32_t target[SERVO_NUM] = {};
  switch (mode)
  {
  case 1:
    fillHighContractionFingerPos(target);
    for (uint8_t i = 0; i < 3; i++)
    {
      testRandomFE(-1, target);
      testRandomFE(1, target);
    }

    servoStop();
    return true;
    break;
  case 2:
    fillHighContractionFingerPos(target);
    testRandomRU(1, target);
    testRandomRU(-1, target);
    servoStop();
    return true;
  default:
    DEBUG_SERIAL.println("不明なコマンド");
    return false;
  }
}

bool unitDriveTest(){
  static const int16_t unit_drive_current_limits[SERVO_NUM] = {
      100, 100, 100, 100,  //  1- 4: IndexFDP, MiddleFDP, RingFDP, PinkyFDP
       60,  30, 200, 200,  //  5- 8: FPL, APM, OPM, APB
      400, 400, 400,       //  9-11: EIP, EDM, ED
      100, 200, 100,       // 12-14: EPB, EPL, APL
      300, 300, 300, 300,  // 15-18: FCR, FCU, ECRL, ECU
       60, 100,            // 19-20: SPN, BPB
      100, 100             // 21-22: PT, PQ
  };
  for (uint8_t i = 0; i < SERVO_NUM; i++) {
    muscles[i]->setCurrentLimit(unit_drive_current_limits[i]);
  }
  currentAndPositionCheck();
  int8_t torque_control_flags[SERVO_NUM] = {};
  // 制御モードを設定
  setControlMode(torque_control_flags);

  int32_t e_angles[SERVO_NUM] = {};
  int32_t target[SERVO_NUM] = {};

  // 初期位置に戻す
  fillInitialPositions(target);
  computeEAngles(e_angles, target);
  sweepRunGoalPosition(target, e_angles, torque_control_flags, MOVING_TIME, millis());

  // 脱力状態にする
  fillLowContractionPos(target);
  computeEAngles(e_angles, target);
  sweepRunGoalPosition(target, e_angles, torque_control_flags, 3, millis());

  delay(1000);
  // 各モーター試行時のタイムスタンプ
  constexpr uint8_t TRACKED_MOTORS = (uint8_t)MuscleID::SPN + 1;
  uint32_t start_timestamps[TRACKED_MOTORS] = {};
  uint32_t end_timestamps[TRACKED_MOTORS] = {};

  DEBUG_SERIAL.println("esyncからの信号を待ちます");
  uint8_t cnt = 0;
  while (1)
  {
    if (digitalRead(ESYNC_PIN))
    {
      uint32_t start_time = millis();
      while (1)
      {
        delay(1000);
        start_timestamps[cnt] = millis() - start_time;

        // 指定されたモーター以外のトルクをオフにする
        for (uint8_t i = 0; i < SERVO_NUM; i++)
        {
          if (i != cnt)
          {
            dxl.torqueOff(i);
          }
        }
        // 目標位置を設定
        target[cnt] = muscles[cnt]->getForwardLimit();
        sw_position.data[cnt].goal_position = target[cnt];
        sw_position.markChanged();
        // 目標位置に移動
        DEBUG_SERIAL.print("目標位置に移動 ID: ");
        DEBUG_SERIAL.println(cnt);
        sw_position.write("Position");
        delay(4 * 1000);

        end_timestamps[cnt] = millis() - start_time;
        cnt++;
        if (cnt < SERVO_NUM && muscles[cnt]->isEndlessWinding())
        {
          cnt++;
        }

        currentAndPositionCheck();
        // 初期位置に戻す
        fillInitialPositions(target);
        computeEAngles(e_angles, target);
        sweepRunGoalPosition(target, e_angles, torque_control_flags, 6, millis());

        currentAndPositionCheck();
        // 脱力状態にする
        fillLowContractionPos(target);
        computeEAngles(e_angles, target);
        sweepRunGoalPosition(target, e_angles, torque_control_flags, 2, millis());

        if (cnt > SPN.getId()){
          for (uint8_t i = 0; i < TRACKED_MOTORS; i++)
          {
            DEBUG_SERIAL.print(start_timestamps[i]);
            DEBUG_SERIAL.print(",");
          }
          DEBUG_SERIAL.println();
          for (uint8_t i = 0; i < TRACKED_MOTORS; i++)
          {
            DEBUG_SERIAL.print(end_timestamps[i]);
            DEBUG_SERIAL.print(",");
          }
          DEBUG_SERIAL.println();
          DEBUG_SERIAL.println("FINISH");
          initCurrentLimit();
          return true;
        }
        // if ((digitalRead(ESYNC_PIN) && (millis() - start_time) > 100) || (millis() - start_time) > 15500)
        // {
        //   DEBUG_SERIAL.println("FINISH");
        //   return true;
        // }
      }
    }
  }
}

// 単一サーボに符号付き Goal Current を直接書き込み，回転方向を観測する診断テスト。
// Drive Mode(10) bit0 の現在値と，±電流印加時の位置デルタをシリアルに出力する。
// sweepRunGoalPosition / rampRelaxation が EEPROM の Drive Mode 逆転設定に
// 依存しているか否かを実機で判定するために用いる。
bool directionTest(uint8_t motor_id){
    if (motor_id >= SERVO_NUM){
        DEBUG_SERIAL.print("Invalid motor id: "); DEBUG_SERIAL.println(motor_id);
        return false;
    }

    const int16_t  TEST_CURRENT = 20;   // mA, MIN_CURRENT と同等
    const uint32_t DRIVE_MS     = 1000; // 各方向の印加時間
    const uint32_t SETTLE_MS    = 400;  // 電流ゼロ後の静定待ち

    // Drive Mode bit0 を読む
    int drive_mode = dxl.readControlTableItem((uint8_t)ControlTableItem::DRIVE_MODE, motor_id, TIMEOUT);
    DEBUG_SERIAL.print("Motor "); DEBUG_SERIAL.print(motor_id);
    DEBUG_SERIAL.print(" DriveMode=0x"); DEBUG_SERIAL.print(drive_mode, HEX);
    DEBUG_SERIAL.print(" (bit0=");
    DEBUG_SERIAL.print(drive_mode & 0x01);
    DEBUG_SERIAL.println((drive_mode & 0x01) ? " Reverse)" : " Normal)");

    // OP_CURRENT に切替
    dxl.torqueOff(motor_id);
    dxl.setOperatingMode(motor_id, OP_CURRENT);
    dxl.torqueOn(motor_id);
    dxl.writeControlTableItem(ControlTableItem::GOAL_CURRENT, motor_id, 0);
    delay(SETTLE_MS);

    auto driveAndMeasure = [&](int16_t goal, const char *label){
        int32_t pos_before = dxl.getPresentPosition(motor_id, UNIT_RAW);
        dxl.writeControlTableItem(ControlTableItem::GOAL_CURRENT, motor_id, goal);
        delay(DRIVE_MS);
        int32_t pos_after    = dxl.getPresentPosition(motor_id, UNIT_RAW);
        int16_t cur_measured = dxl.getPresentCurrent(motor_id, UNIT_MILLI_AMPERE);
        DEBUG_SERIAL.print(label);
        DEBUG_SERIAL.print(" goal="); DEBUG_SERIAL.print(goal);
        DEBUG_SERIAL.print(" mA, present="); DEBUG_SERIAL.print(cur_measured);
        DEBUG_SERIAL.print(" mA, pos "); DEBUG_SERIAL.print(pos_before);
        DEBUG_SERIAL.print(" -> "); DEBUG_SERIAL.print(pos_after);
        DEBUG_SERIAL.print(" delta="); DEBUG_SERIAL.println(pos_after - pos_before);
        dxl.writeControlTableItem(ControlTableItem::GOAL_CURRENT, motor_id, 0);
        delay(SETTLE_MS);
    };

    driveAndMeasure(+TEST_CURRENT, "[+I]");
    driveAndMeasure(-TEST_CURRENT, "[-I]");

    // 片付け
    dxl.torqueOff(motor_id);
    dxl.setOperatingMode(motor_id, OP_CURRENT_BASED_POSITION);
    DEBUG_SERIAL.println("directionTest done");
    return true;
}

// 全サーボに directionTest を順次適用する。rampRelaxation は全サーボの
// DriveMode bit0=Normal を前提にしているため，本関数で混在有無を確認する。
bool directionTestAll(){
    DEBUG_SERIAL.println("=== directionTestAll: sweeping 0..SERVO_NUM-1 ===");
    for (uint8_t id = 0; id < SERVO_NUM; id++){
        DEBUG_SERIAL.println("---");
        if (!directionTest(id)){
            DEBUG_SERIAL.print("directionTest failed at ID=");
            DEBUG_SERIAL.println(id);
            return false;
        }
    }
    DEBUG_SERIAL.println("=== directionTestAll complete ===");
    return true;
}
