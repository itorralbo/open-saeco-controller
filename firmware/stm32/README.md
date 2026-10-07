# Núcleo STM32

C99 portable. CMake compila para host; no es firmware flasheable.
El esquema usa un STM32G431RBT6 y ya fija sus pines
([core-design.md](../../hardware/controller/core-design.md)); startup,
linker script y el puerto de `osc_hal.h` al micro (CubeMX/LL) siguen TBD.

- `controller.c`: máquina de estados. Ningún estado del controlador autoriza
  cargas; solo lo hace una prueba de puesta a punto.
- `service.c`: pruebas de puesta a punto ([protocolo](../common/protocol.md#pruebas-de-puesta-a-punto)).
  Solo mueven cargas con el núcleo en SAFE_IDLE y el enlace vivo; cada una
  tiene tiempo máximo, la puerta y nFAULT se vigilan en cada paso, y el bucle
  principal deja de escribir sus salidas en cuanto el núcleo sale de SAFE_IDLE.
  El molinillo se juzga por su corriente (U704) en bloques de 100 ms con
  `osc_grinder_verdict()`: falta de grano o bloqueo; la dosis, por la subida
  de la corriente del grupo al prensar con `osc_dose_present()`. Umbrales en
  `controller.h`, supuestos hasta caracterizar el motor.
- `osc_hal.h`: el poco acceso al hardware que necesita el BSP (modo y nivel de
  pin, ADC, contador de flancos, PWM, desactivar el *dead battery* de UCPD,
  UART, calibración de VREFINT, milisegundos). En host lo implementa
  `sim/hal/hal_sim.c`.
- `bsp.c`: las señales del [contrato](../common/signals.json) sobre los pines
  de `board_pins.h`, generado desde los netlists. Deja cada orden inactiva antes
  de convertir su pin en salida y quita el Rd de UCPD de PB4/PB6 antes de usarlos.
- `app.c`: bucle principal. Conmuta el impulso del watchdog cada 100 ms (U601
  resetea a los 0,9 s como pronto), atiende el [protocolo v0](../common/protocol.md)
  con el ESP32 (STATUS cada 100 ms, enlace perdido a los 350 ms, TEST y
  TEST_REPORT), lee entradas,
  ejecuta el controlador cada 10 ms y escribe las salidas. La corriente del
  molinillo se muestrea en cada vuelta (1 ms, `bsp_sample()`) y se promedia por
  tick: es una onda rectificada de 100 Hz que un muestreo cada 10 ms aliasaría. Tras el reset espera
  hasta 2 s en `OSC_BOOT` a que aparezca el ESP32; sin enlace pasa a `OSC_FAULT`,
  del que solo sale con CLEAR_FAULT. Los rails y la corriente se escalan con la
  VDDA medida contra VREFINT y su calibración de fábrica, no con 3,3 V supuestos.

El [simulador](../../sim/README.md) (F1, F2) ejecuta este código contra la placa
virtual. No usar este scaffolding como supervisor de seguridad.
`osc_heater_cycles_allowed()` fija ya la regla de reparto de la fase de cargas
(calentador a 3 de cada 5 ciclos mientras muele el molinillo); ver
[power-architecture.md](../../hardware/power/power-architecture.md#reparto-de-corriente-en-la-fase-de-cargas).
`osc_heatsink_step()` y `osc_heater_cycles_thermal()` añaden la limitación
térmica del calentador (issue #2). Con el aire de RT701 (PB14) y la potencia de
cada triac estiman la unión de Q703 y le quitan ciclos por encima de 105 °C,
hasta ninguno a 120 °C. El llamador toma el menor de los dos límites.
Constantes supuestas hasta TH-03.
