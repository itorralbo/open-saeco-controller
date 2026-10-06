/* SPDX-License-Identifier: MIT */
#include "service.h"
#include <string.h>

static void off(osc_service *s) { memset(&s->out, 0, sizeof s->out); }

void svc_init(osc_service *s) { memset(s, 0, sizeof *s); }

bool svc_running(const osc_service *s) { return s->r.phase == OSC_TEST_RUNNING; }

bool svc_drives(const osc_service *s) { return s->r.id != OSC_TEST_INPUTS && s->r.id != OSC_TEST_NONE; }

static bool needs_door(uint8_t id) {
    return id == OSC_TEST_BREW_UNIT || id == OSC_TEST_PUMP || id == OSC_TEST_HEATER ||
           id == OSC_TEST_GRINDER || id == OSC_TEST_DOSE;
}

static bool moves_unit(uint8_t id) { return id == OSC_TEST_BREW_UNIT || id == OSC_TEST_DOSE; }

static void finish(osc_service *s, osc_test_phase phase, osc_test_reason why, uint32_t now) {
    off(s);
    s->r.phase = (uint8_t)phase;
    s->r.reason = (uint8_t)why;
    s->r.elapsed_ms = now - s->t0;
}

void svc_abort(osc_service *s, osc_test_reason why, uint32_t now) {
    if (svc_running(s)) finish(s, OSC_TEST_ABORTED, why, now);
}

static void next(osc_service *s, uint32_t now) {
    s->r.step++;
    s->t_step = now;
}

osc_test_reason svc_start(osc_service *s, uint8_t id, uint16_t param, const osc_inputs *in,
                          bool core_idle, uint32_t now) {
    osc_test_reason why = OSC_REASON_OK;
    if (id == OSC_TEST_NONE || id >= OSC_TEST_COUNT) why = OSC_REASON_UNKNOWN;
    else if (svc_running(s)) why = OSC_REASON_STATE;
    else if (id != OSC_TEST_INPUTS && !core_idle) why = OSC_REASON_STATE;
    else if (needs_door(id) && !in->door_closed) why = OSC_REASON_DOOR;
    else if (moves_unit(id) && !in->bu_present) why = OSC_REASON_UNIT;
    else if (moves_unit(id) && in->brew_fault) why = OSC_REASON_DRIVER;
    else if (id == OSC_TEST_HEATER && in->boiler_dc == OSC_TEMP_INVALID) why = OSC_REASON_SENSOR;
    if (why == OSC_REASON_OK) {
        switch (id) {
        case OSC_TEST_PUMP:
            if (!param) param = 100; /* ml */
            if (param < 10 || param > 500) why = OSC_REASON_PARAM;
            break;
        case OSC_TEST_HEATER:
            if (!param) param = 90; /* degC */
            if (param < 40 || param > 105) why = OSC_REASON_PARAM;
            else if (in->boiler_dc >= (int16_t)(param * 10)) why = OSC_REASON_LIMIT;
            break;
        case OSC_TEST_GRINDER:
        case OSC_TEST_DOSE:
            if (!param) param = id == OSC_TEST_DOSE ? SVC_DOSE_GRIND_MS : 3000u; /* ms */
            if (param < 500 || param > OSC_GRINDER_MAX_ON_MS) why = OSC_REASON_PARAM;
            break;
        default:
            break;
        }
    }
    memset(s, 0, sizeof *s);
    s->r.id = id;
    s->param = param;
    s->t0 = s->t_step = now;
    s->edges0 = in->flow_edges;
    if (why != OSC_REASON_OK) {
        s->r.phase = OSC_TEST_REFUSED;
        s->r.reason = (uint8_t)why;
        return why;
    }
    s->r.phase = OSC_TEST_RUNNING;
    s->r.step = 1;
    return OSC_REASON_OK;
}

static void inputs_test(osc_service *s, const osc_inputs *in, uint32_t t) {
    int32_t *v = s->r.value;
    v[0] = in->door_closed;
    v[1] = in->bu_present;
    v[2] = in->bu_work;
    v[3] = in->water;
    v[4] = in->boiler_dc;
    v[5] = in->rail_24v_mv;
    if (t >= SVC_INPUTS_MS) finish(s, OSC_TEST_DONE, OSC_REASON_OK, s->t0 + t);
}

static void brew_test(osc_service *s, const osc_inputs *in, uint32_t now) {
    int32_t *v = s->r.value;
    const uint32_t ts = now - s->t_step;
    switch (s->r.step) {
    case 1: /* toward the work switch */
        s->out.brew_motor = true;
        s->out.brew_forward = true;
        if (ts < SVC_BREW_PEAK_MS) {
            if ((int32_t)in->brew_ma > s->peak) s->peak = in->brew_ma;
        } else {
            s->acc += in->brew_ma;
            s->n++;
        }
        if (in->bu_work) {
            v[0] = (int32_t)ts;
            v[1] = s->n ? s->acc / s->n : 0;
            v[2] = s->peak;
            v[3] = in->brew_ma;
            off(s);
            next(s, now);
        } else if (ts >= SVC_BREW_TIMEOUT_MS) {
            finish(s, OSC_TEST_ABORTED, OSC_REASON_TIMEOUT, now);
        }
        break;
    case 2: /* settle */
        if (ts >= 300u) next(s, now);
        break;
    case 3: /* back for as long as it took to get there */
        s->out.brew_motor = true;
        s->out.brew_forward = false;
        if (ts >= (uint32_t)v[0]) {
            v[4] = (int32_t)ts;
            finish(s, OSC_TEST_DONE, OSC_REASON_OK, now);
        }
        break;
    default:
        break;
    }
}

/* Relay or valve held for 'ms': 24 V before and in the middle of the run. */
static void hold_test(osc_service *s, const osc_inputs *in, uint32_t now, bool valve, uint32_t ms) {
    int32_t *v = s->r.value;
    const uint32_t t = now - s->t0;
    if (t == 0 || !v[0]) v[0] = in->rail_24v_mv;
    if (valve) s->out.valve = true;
    else s->out.mains = true;
    if (t >= ms / 2u && !v[1]) v[1] = in->rail_24v_mv;
    if (t >= ms) {
        v[2] = (int32_t)t;
        finish(s, OSC_TEST_DONE, OSC_REASON_OK, now);
    }
}

static int32_t pulses_to_ml10(int32_t pulses) {
    return (int32_t)((int64_t)pulses * 10000 / SVC_FLOW_PULSES_PER_L);
}

static void pump_test(osc_service *s, const osc_inputs *in, uint32_t now) {
    int32_t *v = s->r.value;
    const uint32_t ts = now - s->t_step;
    const int32_t pulses = (int32_t)(in->flow_edges - s->edges0);
    const int32_t target = (int32_t)((uint32_t)s->param * SVC_FLOW_PULSES_PER_L / 1000u);
    switch (s->r.step) {
    case 1: /* arm */
        s->out.mains = true;
        v[4] = in->boiler_dc;
        if (ts >= SVC_ARM_MS) {
            s->edges0 = in->flow_edges;
            next(s, now);
        }
        break;
    case 2: /* pump */
        s->out.mains = s->out.pump = true;
        v[0] = (int32_t)ts;
        v[1] = pulses;
        v[2] = pulses_to_ml10(pulses);
        v[3] = ts ? (int32_t)((int64_t)v[2] * 10000 / (int32_t)ts) : 0; /* ml/s x100 */
        v[5] = in->boiler_dc;
        if (pulses == 0 && ts >= SVC_PUMP_DRY_MS) finish(s, OSC_TEST_ABORTED, OSC_REASON_NO_FLOW, now);
        else if (pulses >= target || ts >= SVC_PUMP_MAX_MS) {
            s->out.pump = false;
            next(s, now);
        }
        break;
    case 3: /* release the relay after the pump */
        s->out.mains = true;
        if (ts >= SVC_ARM_MS) finish(s, OSC_TEST_DONE, OSC_REASON_OK, now);
        break;
    default:
        break;
    }
}

static void heater_test(osc_service *s, const osc_inputs *in, uint32_t now) {
    int32_t *v = s->r.value;
    const uint32_t ts = now - s->t_step;
    const int16_t target = (int16_t)(s->param * 10);
    if (in->boiler_dc == OSC_TEMP_INVALID) {
        finish(s, OSC_TEST_ABORTED, OSC_REASON_SENSOR, now);
        return;
    }
    if (in->boiler_dc > SVC_HEATER_LIMIT_DC) {
        finish(s, OSC_TEST_ABORTED, OSC_REASON_LIMIT, now);
        return;
    }
    if (in->boiler_dc > s->peak) s->peak = in->boiler_dc;
    switch (s->r.step) {
    case 1: /* arm */
        s->out.mains = true;
        v[0] = in->boiler_dc;
        s->peak = in->boiler_dc;
        if (ts >= SVC_ARM_MS) next(s, now);
        break;
    case 2: /* heat to the target */
        s->out.mains = s->out.heater = true;
        v[1] = in->boiler_dc;
        v[2] = (int32_t)ts;
        v[3] = ts ? (int32_t)((int64_t)(v[1] - v[0]) * 10000 / (int32_t)ts) : 0; /* 0.01 degC/s */
        if (in->boiler_dc >= target) {
            s->out.heater = false;
            next(s, now);
        } else if (ts >= SVC_HEATER_MAX_MS) {
            finish(s, OSC_TEST_ABORTED, OSC_REASON_TIMEOUT, now);
        }
        break;
    case 3: /* coast: overshoot */
        s->out.mains = ts < SVC_ARM_MS;
        v[4] = s->peak;
        v[5] = s->peak - target;
        if (ts >= SVC_HEATER_COAST_MS) finish(s, OSC_TEST_DONE, OSC_REASON_OK, now);
        break;
    default:
        break;
    }
}

/* One grinder control tick: the zero-corrected current into 100 ms blocks,
 * the start peak, the loaded reference and the verdict. Returns the verdict
 * of the block just closed, OSC_GRIND_OK otherwise. */
static osc_grind_verdict grind_tick(osc_service *s, const osc_inputs *in, uint32_t ts,
                                    int32_t *peak, int32_t *last) {
    const int32_t ma = in->grinder_ma - s->zero;
    int32_t mean;
    osc_grind_verdict verdict;
    if (ts < OSC_GRINDER_START_MS) {
        if (ma > *peak) *peak = ma;
        return OSC_GRIND_OK;
    }
    s->blk_acc += ma;
    if (++s->blk_n * 10 < (int32_t)OSC_GRINDER_BLOCK_MS) return OSC_GRIND_OK;
    mean = s->blk_acc / s->blk_n;
    s->blk_acc = s->blk_n = 0;
    *last = mean;
    verdict = osc_grinder_verdict((int)mean, s->loaded_n >= 3 ? (int)(s->loaded / s->loaded_n) : 0);
    /* The first three blocks above the empty line set the loaded current. */
    if (verdict == OSC_GRIND_OK && s->loaded_n < 3) {
        s->loaded += mean;
        s->loaded_n++;
    }
    if (verdict == OSC_GRIND_EMPTY) {
        if (++s->light < (int32_t)OSC_GRINDER_EMPTY_BLOCKS) return OSC_GRIND_OK;
    } else {
        s->light = 0;
    }
    return verdict;
}

static int32_t loaded_mean(const osc_service *s) { return s->loaded_n ? s->loaded / s->loaded_n : 0; }

static osc_test_reason grind_reason(osc_grind_verdict v) {
    return v == OSC_GRIND_JAM ? OSC_REASON_JAM : OSC_REASON_NO_BEANS;
}

static void grinder_test(osc_service *s, const osc_inputs *in, uint32_t now) {
    int32_t *v = s->r.value;
    const uint32_t ts = now - s->t_step;
    osc_grind_verdict verdict;
    switch (s->r.step) {
    case 1: /* arm K701; the sensor's zero with the motor off */
        s->out.mains = true;
        if (!s->n) {
            s->zero = in->grinder_ma;
            s->n = 1;
        }
        v[4] = s->zero;
        if (ts >= SVC_ARM_MS) next(s, now);
        break;
    case 2:
        s->out.mains = s->out.grinder = true;
        v[0] = (int32_t)ts;
        verdict = grind_tick(s, in, ts, &v[1], &v[3]);
        v[2] = loaded_mean(s);
        if (ts >= s->param / 2u && !v[5]) v[5] = in->rail_24v_mv;
        if (verdict != OSC_GRIND_OK) {
            finish(s, OSC_TEST_ABORTED, grind_reason(verdict), now);
        } else if (ts >= s->param) {
            s->out.grinder = false;
            next(s, now);
        }
        break;
    case 3:
        s->out.mains = true;
        if (ts >= SVC_ARM_MS) finish(s, OSC_TEST_DONE, OSC_REASON_OK, now);
        break;
    default:
        break;
    }
}

/* Grind, then press the dose with the brew unit and bring it back. */
static void dose_test(osc_service *s, const osc_inputs *in, uint32_t now) {
    int32_t *v = s->r.value;
    const uint32_t ts = now - s->t_step;
    osc_grind_verdict verdict;
    int32_t peak = 0, last = 0;
    switch (s->r.step) {
    case 1:
        s->out.mains = true;
        if (!s->n) {
            s->zero = in->grinder_ma;
            s->n = 1;
        }
        if (ts >= SVC_ARM_MS) next(s, now);
        break;
    case 2:
        s->out.mains = s->out.grinder = true;
        v[0] = (int32_t)ts;
        verdict = grind_tick(s, in, ts, &peak, &last);
        v[1] = loaded_mean(s);
        v[2] = (int32_t)verdict;
        if (verdict != OSC_GRIND_OK) {
            finish(s, OSC_TEST_ABORTED, grind_reason(verdict), now);
        } else if (ts >= s->param) {
            s->out.grinder = false;
            next(s, now);
        }
        break;
    case 3: /* K701 open after the grinder, then the unit */
        s->out.mains = true;
        if (ts >= SVC_ARM_MS) {
            off(s);
            s->acc = s->n = 0;
            next(s, now);
        }
        break;
    case 4: /* press: I0 after the start, the current at the work switch */
        s->out.brew_motor = s->out.brew_forward = true;
        if (ts >= SVC_BREW_PEAK_MS && ts < SVC_BREW_PEAK_MS + SVC_DOSE_I0_MS) {
            s->acc += in->brew_ma;
            s->n++;
        }
        if (in->bu_work) {
            v[3] = s->n ? s->acc / s->n : 0;
            v[4] = (int32_t)in->brew_ma - v[3];
            v[5] = osc_dose_present((int)v[3], (int)in->brew_ma);
            s->peak = (int32_t)ts; /* travel time, for the way back */
            off(s);
            next(s, now);
        } else if (ts >= SVC_BREW_TIMEOUT_MS) {
            finish(s, OSC_TEST_ABORTED, OSC_REASON_TIMEOUT, now);
        }
        break;
    case 5:
        if (ts >= 300u) next(s, now);
        break;
    case 6:
        s->out.brew_motor = true;
        s->out.brew_forward = false;
        if (ts >= (uint32_t)s->peak)
            finish(s, OSC_TEST_DONE, v[5] ? OSC_REASON_OK : OSC_REASON_NO_DOSE, now);
        break;
    default:
        break;
    }
}

void svc_poll(osc_service *s, const osc_inputs *in, uint32_t now) {
    if (!svc_running(s)) return;
    s->r.elapsed_ms = now - s->t0;
    if (needs_door(s->r.id) && !in->door_closed) {
        finish(s, OSC_TEST_ABORTED, OSC_REASON_DOOR, now);
        return;
    }
    if (moves_unit(s->r.id) && in->brew_fault) {
        if (s->r.id == OSC_TEST_BREW_UNIT) s->r.value[5]++;
        finish(s, OSC_TEST_ABORTED, OSC_REASON_DRIVER, now);
        return;
    }
    switch (s->r.id) {
    case OSC_TEST_INPUTS: inputs_test(s, in, now - s->t0); break;
    case OSC_TEST_BREW_UNIT: brew_test(s, in, now); break;
    case OSC_TEST_VALVE: hold_test(s, in, now, true, SVC_VALVE_MS); break;
    case OSC_TEST_RELAY: hold_test(s, in, now, false, SVC_RELAY_MS); break;
    case OSC_TEST_PUMP: pump_test(s, in, now); break;
    case OSC_TEST_HEATER: heater_test(s, in, now); break;
    case OSC_TEST_GRINDER: grinder_test(s, in, now); break;
    case OSC_TEST_DOSE: dose_test(s, in, now); break;
    default: finish(s, OSC_TEST_ABORTED, OSC_REASON_UNKNOWN, now); break;
    }
}
