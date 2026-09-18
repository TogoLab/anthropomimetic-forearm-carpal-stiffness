#ifndef _MOTION_H_
#define _MOTION_H_
#include "DXLSetup.h"

enum MotionType{
    Relax,
    Grasp
};

/**
 * @brief Set the Control Mode object.
 * トルクフラッグが立っているモーターを電流制御に変更する．立っていないものは電流位置制御に変更する
 *
 * @param torque_control_flags
 */
void setControlMode(int8_t *torque_control_flags);

void relaxMotion(int32_t *e_angles, int32_t *pos_e);

void coopGraspMotion(int32_t *e_angles, int8_t *torque_control_flags, uint16_t time);

#endif //_MOTION_H_
