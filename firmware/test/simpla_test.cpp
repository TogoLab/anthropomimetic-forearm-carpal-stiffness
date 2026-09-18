#include <Arduino.h>
#include <Dynamixel2Arduino.h>
#include <actuator.h>
#include <TeensyThreads.h>
#include "DXLSetup.h"
#include "muscle.h"

uint32_t goalPosition1[22] = {20,40,80,160,320};
uint32_t goalPosition2[22] = {0,0,0,0,0};

void currentThread(){
  while (1){
    String datas = "";
    for (uint8_t i=0; i < SERVO_NUM; i++){
      muscles[i]->checkCurrent();
    }
    for (uint8_t i=0; i < SERVO_NUM; i++){
      muscles[i]->checkPosition();
    }
    unsigned long time = millis();
    datas += String(time) + ",";
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
      datas += String(muscles[i]->getCurrent()) + "," + String(muscles[i]->getPosition());
      if (i == SERVO_NUM-1)
      {
        DEBUG_SERIAL.println(datas);
      }else{
        datas += ",";
      }
    }
    threads.delay(100);
  }
}

void setup() {  
  // Use UART port of DYNAMIXEL Shield to debug.
  DEBUG_SERIAL.begin(115200);   //Set debugging port baudrate to 115200bps
  while(!DEBUG_SERIAL);         //Wait until the serial port for terminal is opened

  // classとモーターIDを設定
  setMotorID();

  // Set Port baudrate to 57600bps. This has to match with DYNAMIXEL baudrate.
  dxl.begin(1000000);
  // Set Port Protocol Version. This has to match with DYNAMIXEL protocol version.
  dxl.setPortProtocolVersion(DXL_PROTOCOL_VERSION);

  // Turn off torque when configuring items in EEPROM area
  for (uint8_t i = 0; i < SERVO_NUM; i++)
  {
    dxl.write(i, TORQUE_ENABLE_ADDR, (uint8_t*)&turn_off , TORQUE_ENABLE_ADDR_LEN, TIMEOUT);
  }
  
  // Set Operating Mode
  for (uint8_t i = 0; i < SERVO_NUM; i++)
  {
    dxl.write(i, OPERATING_MODE_ADDR, (uint8_t*)&operatingMode, OPERATING_MODE_ADDR_LEN, TIMEOUT);
  }
  
  // Turn on torque
  for (uint8_t i = 0; i < SERVO_NUM; i++){
    dxl.write(i, TORQUE_ENABLE_ADDR, (uint8_t*)&turn_on, TORQUE_ENABLE_ADDR_LEN, TIMEOUT);
  }
  threads.delay(4000);

  // 電流計測スタート
  threads.addThread(currentThread);

}

void loop() {
  // put your main code here, to run repeatedly:

  // LED On
  // DEBUG_SERIAL.println("LED ON");
  for (uint8_t i=0; i <SERVO_NUM; i++){
    dxl.write(i, LED_ADDR, (uint8_t*)&turn_on, LED_ADDR_LEN, TIMEOUT);
  }
  threads.delay(500);
  
  // Please refer to e-Manual(http://emanual.robotis.com/docs/en/parts/interface/dynamixel_shield/) for available range of value. 
  // Set Goal Position
  // DEBUG_SERIAL.print("Goal Position : ");
  // DEBUG_SERIAL.println(goalPosition1);
  // setGoalPositionWithTime(fingers[0].id, goalPosition1, 5, true);  
  for (uint8_t i=0; i <SERVO_NUM; i++){
    muscles[i]->setGoalPositionWithTime(0, 5, false);
  }
  threads.delay(6000);
  
  // LED Off
  // DEBUG_SERIAL.println("LED OFF");
  for (uint8_t i=0; i <SERVO_NUM; i++){
    dxl.write(i, LED_ADDR, (uint8_t*)&turn_off, LED_ADDR_LEN, TIMEOUT);
  }
  threads.delay(500);

  // Set Goal Position
  // DEBUG_SERIAL.print("Goal Position : ");
  // DEBUG_SERIAL.println(goalPosition2);
  for (uint8_t i=0; i <SERVO_NUM; i++){
    muscles[i]->setGoalPositionWithTime(100, 2, false);
  }
  threads.delay(2000);
}