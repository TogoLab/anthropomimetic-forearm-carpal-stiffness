#ifndef _TESTS_H_
#define _TESTS_H_
#include "DXLSetup.h"

int16_t randomize(bool bias=false);
void testRandomFE(int8_t symbol, const int32_t *target);
void testRandomRU(int8_t symbol, const int32_t *target);
bool esyncRead();

bool contractionTest(int mode);
bool fingerDriveTest(uint8_t finger_id);
bool randomTest(int mode);
bool unitDriveTest();
bool directionTest(uint8_t motor_id);
bool directionTestAll();

#endif //_TESTS_H_
