#include "logging.h"
#include "config.h"

void printCsvHeader(Stream &s){
    s.print("timestamp,");
    for (uint8_t i = 1; i <= SERVO_NUM; i++){
        s.print("cur_"); s.print(i); s.print(",");
        s.print("pos_"); s.print(i); s.print(",");
    }
    s.println();
}
