/* SPDX-License-Identifier: MIT */
#include "app.h"
#include "osc_hal.h"

static osc_controller ctl;
static osc_inputs inputs;
static uint32_t last_toggle, last_control;

void osc_app_init(void) {
    const osc_inputs none = {false, false, false, false, 0, 0, 0, 0, 0, 0};
    bsp_init();
    osc_init(&ctl);
    inputs = none;
    last_toggle = last_control = osc_hal_millis();
}

void osc_app_poll(void) {
    const uint32_t now = osc_hal_millis();
    if (now - last_toggle >= OSC_WDT_TOGGLE_MS) {
        last_toggle = now;
        bsp_watchdog_toggle();
    }
    if (now - last_control >= OSC_CONTROL_PERIOD_MS) {
        last_control = now;
        bsp_read(&inputs);
        /* No ESP32 link until protocol v0 exists, so the core stays in
         * OSC_FAULT with every load off. */
        osc_tick(&ctl, inputs.door_closed && !inputs.brew_fault, false);
        bsp_write(&ctl.outputs);
    }
}

const osc_controller *osc_app_controller(void) { return &ctl; }
const osc_inputs *osc_app_inputs(void) { return &inputs; }
