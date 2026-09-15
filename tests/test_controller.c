/* SPDX-License-Identifier: MIT */
#include "controller.h"
#include <stdio.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "check failed at %d\n", __LINE__); return 1; } } while (0)
static bool off(const osc_controller *c) {
    return !(c->outputs.heater || c->outputs.pump || c->outputs.valve ||
             c->outputs.grinder || c->outputs.brew_motor);
}
int main(void) {
    osc_controller c;
    osc_init(&c);
    CHECK(c.state == OSC_BOOT && off(&c));
    CHECK(osc_start(&c) == OSC_REJECTED_NOT_IMPLEMENTED && off(&c));
    osc_tick(&c, true, true);
    CHECK(c.state == OSC_SAFE_IDLE && off(&c));
    CHECK(osc_start(&c) == OSC_REJECTED_NOT_IMPLEMENTED && off(&c));
    osc_tick(&c, false, true);
    CHECK(c.state == OSC_FAULT && off(&c));
    osc_tick(&c, true, true);
    osc_stop(&c);
    CHECK(c.state == OSC_FAULT && off(&c));
    CHECK(osc_start(&c) == OSC_REJECTED_NOT_IMPLEMENTED && off(&c));
    osc_init(&c);
    osc_tick(&c, true, false);
    CHECK(c.state == OSC_FAULT && off(&c));
    return 0;
}
