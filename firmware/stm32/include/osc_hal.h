/* SPDX-License-Identifier: MIT */
/* The little hardware access the BSP needs. The target port (CubeMX/LL) is
 * TBD; on the host sim/hal/hal_sim.c implements it against the virtual board
 * (sim/README.md, F1). Ports are 0 = GPIOA ... 5 = GPIOF, as in board_pins.h. */
#ifndef OSC_HAL_H
#define OSC_HAL_H
#include <stdbool.h>
#include <stdint.h>

typedef enum {
    OSC_PIN_ANALOG, /* reset state of every pin but the debug ones */
    OSC_PIN_INPUT,
    OSC_PIN_OUTPUT,
    OSC_PIN_AF      /* alternate function 'af' (timer, UART) */
} osc_pin_mode;

void osc_hal_pin_mode(unsigned port, unsigned pin, osc_pin_mode mode, unsigned af);
void osc_hal_pin_write(unsigned port, unsigned pin, bool high);
bool osc_hal_pin_read(unsigned port, unsigned pin);
/* 12-bit conversion of a pin's ADC channel against VREF+ (= VDDA). */
uint16_t osc_hal_adc_read(unsigned adc, unsigned channel);
/* Falling edges counted by the timer input on a pin in OSC_PIN_AF mode. */
uint32_t osc_hal_edge_count(unsigned port, unsigned pin);
/* Duty of the timer output on a pin in OSC_PIN_AF mode, 0..1000. */
void osc_hal_pwm_set(unsigned port, unsigned pin, unsigned permille);
/* PWR_CR3.UCPD_DBDIS: removes the dead-battery Rd that UCPD1 keeps on
 * CC1 (PB6) and CC2 (PB4) from power-up (RM0440, UCPD dead battery). */
void osc_hal_disable_ucpd_dead_battery(void);
uint32_t osc_hal_millis(void);
#endif
