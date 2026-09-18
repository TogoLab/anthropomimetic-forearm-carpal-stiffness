#include "teaching.h"
#include "control.h"

static void initEndlessWinding(){
    DEBUG_SERIAL.println("Turn 0 Infinite mechanism");
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
        if (!muscles[i]->isEndlessWinding()) continue;
        dxl.torqueOn(i);
        delay(100);
    }
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
        if (!muscles[i]->isEndlessWinding()) continue;
        muscles[i]->moveToWithDuration(1, 6, true);
    }
}

static void torqueOffAll(){
    for (uint8_t i = 0; i < SERVO_NUM; i++){
        dxl.torqueOff(i);
    }
}

static void applyPoseCurrent(){
    for (auto *f  : fingers)  sw_current_velocity.data[f->getId()].goal_current  = TEACHING_FINGER_CURRENT;
    for (auto *w  : wrists)   sw_current_velocity.data[w->getId()].goal_current  = TEACHING_WRIST_CURRENT;
    for (auto *fo : forearms) sw_current_velocity.data[fo->getId()].goal_current = TEACHING_FOREARM_CURRENT;
    sw_current_velocity.markChanged();
    sw_current_velocity.write("Current and Velocity");
}

static String readCommand(){
    waitForSerialInput();
    String s = DEBUG_SERIAL.readStringUntil('\n');
    s.trim();
    return s;
}

static void writePosToSD(int16_t *pos){
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
        pos[i] = dxl.getPresentPosition(i, UNIT_RAW);
    }
    DEBUG_SERIAL.println("WROTE");
    DEBUG_SERIAL.println("SHOW POSITIONS");
    writeArrayToSD(pos);
    for (uint8_t i = 0; i < SERVO_NUM; i++)
    {
        DEBUG_SERIAL.print(pos[i]);
        DEBUG_SERIAL.print(", ");
    }
}

static void runTeachCycle(bool useEndlessMecha){
    dxlModeSetup(OP_CURRENT_BASED_POSITION);
    if (useEndlessMecha) initEndlessWinding();
    dxlModeSetup(OP_CURRENT);

    bool posed = false;
    DEBUG_SERIAL.println("TEACHING");
    DEBUG_SERIAL.println("OK? ENTER Y");
    while (true){
        String cmd = readCommand();
        if (cmd.equalsIgnoreCase("Y")){
            if (posed) return;
            posed = true;
            DEBUG_SERIAL.print("TORQUE ON");
            torqueOnExceptEndless(useEndlessMecha);
            applyPoseCurrent();
            DEBUG_SERIAL.println("TEACHING FINISH? ENTER Y OR N");
        } else if (cmd.equalsIgnoreCase("N")){
            torqueOffAll();
            dxlModeSetup(OP_CURRENT_BASED_POSITION);
            if (useEndlessMecha) initEndlessWinding();
            DEBUG_SERIAL.println("TORQUE OFF");
            DEBUG_SERIAL.println("POSE OK? ENTER Y");
            posed = false;
        }
    }
}

static bool promptContinueTeaching(){
    while (DEBUG_SERIAL.available()) DEBUG_SERIAL.read();
    DEBUG_SERIAL.print("Write position. Continue?(Y/N): ");
    DEBUG_SERIAL.println();
    while (true){
        String s = readCommand();
        if (s.equalsIgnoreCase("y")) return true;
        if (s.equalsIgnoreCase("n")) return false;
    }
}

void teachingMode(bool useEndlessMecha){
    int16_t pos[SERVO_NUM] = {};
    while (true){
        runTeachCycle(useEndlessMecha);
        writePosToSD(pos);
        if (!promptContinueTeaching()) break;
    }
    dxlModeSetup(OP_CURRENT_BASED_POSITION);
    DEBUG_SERIAL.println("TEACHING MODE FINISH");
}
