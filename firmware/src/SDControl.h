#ifndef _SDCONTROL_H_
#define _SDCONTROL_H_
#include <Arduino.h>
#include "SdFat.h"
#include "config.h"

// Use Teensy SDIO
#define SD_CONFIG  SdioConfig(FIFO_SDIO)

extern SdFs sd;
extern FsFile dataFile;
extern String fileName;
extern bool isReading;

// SD から読み込んだ再生用モーションバッファ（Start() がこれを順に再生する）
extern int32_t playback_positions[MAX_ROWS][SERVO_NUM];

bool initSD();
bool chooseFile();
bool initFileName();
void writeArrayToSD(int16_t *array);
uint8_t readAllData();
void listFiles();
void deleteFile();

#endif //_SDCONTROL_H_
