/* SPDX-License-Identifier: MIT */
#include "app.h"
#include "osc_hal.h"
#include "proto.h"

/* ADC scaling from sim/board-report.md: rails through 200k/10k (x21), brew
 * current through IPROPI 1000 uA/A into R510 = 2.4k (2.4 V/A), both against
 * the VDDA that bsp_read() measured. */
#define RAIL_MV(code, vdda) ((uint16_t)(((uint32_t)(code) * (vdda) * 21u) / 4095u))
#define BREW_MA(code, vdda) ((uint16_t)(((uint32_t)(code) * (vdda) * 10u) / (4095u * 24u)))

static osc_controller ctl;
static osc_inputs inputs;
static osc_parser parser;
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
    s.inputs = (uint8_t)((inputs.door_closed ? OSC_IN_DOOR_CLOSED : 0u) |
                         (inputs.bu_present ? OSC_IN_BU_PRESENT : 0u) |
                         (inputs.bu_work ? OSC_IN_BU_WORK : 0u) |
                         (inputs.brew_fault ? OSC_IN_BREW_FAULT : 0u) |
                         (ui_on ? OSC_IN_UI_POWER : 0u));
    s.outputs = (uint16_t)((o->heater ? 1u : 0u) | (o->pump ? 2u : 0u) | (o->valve ? 4u : 0u) |
                           (o->grinder ? 8u : 0u) | (o->brew_motor ? 16u : 0u));
    s.rail_12v_mv = RAIL_MV(inputs.rail_12v, inputs.vdda_mv);
    s.rail_24v_mv = RAIL_MV(inputs.rail_24v, inputs.vdda_mv);
    s.brew_ma = BREW_MA(inputs.brew_current, inputs.vdda_mv);
    s.ntc_raw = inputs.ntc;
    s.uptime_ms = now - started;
    f.type = OSC_MSG_STATUS;
    f.seq = tx_seq++;
    f.len = OSC_STATUS_LEN;
    osc_status_pack(&s, f.payload);
    send(&f);
}

void osc_app_init(void) {
    const osc_inputs none = {false, false, false, false, 0, 0, 0, 0, 0, 0, 0, 3300};
    bsp_init();
    osc_init(&ctl);
    osc_parser_init(&parser);
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
        bsp_read(&inputs);
        /* Until the ESP32 first answers, the core waits in OSC_BOOT; after
         * the grace time, or once the link has been up, a missing link is a
         * fault like any other. */
        if (link_seen || now - started >= OSC_LINK_BOOT_GRACE_MS)
            osc_tick(&ctl, interlocks_ok(), link_ok(now));
        bsp_write(&ctl.outputs);
    }
    if (now - last_status >= OSC_PROTO_STATUS_PERIOD_MS) {
        last_status = now;
        send_status(now);
    }
}

const osc_controller *osc_app_controller(void) { return &ctl; }
const osc_inputs *osc_app_inputs(void) { return &inputs; }
bool osc_app_link_ok(void) { return link_ok(osc_hal_millis()); }
