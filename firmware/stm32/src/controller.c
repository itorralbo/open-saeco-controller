/* SPDX-License-Identifier: MIT */
#include "controller.h"
static void disable(osc_controller *c) {
    const osc_outputs off = {false, false, false, false, false};
    c->outputs = off;
}
void osc_init(osc_controller *c) {
    c->state = OSC_BOOT;
    disable(c);
}
void osc_tick(osc_controller *c, bool interlocks_ok, bool link_ok) {
    disable(c);
    if (!interlocks_ok || !link_ok) c->state = OSC_FAULT;
    else if (c->state == OSC_BOOT) c->state = OSC_SAFE_IDLE;
    else if (c->state != OSC_SAFE_IDLE && c->state != OSC_FAULT)
        c->state = OSC_FAULT;
}
void osc_stop(osc_controller *c) { disable(c); }
osc_result osc_start(osc_controller *c) {
    disable(c);
    return OSC_REJECTED_NOT_IMPLEMENTED;
}
unsigned osc_heater_cycles_allowed(bool grinder_on) {
    return grinder_on ? OSC_HEATER_CYCLES_WHILE_GRINDING : OSC_HEATER_WINDOW_CYCLES;
}
