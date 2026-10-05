/* SPDX-License-Identifier: MIT */
/* esp_hal.h on the host. Every pin starts high impedance, as after the
 * ESP32-S3 reset; peripherals take their pins through the GPIO matrix. */
#include <string.h>
#include "esp_hal.h"
#include "sim_esp_io.h"
#include "esp_app.h"

sim_esp_io osc_esp_io;
static unsigned spi_cs = SIM_ESP_GPIOS, i2c_pins[2] = {SIM_ESP_GPIOS, SIM_ESP_GPIOS};
static unsigned spi_pins[2] = {SIM_ESP_GPIOS, SIM_ESP_GPIOS};

static int valid(unsigned gpio) { return gpio < SIM_ESP_GPIOS; }

void osc_esp_sim_reset(void) {
    const uint32_t now = osc_esp_io.millis;
    const sim_i2c_fn i2c = osc_esp_io.i2c;
    const sim_spi_fn spi = osc_esp_io.spi;
    memset(&osc_esp_io, 0, sizeof osc_esp_io);
    osc_esp_io.millis = now;
    osc_esp_io.i2c = i2c;
    osc_esp_io.spi = spi;
    spi_cs = i2c_pins[0] = i2c_pins[1] = spi_pins[0] = spi_pins[1] = SIM_ESP_GPIOS;
}

static void set_mode(unsigned gpio, uint8_t mode) {
    if (!valid(gpio)) {
        osc_esp_io.bad_calls++;
        return;
    }
    osc_esp_io.mode[gpio] = mode;
}

void esp_hal_gpio_mode(unsigned gpio, esp_gpio_mode mode) {
    set_mode(gpio, mode == ESP_GPIO_OUTPUT ? SIM_PIN_OUTPUT : mode == ESP_GPIO_INPUT ? SIM_PIN_INPUT : SIM_PIN_OFF);
}

void esp_hal_gpio_write(unsigned gpio, bool high) {
    if (!valid(gpio)) {
        osc_esp_io.bad_calls++;
        return;
    }
    osc_esp_io.level[gpio] = high ? 1u : 0u;
}

bool esp_hal_gpio_read(unsigned gpio) {
    if (!valid(gpio)) {
        osc_esp_io.bad_calls++;
        return false;
    }
    if (!osc_esp_io.in_valid[gpio]) osc_esp_io.undefined_reads++;
    return osc_esp_io.in[gpio] != 0;
}

void esp_hal_i2c_init(unsigned sda, unsigned scl, uint32_t hz) {
    set_mode(sda, SIM_PIN_I2C);
    set_mode(scl, SIM_PIN_I2C);
    i2c_pins[0] = sda;
    i2c_pins[1] = scl;
    osc_esp_io.i2c_hz = hz;
}

void esp_hal_i2c_deinit(void) {
    unsigned i;
    for (i = 0; i < 2; ++i)
        if (valid(i2c_pins[i])) osc_esp_io.mode[i2c_pins[i]] = SIM_PIN_OFF;
    osc_esp_io.i2c_hz = 0;
}

bool esp_hal_i2c_xfer(uint8_t addr, const uint8_t *w, unsigned wn, uint8_t *r, unsigned rn) {
    osc_esp_io.i2c_xfers++;
    if (!osc_esp_io.i2c_hz || !osc_esp_io.i2c) return false;
    return osc_esp_io.i2c(addr, w, wn, r, rn) != 0;
}

void esp_hal_spi_init(unsigned sclk, unsigned mosi, unsigned cs, uint32_t hz) {
    set_mode(sclk, SIM_PIN_SPI_CLK);
    set_mode(mosi, SIM_PIN_SPI_MOSI);
    set_mode(cs, SIM_PIN_SPI_CS);
    spi_pins[0] = sclk;
    spi_pins[1] = mosi;
    spi_cs = cs;
    osc_esp_io.spi_hz = hz;
}

void esp_hal_spi_deinit(void) {
    unsigned i;
    for (i = 0; i < 2; ++i)
        if (valid(spi_pins[i])) osc_esp_io.mode[spi_pins[i]] = SIM_PIN_OFF;
    if (valid(spi_cs)) osc_esp_io.mode[spi_cs] = SIM_PIN_OFF;
    osc_esp_io.spi_hz = 0;
}

void esp_hal_spi_write(const uint8_t *data, unsigned n) {
    if (!osc_esp_io.spi_hz) {
        osc_esp_io.bad_calls++;
        return;
    }
    osc_esp_io.spi_bytes += n;
    if (osc_esp_io.spi) osc_esp_io.spi(data, n);
}

void esp_hal_uart_init(unsigned tx, unsigned rx, uint32_t baud) {
    set_mode(tx, SIM_PIN_UART_TX);
    set_mode(rx, SIM_PIN_UART_RX);
    osc_esp_io.uart_baud = baud;
}

unsigned esp_hal_uart_write(const uint8_t *data, unsigned n) {
    unsigned room = SIM_UART_BUF - osc_esp_io.uart_tx_len;
    if (n > room) n = room;
    memcpy(&osc_esp_io.uart_tx[osc_esp_io.uart_tx_len], data, n);
    osc_esp_io.uart_tx_len = (uint16_t)(osc_esp_io.uart_tx_len + n);
    return n;
}

bool esp_hal_uart_read(uint8_t *byte) {
    if (osc_esp_io.uart_rx_head >= osc_esp_io.uart_rx_len) return false;
    *byte = osc_esp_io.uart_rx[osc_esp_io.uart_rx_head++];
    return true;
}

void esp_hal_ledc_set(unsigned gpio, unsigned permille) {
    if (!valid(gpio) || permille > 1000u) {
        osc_esp_io.bad_calls++;
        return;
    }
    osc_esp_io.duty[gpio] = (uint16_t)permille;
    osc_esp_io.mode[gpio] = SIM_PIN_LEDC;
}

uint32_t esp_hal_millis(void) { return osc_esp_io.millis; }

/* Sizes the ctypes mirrors in sim/osc_sim/firmware.py check on load. */
unsigned osc_esp_sim_size(int which) {
    return which == 0 ? (unsigned)sizeof(sim_esp_io) : (unsigned)sizeof(osc_esp_view);
}
