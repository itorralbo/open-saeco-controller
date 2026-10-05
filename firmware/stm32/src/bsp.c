/* SPDX-License-Identifier: MIT */
#include "bsp.h"
#include "board_pins.h"
#include "osc_hal.h"

#define PORT(s) BOARD_##s##_PORT
#define PIN(s) BOARD_##s##_PIN
/* Level that makes an order active, from the contract's polarity. */
#define LEVEL(s, on) ((on) ? (BOARD_##s##_ACTIVE_HIGH != 0) : (BOARD_##s##_ACTIVE_HIGH == 0))
#define ORDER(s, on) osc_hal_pin_write(PORT(s), PIN(s), LEVEL(s, on))
#define ACTIVE(s) (osc_hal_pin_read(PORT(s), PIN(s)) == (BOARD_##s##_ACTIVE_HIGH != 0))
#define ADC(s) osc_hal_adc_read(BOARD_##s##_ADC, BOARD_##s##_ADC_CHANNEL)

static bool kick;

static void output(unsigned port, unsigned pin, bool level) {
    osc_hal_pin_write(port, pin, level);
    osc_hal_pin_mode(port, pin, OSC_PIN_OUTPUT, 0);
}

void bsp_init(void) {
    /* PB4 (WDI) and PB6 (nFAULT) are UCPD1 CC2/CC1: drop the dead-battery
     * pull-downs before driving or reading them. */
    osc_hal_disable_ucpd_dead_battery();
    output(PORT(HEATER_EN), PIN(HEATER_EN), LEVEL(HEATER_EN, false));
    output(PORT(PUMP_EN), PIN(PUMP_EN), LEVEL(PUMP_EN, false));
    output(PORT(GRINDER_EN), PIN(GRINDER_EN), LEVEL(GRINDER_EN, false));
    output(PORT(MAINS_ARM), PIN(MAINS_ARM), LEVEL(MAINS_ARM, false));
    output(PORT(VALVE_EN), PIN(VALVE_EN), LEVEL(VALVE_EN, false));
    output(PORT(BREW_SLEEP_N), PIN(BREW_SLEEP_N), LEVEL(BREW_SLEEP_N, false));
    output(PORT(BREW_DIR), PIN(BREW_DIR), LEVEL(BREW_DIR, false));
    output(PORT(WDT_KICK), PIN(WDT_KICK), false);
    output(PORT(UI_PWR_EN), PIN(UI_PWR_EN), LEVEL(UI_PWR_EN, true));
    osc_hal_pwm_set(PORT(BREW_PWM), PIN(BREW_PWM), 0);
    osc_hal_pin_mode(PORT(BREW_PWM), PIN(BREW_PWM), OSC_PIN_AF, BOARD_BREW_PWM_AF);
    osc_hal_pin_mode(PORT(DOOR_CLOSED_N), PIN(DOOR_CLOSED_N), OSC_PIN_INPUT, 0);
    osc_hal_pin_mode(PORT(BU_PRESENT_N), PIN(BU_PRESENT_N), OSC_PIN_INPUT, 0);
    osc_hal_pin_mode(PORT(BU_WORK_N), PIN(BU_WORK_N), OSC_PIN_INPUT, 0);
    osc_hal_pin_mode(PORT(BREW_FAULT_N), PIN(BREW_FAULT_N), OSC_PIN_INPUT, 0);
    osc_hal_pin_mode(PORT(FLOW), PIN(FLOW), OSC_PIN_AF, BOARD_FLOW_AF);
    osc_hal_pin_mode(PORT(UART_TX), PIN(UART_TX), OSC_PIN_AF, BOARD_UART_TX_AF);
    osc_hal_pin_mode(PORT(UART_RX), PIN(UART_RX), OSC_PIN_AF, BOARD_UART_RX_AF);
    kick = false;
}

void bsp_watchdog_toggle(void) {
    kick = !kick;
    osc_hal_pin_write(PORT(WDT_KICK), PIN(WDT_KICK), kick);
}

void bsp_read(osc_inputs *in) {
    in->door_closed = ACTIVE(DOOR_CLOSED_N);
    in->bu_present = ACTIVE(BU_PRESENT_N);
    in->bu_work = ACTIVE(BU_WORK_N);
    in->brew_fault = ACTIVE(BREW_FAULT_N);
    in->ntc = ADC(NTC);
    in->water = ADC(WATER_LEVEL);
    in->rail_12v = ADC(RAIL_12V);
    in->rail_24v = ADC(RAIL_24V);
    in->brew_current = ADC(BREW_CURRENT);
    in->flow_edges = osc_hal_edge_count(PORT(FLOW), PIN(FLOW));
}

void bsp_write(const osc_outputs *out) {
    const bool mains = out->heater || out->pump || out->grinder;
    ORDER(HEATER_EN, out->heater);
    ORDER(PUMP_EN, out->pump);
    ORDER(GRINDER_EN, out->grinder);
    ORDER(MAINS_ARM, mains);
    ORDER(VALVE_EN, out->valve);
    ORDER(BREW_SLEEP_N, out->brew_motor);
    osc_hal_pwm_set(PORT(BREW_PWM), PIN(BREW_PWM), out->brew_motor ? 1000u : 0u);
}

void bsp_ui_power(bool on) { ORDER(UI_PWR_EN, on); }
