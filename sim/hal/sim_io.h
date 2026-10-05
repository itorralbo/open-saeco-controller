/* SPDX-License-Identifier: MIT */
/* Shared state between hal_sim.c and the Python virtual board (ctypes
 * mirror in sim/osc_sim/firmware.py: keep both in step). */
#ifndef OSC_SIM_IO_H
#define OSC_SIM_IO_H
#include <stdint.h>

#define SIM_PORTS 6
#define SIM_PINS 16
#define SIM_ADCS 2
#define SIM_ADC_CHANNELS 20

typedef struct {
    uint32_t millis;
    uint8_t mode[SIM_PORTS][SIM_PINS];      /* osc_pin_mode */
    uint8_t af[SIM_PORTS][SIM_PINS];
    uint8_t odr[SIM_PORTS][SIM_PINS];
    uint8_t idr[SIM_PORTS][SIM_PINS];       /* written by the board */
    uint8_t idr_valid[SIM_PORTS][SIM_PINS]; /* 0: level between VIL and VIH */
    uint16_t pwm[SIM_PORTS][SIM_PINS];      /* permille */
    uint32_t edges[SIM_PORTS][SIM_PINS];    /* written by the board */
    uint16_t adc[SIM_ADCS][SIM_ADC_CHANNELS];
    uint8_t dead_battery;
    uint32_t undefined_reads, analog_reads, bad_calls;
} sim_io;

extern sim_io osc_sim_io;
void osc_sim_reset(void);
#endif
