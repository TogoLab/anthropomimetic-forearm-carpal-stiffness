#include <Dynamixel2Arduino.h>
#include <TeensyThreads.h>
#include "DXLSetup.h"
#include "muscle.h"
#include "SDControl.h"
#include "control.h"

void Start(){
  for (uint8_t i = 0; i < MAX_ROWS; i++)
  {
    uint8_t moving_time = 3;
    unsigned long start = millis();
    setGoalPositionWithTime(goal_positions[i], moving_time, false);
    while (moving_time > (millis() - start))
    {
      currentThread();
      delay(100);
    }
  }
  DEBUG_SERIAL.println("Finish");
}

void setup() {
  DEBUG_SERIAL.begin(115200);
  while(!DEBUG_SERIAL);   // デバッグシリアルが接続されるまで待つ
  
  dxl.begin(1000000);  // 1Mbps baud rate
  dxl.setPortProtocolVersion(DXL_PROTOCOL_VERSION);
  setMotorID();

  for(uint8_t i = 0; i < SERVO_NUM; i++) {
    dxl.torqueOff(muscles_id[i]);
  }
  for(uint8_t i = 0; i < SERVO_NUM; i++) {
    dxl.setOperatingMode(muscles_id[i], OP_CURRENT_BASED_POSITION);
  }
  for(uint8_t i = 0; i < SERVO_NUM; i++) {
    dxl.torqueOn(muscles_id[i]);
  }
  // SyncRead構造体の準備
  sr_infos.packet.p_buf = user_pkt_buf;
  sr_infos.packet.buf_capacity = user_pkt_buf_cap;
  sr_infos.packet.is_completed = false;
  sr_infos.addr = SR_START_ADDR;
  sr_infos.addr_length = SR_ADDR_LEN;
  sr_infos.p_xels = info_xels_sr;
  sr_infos.xel_count = 0;

  for(uint8_t i = 0; i < SERVO_NUM; i++) {
    info_xels_sr[i].id = muscles_id[i];
    info_xels_sr[i].p_recv_buf = (uint8_t*)&sr_data[i];
    sr_infos.xel_count++;
  }

  sr_infos.is_info_changed = true;

  // SyncWrite構造体の準備（電流・速度用）
  sw_current_velocity_infos.packet.p_buf = nullptr;
  sw_current_velocity_infos.packet.is_completed = false;
  sw_current_velocity_infos.addr = SW_CURRENT_VELOCITY_START_ADDR;
  sw_current_velocity_infos.addr_length = SW_CURRENT_VELOCITY_LEN;
  sw_current_velocity_infos.p_xels = info_xels_sw_current_velocity;
  sw_current_velocity_infos.xel_count = 0;

  // SyncWrite構造体の準備（位置用）
  sw_position_infos.packet.p_buf = nullptr;
  sw_position_infos.packet.is_completed = false;
  sw_position_infos.addr = SW_POSITION_ADDR;
  sw_position_infos.addr_length = SW_POSITION_LEN;
  sw_position_infos.p_xels = info_xels_sw_position;
  sw_position_infos.xel_count = 0;

  for(uint8_t i = 0; i < SERVO_NUM; i++) {
    info_xels_sw_current_velocity[i].id = muscles_id[i];
    info_xels_sw_current_velocity[i].p_data = (uint8_t*)&sw_current_velocity_data[i];
    sw_current_velocity_infos.xel_count++;

    info_xels_sw_position[i].id = muscles_id[i];
    info_xels_sw_position[i].p_data = (uint8_t*)&sw_position_data[i];
    sw_position_infos.xel_count++;
  }

  sw_current_velocity_infos.is_info_changed = true;
  sw_position_infos.is_info_changed = true;
  // threads.addThread(currentThread);
}

void loop() {
  if (DEBUG_SERIAL.available()) {
    String input = DEBUG_SERIAL.readStringUntil('\n');
    input.trim();
    
    if (input.equalsIgnoreCase("Teach") && !isReading) {
      if (initSD()){
        teachingMode();
      }
    }else if (input.equalsIgnoreCase("Start")){
      if (initSD()){
        // readAllData();
        Start();
      }
    }
  }
}