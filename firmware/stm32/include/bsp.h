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
    uint16_t vrefint;    /* raw code of the internal reference */
    uint16_t vdda_mv;    /* VDDA from VREFINT and its factory calibration */
    uint32_t flow_edges;
    /* Engineering units, from the codes above and the board's dividers. */
    uint16_t rail_12v_mv, rail_24v_mv, brew_ma;
    int16_t boiler_dc;   /* 0.1 degC; OSC_TEMP_INVALID when the NTC is open or shorted */
    /* Grinder current: mean of the samples since the last read (U704, 100 mV/A
     * about VS/2; VS is 3V3_CORE, the ADC's own VDDA). */
    uint16_t grinder;    /* mean raw ADC code */
    int16_t grinder_ma;
} osc_inputs;

#define OSC_TEMP_INVALID (-32768)
/* NTC network (sim/board-report.md): R401 = 4.7k from VDDA, the NTC to
 * ground, read ratiometrically. Fit R25 = 49.9k, B = 4037 K
 * (docs/HD8911/components.md), to be replaced by the NT-01 table. */
#define OSC_NTC_PULLUP_OHMS 4700.0f
#define OSC_NTC_R25_OHMS 49900.0f
#define OSC_NTC_BETA_K 4037.0f
int16_t bsp_ntc_dc(uint16_t code);

/* Every order inactive before its pin becomes an output, then inputs,
 * analog pins and peripherals. The UI supply is switched on. */
void bsp_init(void);
/* One edge on WDI; U601 needs a falling edge at least every 0.9 s. */
void bsp_watchdog_toggle(void);
void bsp_read(osc_inputs *in);
/* Called every poll (1 ms): samples the grinder current, a full-wave 100 Hz
 * waveform that a 10 ms control tick alone would alias. */
void bsp_sample(void);
/* Loads, mains arm and the brew bridge from the controller's outputs. */
void bsp_write(const osc_outputs *out);
void bsp_ui_power(bool on);
#endif
