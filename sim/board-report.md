# Informe del modelo de placa

Generado por `tools/build_board_model.py` a partir de los netlists de las dos placas y del
[contrato de firmware](../firmware/common/signals.json). No sustituye a ERC/DRC.
Qué comprueba cada regla: [README del simulador](README.md).

**0 errores, 0 avisos.**

## Hallazgos

- **Nota** `pin-note`: stm32.BREW_DIR en PC14: Dominio de respaldo (pin RTC/LSE): salida de 2 MHz y 3 mA como máximo, una sola a la vez con PC13/PC15.
- **Nota** `pin-note`: stm32.BREW_FAULT_N en PB6: UCPD1_CC1: el BSP debe llamar a HAL_PWREx_DisableUCPDDeadBattery() antes de fiarse del nivel leído.
- **Nota** `pin-note`: stm32.WDT_KICK en PB4: Tras el reset es NJTRST con pull-up interno y además UCPD1_CC2: el BSP debe liberar JTAG y llamar a HAL_PWREx_DisableUCPDDeadBattery() antes de usarlo.
- **Nota** `power-domain`: esp32.KEY_INT_N (R3), esp32.KEY_SCL (R1), esp32.KEY_SDA (R2), esp32.LCD_CS_N (R4), esp32.LCD_RST_N (R5) tienen pull-up a controller:3V3_UI, no a controller:3V3_CORE: con controller:3V3_UI apagado los GPIO en alto lo alimentan a través de esas líneas.

## Señales

| MCU | Señal | Red | Pad | Pin real | Periférico | Reset | Camino |
|---|---|---|---|---|---|---|---|
| esp32 | KEY_INT_N | `KEY_INT_N` | 6 | GPIO6 | gpio_in |  |  |
| esp32 | KEY_SCL | `KEY_SCL` | 5 | GPIO5 | i2c_scl |  |  |
| esp32 | KEY_SDA | `KEY_SDA` | 4 | GPIO4 | i2c_sda |  |  |
| esp32 | LCD_BL | `BL_RAW` | 7 | GPIO7 | ledc | low | R218 |
| esp32 | LCD_CS_N | `CS_RAW` | 18 | GPIO10 | spi_cs | high | R215 |
| esp32 | LCD_DC | `DC_RAW` | 17 | GPIO9 | gpio_out |  | R216 |
| esp32 | LCD_MOSI | `MOSI_RAW` | 19 | GPIO11 | spi_mosi |  | R214 |
| esp32 | LCD_RST_N | `RST_RAW` | 12 | GPIO8 | gpio_out | high | R217 |
| esp32 | LCD_SCLK | `SCLK_RAW` | 20 | GPIO12 | spi_sclk |  | R213 |
| esp32 | UART_RX | `STM_TO_ESP` | 38 | GPIO2 | uart_rx |  | R211 |
| esp32 | UART_TX | `ESP_TX_RAW` | 35 | GPIO42 | uart_tx |  | R212 |
| esp32 | USB_DM | `USB_DM_RAW` | 13 | GPIO19 | usb_dm |  | R221 → U203 |
| esp32 | USB_DP | `USB_DP_RAW` | 14 | GPIO20 | usb_dp |  | R222 → U203 |
| esp32 | VBUS_SENSE | `USB_VBUS_SENSE` | 8 | GPIO15 | gpio_in |  | R225 |
| stm32 | BREW_CURRENT | `BREW_CURRENT_ADC` | 8 | PC0 | ADC1_IN6 |  |  |
| stm32 | BREW_DIR | `BREW_DIR_RAW` | 3 | PC14 |  | low | R503 → U501 |
| stm32 | BREW_FAULT_N | `BREW_FAULT_N` | 59 | PB6 |  |  |  |
| stm32 | BREW_PWM | `BREW_PWM_RAW` | 5 | PF0 | TIM1_CH3N AF6 | low | R501 → U501 |
| stm32 | BREW_SLEEP_N | `BREW_SLEEP_RAW` | 58 | PB5 |  | low | U602 → R505 → U501 |
| stm32 | BU_PRESENT_N | `BU_PRESENT_N` | 10 | PC2 |  |  | R408 |
| stm32 | BU_WORK_N | `BU_WORK_N` | 12 | PA0 |  |  | R410 |
| stm32 | DOOR_CLOSED_N | `DOOR_CLOSED_N` | 13 | PA1 |  |  | R406 |
| stm32 | FLOW | `FLOW_TIM` | 14 | PA2 | TIM2_CH3 AF1 |  | R404 |
| stm32 | GRINDER_CURRENT | `GRINDER_CURRENT_ADC` | 20 | PA6 | ADC2_IN3 |  | R412 |
| stm32 | GRINDER_EN | `GRINDER_EN_RAW` | 22 | PC4 |  | low | U604 → R718 → Q707 → U703 → Q708 → F703 → BR701 → U704 |
| stm32 | HEATER_EN | `HEATER_EN_RAW` | 23 | PC5 |  | low | U603 → R707 → Q705 → U701 → Q703 |
| stm32 | HEATSINK_AIR | `HS_NTC_ADC` | 36 | PB14 | ADC1_IN5 |  | R726 |
| stm32 | MAINS_ARM | `MAINS_ARM_RAW` | 60 | PB7 |  | low | U603 → R801 → Q701 → K701 |
| stm32 | NTC | `NTC_ADC` | 17 | PA3 | ADC1_IN4 |  | R402 |
| stm32 | PUMP_EN | `PUMP_EN_RAW` | 33 | PB11 |  | low | U604 → R714 → Q706 → U702 → Q704 |
| stm32 | RAIL_12V | `RAIL_12V_ADC` | 6 | PF1 | ADC2_IN10 |  | R702 → R701 |
| stm32 | RAIL_24V | `RAIL_24V_ADC` | 9 | PC1 | ADC1_IN7 |  | R705 → R704 |
| stm32 | UART_RX | `ESP_TO_STM` | 44 | PA10 | USART1_RX AF7 |  | R212 |
| stm32 | UART_TX | `STM_TX_RAW` | 43 | PA9 | USART1_TX AF7 |  | R211 |
| stm32 | UI_PWR_EN | `UI_PWR_EN` | 34 | PB12 |  | high | U302 |
| stm32 | VALVE_EN | `VALVE_EN_RAW` | 21 | PA7 |  | low | U602 → R511 → U502 → R513 → Q501 |
| stm32 | WATER_LEVEL | `WATER_LEVEL` | 11 | PC3 | ADC1_IN9 |  | R411 |
| stm32 | WDT_KICK | `WATCHDOG_KICK_RAW` | 57 | PB4 |  | low | R601 → U606 |

## Entradas analógicas

| Señal | Resultado |
|---|---|
| BREW_CURRENT | VREF 2.425 V; regulación a 1.01 A; 2.400 V/A; 0.34 mA/LSB |
| HEATSINK_AIR | 0 °C → 2.437 V, 120 °C → 0.200 V; 40 °C: 1.213 V, 0.030 °C/LSB; 80 °C: 0.482 V, 0.072 °C/LSB |
| NTC | 0 °C → 3.212 V, 150 °C → 0.537 V; 90 °C: 1.600 V, 0.032 °C/LSB; 125 °C: 0.863 V, 0.050 °C/LSB |
| GRINDER_CURRENT | 100 mV/A sobre 1.65 V; 0 A → 1.650 V, 4.8 A → 2.130 V; 8.1 mA/LSB |
| RAIL_12V | 15 V → 0.714 V; fondo de escala 69.3 V; 16.9 mV/LSB |
| RAIL_24V | 28 V → 1.333 V; fondo de escala 69.3 V; 16.9 mV/LSB |

## Excitación en el peor caso

Cada orden activa con los rails al mínimo (sim/osc_sim/drive.py): lo que cambia de estado y su margen frente al punto que garantiza el fabricante (sim/reference/devices.json).

| Señal | Carga | Cadena |
|---|---|---|
| BREW_DIR | J108.8 | U501 fwd: nSLEEP 3.17 V, EN/IN1 3.17 V, PH/IN2 3.17 V (VIH 1.5 V) |
| BREW_PWM | J108.7 | U501 rev: nSLEEP 3.17 V, EN/IN1 3.17 V, PH/IN2 0.00 V (VIH 1.5 V) |
| BREW_SLEEP_N | J108.7 | U501 rev: nSLEEP 3.17 V, EN/IN1 3.17 V, PH/IN2 0.00 V (VIH 1.5 V) |
| GRINDER_EN | J115.1 | Q707 VGS 3.20 V ≥ 2.75 V; Q708 disparado; U703 IF 9.5 mA ≥ 5 mA |
| HEATER_EN | J116.1 | Q703 disparado; Q705 VGS 3.20 V ≥ 2.75 V; U701 IF 9.5 mA ≥ 5 mA |
| MAINS_ARM | Q703.A2 | K701 bobina 21.5 V ≥ 16.8 V; Q701 VGS 3.20 V ≥ 2.75 V |
| PUMP_EN | J117.1 | Q704 disparado; Q706 VGS 3.20 V ≥ 2.75 V; U702 IF 9.5 mA ≥ 5 mA |
| UI_PWR_EN | J104.1 | U302 ON 3.20 V ≥ 1.1 V |
| VALVE_EN | J113.4 | Q501 VGS 11.00 V ≥ 4.5 V; U502 IN+ 3.17 V ≥ 2.4 V |
