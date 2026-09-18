#ifndef _DXLSETUP_H_
#define _DXLSETUP_H_

#include <Arduino.h>
#include <Dynamixel2Arduino.h>
#include "config.h"

#define TORQUE_ENABLE_ADDR          64
#define CURRENT_ADDR                38
#define TORQUE_ENABLE_ADDR_LEN      1
#define LED_ADDR                    65
#define LED_ADDR_LEN                1
#define GOAL_POSITION_ADDR          116
#define GOAL_POSITION_ADDR_LEN      4
#define GOAL_CURRENT_ADDR           102
#define GOAL_CURRENT_ADDR_LEN       2
#define PRESENT_POSITION_ADDR       132
#define PRESENT_POSITION_ADDR_LEN   4
#define PROFILE_VELOCITY_ADDR       112
#define PROFILE_VELOCITY_ADDR_LEN   4
#define POSITION_CONTROL_MODE       3
#define VELOCITY_UNIT_SCALE       (0.22888 * 360 / 60)
#define ACCEL_UNIT_SCALE          (214.58 * 360 / 60 / 60)
#define MAX_FLEX_CURRENT 20     // 指屈曲時の最大目標電流値
#define THUMB_FLEX_CURRENT 30   // FPL（長母指屈筋）の把持電流（4指に対向するため少し高め）
#define MAX_EXTENS_CURRENT 20  // 指伸展時の最大目標電流値
#define MAX_EXTENS_ED_CURRENT 40  // 指伸展時の最大目標電流値
#define MIN_CURRENT 30          // 弛緩時の最小目標電流値
#define GENERAL_CURRENT 100     // 指以外の位置制御時の目標電流値
#define CARPAL_CURRENT 200     // 指以外の位置制御時の目標電流値
#define PR_CURRENT      200     // 回内筋の目標電流
#define SP_CURRENT      150     // 回外筋の目標電流値
#define TEACHING_FINGER_CURRENT  30   // 教示モードの指の目標電流
#define TEACHING_WRIST_CURRENT   60   // 教示モードの手首関節の目標電流
#define TEACHING_FOREARM_CURRENT 60   // 教示モードの前腕関節の目標電流
#define MOVING_TIME 3           // 1モーションまでの遷移時間（秒）

// SyncRead構造体の設定
const uint16_t SR_START_ADDR = 126;  // Starting address for Present Current
const uint16_t SR_ADDR_LEN = 10;    // 2 bytes for Current + 4 bytes for Position + 4 bytes for Velocity

typedef struct sr_data{
  int16_t present_current;
  int32_t present_velocity;
  int32_t present_position;
} __attribute__((packed)) sr_data_t;

// SyncWrite構造体の設定（分離）
const uint16_t SW_CURRENT_VELOCITY_START_ADDR = 102;
const uint16_t SW_CURRENT_VELOCITY_LEN = 6;
const uint16_t SW_POSITION_ADDR = 116;
const uint16_t SW_POSITION_LEN = 4;
const uint16_t OPERATING_MODE_ADDR = 11;
const uint16_t OPERATING_MODE_ADDR_LEN = 1;


typedef struct sw_current_velocity_data {
  int16_t goal_current;
  int32_t goal_velocity;
} __attribute__((packed)) sw_current_velocity_t;

typedef struct sw_position_data {
  int32_t goal_position = 0;
} __attribute__((packed)) sw_position_t;

typedef struct sw_op_mode_data {
  uint8_t mode = OP_CURRENT_BASED_POSITION;
} __attribute__((packed)) sw_op_mode_t;

#define DXL_SERIAL Serial2  // Attatch 7, 8 pins
#define DEBUG_SERIAL SerialUSB
#define DISPLAY_SERIAL Serial3
const int DXL_DIR_PIN = 2; // DYNAMIXEL Shield DIR PIN

const float DXL_PROTOCOL_VERSION = 2.0;

extern Dynamixel2Arduino dxl;

// SyncWrite の info/xels/data をまとめて所有するチャンネル。
// 同一アドレス範囲に対して「全サーボ分をひと纏めに書き込む」単位を表す。
template<typename DataT>
class SyncWriteChannel {
public:
    DataT data[SERVO_NUM] = {};

    void init(uint16_t addr, uint16_t addr_len){
        info.packet.p_buf = nullptr;
        info.packet.is_completed = false;
        info.addr = addr;
        info.addr_length = addr_len;
        info.p_xels = xels;
        info.xel_count = 0;
        for (uint8_t i = 0; i < SERVO_NUM; i++){
            xels[i].id = i;
            xels[i].p_data = (uint8_t*)&data[i];
            info.xel_count++;
        }
        info.is_info_changed = true;
    }

    void markChanged(){ info.is_info_changed = true; }

    bool write(const char *label){
        if (dxl.syncWrite(&info)) return true;
        DEBUG_SERIAL.print(label);
        DEBUG_SERIAL.print(" syncWrite failed. Lib error code: ");
        DEBUG_SERIAL.println(dxl.getLastLibErrCode());
        return false;
    }

private:
    DYNAMIXEL::InfoSyncWriteInst_t info;
    DYNAMIXEL::XELInfoSyncWrite_t  xels[SERVO_NUM];
};

// SyncRead 版。受信バッファもクラス内で所有する。
template<typename DataT>
class SyncReadChannel {
public:
    DataT data[SERVO_NUM] = {};

    void init(uint16_t addr, uint16_t addr_len){
        info.packet.p_buf = pkt_buf;
        info.packet.buf_capacity = sizeof(pkt_buf);
        info.packet.is_completed = false;
        info.addr = addr;
        info.addr_length = addr_len;
        info.p_xels = xels;
        info.xel_count = 0;
        for (uint8_t i = 0; i < SERVO_NUM; i++){
            xels[i].id = i;
            xels[i].p_recv_buf = (uint8_t*)&data[i];
            info.xel_count++;
        }
        info.is_info_changed = true;
    }

    void markChanged(){ info.is_info_changed = true; }
    DYNAMIXEL::InfoSyncReadInst_t* raw(){ return &info; }

private:
    DYNAMIXEL::InfoSyncReadInst_t info;
    DYNAMIXEL::XELInfoSyncRead_t  xels[SERVO_NUM];
    uint8_t pkt_buf[128];
};

extern SyncWriteChannel<sw_current_velocity_t> sw_current_velocity;
extern SyncWriteChannel<sw_position_t>         sw_position;
extern SyncWriteChannel<sw_op_mode_t>          sw_op_mode;
extern SyncReadChannel<sr_data_t>              sr;

inline void waitForSerialInput(){
  while (!DEBUG_SERIAL.available())
  {
    ;
  }
}

void initDXL();

#endif //_DXLSETUP_H_
