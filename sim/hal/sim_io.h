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
#define SIM_UART_BUF 512

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
    uint16_t vrefint_cal; /* factory code of VREFINT at VDDA = 3.0 V */
    uint32_t undefined_reads, analog_reads, bad_calls;
    /* USART1: the firmware appends to tx, the board drains it; the board
     * appends to rx, the firmware consumes from rx_head. */
    uint8_t uart_tx[SIM_UART_BUF];
    uint16_t uart_tx_len;
    uint8_t uart_rx[SIM_UART_BUF];
    uint16_t uart_rx_head, uart_rx_len;
} sim_io;

extern sim_io osc_sim_io;
void osc_sim_reset(void);
#endif
