#ifndef _CONTROL_H_
#define _CONTROL_H_
#include "DXLSetup.h"
#include "muscle.h"
#include "config.h"
#include "SDControl.h"

void dxlModeSetup(uint8_t mode);
void initGoalCurrent(int8_t *torque_control_flags);
void computeEAngles(int32_t *e_angles, const int32_t *goal_row);
bool sweepRunGoalPosition(const int32_t *goal_pos, int32_t *e_angles, int8_t *torque_control_flags, uint16_t time, uint32_t start);
String getCurrentAndPositionArray(uint32_t start);
void currentAndPositionCheck();
void torqueOnExceptEndless(bool useEndlessMecha);
void servoStop();
bool fix();

#endif //_CONTROL_H_
