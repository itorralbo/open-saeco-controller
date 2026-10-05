/* SPDX-License-Identifier: MIT */
#include "display.h"
#include <string.h>
#include "board_pins.h"
#include "esp_hal.h"
#include "font5x7.h"

/* Waits after each step, from the ST7789V datasheet: reset pulse >= 10 us
 * and 120 ms before commands, 5 ms after SWRESET (120 ms if it was asleep),
 * 120 ms after SLPOUT. Generous values, the panel MPN is still TBD. */
static const uint32_t wait_ms[] = {0, 10, 120, 150, 120};

static void copy(char *dst, const char *src) {
    unsigned i = 0;
    for (; src && src[i] && i < TXT_COLS; ++i) dst[i] = src[i];
    for (; i <= TXT_COLS; ++i) dst[i] = '\0';
}

void txt_clear(osc_text_screen *s, const char *title, uint16_t title_bg) {
    memset(s, 0, sizeof *s);
    copy(s->title, title);
    s->title_bg = title_bg;
}

void txt_line(osc_text_screen *s, unsigned row, txt_style style, const char *text) {
    if (row >= TXT_ROWS) return;
    copy(s->line[row], text);
    s->style[row] = (uint8_t)style;
}

void txt_foot(osc_text_screen *s, const char *text) { copy(s->foot, text); }

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

static void colours(txt_style style, uint16_t *fg, uint16_t *bg) {
    *bg = DISP_BLACK;
    switch (style) {
    case TXT_SELECTED: *fg = DISP_BLACK; *bg = DISP_WHITE; break;
    case TXT_DIM: *fg = DISP_GREY; break;
    case TXT_OK: *fg = DISP_GREEN; break;
    case TXT_WARN: *fg = DISP_AMBER; break;
    case TXT_BAD: *fg = DISP_RED; break;
    default: *fg = DISP_WHITE; break;
    }
}

/* One pixel row of a text line: glyph row gy (0..6) or -1 for padding. */
static void text_row(uint8_t *line, const char *text, int gy, uint16_t fg, uint16_t bg) {
    unsigned x;
    for (x = 0; x < DISP_W; ++x) {
        uint16_t c = bg;
        const unsigned col = (x >= 4u) ? (x - 4u) / DISP_CELL_W : TXT_COLS;
        const unsigned gx = (x >= 4u) ? ((x - 4u) % DISP_CELL_W) / DISP_SCALE : 0u;
        if (gy >= 0 && col < TXT_COLS && gx < FONT_W && text[col]) {
            const uint8_t bits = font_glyph((unsigned char)text[col])[gy];
            if (bits & (0x10u >> gx)) c = fg;
        }
        line[2 * x] = (uint8_t)(c >> 8);
        line[2 * x + 1] = (uint8_t)(c & 0xFFu);
    }
}

static void paint(osc_display *d) {
    static uint8_t line[DISP_W * 2u];
    const osc_text_screen *s = &d->want;
    unsigned y;
    window(DISP_W, DISP_H);
    esp_hal_gpio_write(BOARD_LCD_DC_GPIO, true);
    for (y = 0; y < DISP_H; ++y) {
        uint16_t fg = DISP_WHITE, bg = DISP_BLACK;
        const char *text = "";
        int gy = -1;
        if (y < DISP_TITLE_H) {
            bg = s->title_bg;
            text = s->title;
            if (y >= 5u && y < 5u + FONT_H * DISP_SCALE) gy = (int)((y - 5u) / DISP_SCALE);
        } else if (y >= DISP_ROW_TOP && y < DISP_ROW_TOP + TXT_ROWS * DISP_ROW_H) {
            const unsigned r = (y - DISP_ROW_TOP) / DISP_ROW_H, ry = (y - DISP_ROW_TOP) % DISP_ROW_H;
            colours((txt_style)s->style[r], &fg, &bg);
            text = s->line[r];
            if (ry >= 1u && ry < 1u + FONT_H * DISP_SCALE) gy = (int)((ry - 1u) / DISP_SCALE);
        } else if (y >= DISP_FOOT_TOP) {
            fg = DISP_GREY;
            bg = DISP_DARK;
            text = s->foot;
            if (y >= DISP_FOOT_TOP + 1u && y < DISP_FOOT_TOP + 1u + FONT_H * DISP_SCALE)
                gy = (int)((y - DISP_FOOT_TOP - 1u) / DISP_SCALE);
        }
        text_row(line, text, gy, fg, bg);
        esp_hal_spi_write(line, sizeof line);
    }
    d->shown = d->want;
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
    if (!d->painted || memcmp(&d->want, &d->shown, sizeof d->want) != 0) paint(d);
    /* The backlight only comes up over a painted frame. */
    esp_hal_ledc_set(BOARD_LCD_BL_GPIO, d->backlight ? 1000u : 0u);
}

void disp_show(osc_display *d, const osc_text_screen *s) { d->want = *s; }

void disp_backlight(osc_display *d, bool on) { d->backlight = on; }

bool disp_ready(const osc_display *d) { return d->phase == 5 && d->painted; }
