# Firmware patch: `Goal` command for host scripting

Status: **APPLIED to source (`unit_test/src/main.cpp`), not yet flashed
to Teensy.** Required by the sim2real `run_static_handoff.py` runner
once we move out of `--dry-run`. Flash via `pio run -t upload` from
the `unit_test/` directory.

## Why

The current Teensy command set is interactive (`Teach`, `Start`,
`Static`, ...) — they prompt the user, then wait for a `readStringUntil`
on each step. That's fine for hands-on testing, but it means the host
PC cannot drive the rig from a script: there is no single-line "set
all 22 goal positions and acknowledge" command.

`cmdManual` looks like it should fill this role, but
[main.cpp:119-135](../src/main.cpp) shows that it parses the 22 CSV
ints from serial and never calls `sweepRunGoalPosition` — the parsed
`target[]` falls out of scope and the motors don't move.

## Protocol (two-line, matches existing handler idiom)

Host -> Teensy:

```
Goal\n
1234,5678,1024,...,2048\n     (22 ints, comma-separated)
```

Teensy -> host:

```
OK\n            (success: motors are being driven)
ERR:<reason>\n  (parse error or wrong count)
```

No interactive prompts. The two-line form matches how `cmdManual`,
`cmdDirection`, `cmdFingerDrive` already parse their inputs, so the
dispatch loop in `main.cpp:loop()` does not need to change.

## Patch

Append to `unit_test/src/main.cpp`:

```cpp
static void cmdGoal(){
  // Read the rest of the line after "Goal" -- expects ":1234,5678,...\n"
  String input = DEBUG_SERIAL.readStringUntil('\n');
  input.trim();
  int colon = input.indexOf(':');
  String csv = (colon >= 0) ? input.substring(colon + 1) : input;

  char buf[256];
  csv.toCharArray(buf, sizeof(buf));
  char* token = strtok(buf, ",");
  int32_t target[SERVO_NUM] = {};
  int8_t  torque_control_flags[SERVO_NUM] = {};
  int32_t e_angles[SERVO_NUM] = {};
  int count = 0;
  while (token != NULL && count < SERVO_NUM) {
    target[count++] = atoi(token);
    token = strtok(NULL, ",");
  }
  if (count != SERVO_NUM) {
    DEBUG_SERIAL.print("ERR:expected ");
    DEBUG_SERIAL.print(SERVO_NUM);
    DEBUG_SERIAL.print(" ints, got ");
    DEBUG_SERIAL.println(count);
    return;
  }
  sweepRunGoalPosition(target, e_angles, torque_control_flags,
                        MOVING_TIME, millis());
  DEBUG_SERIAL.println("OK");
}
```

And add to the `COMMANDS[]` array near line 213:

```cpp
{"Goal",        cmdGoal},
```

## Host-side expectation

`sim2real/dxl_host.py:send_goals` already implements the two-line
protocol:

```python
self._write_line("Goal")
self._write_line(",".join(str(x) for x in ints))
ack = self._wait_for_ack("OK")
```

The colon prefix removal in `cmdGoal` above tolerates either `Goal\nN,N,..\n`
or `Goal\n:N,N,..\n` (defensive against a future single-line variant).

## Testing plan after flashing

1. `python -m sim2real.dxl_host --port COMx --action show` — confirm
   existing `Show` still parses (regression check).
2. `python -m sim2real.dxl_host --port COMx --action test-goal` —
   sends all 22 motors to mid-range (2048); look for synchronised
   motion and `OK` ack.
3. `python -m sim2real.run_static_handoff --hold rest --port COMx` —
   smallest realistic move.
4. Withdrawal: if `OK` is not printed within 2 s, or if motors keep
   moving after `Relax`, do NOT proceed to keyframe sequences. Revert
   the firmware and investigate.
