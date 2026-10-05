/* SPDX-License-Identifier: MIT */
/* ST7789V 240 x 320 over SPI, landscape (docs/display-ui.md). A minimal,
 * non-blocking driver: reset and wake-up timing as a state machine, then
 * full-frame fills by screen. On the target LVGL (esp_lcd + esp_lvgl_port)
 * replaces the painting; the bring-up order stays the same. */
#ifndef OSC_DISPLAY_H
#define OSC_DISPLAY_H
#include <stdbool.h>
#include <stdint.h>

#define DISP_W 320u
#define DISP_H 240u
#define DISP_BAR_H 24u
#define DISP_SPI_HZ 10000000u

/* RGB565 */
#define DISP_BLACK 0x0000u
#define DISP_GREY 0x7BEFu
#define DISP_BLUE 0x001Fu
#define DISP_GREEN 0x07E0u
#define DISP_RED 0xF800u
#define DISP_AMBER 0xFD20u

#define ST7789_SWRESET 0x01u
#define ST7789_SLPOUT 0x11u
#define ST7789_NORON 0x13u
#define ST7789_INVON 0x21u
#define ST7789_DISPON 0x29u
#define ST7789_CASET 0x2Au
#define ST7789_RASET 0x2Bu
#define ST7789_RAMWR 0x2Cu
#define ST7789_MADCTL 0x36u
#define ST7789_COLMOD 0x3Au

typedef struct {
    int phase;           /* 0 off, 1..4 reset/wake-up steps, 5 ready */
    uint32_t t;
    uint16_t bg, bar, shown_bg, shown_bar;
    bool painted, backlight;
    uint32_t frames;
} osc_display;

void disp_start(osc_display *d, uint32_t now);
void disp_stop(osc_display *d);
void disp_poll(osc_display *d, uint32_t now);
void disp_show(osc_display *d, uint16_t bg, uint16_t bar);
void disp_backlight(osc_display *d, bool on);
bool disp_ready(const osc_display *d);
#endif
