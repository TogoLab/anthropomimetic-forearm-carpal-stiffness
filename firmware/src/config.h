#ifndef _CONFIG_H_
#define _CONFIG_H_

#include <Arduino.h>

#define READ_PERIOD 10 // 10ms 100Hz
#define TIMEOUT 10    //default communication timeout 10ms
#define NORMAL_SERVO 20
#define INFINITE_SERVO_NUM 2
#define SERVO_NUM (NORMAL_SERVO + INFINITE_SERVO_NUM)
#define MAX_ROWS 10          // 格納できる最大行数

const uint8_t FORCE_GAGE_PIN = A16;
const uint8_t ESYNC_PIN = A17;

#endif //_CONFIG_H_
