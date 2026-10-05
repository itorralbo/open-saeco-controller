/* SPDX-License-Identifier: MIT */
/* Shared state between hal_esp_sim.c and the Python virtual board (ctypes
 * mirror EspIO in sim/osc_sim/firmware.py: keep both in step). */
#ifndef OSC_SIM_ESP_IO_H
#define OSC_SIM_ESP_IO_H
#include <stdint.h>

#define SIM_ESP_GPIOS 49
#define SIM_UART_BUF 512

/* Bus transactions are answered by the board at once, through these. */
typedef int (*sim_i2c_fn)(uint8_t addr, const uint8_t *w, unsigned wn, uint8_t *r, unsigned rn);
typedef void (*sim_spi_fn)(const uint8_t *data, unsigned n);

enum { SIM_PIN_OFF, SIM_PIN_INPUT, SIM_PIN_OUTPUT, SIM_PIN_I2C, SIM_PIN_SPI_CLK, SIM_PIN_SPI_MOSI,
       SIM_PIN_SPI_CS, SIM_PIN_UART_TX, SIM_PIN_UART_RX, SIM_PIN_LEDC };

typedef struct {
    uint32_t millis;
    uint8_t mode[SIM_ESP_GPIOS];  /* SIM_PIN_* */
    uint8_t level[SIM_ESP_GPIOS]; /* output level */
    uint8_t in[SIM_ESP_GPIOS];    /* written by the board */
    uint8_t in_valid[SIM_ESP_GPIOS];
    uint16_t duty[SIM_ESP_GPIOS];
    uint32_t i2c_hz, spi_hz, uart_baud;
    uint32_t undefined_reads, bad_calls, spi_bytes, i2c_xfers;
    sim_i2c_fn i2c;
    sim_spi_fn spi;
    uint8_t uart_tx[SIM_UART_BUF];
    uint16_t uart_tx_len;
    uint8_t uart_rx[SIM_UART_BUF];
    uint16_t uart_rx_head, uart_rx_len;
} sim_esp_io;

extern sim_esp_io osc_esp_io;
void osc_esp_sim_reset(void);
#endif
