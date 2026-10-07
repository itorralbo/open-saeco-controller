/* SPDX-License-Identifier: MIT */
#include "controller.h"
static void disable(osc_controller *c) {
    const osc_outputs off = {false, false, false, false, false, false, false};
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
bool osc_clear_fault(osc_controller *c, bool interlocks_ok, bool link_ok) {
    disable(c);
    if (c->state != OSC_FAULT || !interlocks_ok || !link_ok) return false;
    c->state = OSC_SAFE_IDLE;
    return true;
}
unsigned osc_heater_cycles_allowed(bool grinder_on) {
    return grinder_on ? OSC_HEATER_CYCLES_WHILE_GRINDING : OSC_HEATER_WINDOW_CYCLES;
}

void osc_heatsink_init(osc_heatsink *h) {
    h->heatsink_c = 0.0f;
    h->primed = false;
}
void osc_heatsink_step(osc_heatsink *h, float air_c, bool air_ok, float heater_frac,
                       bool pump_on, bool grinder_on, float dt_s) {
    float air = air_ok ? air_c : OSC_HS_AIR_FALLBACK_C;
    float watts, flow;
    if (heater_frac < 0.0f) heater_frac = 0.0f;
    if (heater_frac > 1.0f) heater_frac = 1.0f;
    if (!h->primed || h->heatsink_c < air) {
        /* Never colder than the air: a start, or a sensor back from fault. */
        h->heatsink_c = h->primed && h->heatsink_c > air ? h->heatsink_c : air;
        h->primed = true;
    }
    watts = heater_frac * OSC_HEATER_TRIAC_W + (pump_on ? OSC_PUMP_TRIAC_W : 0.0f) +
            (grinder_on ? OSC_GRINDER_TRIAC_W : 0.0f);
    flow = watts - (h->heatsink_c - air) / OSC_HS_RTH_HA_C_PER_W;
    h->heatsink_c += flow * dt_s / OSC_HS_CAPACITY_J_PER_C;
    if (h->heatsink_c < air) h->heatsink_c = air;
}
float osc_heater_junction_full_c(const osc_heatsink *h) {
    return h->heatsink_c + OSC_HEATER_TRIAC_W * OSC_HS_RTH_JH_C_PER_W;
}
unsigned osc_heater_cycles_thermal(const osc_heatsink *h) {
    float tj = osc_heater_junction_full_c(h);
    float share;
    if (!h->primed || tj >= OSC_TJ_CUTOFF_C) return 0u;
    if (tj <= OSC_TJ_DERATE_C) return OSC_HEATER_WINDOW_CYCLES;
    share = (OSC_TJ_CUTOFF_C - tj) / (OSC_TJ_CUTOFF_C - OSC_TJ_DERATE_C);
    return (unsigned)(share * (float)OSC_HEATER_WINDOW_CYCLES);
}

osc_grind_verdict osc_grinder_verdict(int mean_ma, int loaded_ma) {
    if (mean_ma >= OSC_GRINDER_JAM_MA) return OSC_GRIND_JAM;
    if (mean_ma < OSC_GRINDER_EMPTY_MA) return OSC_GRIND_EMPTY;
    if (loaded_ma > 0 && (long)mean_ma * 100 < (long)loaded_ma * OSC_GRINDER_EMPTY_DROP_PCT)
        return OSC_GRIND_EMPTY;
    return OSC_GRIND_OK;
}

bool osc_dose_present(int i0_ma, int stop_ma) { return stop_ma - i0_ma >= OSC_DOSE_MIN_RISE_MA; }
