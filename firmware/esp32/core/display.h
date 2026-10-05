/* SPDX-License-Identifier: MIT */
/* ST7789V 240 x 320 over SPI, landscape (docs/display-ui.md). A minimal,
 * non-blocking driver: reset and wake-up timing as a state machine, then a
 * text screen (title, 12 lines, footer) painted row by row without a frame
 * buffer, only when it changes. On the target LVGL (esp_lcd +
 * esp_lvgl_port) replaces the painting; the bring-up order stays the same. */
#ifndef OSC_DISPLAY_H
#define OSC_DISPLAY_H
#include <stdbool.h>
#include <stdint.h>

#define DISP_W 320u
#define DISP_H 240u
#define DISP_SPI_HZ 10000000u
#define DISP_SCALE 2u
#define DISP_CELL_W 12u             /* 5 px glyph x2 + 2 px gap */
#define DISP_TITLE_H 24u
#define DISP_ROW_TOP 28u
#define DISP_ROW_H 16u
#define DISP_FOOT_TOP 224u
#define TXT_COLS 26u
#define TXT_ROWS 12u

/* RGB565 */
#define DISP_BLACK 0x0000u
#define DISP_WHITE 0xFFFFu
#define DISP_GREY 0x7BEFu
#define DISP_DARK 0x2104u
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

typedef enum { TXT_NORMAL, TXT_SELECTED, TXT_DIM, TXT_OK, TXT_WARN, TXT_BAD } txt_style;

typedef struct {
    char title[TXT_COLS + 1];
    uint16_t title_bg;
    char line[TXT_ROWS][TXT_COLS + 1];
    uint8_t style[TXT_ROWS];
    char foot[TXT_COLS + 1];
} osc_text_screen;

typedef struct {
    int phase;           /* 0 off, 1..4 reset/wake-up steps, 5 ready */
    uint32_t t;
    osc_text_screen want, shown;
    bool painted, backlight;
    uint32_t frames;
} osc_display;

void disp_start(osc_display *d, uint32_t now);
void disp_stop(osc_display *d);
void disp_poll(osc_display *d, uint32_t now);
void disp_show(osc_display *d, const osc_text_screen *s);
void disp_backlight(osc_display *d, bool on);
bool disp_ready(const osc_display *d);

/* Helpers to fill a text screen (strings clipped to TXT_COLS). */
void txt_clear(osc_text_screen *s, const char *title, uint16_t title_bg);
void txt_line(osc_text_screen *s, unsigned row, txt_style style, const char *text);
void txt_foot(osc_text_screen *s, const char *text);
#endif
