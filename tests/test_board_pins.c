/* SPDX-License-Identifier: MIT */
/* The generated pin header compiles and assigns no pad twice. */
#include <stdio.h>
#include "board_pins.h"

#define PAD(name) { #name, BOARD_##name##_PORT, BOARD_##name##_PIN },

int main(void) {
    static const struct { const char *name; unsigned port, pin; } pads[] = {
        BOARD_SIGNALS(PAD)
    };
    const unsigned n = sizeof pads / sizeof pads[0];
    unsigned i, j;
    for (i = 0; i < n; ++i)
        for (j = i + 1; j < n; ++j)
            if (pads[i].port == pads[j].port && pads[i].pin == pads[j].pin) {
                printf("%s and %s share a pad\n", pads[i].name, pads[j].name);
                return 1;
            }
    printf("%u pads, all distinct\n", n);
    return 0;
}
