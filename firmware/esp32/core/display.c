/* SPDX-License-Identifier: MIT */
#include "display.h"
#include "board_pins.h"
#include "esp_hal.h"

/* Waits after each step, from the ST7789V datasheet: reset pulse >= 10 us
 * and 120 ms before commands, 5 ms after SWRESET (120 ms if it was asleep),
 * 120 ms after SLPOUT. Generous values, the panel MPN is still TBD. */
static const uint32_t wait_ms[] = {0, 10, 120, 150, 120};

static void cmd(uint8_t c, const uint8_t *data, unsigned n) {
    esp_hal_gpio_write(BOARD_LCD_DC_GPIO, false);
    esp_hal_spi_write(&c, 1);
    if (n) {
        esp_hal_gpio_write(BOARD_LCD_DC_GPIO, true);
        esp_hal_spi_write(data, n);
    }
}

static void window(unsigned w, unsigned h) {
    const uint8_t cols[4] = {0, 0, (uint8_t)((w - 1) >> 8), (uint8_t)((w - 1) & 0xFFu)};
    const uint8_t rows[4] = {0, 0, (uint8_t)((h - 1) >> 8), (uint8_t)((h - 1) & 0xFFu)};
    cmd(ST7789_CASET, cols, 4);
    cmd(ST7789_RASET, rows, 4);
    cmd(ST7789_RAMWR, 0, 0);
}

static void paint(osc_display *d) {
    static uint8_t line[DISP_W * 2u];
    unsigned y, x;
    uint16_t last = 0;
    bool filled = false;
    window(DISP_W, DISP_H);
    esp_hal_gpio_write(BOARD_LCD_DC_GPIO, true);
    for (y = 0; y < DISP_H; ++y) {
        const uint16_t c = y < DISP_BAR_H ? d->bar : d->bg;
        if (!filled || c != last) {
            for (x = 0; x < DISP_W; ++x) {
                line[2 * x] = (uint8_t)(c >> 8);
                line[2 * x + 1] = (uint8_t)(c & 0xFFu);
            }
            last = c;
            filled = true;
        }
        esp_hal_spi_write(line, sizeof line);
    }
    d->shown_bg = d->bg;
    d->shown_bar = d->bar;
    d->painted = true;
    d->frames++;
}

void disp_start(osc_display *d, uint32_t now) {
    d->phase = 1;
    d->t = now;
    d->painted = false;
    d->backlight = false;
    esp_hal_ledc_set(BOARD_LCD_BL_GPIO, 0);
    esp_hal_gpio_write(BOARD_LCD_DC_GPIO, false);
    esp_hal_gpio_mode(BOARD_LCD_DC_GPIO, ESP_GPIO_OUTPUT);
    esp_hal_gpio_write(BOARD_LCD_RST_N_GPIO, false);
    esp_hal_gpio_mode(BOARD_LCD_RST_N_GPIO, ESP_GPIO_OUTPUT);
}

void disp_stop(osc_display *d) {
    d->phase = 0;
    d->painted = false;
    d->backlight = false;
}

void disp_poll(osc_display *d, uint32_t now) {
    static const uint8_t colmod = 0x55u; /* 16 bit/pixel */
    static const uint8_t madctl = 0x60u; /* MX | MV: landscape */
    if (d->phase == 0) return;
    if (d->phase < 5) {
        if (now - d->t < wait_ms[d->phase]) return;
        switch (d->phase) {
        case 1: esp_hal_gpio_write(BOARD_LCD_RST_N_GPIO, true); break;
        case 2: cmd(ST7789_SWRESET, 0, 0); break;
        case 3: cmd(ST7789_SLPOUT, 0, 0); break;
        default:
            cmd(ST7789_COLMOD, &colmod, 1);
            cmd(ST7789_MADCTL, &madctl, 1);
            cmd(ST7789_INVON, 0, 0);
            cmd(ST7789_NORON, 0, 0);
            cmd(ST7789_DISPON, 0, 0);
            break;
        }
        d->phase++;
        d->t = now;
        return;
    }
    if (!d->painted || d->bg != d->shown_bg || d->bar != d->shown_bar) paint(d);
    /* The backlight only comes up over a painted frame. */
    esp_hal_ledc_set(BOARD_LCD_BL_GPIO, d->backlight ? 1000u : 0u);
}

void disp_show(osc_display *d, uint16_t bg, uint16_t bar) {
    d->bg = bg;
    d->bar = bar;
}

void disp_backlight(osc_display *d, bool on) { d->backlight = on; }

bool disp_ready(const osc_display *d) { return d->phase == 5 && d->painted; }
