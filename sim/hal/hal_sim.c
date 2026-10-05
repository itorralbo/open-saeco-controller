/* SPDX-License-Identifier: MIT */
/* osc_hal.h on the host. The firmware sees registers; sim/osc_sim/board.py
 * reads the pin modes and output levels from osc_sim_io and writes back the
 * input levels, ADC codes and timer counts that the virtual board produces.
 * Reset state follows RM0440: every pin analog except the debug pins, and
 * UCPD1's dead-battery pull-downs present on PB4/PB6 until disabled. */
#include <string.h>
#include "osc_hal.h"
#include "sim_io.h"

sim_io osc_sim_io;

static int valid(unsigned port, unsigned pin) {
    return port < SIM_PORTS && pin < SIM_PINS;
}

void osc_sim_reset(void) {
    const uint32_t now = osc_sim_io.millis;
    const uint16_t cal = osc_sim_io.vrefint_cal;
    memset(&osc_sim_io, 0, sizeof osc_sim_io);
    osc_sim_io.millis = now;
    osc_sim_io.vrefint_cal = cal; /* system memory survives reset */
    osc_sim_io.dead_battery = 1;
}

void osc_hal_pin_mode(unsigned port, unsigned pin, osc_pin_mode mode, unsigned af) {
    if (!valid(port, pin)) {
        osc_sim_io.bad_calls++;
        return;
    }
    osc_sim_io.mode[port][pin] = (uint8_t)mode;
    osc_sim_io.af[port][pin] = (uint8_t)af;
}

void osc_hal_pin_write(unsigned port, unsigned pin, bool high) {
    if (!valid(port, pin)) {
        osc_sim_io.bad_calls++;
        return;
    }
    osc_sim_io.odr[port][pin] = high ? 1u : 0u;
}

bool osc_hal_pin_read(unsigned port, unsigned pin) {
    if (!valid(port, pin)) {
        osc_sim_io.bad_calls++;
        return false;
    }
    if (osc_sim_io.mode[port][pin] == OSC_PIN_ANALOG)
        osc_sim_io.analog_reads++; /* IDR reads 0 in analog mode */
    else if (!osc_sim_io.idr_valid[port][pin])
        osc_sim_io.undefined_reads++;
    return osc_sim_io.mode[port][pin] != OSC_PIN_ANALOG && osc_sim_io.idr[port][pin];
}

uint16_t osc_hal_adc_read(unsigned adc, unsigned channel) {
    if (adc < 1 || adc > SIM_ADCS || channel >= SIM_ADC_CHANNELS) {
        osc_sim_io.bad_calls++;
        return 0;
    }
    return osc_sim_io.adc[adc - 1][channel];
}

uint32_t osc_hal_edge_count(unsigned port, unsigned pin) {
    return valid(port, pin) ? osc_sim_io.edges[port][pin] : 0u;
}

void osc_hal_pwm_set(unsigned port, unsigned pin, unsigned permille) {
    if (!valid(port, pin) || permille > 1000u) {
        osc_sim_io.bad_calls++;
        return;
    }
    osc_sim_io.pwm[port][pin] = (uint16_t)permille;
}

void osc_hal_disable_ucpd_dead_battery(void) { osc_sim_io.dead_battery = 0; }

uint32_t osc_hal_millis(void) { return osc_sim_io.millis; }

uint16_t osc_hal_vrefint_cal(void) { return osc_sim_io.vrefint_cal; }

unsigned osc_hal_uart_write(const uint8_t *data, unsigned n) {
    unsigned room = SIM_UART_BUF - osc_sim_io.uart_tx_len;
    if (n > room) n = room;
    memcpy(&osc_sim_io.uart_tx[osc_sim_io.uart_tx_len], data, n);
    osc_sim_io.uart_tx_len = (uint16_t)(osc_sim_io.uart_tx_len + n);
    return n;
}

bool osc_hal_uart_read(uint8_t *byte) {
    if (osc_sim_io.uart_rx_head >= osc_sim_io.uart_rx_len) return false;
    *byte = osc_sim_io.uart_rx[osc_sim_io.uart_rx_head++];
    return true;
}

/* Size the ctypes mirror in sim/osc_sim/firmware.py checks on load. */
unsigned osc_sim_size(void) { return (unsigned)sizeof(sim_io); }
