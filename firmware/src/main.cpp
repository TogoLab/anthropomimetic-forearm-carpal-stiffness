#include <Dynamixel2Arduino.h>
#include <TeensyThreads.h>
#include "DXLSetup.h"
#include "muscle.h"
#include "SDControl.h"
#include "control.h"
#include "motion.h"
#include "tests.h"
#include "logging.h"
#include "teaching.h"

// RCサーボモード用のコード
#include <Servo.h>

const int SERVO_PIN = 9;  // Teensyのサーボ対応ピンを使用
Servo actuator;        // PWMServoオブジェクト

// 0-100%の位置をサーボパルスに変換
void setPosition(float percentage) {
  // 位置を0-100%で指定
  percentage = constrain(percentage, 0.0f, 100.0f);
  
  // 12bit解像度（0-4095）にマッピング
  int pwmValue = map(percentage * 10, 0, 1000, 0, 4095);
  DEBUG_SERIAL.println(pwmValue);
  analogWrite(SERVO_PIN, pwmValue);
}

void Start(uint8_t row_cnt, MotionType motion){
  // 現在の電流値とモーターのポジションを取得
  currentAndPositionCheck();
  DISPLAY_SERIAL.println("start");

  // モーションデータを１行ずつ読み込んで再生する
  for (uint8_t i = 0; i < row_cnt; i++)
  {
    uint8_t moving_time = MOVING_TIME;
    uint32_t start_time = millis();
    currentAndPositionCheck();
    // トルク制御するモーターのインデックス
    int8_t torque_control_flags[SERVO_NUM] = {};
    int32_t e_angles[SERVO_NUM] = {};
    computeEAngles(e_angles, playback_positions[i]);

    if (motion == MotionType::Grasp) {
      coopGraspMotion(e_angles, torque_control_flags, moving_time);
    }else if(motion == MotionType::Relax){
      relaxMotion(e_angles, playback_positions[i]);
    }
      sweepRunGoalPosition(playback_positions[i], e_angles, torque_control_flags, moving_time, start_time);
    // DEBUG_SERIAL.println("Finish");
  }
  DEBUG_SERIAL.println("Finish");
  DISPLAY_SERIAL.println("Finish");
}

static void cmdTeach(){
  listFiles();
  if (initFileName()){
    DEBUG_SERIAL.println("無限巻取り機構を使いますか？ y/n");
    waitForSerialInput();
    String input = DEBUG_SERIAL.readStringUntil('\n');
    input.trim();
    if (input.equalsIgnoreCase("Y")){
      teachingMode(true);
      DEBUG_SERIAL.println("無限巻取り機構を使います");
    }
    else{
      teachingMode(false);
      DEBUG_SERIAL.println("無限巻取り機構を使いません");
    }
  }
}

static void cmdStart(){
  DEBUG_SERIAL.println("How many times?");
  waitForSerialInput();
  String input = DEBUG_SERIAL.readStringUntil('\n');
  input.trim();
  if (chooseFile() && input.toInt()){
    DEBUG_SERIAL.println("Which motion type? relax: 1, grasp: 2\nmotion type: ");
    waitForSerialInput();
    String motion_type = DEBUG_SERIAL.readStringUntil('\n');
    motion_type.trim();
    uint8_t row_cnt = readAllData();
    printCsvHeader(DEBUG_SERIAL);
    for (uint8_t i = 0; i < input.toInt(); i++)
    {
      if (motion_type == "2"){
        Start(row_cnt, MotionType::Grasp);
      }else{
        Start(row_cnt, MotionType::Relax);
      }
    }
  }else{
    DEBUG_SERIAL.println("Failure.. Please check your input");
  }
}

static void cmdDelete(){
  deleteFile();
}

static void cmdLs(){
  listFiles();
}

static void cmdRelax(){
  for (uint8_t i = 0; i < SERVO_NUM; i++)
  {
    dxl.torqueOff(i);
  }
}

static void cmdFix(){
  fix();
}

static void cmdManual(){
  DEBUG_SERIAL.println("Manual move. Please input 22 servo positions, like 3200, 4300, 3444");
  waitForSerialInput();
  String input = DEBUG_SERIAL.readStringUntil('\n');
  input.trim();
  char buf[256];
  input.toCharArray(buf, sizeof(buf));
  char* token = strtok(buf, ",");
  int count = 0;
  int32_t target[SERVO_NUM] = {};
  while (token != NULL && count < SERVO_NUM) {
    target[count] = atoi(token);
    DEBUG_SERIAL.println(target[count]);
    count++;
    token = strtok(NULL, ",");
  }
}

static void cmdStatic(){
  DEBUG_SERIAL.println("関節剛性計測モード\nモードを選択してください\n1: 低剛性\n2: 高剛性\n3: 高剛性かつ把持\n4: 指筋のみ");
  waitForSerialInput();
  String input = DEBUG_SERIAL.readStringUntil('\n');
  input.trim();
  contractionTest(atoi(input.c_str()));
}

static void cmdRandom(){
  DEBUG_SERIAL.println("ランダム筋駆動モーションテスト\nモードを選択してください\n1: FE\n2: RU\n3: DTM");
  waitForSerialInput();
  String input = DEBUG_SERIAL.readStringUntil('\n');
  input.trim();
  randomTest(atoi(input.c_str()));
}

static void cmdUnit(){
  DEBUG_SERIAL.println("筋肉単体テスト");
  unitDriveTest();
}

static void cmdFingerDrive(){
  DEBUG_SERIAL.println("指の番号を入力してください");
  waitForSerialInput();
  uint8_t finger = DEBUG_SERIAL.parseInt();
  fingerDriveTest(finger);
}

static void cmdDirection(){
  DEBUG_SERIAL.println("方向性確認: サーボ ID (0-21) を入力してください");
  waitForSerialInput();
  uint8_t id = DEBUG_SERIAL.parseInt();
  directionTest(id);
}

static void cmdDirectionAll(){
  DEBUG_SERIAL.println("全サーボ方向性確認を開始します。実機が±20mAで動きます。y/n");
  waitForSerialInput();
  String input = DEBUG_SERIAL.readStringUntil('\n');
  input.trim();
  if (input.equalsIgnoreCase("Y")) directionTestAll();
  else DEBUG_SERIAL.println("cancelled");
}

static void cmdServo(){
  DEBUG_SERIAL.println("サーボテスト　角度: ");
  waitForSerialInput();
  float pos = DEBUG_SERIAL.parseFloat();
  if (pos >= 0 && pos <= 100) {
    setPosition(pos);
    DEBUG_SERIAL.print("Position set to: ");
    DEBUG_SERIAL.print(pos);
    DEBUG_SERIAL.println("%");
  }
}

static void cmdShow(){
  float pos[SERVO_NUM] = {};
  String positions = "";
  currentAndPositionCheck();
  for (uint8_t i = 0; i < SERVO_NUM; i++)
  {
    pos[i] = dxl.getPresentPosition(i, UNIT_RAW);
  }
  for (uint8_t i = 0; i < SERVO_NUM; i++)
  {
    positions += String(int(pos[i])) + ",";
  }
  DEBUG_SERIAL.println(positions);
}

// Host-scripted single-line goal command. Two-line protocol:
//   >> Goal\n
//   >> 1234,5678,...,2048\n      (22 ints, comma-separated; optional ':' prefix)
//   << OK\n                       (success: motors driven)
//   << ERR:<reason>\n             (parse error or wrong count)
// See unit_test/docs/proposed_goal_command.md and the host wrapper
// sim2real/dxl_host.py.
static void cmdGoal(){
  waitForSerialInput();
  String input = DEBUG_SERIAL.readStringUntil('\n');
  input.trim();
  int colon = input.indexOf(':');
  String csv = (colon >= 0) ? input.substring(colon + 1) : input;

  char buf[256];
  csv.toCharArray(buf, sizeof(buf));
  char* token = strtok(buf, ",");
  int32_t target[SERVO_NUM] = {};
  int8_t  torque_control_flags[SERVO_NUM] = {};
  int32_t e_angles[SERVO_NUM] = {};
  int count = 0;
  while (token != NULL && count < SERVO_NUM) {
    target[count++] = atoi(token);
    token = strtok(NULL, ",");
  }
  if (count != SERVO_NUM) {
    DEBUG_SERIAL.print("ERR:expected ");
    DEBUG_SERIAL.print(SERVO_NUM);
    DEBUG_SERIAL.print(" ints, got ");
    DEBUG_SERIAL.println(count);
    return;
  }
  sweepRunGoalPosition(target, e_angles, torque_control_flags,
                        MOVING_TIME, millis());
  DEBUG_SERIAL.println("OK");
}

struct Command {
  const char* name;
  void (*handler)();
};

static const Command COMMANDS[] = {
  {"Teach",       cmdTeach},
  {"Start",       cmdStart},
  {"Delete",      cmdDelete},
  {"ls",          cmdLs},
  {"Relax",       cmdRelax},
  {"Fix",         cmdFix},
  {"Manual",      cmdManual},
  {"Static",      cmdStatic},
  {"Random",      cmdRandom},
  {"Unit",        cmdUnit},
  {"FingerDrive", cmdFingerDrive},
  {"Direction",   cmdDirection},
  {"DirectionAll",cmdDirectionAll},
  {"servo",       cmdServo},
  {"Show",        cmdShow},
  {"Goal",        cmdGoal},
};

void setup() {
  DEBUG_SERIAL.begin(115200);
  // while(!DEBUG_SERIAL);   // デバッグシリアルが接続されるまで待つ
  delay(1000);  // シリアルポートの安定化のために少し待つ
  // DISPLAY_SERIAL.begin(115200);
  dxl.begin(1000000);  // 1Mbps baud rate
  dxl.setPortProtocolVersion(DXL_PROTOCOL_VERSION);
  setMotorID();
  initCurrentLimit();
  // analogWriteFrequency(SERVO_PIN, 2000);  // 50Hz for servo control
  analogWriteResolution(12);  // 12-bit resolution for Teensy 4.1
  pinMode(SERVO_PIN, OUTPUT);

  initDXL();
  currentAndPositionCheck();
  initSD();
  randomSeed(analogRead(0));
  // DEBUG_SERIAL.println("COMMANDS:\nTeach: 教示モード\nStart: 連続運転モード\nStatic: 剛性試験モード");

  // デモ用: demo2.csv を Relax モーションで無限ループ再生
  fileName = "demo2.csv";
  uint8_t row_cnt = readAllData();
  DEBUG_SERIAL.print("DEMO: ");
  DEBUG_SERIAL.print(fileName);
  DEBUG_SERIAL.print(" rows=");
  DEBUG_SERIAL.println(row_cnt);
  while (1) {
    Start(row_cnt, MotionType::Relax);
  }
}

void loop() {
  if (!DEBUG_SERIAL.available()) return;

  String input = DEBUG_SERIAL.readStringUntil('\n');
  input.trim();

  for (const auto& cmd : COMMANDS) {
    if (input.equalsIgnoreCase(cmd.name)) {
      cmd.handler();
      return;
    }
  }
}