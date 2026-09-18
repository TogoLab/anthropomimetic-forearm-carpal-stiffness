#include <SPI.h>
#include <SdFat.h>
#include <Dynamixel2Arduino.h>
#include <actuator.h>
#include <TeensyThreads.h>
#include "DXLSetup.h"

#define SD_CONFIG SdioConfig(FIFO_SDIO)
#define MAX_ROWS 1000     // 格納できる最大行数
#define MAX_COLUMNS 10    // 各行の最大列数

SdFat sd;
FsFile dataFile;

String fileName = "sensor_data.csv";  // デフォルトのファイル名
bool isReading = false;

int sensorData[MAX_ROWS][MAX_COLUMNS];
int rowCount = 0;
int columnCount = 0;


void requestFileName() {
  Serial.println("読み取るファイル名を入力してください（拡張子 .csv を含む）:");
  while (!Serial.available()) {
    ; // 入力を待つ
  }
  fileName = Serial.readStringUntil('\n');
  fileName.trim();  // 空白文字を削除

  if (!fileName.endsWith(".csv")) {
    fileName += ".csv";
  }

  Serial.print("読み取るファイル名: ");
  Serial.println(fileName);

  if (!sd.exists(fileName.c_str())) {
    Serial.println("指定されたファイルが存在しません。");
    requestFileName();  // 再度ファイル名を要求
    return;
  }

  Serial.println("準備完了。'Start'と入力してデータ読み取りを開始してください。");
}

void readAllData() {
  Serial.println("データ読み取りを開始します...");
  isReading = true;
  
  if (!sd.card()->errorCode()) {
    Serial.println("SDカードは正常です。");
  } else {
    Serial.print("SDカードエラー: ");
    Serial.println(sd.card()->errorCode());
    isReading = false;
    return;
  }

  if (!dataFile.open(fileName.c_str(), O_READ)) {
    Serial.println("ファイルのオープンに失敗しました。");
    Serial.print("SDカードエラー: ");
    Serial.println(sd.card()->errorCode());
    isReading = false;
    return;
  }

  Serial.print("ファイルサイズ: ");
  Serial.println(dataFile.size());

  Serial.println("センサーデータを読み込んでいます...");
  char buffer[256];  // 1行の最大長を想定（必要に応じて調整）
  rowCount = 0;
  columnCount = 0;
  
  while (dataFile.available() && rowCount < MAX_ROWS) {
    if (dataFile.fgets(buffer, sizeof(buffer)) > 0) {
      char* token = strtok(buffer, ",");
      int col = 0;
      while (token != NULL && col < MAX_COLUMNS) {
        sensorData[rowCount][col] = atoi(token);
        token = strtok(NULL, ",");
        col++;
      }
      if (col > columnCount) columnCount = col;
      rowCount++;
    }
    
    // 進捗状況を表示（10行ごと）
    if (rowCount % 10 == 0) {
      Serial.print("読み込み中... 行数: ");
      Serial.println(rowCount);
    }
  }

  dataFile.close();
  
  Serial.println("---");
  Serial.print("読み込んだ行数: ");
  Serial.println(rowCount);
  Serial.print("列数: ");
  Serial.println(columnCount);
  Serial.println("データ読み取りが完了しました。'Print'と入力してデータを表示するか、'Start'と入力して新しい読み取りを開始できます。");
  
  isReading = false;
}

void changeVerocity(uint32_t profile_v, uint8_t motorId){
    dxl.writeControlTableItem(ControlTableItem::PROFILE_VELOCITY, motorId, profile_v);
}
void setGoalPositionWithTime(uint8_t motorId, int32_t pos_s, int32_t pos_e, uint16_t time, bool sync){
    int32_t angle = pos_e - pos_s;
    uint32_t v = abs(angle / time / VELOCITY_UNIT_SCALE);
    uint32_t ret = (int32_t)round((float)pos_e/0.088);

    changeVerocity(v, motorId);
    // dxl.setGoalPosition(id, pos_e, UNIT_DEGREE);
    dxl.write(motorId, GOAL_POSITION_ADDR, (uint8_t*)&ret, GOAL_POSITION_ADDR_LEN, TIMEOUT);
    if(sync) threads.delay(time*1000);
}

void printData() {
  Serial.println("格納されたセンサーデータ:");
  int32_t pos_s = 0;
  for (int i = 0; i < rowCount; i++) {
    for (int j = 0; j < columnCount; j++) {
      Serial.print(sensorData[i][j]);
      Serial.print("\t");  // タブで区切る
      if(sensorData[i][j]>0){
        setGoalPositionWithTime(0, pos_s, sensorData[i][j], 2, true);
        pos_s = sensorData[i][j];
      }
    }
    Serial.println();  // 各行の終わりに改行
  }
  Serial.println();
}

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 5000) {
    ; // シリアルポートの接続を待つ（最大5秒）
  }
  // Set Port baudrate to 57600bps. This has to match with DYNAMIXEL baudrate.
  dxl.begin(1000000);
  // Set Port Protocol Version. This has to match with DYNAMIXEL protocol version.
  dxl.setPortProtocolVersion(DXL_PROTOCOL_VERSION);

  // Turn off torque when configuring items in EEPROM area
  // for (uint8_t i = 0; i < SERVO_NUM; i++)
  // {
    dxl.write(0, TORQUE_ENABLE_ADDR, (uint8_t*)&turn_off , TORQUE_ENABLE_ADDR_LEN, TIMEOUT);
  // }
  
  // Set Operating Mode
  // for (uint8_t i = 0; i < SERVO_NUM; i++)
  // {
    dxl.write(0, OPERATING_MODE_ADDR, (uint8_t*)&operatingMode, OPERATING_MODE_ADDR_LEN, TIMEOUT);
  // }
  
  // Turn on torque
  // for (uint8_t i = 0; i < SERVO_NUM; i++){
    dxl.write(0, TORQUE_ENABLE_ADDR, (uint8_t*)&turn_on, TORQUE_ENABLE_ADDR_LEN, TIMEOUT);
  // }

  Serial.println("Teensy 4.1 SDカードリーダーを初期化中...");

  if (!sd.begin(SD_CONFIG)) {
    Serial.println("SDカードの初期化に失敗しました。");
    while (1);
  }
  Serial.println("SDカードの初期化に成功しました。");

  requestFileName();
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.equalsIgnoreCase("Start") && !isReading) {
      readAllData();
    } else if (input.equalsIgnoreCase("Print")) {
      printData();
    }
  }
}
