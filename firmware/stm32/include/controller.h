/* SPDX-License-Identifier: MIT */
#ifndef OSC_CONTROLLER_H
#define OSC_CONTROLLER_H
#include <stdbool.h>
typedef enum { OSC_BOOT, OSC_SAFE_IDLE, OSC_FAULT } osc_state;
typedef enum { OSC_REJECTED_NOT_IMPLEMENTED } osc_result;
/* brew_forward drives the unit toward the work position; mains arms K701
 * on its own (the BSP also arms it for heater, pump and grinder). */
typedef struct { bool heater, pump, valve, grinder, brew_motor, brew_forward, mains; } osc_outputs;
typedef struct { osc_state state; osc_outputs outputs; } osc_controller;
void osc_init(osc_controller *c);
void osc_tick(osc_controller *c, bool interlocks_ok, bool link_ok);
void osc_stop(osc_controller *c);
osc_result osc_start(osc_controller *c);
/* Leaves OSC_FAULT for OSC_SAFE_IDLE only when the interlocks and the link
 * are both good again; returns whether it did. */
bool osc_clear_fault(osc_controller *c, bool interlocks_ok, bool link_ok);
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

/* Grinder current through U704 (hardware/power/power-architecture.md): the
 * original machine reads it to tell an empty hopper (the motor runs light)
 * from jammed burrs (it stalls). Means over 100 ms blocks after the inrush.
 * Thresholds ASSUMED until GR-02, GR-03 and GR-08 measure the motor: the
 * stall is 230 V x 0.9 / 68 Ohm = 3.0 A mean, and the stage is checked for
 * a running current up to 1.5 A. */
#define OSC_GRINDER_START_MS 300u
#define OSC_GRINDER_BLOCK_MS 100u
#define OSC_GRINDER_JAM_MA 2000
#define OSC_GRINDER_EMPTY_MA 550
#define OSC_GRINDER_EMPTY_DROP_PCT 75   /* of the current loaded at the start */
#define OSC_GRINDER_EMPTY_BLOCKS 2u     /* consecutive light blocks */
typedef enum { OSC_GRIND_OK = 0, OSC_GRIND_EMPTY = 1, OSC_GRIND_JAM = 2 } osc_grind_verdict;
/* mean_ma: one block; loaded_ma: the reference from the first loaded blocks,
 * 0 while there is none. */
osc_grind_verdict osc_grinder_verdict(int mean_ma, int loaded_ma);

/* Brew-unit compression: with ground coffee in the chamber the current at
 * the work stop rises over the running current I0 (manual: I0 + 55 to
 * 200 mA); an empty chamber barely raises it. ASSUMED until BU-05. */
#define OSC_DOSE_MIN_RISE_MA 40
bool osc_dose_present(int i0_ma, int stop_ma);
#endif
