/* SPDX-License-Identifier: MIT */
#ifndef OSC_CONTROLLER_H
#define OSC_CONTROLLER_H
#include <stdbool.h>
typedef enum { OSC_BOOT, OSC_SAFE_IDLE, OSC_FAULT } osc_state;
typedef enum { OSC_REJECTED_NOT_IMPLEMENTED } osc_result;
typedef struct { bool heater, pump, valve, grinder, brew_motor; } osc_outputs;
typedef struct { osc_state state; osc_outputs outputs; } osc_controller;
void osc_init(osc_controller *c);
void osc_tick(osc_controller *c, bool interlocks_ok, bool link_ok);
void osc_stop(osc_controller *c);
osc_result osc_start(osc_controller *c);
/* Load sharing on the relay-switched phase (hardware/power/power-architecture.md).
 * Heater 8.4 A plus a grinder sized for 3 A would draw 11.6 A through F701
 * (T10A) and JP17 (10 A per VH contact). While the grinder runs the heater
 * conducts at most 3 whole mains cycles in every window of 5: 8.4 A x
 * sqrt(0.6) = 6.5 A, 9.7 A with grinder and pump. Each grind lasts at most
 * OSC_GRINDER_MAX_ON_MS, the most BR701 takes at 3 A without a pause. */
#define OSC_HEATER_WINDOW_CYCLES 5u
#define OSC_HEATER_CYCLES_WHILE_GRINDING 3u
#define OSC_GRINDER_MAX_ON_MS 10000u
unsigned osc_heater_cycles_allowed(bool grinder_on);
#endif
