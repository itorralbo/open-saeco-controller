/* SPDX-License-Identifier: MIT */
/* Menus of the interface: home, menu, set-up tests, information. Pure logic:
 * keys in, one request out, a text screen to paint. */
#ifndef OSC_UI_H
#define OSC_UI_H
#include <stdbool.h>
#include <stdint.h>
#include "display.h"
#include "proto.h"
#include "service_ids.h"

/* Keys by TCA9534 port, laid out as on the panel: left column up, down and
 * back (SW1-SW3); right column STOP, MENU and OK (SW7, SW6, SW5); SW4,
 * under the STBY LED, standby. Provisional until the UX labels them. */
#define UI_KEY_UP 0x01u    /* P0, SW1 */
#define UI_KEY_DOWN 0x02u  /* P1, SW2 */
#define UI_KEY_BACK 0x04u  /* P2, SW3 */
#define UI_KEY_STBY 0x08u  /* P3, SW4 */
#define UI_KEY_OK 0x10u    /* P4, SW5 */
#define UI_KEY_MENU 0x20u  /* P5, SW6 */
#define UI_KEY_STOP 0x40u  /* P6, SW7 */

typedef enum { UI_HOME, UI_MENU, UI_SETUP, UI_CONFIRM, UI_TEST, UI_ENTRY, UI_INFO } ui_page;

typedef struct {
    uint8_t page;        /* ui_page */
    uint8_t sel;         /* selection in the current list */
    uint8_t test;        /* chosen set-up test */
    uint16_t param;      /* its parameter */
    uint16_t entry_ml;   /* weighed volume, flow calibration */
    int32_t flow_ppl;    /* pulses per litre from the last calibration, 0 = none */
    bool standby;
} osc_ui;

typedef struct {
    bool link_ok, have_status, have_report, keypad_valid;
    const osc_status *status;
    const osc_test_report *report;
    uint8_t last_reply_type, last_reply_for, last_reply_code;
    uint32_t requests, replies, recoveries;
} ui_ctx;

typedef struct {
    uint8_t type;        /* osc_msg_type to send, 0 = none */
    uint8_t len;
    uint8_t payload[3];
} ui_request;

void ui_init(osc_ui *u);
/* Applies new key presses; returns true and fills req when it asks the core
 * for something. */
bool ui_keys(osc_ui *u, uint8_t presses, const ui_ctx *c, ui_request *req);
void ui_render(const osc_ui *u, const ui_ctx *c, osc_text_screen *s);
/* Name of a set-up test, for logs and the simulator. */
const char *ui_test_name(uint8_t id);
#endif
