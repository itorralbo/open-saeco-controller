/* SPDX-License-Identifier: MIT */
/* Set-up tests (firmware/common/service_ids.h): bounded, abortable runs of
 * single loads that measure what the board can see and give the operator a
 * steady load to measure with a clamp. The core only lets them drive loads
 * from OSC_SAFE_IDLE, and every one stops on STOP, link loss, an open door
 * or a driver fault. */
#ifndef OSC_SERVICE_H
#define OSC_SERVICE_H
#include <stdbool.h>
#include <stdint.h>
#include "bsp.h"
#include "controller.h"
#include "proto.h"
#include "service_ids.h"

#define SVC_ARM_MS 100u          /* K701 closes before a mains load and opens after it */
#define SVC_INPUTS_MS 3000u
#define SVC_BREW_TIMEOUT_MS 10000u /* travel ASSUMED ~3 s at 24 V, ~5 s at the min rail (BU-03) */
#define SVC_BREW_PEAK_MS 200u    /* start peak window, then the running mean */
#define SVC_VALVE_MS 2000u
#define SVC_RELAY_MS 1000u
#define SVC_PUMP_MAX_MS 30000u
#define SVC_PUMP_DRY_MS 3000u    /* no flow pulse by then: dry or blocked */
#define SVC_FLOW_PULSES_PER_L 1925u
#define SVC_HEATER_MAX_MS 60000u
#define SVC_HEATER_COAST_MS 15000u
#define SVC_HEATER_LIMIT_DC 1100 /* 110 degC */

typedef struct {
    osc_test_report r;
    osc_outputs out;
    uint16_t param;
    uint32_t t0, t_step, edges0;
    int32_t acc, n, peak;
} osc_service;

void svc_init(osc_service *s);
/* Loads the test; returns OSC_REASON_OK or why it was refused. core_idle is
 * OSC_SAFE_IDLE; tests without loads also run with the core in OSC_FAULT. */
osc_test_reason svc_start(osc_service *s, uint8_t id, uint16_t param, const osc_inputs *in,
                          bool core_idle, uint32_t now);
void svc_poll(osc_service *s, const osc_inputs *in, uint32_t now);
void svc_abort(osc_service *s, osc_test_reason why, uint32_t now);
bool svc_running(const osc_service *s);
/* Whether the loaded test drives any output. */
bool svc_drives(const osc_service *s);
#endif
