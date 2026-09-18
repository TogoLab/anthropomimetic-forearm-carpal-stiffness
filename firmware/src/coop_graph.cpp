#include "coop_graph.h"
#include "muscle.h"
#include "DXLSetup.h"

void setWristCoopFlags(uint8_t ID, int8_t *flags){
    switch (ID){
        case (uint8_t)MuscleID::FCR:
            flags[(uint8_t)MuscleID::IndexFDP] = 1;
            flags[(uint8_t)MuscleID::FPL] = 1;
            break;
        case (uint8_t)MuscleID::FCU:
            flags[(uint8_t)MuscleID::PinkyFDP] = 1;
            break;
        case (uint8_t)MuscleID::ECRL:
            flags[(uint8_t)MuscleID::EIP] = 1;
            break;
        case (uint8_t)MuscleID::ECU:
            flags[(uint8_t)MuscleID::EDM] = 1;
            break;
    }
}

void applyGraspCurrent(uint8_t ID){
    switch (ID){
        case (uint8_t)MuscleID::IndexFDP:
        case (uint8_t)MuscleID::MiddleFDP:
        case (uint8_t)MuscleID::RingFDP:
        case (uint8_t)MuscleID::PinkyFDP:
            sw_current_velocity.data[ID].goal_current = MAX_FLEX_CURRENT;
            break;
        case (uint8_t)MuscleID::FPL:
            sw_current_velocity.data[ID].goal_current = THUMB_FLEX_CURRENT;
            break;
        case (uint8_t)MuscleID::EIP:
        case (uint8_t)MuscleID::EDM:
        case (uint8_t)MuscleID::ED:
            sw_current_velocity.data[ID].goal_current = MAX_EXTENS_CURRENT;
            break;
        case (uint8_t)MuscleID::SPN:
        case (uint8_t)MuscleID::PQ:
            sw_current_velocity.data[ID].goal_current = MIN_CURRENT;
            break;
        case (uint8_t)MuscleID::APM:
        case (uint8_t)MuscleID::APB:
        case (uint8_t)MuscleID::OPM:
        case (uint8_t)MuscleID::EPB:
        case (uint8_t)MuscleID::EPL:
        case (uint8_t)MuscleID::APL:
            sw_current_velocity.data[ID].goal_current = GENERAL_CURRENT;
            break;
        case (uint8_t)MuscleID::FCR:
        case (uint8_t)MuscleID::FCU:
        case (uint8_t)MuscleID::ECRL:
        case (uint8_t)MuscleID::ECU:
            sw_current_velocity.data[ID].goal_current = CARPAL_CURRENT;
            break;
        case (uint8_t)MuscleID::BPB:
        case (uint8_t)MuscleID::PT:
            sw_current_velocity.data[ID].goal_current = SP_CURRENT;
            break;
    }
}

void propagateCoopFlags(int8_t *flags){
    const uint8_t EIP = (uint8_t)MuscleID::EIP;
    const uint8_t EDM = (uint8_t)MuscleID::EDM;
    const uint8_t ED  = (uint8_t)MuscleID::ED;
    const uint8_t FPL = (uint8_t)MuscleID::FPL;
    const uint8_t IndexFDP = (uint8_t)MuscleID::IndexFDP;
    const uint8_t PinkyFDP = (uint8_t)MuscleID::PinkyFDP;
    const uint8_t MiddleFDP = (uint8_t)MuscleID::MiddleFDP;
    const uint8_t RingFDP = (uint8_t)MuscleID::RingFDP;

    if (flags[EIP] && flags[EDM]){
        flags[ED] = 1;
        flags[FPL] = 1;
        sw_current_velocity.data[ED].goal_current = 0;
        sw_current_velocity.data[FPL].goal_current = 0;
    }
    if (flags[IndexFDP] && flags[PinkyFDP]){
        flags[MiddleFDP] = 1;
        flags[RingFDP] = 1;
        sw_current_velocity.data[MiddleFDP].goal_current = 0;
        sw_current_velocity.data[RingFDP].goal_current = 0;
    }
}
