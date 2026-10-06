/* SPDX-License-Identifier: MIT */
#include "controller.h"
#include <stdio.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "check failed at %d\n", __LINE__); return 1; } } while (0)
static bool off(const osc_controller *c) {
    return !(c->outputs.heater || c->outputs.pump || c->outputs.valve ||
             c->outputs.grinder || c->outputs.brew_motor || c->outputs.mains);
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
    CHECK(!osc_clear_fault(&c, true, false) && c.state == OSC_FAULT && off(&c));
    CHECK(!osc_clear_fault(&c, false, true) && c.state == OSC_FAULT);
    CHECK(osc_clear_fault(&c, true, true) && c.state == OSC_SAFE_IDLE && off(&c));
    CHECK(!osc_clear_fault(&c, true, true) && c.state == OSC_SAFE_IDLE);
    CHECK(osc_heater_cycles_allowed(false) == OSC_HEATER_WINDOW_CYCLES);
    CHECK(osc_heater_cycles_allowed(true) == 3u);
    CHECK(osc_heater_cycles_allowed(true) < OSC_HEATER_WINDOW_CYCLES);
    /* Grinder current: stall, light running and a drop from the loaded current. */
    CHECK(osc_grinder_verdict(900, 0) == OSC_GRIND_OK);
    CHECK(osc_grinder_verdict(3000, 900) == OSC_GRIND_JAM);
    CHECK(osc_grinder_verdict(OSC_GRINDER_JAM_MA, 0) == OSC_GRIND_JAM);
    CHECK(osc_grinder_verdict(450, 0) == OSC_GRIND_EMPTY);
    CHECK(osc_grinder_verdict(650, 1000) == OSC_GRIND_EMPTY);  /* 65 % of the loaded current */
    CHECK(osc_grinder_verdict(800, 1000) == OSC_GRIND_OK);
    CHECK(osc_grinder_verdict(650, 0) == OSC_GRIND_OK);        /* no reference yet */
    /* Dose: the press raises the brew-unit current over I0. */
    CHECK(osc_dose_present(200, 300));
    CHECK(!osc_dose_present(200, 220));
    CHECK(osc_dose_present(200, 200 + OSC_DOSE_MIN_RISE_MA));
    return 0;
}
