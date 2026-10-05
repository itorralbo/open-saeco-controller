/* SPDX-License-Identifier: MIT */
#include "proto.h"
#include <string.h>

uint16_t osc_crc16(const uint8_t *data, unsigned n) {
    uint16_t crc = 0xFFFFu;
    unsigned i, b;
    for (i = 0; i < n; ++i) {
        crc ^= (uint16_t)((uint16_t)data[i] << 8);
        for (b = 0; b < 8; ++b)
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u) : (uint16_t)(crc << 1);
    }
    return crc;
}

unsigned osc_proto_encode(const osc_frame *f, uint8_t *out) {
    uint16_t crc;
    if (f->len > OSC_PROTO_MAX_PAYLOAD) return 0;
    out[0] = OSC_PROTO_SOF;
    out[1] = OSC_PROTO_VERSION;
    out[2] = f->type;
    out[3] = f->seq;
    out[4] = f->len;
    memcpy(&out[5], f->payload, f->len);
    crc = osc_crc16(&out[1], 4u + f->len);
    out[5 + f->len] = (uint8_t)(crc & 0xFFu);
    out[6 + f->len] = (uint8_t)(crc >> 8);
    return OSC_PROTO_OVERHEAD + f->len;
}

void osc_parser_init(osc_parser *p) { memset(p, 0, sizeof *p); }

/* Drops the first byte and rescans what is left for the next SOF. */
static void resync(osc_parser *p) {
    unsigned i;
    for (i = 1; i < p->have && p->buf[i] != OSC_PROTO_SOF; ++i) {}
    memmove(p->buf, &p->buf[i], p->have - i);
    p->have -= i;
}

bool osc_parser_feed(osc_parser *p, uint8_t byte, osc_frame *out) {
    if (p->have == 0 && byte != OSC_PROTO_SOF) return false;
    p->buf[p->have++] = byte;
    for (;;) {
        unsigned len, total;
        uint16_t crc;
        if (p->have < 5) return false;
        if (p->buf[1] != OSC_PROTO_VERSION) {
            p->bad_version++;
            resync(p);
            continue;
        }
        len = p->buf[4];
        if (len > OSC_PROTO_MAX_PAYLOAD) {
            p->overflow++;
            resync(p);
            continue;
        }
        total = OSC_PROTO_OVERHEAD + len;
        if (p->have < total) return false;
        crc = (uint16_t)(p->buf[5 + len] | (p->buf[6 + len] << 8));
        if (crc != osc_crc16(&p->buf[1], 4u + len)) {
            p->bad_crc++;
            resync(p);
            continue;
        }
        out->type = p->buf[2];
        out->seq = p->buf[3];
        out->len = (uint8_t)len;
        memcpy(out->payload, &p->buf[5], len);
        p->have -= total;
        memmove(p->buf, &p->buf[total], p->have);
        return true;
    }
}

static void put16(uint8_t *p, uint16_t v) {
    p[0] = (uint8_t)(v & 0xFFu);
    p[1] = (uint8_t)(v >> 8);
}

static uint16_t get16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }

void osc_status_pack(const osc_status *s, uint8_t *payload) {
    payload[0] = s->state;
    payload[1] = s->inputs;
    put16(&payload[2], s->outputs);
    put16(&payload[4], s->rail_12v_mv);
    put16(&payload[6], s->rail_24v_mv);
    put16(&payload[8], s->brew_ma);
    put16(&payload[10], s->ntc_raw);
    put16(&payload[12], (uint16_t)(s->uptime_ms & 0xFFFFu));
    put16(&payload[14], (uint16_t)(s->uptime_ms >> 16));
    put16(&payload[16], (uint16_t)s->boiler_dc);
}

bool osc_status_unpack(const uint8_t *payload, unsigned len, osc_status *s) {
    if (len != OSC_STATUS_LEN) return false;
    s->state = payload[0];
    s->inputs = payload[1];
    s->outputs = get16(&payload[2]);
    s->rail_12v_mv = get16(&payload[4]);
    s->rail_24v_mv = get16(&payload[6]);
    s->brew_ma = get16(&payload[8]);
    s->ntc_raw = get16(&payload[10]);
    s->uptime_ms = (uint32_t)get16(&payload[12]) | ((uint32_t)get16(&payload[14]) << 16);
    s->boiler_dc = (int16_t)get16(&payload[16]);
    return true;
}

static void put32(uint8_t *p, uint32_t v) {
    put16(p, (uint16_t)(v & 0xFFFFu));
    put16(p + 2, (uint16_t)(v >> 16));
}

static uint32_t get32(const uint8_t *p) { return (uint32_t)get16(p) | ((uint32_t)get16(p + 2) << 16); }

void osc_test_report_pack(const osc_test_report *r, uint8_t *payload) {
    unsigned i;
    payload[0] = r->id;
    payload[1] = r->phase;
    payload[2] = r->step;
    payload[3] = r->reason;
    put32(&payload[4], r->elapsed_ms);
    for (i = 0; i < OSC_TEST_VALUES; ++i) put32(&payload[8 + 4 * i], (uint32_t)r->value[i]);
}

bool osc_test_report_unpack(const uint8_t *payload, unsigned len, osc_test_report *r) {
    unsigned i;
    if (len != OSC_TEST_REPORT_LEN) return false;
    r->id = payload[0];
    r->phase = payload[1];
    r->step = payload[2];
    r->reason = payload[3];
    r->elapsed_ms = get32(&payload[4]);
    for (i = 0; i < OSC_TEST_VALUES; ++i) r->value[i] = (int32_t)get32(&payload[8 + 4 * i]);
    return true;
}
