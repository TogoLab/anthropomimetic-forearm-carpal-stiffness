#include "DXLSetup.h"
#include "muscle.h"

SyncWriteChannel<sw_current_velocity_t> sw_current_velocity;
SyncWriteChannel<sw_position_t>         sw_position;
SyncWriteChannel<sw_op_mode_t>          sw_op_mode;
SyncReadChannel<sr_data_t>              sr;

Dynamixel2Arduino dxl(DXL_SERIAL, DXL_DIR_PIN);

void initDXL(){
  // Keep these three loops separate — interleaving off/mode/on per servo
  // causes Dynamixel setup to fail (suspected comms timing issue).
  for(uint8_t i = 0; i < SERVO_NUM; i++) {
    dxl.torqueOff(i);
  }
  for(uint8_t i = 0; i < SERVO_NUM; i++) {
    dxl.setOperatingMode(i, OP_CURRENT_BASED_POSITION);
  }
  for(uint8_t i = 0; i < SERVO_NUM; i++) {
    dxl.torqueOn(i);
  }

  sr.init(SR_START_ADDR, SR_ADDR_LEN);
  sw_current_velocity.init(SW_CURRENT_VELOCITY_START_ADDR, SW_CURRENT_VELOCITY_LEN);
  sw_position.init(SW_POSITION_ADDR, SW_POSITION_LEN);
  sw_op_mode.init(OPERATING_MODE_ADDR, OPERATING_MODE_ADDR_LEN);
}
