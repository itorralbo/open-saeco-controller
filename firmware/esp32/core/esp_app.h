/* SPDX-License-Identifier: MIT */
/* Interface side of the machine: link to the STM32, front panel and
 * display. It shows state and asks; the STM32 decides (protocol.md). */
#ifndef OSC_ESP_APP_H
#define OSC_ESP_APP_H
#include <stdbool.h>
#include <stdint.h>
#include "display.h"
#include "frontpanel.h"
#include "proto.h"

/* Provisional key map until the UX labels the seven keys
 * (docs/display-ui.md section 6): bit = TCA9534 port. */
#define ESP_KEY_START 0x01u       /* P0, SW1 */
#define ESP_KEY_CLEAR_FAULT 0x02u /* P1, SW2 */
#define ESP_KEY_STANDBY 0x08u     /* P3, SW4, the key under the STBY LED */
#define ESP_KEY_STOP 0x40u        /* P6, SW7 */

/* A keypad that stays invalid this long gets its supply cycled. */
#define ESP_FRONT_RECOVERY_MS 1000u
#define ESP_FRONT_OFF_MS 200u

typedef enum {
    ESP_SCREEN_BOOT,      /* waiting for the first STATUS */
    ESP_SCREEN_LINK_LOST,
    ESP_SCREEN_STARTING,  /* STM32 core in OSC_BOOT */
    ESP_SCREEN_IDLE,
    ESP_SCREEN_FAULT,
    ESP_SCREEN_STANDBY
} esp_screen;

typedef enum {
    ESP_FRONT_WAIT,      /* supply state unknown: pins left high impedance */
    ESP_FRONT_ON,
    ESP_FRONT_POWER_OFF, /* UI_POWER 0 asked, pins released */
    ESP_FRONT_POWER_ON   /* UI_POWER 1 asked */
} esp_front;

typedef struct {
    bool link_ok, have_status, standby;
    osc_status status;
    esp_screen screen;
    esp_front front;
    uint8_t last_reply_type, last_reply_code, last_reply_for;
    uint32_t requests, replies, recoveries;
    osc_keypad keypad;
    osc_display display;
} osc_esp_view;

void esp_app_init(void);
void esp_app_poll(void);
const osc_esp_view *esp_app_view(void);
#endif
