/* SPDX-License-Identifier: MIT */
/* Protocol v0 framing: round trip, CRC, resynchronisation and limits. */
#include <stdio.h>
#include <string.h>
#include "proto.h"
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "check failed at %d\n", __LINE__); return 1; } } while (0)

static int feed(osc_parser *p, const uint8_t *buf, unsigned n, osc_frame *out) {
    int frames = 0;
    unsigned i;
    for (i = 0; i < n; ++i)
        if (osc_parser_feed(p, buf[i], out)) frames++;
    return frames;
}

int main(void) {
    static const uint8_t check[] = "123456789";
    uint8_t buf[2 * OSC_PROTO_MAX_FRAME + 8];
    osc_frame f, g;
    osc_parser p;
    osc_status s, t;
    unsigned n, n2;
    /* CRC-16/CCITT-FALSE check value. */
    CHECK(osc_crc16(check, 9) == 0x29B1u);
    memset(&s, 0, sizeof s);
    s.state = OSC_CORE_SAFE_IDLE;
    s.inputs = OSC_IN_DOOR_CLOSED | OSC_IN_UI_POWER;
    s.rail_12v_mv = 11800;
    s.uptime_ms = 0x12345678u;
    f.type = OSC_MSG_STATUS;
    f.seq = 7;
    f.len = OSC_STATUS_LEN;
    osc_status_pack(&s, f.payload);
    n = osc_proto_encode(&f, buf);
    CHECK(n == OSC_PROTO_OVERHEAD + OSC_STATUS_LEN);
    osc_parser_init(&p);
    CHECK(feed(&p, buf, n, &g) == 1 && g.type == f.type && g.seq == 7 && g.len == f.len);
    CHECK(osc_status_unpack(g.payload, g.len, &t) && t.rail_12v_mv == 11800 && t.uptime_ms == 0x12345678u);
    /* A flipped bit is dropped and counted; the next frame still decodes. */
    buf[6] ^= 0x10u;
    memcpy(&buf[n], buf, n);
    buf[n + 6] ^= 0x10u;
    CHECK(feed(&p, buf, 2 * n, &g) == 1 && p.bad_crc == 1);
    /* Garbage, a stray SOF and a wrong version before a good frame. */
    buf[0] = 0x00; buf[1] = OSC_PROTO_SOF; buf[2] = 0x55; buf[3] = OSC_PROTO_SOF; buf[4] = 0x09;
    f.type = OSC_MSG_STOP;
    f.len = 0;
    n2 = osc_proto_encode(&f, &buf[5]);
    CHECK(feed(&p, buf, 5 + n2, &g) == 1 && g.type == OSC_MSG_STOP && p.bad_version >= 1);
    /* Over-long payloads are neither encoded nor accepted. */
    f.len = OSC_PROTO_MAX_PAYLOAD + 1;
    CHECK(osc_proto_encode(&f, buf) == 0);
    buf[0] = OSC_PROTO_SOF; buf[1] = OSC_PROTO_VERSION; buf[2] = 1; buf[3] = 0; buf[4] = 200;
    CHECK(feed(&p, buf, 5, &g) == 0 && p.overflow == 1);
    CHECK(!osc_status_unpack(g.payload, 3, &t));
    printf("protocol v0 framing checks pass\n");
    return 0;
}
