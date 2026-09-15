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
#endif
