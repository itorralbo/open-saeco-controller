/* SPDX-License-Identifier: MIT */
/* Board support: the signals of firmware/common/signals.json on the pins of
 * board_pins.h, through osc_hal.h. */
#ifndef OSC_BSP_H
#define OSC_BSP_H
#include <stdbool.h>
#include <stdint.h>
#include "controller.h"

typedef struct {
    bool door_closed, bu_present, bu_work, brew_fault;
    uint16_t ntc, water, rail_12v, rail_24v, brew_current; /* raw ADC codes */
    uint32_t flow_edges;
} osc_inputs;

/* Every order inactive before its pin becomes an output, then inputs,
 * analog pins and peripherals. The UI supply is switched on. */
void bsp_init(void);
/* One edge on WDI; U601 needs a falling edge at least every 0.9 s. */
void bsp_watchdog_toggle(void);
void bsp_read(osc_inputs *in);
/* Loads, mains arm and the brew bridge from the controller's outputs. */
void bsp_write(const osc_outputs *out);
void bsp_ui_power(bool on);
#endif
