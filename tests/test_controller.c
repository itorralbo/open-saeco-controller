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

    /* Heater triac derating (issue #2). */
    {
        osc_heatsink h;
        int s;
        unsigned n = 0;
        osc_heatsink_init(&h);
        CHECK(osc_heater_cycles_thermal(&h) == 0u);   /* no reading yet: no heater */
        /* A one-minute heat-up from cold air keeps full power. */
        for (s = 0; s < 60; ++s) osc_heatsink_step(&h, 25.0f, true, 1.0f, false, false, 1.0f);
        CHECK(osc_heater_cycles_thermal(&h) == OSC_HEATER_WINDOW_CYCLES);
        /* An hour of descaling with hot air and the pump on: the loop settles
         * below the cut-off, the heater is derated but not stopped. */
        osc_heatsink_init(&h);
        for (s = 0; s < 3600; ++s) {
            n = osc_heater_cycles_thermal(&h);
            if (s == 0) n = OSC_HEATER_WINDOW_CYCLES;
            osc_heatsink_step(&h, 60.0f, true, (float)n / OSC_HEATER_WINDOW_CYCLES, true, false, 1.0f);
            CHECK(osc_heater_junction_full_c(&h) < OSC_TJ_CUTOFF_C + 1.0f);
        }
        CHECK(n > 0u && n < OSC_HEATER_WINDOW_CYCLES);
        /* Steady state: junction at the cycles granted stays under 125 C. */
        CHECK(h.heatsink_c + (float)n / OSC_HEATER_WINDOW_CYCLES * OSC_HEATER_TRIAC_W *
              OSC_HS_RTH_JH_C_PER_W < 125.0f);
        /* A dead RT701 falls back to hot air and derates at once. */
        osc_heatsink_init(&h);
        for (s = 0; s < 600; ++s) osc_heatsink_step(&h, 0.0f, false, 1.0f, false, false, 1.0f);
        CHECK(osc_heater_cycles_thermal(&h) < OSC_HEATER_WINDOW_CYCLES);
        /* At the cut-off the heater stops. */
        h.heatsink_c = OSC_TJ_CUTOFF_C;
        CHECK(osc_heater_cycles_thermal(&h) == 0u);
    }
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
