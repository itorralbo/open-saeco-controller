/* SPDX-License-Identifier: MIT */
/* Main loop of the STM32: watchdog, inputs, controller and outputs. */
#ifndef OSC_APP_H
#define OSC_APP_H
#include "bsp.h"
#include "controller.h"

/* U601 (TPS3828-33) resets after 0.9 s at the earliest without a falling
 * edge on WDI; toggling every 100 ms gives one every 200 ms. */
#define OSC_WDT_TOGGLE_MS 100u
#define OSC_CONTROL_PERIOD_MS 10u
/* The ESP32 boots in a few hundred ms; until then the core waits in BOOT. */
#define OSC_LINK_BOOT_GRACE_MS 2000u

/* Called once out of reset, then osc_app_poll() as often as possible. */
void osc_app_init(void);
void osc_app_poll(void);
const osc_controller *osc_app_controller(void);
const osc_inputs *osc_app_inputs(void);
bool osc_app_link_ok(void);
#endif
