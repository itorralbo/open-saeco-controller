/* SPDX-License-Identifier: MIT */
/* Keypad and standby LED on the TCA9534 of the front panel
 * (hardware/front-panel/layout.md, docs/display-ui.md section 6). */
#ifndef OSC_FRONTPANEL_H
#define OSC_FRONTPANEL_H
#include <stdbool.h>
#include <stdint.h>

#define FP_ADDR 0x20u
#define FP_REG_INPUT 0x00u
#define FP_REG_OUTPUT 0x01u
#define FP_REG_POLARITY 0x02u
#define FP_REG_CONFIG 0x03u
#define FP_KEY_MASK 0x7Fu   /* P0-P6 keys, active low */
#define FP_LED_BIT 0x80u    /* P7 standby LED, on when low */
#define FP_SAMPLE_MS 5u
#define FP_STABLE_MS 20u
#define FP_RETRY_MS 100u

typedef struct {
    bool valid;      /* configured and answering; false is not "no key" */
    bool armed;      /* every key seen released since (re)initialisation */
    bool led;
    uint8_t keys;    /* debounced, bit set = pressed */
    uint8_t candidate, presses;
    uint32_t since, last_sample, last_try;
    uint32_t nacks;
} osc_keypad;

/* Output, Polarity, then Configuration, so P7 never drives low unasked. */
bool fp_init(osc_keypad *k, uint32_t now);
/* Samples every FP_SAMPLE_MS, or at once when int_low; re-initialises after
 * a bus error every FP_RETRY_MS. */
void fp_poll(osc_keypad *k, uint32_t now, bool int_low);
/* New presses since the last call (bit per key), only once armed. */
uint8_t fp_take_presses(osc_keypad *k);
bool fp_set_led(osc_keypad *k, bool on);
#endif
