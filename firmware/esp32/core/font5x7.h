/* SPDX-License-Identifier: MIT */
/* 5 x 7 font for the service screens (font5x7.c, from tools/make_font5x7.py).
 * Strings are 8-bit: printable ASCII, lowercase drawn as uppercase, plus the
 * FONT_* control codes below for the few symbols outside ASCII. */
#ifndef OSC_FONT5X7_H
#define OSC_FONT5X7_H
#include <stdint.h>

#define FONT_W 5u
#define FONT_H 7u
#define FONT_N_TILDE "\x01" /* Ñ */
#define FONT_DEGREE "\x02"  /* ° */
#define FONT_UP "\x03"
#define FONT_DOWN "\x04"
#define FONT_RIGHT "\x05"
#define FONT_LEFT "\x06"

extern const uint8_t font5x7[70][7];

/* Row bits (bit 4 leftmost) of a character's glyph. */
static inline const uint8_t *font_glyph(unsigned char c) {
    if (c >= 1u && c <= 6u) return font5x7[63u + c];
    if (c >= 'a' && c <= 'z') c = (unsigned char)(c - 'a' + 'A');
    if (c < 32u || c > 95u) c = '?';
    return font5x7[c - 32u];
}
#endif
