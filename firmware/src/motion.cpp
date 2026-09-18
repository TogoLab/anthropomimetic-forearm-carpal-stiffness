#include "motion.h"
#include "control.h"
#include "muscle.h"
#include "coop_graph.h"

void setControlMode(int8_t *torque_control_flags){
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
        dxl.torqueOff(i);
    }
    // フラッグが立っているものを電流制御に変更する
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
        if (torque_control_flags[i] != 0) {
            sw_op_mode.data[i].mode = OP_CURRENT;
        }else{
            sw_op_mode.data[i].mode = OP_CURRENT_BASED_POSITION;
        }
    }
    sw_op_mode.markChanged();
    sw_op_mode.write("Operating Mode");
}

void relaxMotion(int32_t *e_angles, int32_t *pos_e){
    // 収縮側は category 別の目標電流，弛緩側は MIN_CURRENT に落とす
    auto setByCategory = [&](Muscle *m, int32_t pullCurrent){
        uint8_t id = m->getId();
        e_angles[id] = pos_e[id] - m->getPosition();
        sw_current_velocity.data[id].goal_current =
            (e_angles[id] > 0) ? pullCurrent : MIN_CURRENT;
    };
    for (auto *f  : fingers)  setByCategory(f,  GENERAL_CURRENT);
    for (auto *w  : wrists)   setByCategory(w,  CARPAL_CURRENT);
    for (auto *fo : forearms) setByCategory(fo, SP_CURRENT);

    sw_current_velocity.markChanged();
    dxlModeSetup(OP_CURRENT_BASED_POSITION);
}

void coopGraspMotion(int32_t *e_angles, int8_t *torque_control_flags, uint16_t time){
    for (uint8_t ID = 0; ID < SERVO_NUM; ID++){
        if (e_angles[ID] <= 10){
            sw_current_velocity.data[ID].goal_current = MIN_CURRENT;
            continue;
        }
        setWristCoopFlags(ID, torque_control_flags);
        if (torque_control_flags[ID] == 1){
            sw_current_velocity.data[ID].goal_current = 0;
        } else {
            applyGraspCurrent(ID);
        }
    }
    sw_current_velocity.markChanged();
    propagateCoopFlags(torque_control_flags);
    setControlMode(torque_control_flags);
}
