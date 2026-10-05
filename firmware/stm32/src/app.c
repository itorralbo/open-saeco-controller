/* SPDX-License-Identifier: MIT */
#include "app.h"
#include "osc_hal.h"
#include "proto.h"
#include "service.h"

static osc_controller ctl;
static osc_inputs inputs;
static osc_parser parser;
static osc_service svc;
static uint32_t last_toggle, last_control, last_status, last_rx, started;
static bool link_seen, ui_on;
static uint8_t tx_seq, last_type, last_seq;
static bool have_last;
static osc_frame last_reply;

static bool link_ok(uint32_t now) { return link_seen && now - last_rx < OSC_PROTO_LINK_TIMEOUT_MS; }
static bool interlocks_ok(void) { return inputs.door_closed && !inputs.brew_fault; }

static void send(const osc_frame *f) {
    uint8_t buf[OSC_PROTO_MAX_FRAME];
    const unsigned n = osc_proto_encode(f, buf);
    osc_hal_uart_write(buf, n);
}

static void reply(uint8_t seq, uint8_t type, osc_err_code err) {
    osc_frame f;
    f.seq = seq;
    f.type = err ? OSC_MSG_ERROR : OSC_MSG_ACK;
    f.payload[0] = type;
    f.payload[1] = (uint8_t)err;
    f.len = err ? 2u : 1u;
    last_reply = f;
    send(&f);
}

static void send_report(void) {
    osc_frame f;
    f.type = OSC_MSG_TEST_REPORT;
    f.seq = tx_seq++;
    f.len = OSC_TEST_REPORT_LEN;
    osc_test_report_pack(&svc.r, f.payload);
    send(&f);
}

static osc_err_code test_request(const osc_frame *f, uint32_t now) {
    uint16_t param;
    if (f->len < 1) return OSC_ERR_BAD_LENGTH;
    if (f->payload[0] == OSC_TEST_NONE) {
        svc_abort(&svc, OSC_REASON_STOP, now);
        svc_init(&svc); /* clears the report */
        return (osc_err_code)0;
    }
    param = f->len >= 3 ? (uint16_t)(f->payload[1] | (f->payload[2] << 8)) : 0u;
    if (svc_start(&svc, f->payload[0], param, &inputs, ctl.state == OSC_SAFE_IDLE && link_ok(now), now)
        != OSC_REASON_OK) {
        send_report(); /* carries the reason */
        return OSC_ERR_REJECTED;
    }
    return (osc_err_code)0;
}

static void handle(const osc_frame *f, uint32_t now) {
    osc_err_code err = (osc_err_code)0;
    last_rx = now;
    link_seen = true;
    if (f->type == OSC_MSG_KEEPALIVE) return;
    /* A repeated request (same type and sequence) is answered, not redone. */
    if (have_last && f->type == last_type && f->seq == last_seq) {
        send(&last_reply);
        return;
    }
    switch (f->type) {
    case OSC_MSG_HELLO:
        if (f->len < 1) err = OSC_ERR_BAD_LENGTH;
        else if (f->payload[0] != OSC_PROTO_VERSION) err = OSC_ERR_REJECTED;
        break;
    case OSC_MSG_STOP:
        svc_abort(&svc, OSC_REASON_STOP, now);
        osc_stop(&ctl);
        break;
    case OSC_MSG_CLEAR_FAULT:
        if (!osc_clear_fault(&ctl, interlocks_ok(), link_ok(now))) err = OSC_ERR_REJECTED;
        break;
    case OSC_MSG_START_RECIPE:
        if (f->len != 1) err = OSC_ERR_BAD_LENGTH;
        else if (osc_start(&ctl) == OSC_REJECTED_NOT_IMPLEMENTED) err = OSC_ERR_REJECTED;
        break;
    case OSC_MSG_UI_POWER:
        if (f->len != 1) {
            err = OSC_ERR_BAD_LENGTH;
        } else {
            ui_on = f->payload[0] != 0;
            bsp_ui_power(ui_on);
        }
        break;
    case OSC_MSG_TEST:
        err = test_request(f, now);
        break;
    default:
        err = OSC_ERR_UNKNOWN_TYPE;
        break;
    }
    have_last = true;
    last_type = f->type;
    last_seq = f->seq;
    reply(f->seq, f->type, err);
}

static void send_status(uint32_t now) {
    osc_frame f;
    osc_status s;
    const osc_outputs *o = &ctl.outputs;
    s.state = (uint8_t)ctl.state;
    if (svc_running(&svc) && svc_drives(&svc)) s.state = OSC_CORE_SERVICE;
    s.inputs = (uint8_t)((inputs.door_closed ? OSC_IN_DOOR_CLOSED : 0u) |
                         (inputs.bu_present ? OSC_IN_BU_PRESENT : 0u) |
                         (inputs.bu_work ? OSC_IN_BU_WORK : 0u) |
                         (inputs.brew_fault ? OSC_IN_BREW_FAULT : 0u) |
                         (ui_on ? OSC_IN_UI_POWER : 0u));
    s.outputs = (uint16_t)((o->heater ? 1u : 0u) | (o->pump ? 2u : 0u) | (o->valve ? 4u : 0u) |
                           (o->grinder ? 8u : 0u) | (o->brew_motor ? 16u : 0u) |
                           (o->brew_forward ? 32u : 0u) | (o->mains ? 64u : 0u));
    s.rail_12v_mv = inputs.rail_12v_mv;
    s.rail_24v_mv = inputs.rail_24v_mv;
    s.brew_ma = inputs.brew_ma;
    s.ntc_raw = inputs.ntc;
    s.boiler_dc = inputs.boiler_dc;
    s.uptime_ms = now - started;
    f.type = OSC_MSG_STATUS;
    f.seq = tx_seq++;
    f.len = OSC_STATUS_LEN;
    osc_status_pack(&s, f.payload);
    send(&f);
}

static void control(uint32_t now) {
    bsp_read(&inputs);
    /* Until the ESP32 first answers, the core waits in OSC_BOOT; after the
     * grace time, or once the link has been up, a missing link is a fault
     * like any other. */
    if (link_seen || now - started >= OSC_LINK_BOOT_GRACE_MS)
        osc_tick(&ctl, interlocks_ok(), link_ok(now));
    if (svc_running(&svc)) {
        if (!link_ok(now)) svc_abort(&svc, OSC_REASON_LINK, now);
        else if (svc_drives(&svc) && ctl.state != OSC_SAFE_IDLE)
            /* The core faulted first: report the cause it saw, if it is one of ours. */
            svc_abort(&svc, !inputs.door_closed ? OSC_REASON_DOOR
                            : inputs.brew_fault ? OSC_REASON_DRIVER : OSC_REASON_STATE, now);
        else svc_poll(&svc, &inputs, now);
    }
    /* A test drives the outputs only from SAFE_IDLE; anything else is off. */
    if (svc_running(&svc) && svc_drives(&svc) && ctl.state == OSC_SAFE_IDLE) bsp_write(&svc.out);
    else bsp_write(&ctl.outputs);
}

void osc_app_init(void) {
    const osc_inputs none = {false, false, false, false, 0, 0, 0, 0, 0, 0, 3300, 0, 0, 0, 0,
                             OSC_TEMP_INVALID};
    bsp_init();
    osc_init(&ctl);
    osc_parser_init(&parser);
    svc_init(&svc);
    inputs = none;
    started = last_toggle = last_control = last_status = last_rx = osc_hal_millis();
    link_seen = have_last = false;
    ui_on = true; /* bsp_init() switches the front panel on */
    tx_seq = 0;
}

void osc_app_poll(void) {
    const uint32_t now = osc_hal_millis();
    uint8_t byte;
    osc_frame f;
    if (now - last_toggle >= OSC_WDT_TOGGLE_MS) {
        last_toggle = now;
        bsp_watchdog_toggle();
    }
    while (osc_hal_uart_read(&byte))
        if (osc_parser_feed(&parser, byte, &f)) handle(&f, now);
    if (now - last_control >= OSC_CONTROL_PERIOD_MS) {
        last_control = now;
        control(now);
    }
    if (now - last_status >= OSC_PROTO_STATUS_PERIOD_MS) {
        last_status = now;
        send_status(now);
        if (svc.r.id != OSC_TEST_NONE) send_report();
    }
}

const osc_controller *osc_app_controller(void) { return &ctl; }
const osc_inputs *osc_app_inputs(void) { return &inputs; }
bool osc_app_link_ok(void) { return link_ok(osc_hal_millis()); }
const osc_service *osc_app_service(void) { return &svc; }
