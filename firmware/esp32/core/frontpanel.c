/* SPDX-License-Identifier: MIT */
#include "frontpanel.h"
#include "esp_hal.h"

static bool write_reg(uint8_t reg, uint8_t value) {
    const uint8_t w[2] = {reg, value};
    return esp_hal_i2c_xfer(FP_ADDR, w, 2, 0, 0);
}

bool fp_init(osc_keypad *k, uint32_t now) {
    const uint8_t out = (uint8_t)(FP_KEY_MASK | (k->led ? 0u : FP_LED_BIT));
    k->last_try = k->last_sample = k->since = now;
    k->armed = false;
    k->keys = k->candidate = k->presses = 0;
    k->valid = write_reg(FP_REG_OUTPUT, out) && write_reg(FP_REG_POLARITY, 0x00u) &&
               write_reg(FP_REG_CONFIG, FP_KEY_MASK);
    if (!k->valid) k->nacks++;
    return k->valid;
}

void fp_poll(osc_keypad *k, uint32_t now, bool int_low) {
    const uint8_t reg = FP_REG_INPUT;
    uint8_t in, raw, fresh;
    if (!k->valid) {
        if (now - k->last_try >= FP_RETRY_MS) fp_init(k, now);
        return;
    }
    if (!int_low && now - k->last_sample < FP_SAMPLE_MS) return;
    k->last_sample = now;
    if (!esp_hal_i2c_xfer(FP_ADDR, &reg, 1, &in, 1)) {
        k->valid = false;
        k->last_try = now;
        k->nacks++;
        return;
    }
    raw = (uint8_t)(~in & FP_KEY_MASK);
    if (raw != k->candidate) {
        k->candidate = raw;
        k->since = now;
        return;
    }
    if (now - k->since < FP_STABLE_MS) return;
    if (!k->armed) {
        /* A key held through reset or reconnection never counts. */
        k->keys = raw;
        k->armed = raw == 0;
        return;
    }
    if (raw == k->keys) return;
    fresh = (uint8_t)(raw & ~k->keys);
    k->keys = raw;
    k->presses |= fresh;
}

uint8_t fp_take_presses(osc_keypad *k) {
    const uint8_t p = k->presses;
    k->presses = 0;
    return p;
}

bool fp_set_led(osc_keypad *k, bool on) {
    k->led = on;
    if (!k->valid) return false;
    if (!write_reg(FP_REG_OUTPUT, (uint8_t)(FP_KEY_MASK | (on ? 0u : FP_LED_BIT)))) {
        k->valid = false;
        k->nacks++;
        return false;
    }
    return true;
}
