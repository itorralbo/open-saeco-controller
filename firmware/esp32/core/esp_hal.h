/* SPDX-License-Identifier: MIT */
/* The hardware access the ESP32 interface core needs. The ESP-IDF port
 * (driver/gpio, i2c_master, spi_master, uart, ledc) is TBD; on the host
 * sim/hal/hal_esp_sim.c implements it against the virtual board. GPIO
 * numbers are those of board_pins.h. */
#ifndef OSC_ESP_HAL_H
#define OSC_ESP_HAL_H
#include <stdbool.h>
#include <stdint.h>

typedef enum {
    ESP_GPIO_OFF,   /* high impedance, as after reset */
    ESP_GPIO_INPUT,
    ESP_GPIO_OUTPUT
} esp_gpio_mode;

void esp_hal_gpio_mode(unsigned gpio, esp_gpio_mode mode);
void esp_hal_gpio_write(unsigned gpio, bool high);
bool esp_hal_gpio_read(unsigned gpio);

/* Bus peripherals route their pins through the GPIO matrix on init and
 * leave them high impedance on deinit. */
void esp_hal_i2c_init(unsigned sda, unsigned scl, uint32_t hz);
void esp_hal_i2c_deinit(void);
/* Write wn bytes, then (repeated start) read rn; false on NACK or bus error. */
bool esp_hal_i2c_xfer(uint8_t addr, const uint8_t *w, unsigned wn, uint8_t *r, unsigned rn);
void esp_hal_spi_init(unsigned sclk, unsigned mosi, unsigned cs, uint32_t hz);
void esp_hal_spi_deinit(void);
/* Mode 0, MSB first; CS is held low for the whole call. */
void esp_hal_spi_write(const uint8_t *data, unsigned n);
void esp_hal_uart_init(unsigned tx, unsigned rx, uint32_t baud);
unsigned esp_hal_uart_write(const uint8_t *data, unsigned n);
bool esp_hal_uart_read(uint8_t *byte);
/* LEDC duty on a pin, 0..1000; 0 also returns the pin to a driven low. */
void esp_hal_ledc_set(unsigned gpio, unsigned permille);
uint32_t esp_hal_millis(void);
#endif
