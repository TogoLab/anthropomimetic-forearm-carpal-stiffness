#include <Dynamixel2Arduino.h>

#define DXL_SERIAL   Serial2
#define DXL_DIR_PIN  2

const float DYNAMIXEL_PROTOCOL_VERSION = 2.0;

// サーボのID配列
const uint8_t DXL_ID_CNT = 2;  // サーボの数
const uint8_t DXL_ID_LIST[DXL_ID_CNT] = {0, 1};  // サーボのID

// SyncRead構造体の設定
const uint16_t SR_START_ADDR = 126;  // Starting address for Present Current
const uint16_t SR_ADDR_LEN = 10;     // 2 bytes for Current + 4 bytes for Position + 4 bytes for Velocity

typedef struct sr_data{
  int16_t present_current;
  int32_t present_velocity;
  int32_t present_position;
} __attribute__((packed)) sr_data_t;

sr_data_t sr_data[DXL_ID_CNT];
DYNAMIXEL::InfoSyncReadInst_t sr_infos;
DYNAMIXEL::XELInfoSyncRead_t info_xels_sr[DXL_ID_CNT];

// SyncWrite構造体の設定
const uint16_t SW_START_ADDR = 116;  // Starting address for Goal Position
const uint16_t SW_ADDR_LEN = 4;      // 4 bytes for Position

typedef struct sw_data{
  int32_t goal_position;
} __attribute__((packed)) sw_data_t;

sw_data_t sw_data[DXL_ID_CNT];
DYNAMIXEL::InfoSyncWriteInst_t sw_infos;
DYNAMIXEL::XELInfoSyncWrite_t info_xels_sw[DXL_ID_CNT];

const uint16_t user_pkt_buf_cap = 128;
uint8_t user_pkt_buf[user_pkt_buf_cap];

Dynamixel2Arduino dxl(DXL_SERIAL, DXL_DIR_PIN);

void setup() {
  Serial.begin(115200);
  while(!Serial);
  
  dxl.begin(1000000);  // 1Mbps baud rate
  dxl.setPortProtocolVersion(DYNAMIXEL_PROTOCOL_VERSION);

  for(uint8_t i = 0; i < DXL_ID_CNT; i++) {
    dxl.torqueOff(DXL_ID_LIST[i]);
  }
  for(uint8_t i = 0; i < DXL_ID_CNT; i++) {
    dxl.setOperatingMode(DXL_ID_LIST[i], OP_POSITION);
  }
  for(uint8_t i = 0; i < DXL_ID_CNT; i++) {
    dxl.torqueOn(DXL_ID_LIST[i]);
  }

  // SyncRead構造体の準備
  sr_infos.packet.p_buf = user_pkt_buf;
  sr_infos.packet.buf_capacity = user_pkt_buf_cap;
  sr_infos.packet.is_completed = false;
  sr_infos.addr = SR_START_ADDR;
  sr_infos.addr_length = SR_ADDR_LEN;
  sr_infos.p_xels = info_xels_sr;
  sr_infos.xel_count = 0;

  for(uint8_t i = 0; i < DXL_ID_CNT; i++) {
    info_xels_sr[i].id = DXL_ID_LIST[i];
    info_xels_sr[i].p_recv_buf = (uint8_t*)&sr_data[i];
    sr_infos.xel_count++;
  }

  sr_infos.is_info_changed = true;

  // SyncWrite構造体の準備
  sw_infos.packet.p_buf = nullptr;
  sw_infos.packet.is_completed = false;
  sw_infos.addr = SW_START_ADDR;
  sw_infos.addr_length = SW_ADDR_LEN;
  sw_infos.p_xels = info_xels_sw;
  sw_infos.xel_count = 0;

  for(uint8_t i = 0; i < DXL_ID_CNT; i++) {
    info_xels_sw[i].id = DXL_ID_LIST[i];
    info_xels_sw[i].p_data = (uint8_t*)&sw_data[i].goal_position;
    sw_infos.xel_count++;
  }

  sw_infos.is_info_changed = true;
}

void loop() {
  static int32_t goal_position = 0;
  static int direction = 1;

  // 目標位置の更新
  for(uint8_t i = 0; i < DXL_ID_CNT; i++) {
    sw_data[i].goal_position = goal_position;
  }
  sw_infos.is_info_changed = true;

  // SyncWrite実行
  if(dxl.syncWrite(&sw_infos) == true) {
    Serial.print("Goal Position set to: ");
    Serial.println(goal_position);
  } else {
    Serial.print("syncWrite failed. Lib error code: ");
    Serial.println(dxl.getLastLibErrCode());
  }

  // SyncRead実行
  uint8_t recv_cnt = dxl.syncRead(&sr_infos);
  
  if(recv_cnt > 0) {
    for(uint8_t i = 0; i < DXL_ID_CNT; i++) {
      Serial.print("ID ");
      Serial.print(DXL_ID_LIST[i]);
      Serial.print(" - Current: ");
      Serial.print(sr_data[i].present_current);
      Serial.print(", Position: ");
      Serial.print(sr_data[i].present_position);
      Serial.print(", Velocity: ");
      Serial.println(sr_data[i].present_velocity);
    }
  } else {
    Serial.print("syncRead failed. Lib error code: ");
    Serial.println(dxl.getLastLibErrCode());
  }

  // 目標位置の更新
  goal_position += direction * 100;
  if(goal_position >= 4095) {  // XL330-M288-tの最大位置値
    direction = -1;
  } else if(goal_position <= 0) {
    direction = 1;
  }

  Serial.println("-------------------");
  delay(100);  // 動作を遅くするために待機時間を設定
}