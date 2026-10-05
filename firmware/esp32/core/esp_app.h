/* SPDX-License-Identifier: MIT */
/* Interface side of the machine: link to the STM32, front panel, menus and
 * display. It shows state and asks; the STM32 decides (protocol.md). */
#ifndef OSC_ESP_APP_H
#define OSC_ESP_APP_H
#include <stdbool.h>
#include <stdint.h>
#include "display.h"
#include "frontpanel.h"
#include "proto.h"
#include "ui.h"

/* A keypad that stays invalid this long gets its supply cycled. */
#define ESP_FRONT_RECOVERY_MS 1000u
#define ESP_FRONT_OFF_MS 200u

typedef enum {
    ESP_FRONT_WAIT,      /* supply state unknown: pins left high impedance */
    ESP_FRONT_ON,
    ESP_FRONT_POWER_OFF, /* UI_POWER 0 asked, pins released */
    ESP_FRONT_POWER_ON   /* UI_POWER 1 asked */
} esp_front;

typedef struct {
    bool link_ok, have_status, have_report;
    osc_status status;
    osc_test_report report;
    uint8_t front;       /* esp_front */
    uint8_t last_reply_type, last_reply_code, last_reply_for;
    uint32_t requests, replies, recoveries;
    osc_ui ui;
    osc_keypad keypad;
    osc_display display;
} osc_esp_view;

void esp_app_init(void);
void esp_app_poll(void);
const osc_esp_view *esp_app_view(void);
#endif
