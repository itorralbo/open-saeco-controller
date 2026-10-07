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

/* Heater triac derating (issue #2, hardware/power/power-architecture.md).
 * The heatsink only reaches about 8 K/W in the volume it has, so the heater
 * cannot conduct continuously with warm air inside the machine: at 253 V it
 * dissipates 8.4 W in Q703 and the junction would pass 125 C above 39 C of
 * air. A first-order model of the profile, fed by the air temperature RT701
 * reads above it and by the power each triac dissipates, estimates the
 * junction at full heater power; above OSC_TJ_DERATE_C the heater loses
 * cycles of the window, down to none at OSC_TJ_CUTOFF_C. Rth and the heat
 * capacity are ASSUMED until TH-03 measures them in a descaling run. */
#define OSC_HS_RTH_HA_C_PER_W 8.0f    /* profile to air, catalogue class for the volume */
#define OSC_HS_RTH_JH_C_PER_W 2.2f    /* BTA24 junction to case 1.7 + greased interface 0.5 */
#define OSC_HS_CAPACITY_J_PER_C 30.0f /* about 33 g of aluminium */
#define OSC_HEATER_TRIAC_W 8.4f       /* 9.2 A at 253 V */
#define OSC_PUMP_TRIAC_W 0.3f
#define OSC_GRINDER_TRIAC_W 2.5f
#define OSC_TJ_DERATE_C 105.0f
#define OSC_TJ_CUTOFF_C 120.0f
#define OSC_HS_AIR_FALLBACK_C 70.0f   /* RT701 open or shorted: assume hot air */
typedef struct { float heatsink_c; bool primed; } osc_heatsink;
void osc_heatsink_init(osc_heatsink *h);
/* air_ok false (RT701 out of its window) uses the fallback air temperature.
 * heater_frac is the share of cycles the heater conducted over dt_s. */
void osc_heatsink_step(osc_heatsink *h, float air_c, bool air_ok, float heater_frac,
                       bool pump_on, bool grinder_on, float dt_s);
/* Heater triac junction if the heater conducted every cycle from now on. */
float osc_heater_junction_full_c(const osc_heatsink *h);
/* Cycles of OSC_HEATER_WINDOW_CYCLES the heater may conduct; the caller
 * takes the lower of this and osc_heater_cycles_allowed(). */
unsigned osc_heater_cycles_thermal(const osc_heatsink *h);

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
