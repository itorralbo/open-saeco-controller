/* SPDX-License-Identifier: MIT */
/* Protocol v0 between the ESP32 (requests) and the STM32 (decides), see
 * protocol.md. Portable C99, no allocation; both firmwares and the host
 * tests build it.
 *
 * Frame: SOF 0xA5 | VER | TYPE | SEQ | LEN | PAYLOAD[LEN] | CRC16 lo | hi
 * CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF) over VER..PAYLOAD. */
#ifndef OSC_PROTO_H
#define OSC_PROTO_H
#include <stdbool.h>
#include <stdint.h>

#define OSC_PROTO_SOF 0xA5u
#define OSC_PROTO_VERSION 0u
#define OSC_PROTO_MAX_PAYLOAD 32u
#define OSC_PROTO_OVERHEAD 7u /* SOF, VER, TYPE, SEQ, LEN, CRC x2 */
#define OSC_PROTO_MAX_FRAME (OSC_PROTO_MAX_PAYLOAD + OSC_PROTO_OVERHEAD)
#define OSC_PROTO_BAUD 115200u
/* The STM32 sends STATUS every period; either side drops the link when no
 * valid frame arrived for the timeout. */
#define OSC_PROTO_STATUS_PERIOD_MS 100u
#define OSC_PROTO_KEEPALIVE_PERIOD_MS 100u
#define OSC_PROTO_LINK_TIMEOUT_MS 350u

typedef enum {
    OSC_MSG_HELLO = 0x01,        /* ESP -> STM: version, role; answered with ACK */
    OSC_MSG_KEEPALIVE = 0x02,    /* ESP -> STM, empty */
    OSC_MSG_STATUS = 0x10,       /* STM -> ESP, osc_status */
    OSC_MSG_TEST_REPORT = 0x11,  /* STM -> ESP, osc_test_report, while a test is loaded */
    OSC_MSG_STOP = 0x20,         /* ESP -> STM: every load off */
    OSC_MSG_CLEAR_FAULT = 0x21,  /* ESP -> STM */
    OSC_MSG_START_RECIPE = 0x22, /* ESP -> STM: u8 recipe; rejected in this core */
    OSC_MSG_UI_POWER = 0x23,     /* ESP -> STM: u8 0 = front panel off, 1 = on */
    OSC_MSG_TEST = 0x24,         /* ESP -> STM: u8 test (osc_test_id, 0 clears), u16 parameter */
    OSC_MSG_ACK = 0x7E,          /* STM -> ESP: u8 type acknowledged */
    OSC_MSG_ERROR = 0x7F         /* STM -> ESP: u8 type, u8 code */
} osc_msg_type;

typedef enum {
    OSC_ERR_UNKNOWN_TYPE = 1,
    OSC_ERR_BAD_LENGTH = 2,
    OSC_ERR_REJECTED = 3, /* valid request the core refuses (START, CLEAR_FAULT) */
    OSC_ERR_NOT_IMPLEMENTED = 4
} osc_err_code;

typedef struct {
    uint8_t type, seq, len;
    uint8_t payload[OSC_PROTO_MAX_PAYLOAD];
} osc_frame;

/* Core states carried in STATUS.state: the values of osc_state (STM32). */
#define OSC_CORE_BOOT 0u
#define OSC_CORE_SAFE_IDLE 1u
#define OSC_CORE_FAULT 2u
#define OSC_CORE_SERVICE 3u /* a set-up test drives the outputs */

/* STATUS payload, little endian on the wire (osc_status_pack/unpack). */
#define OSC_STATUS_LEN 18u
#define OSC_IN_DOOR_CLOSED 0x01u
#define OSC_IN_BU_PRESENT 0x02u
#define OSC_IN_BU_WORK 0x04u
#define OSC_IN_BREW_FAULT 0x08u
#define OSC_IN_UI_POWER 0x10u
typedef struct {
    uint8_t state;       /* osc_state of the STM32 core */
    uint8_t inputs;      /* OSC_IN_* */
    uint16_t outputs;    /* bit 0 heater, 1 pump, 2 valve, 3 grinder, 4 brew motor */
    uint16_t rail_12v_mv, rail_24v_mv, brew_ma;
    uint16_t ntc_raw;    /* ADC code */
    uint32_t uptime_ms;
    int16_t boiler_dc;   /* boiler temperature in 0.1 degC from the NTC fit; -32768 = invalid */
} osc_status;

/* Set-up tests (firmware/common/service.h): the STM32 runs them, bounded and
 * abortable, and reports progress and results. */
#define OSC_TEST_VALUES 6u
#define OSC_TEST_REPORT_LEN (8u + 4u * OSC_TEST_VALUES)
typedef struct {
    uint8_t id, phase, step, reason;
    uint32_t elapsed_ms;
    int32_t value[OSC_TEST_VALUES];
} osc_test_report;
void osc_test_report_pack(const osc_test_report *r, uint8_t *payload);
bool osc_test_report_unpack(const uint8_t *payload, unsigned len, osc_test_report *r);

uint16_t osc_crc16(const uint8_t *data, unsigned n);
/* Encodes into out (OSC_PROTO_MAX_FRAME bytes); returns the frame length,
 * 0 if the payload is too long. */
unsigned osc_proto_encode(const osc_frame *f, uint8_t *out);

/* Byte-wise decoder. Resynchronises on the next SOF after any error. */
typedef struct {
    uint8_t buf[OSC_PROTO_MAX_FRAME];
    unsigned have;
    uint32_t bad_crc, bad_version, overflow;
} osc_parser;
void osc_parser_init(osc_parser *p);
/* Feeds one byte; returns true when out holds a complete, valid frame. */
bool osc_parser_feed(osc_parser *p, uint8_t byte, osc_frame *out);

void osc_status_pack(const osc_status *s, uint8_t *payload);
bool osc_status_unpack(const uint8_t *payload, unsigned len, osc_status *s);
#endif
