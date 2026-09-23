# Watchdog e interlock hardware de actuadores

Estado: incorporado al esquema y a la PCB de trabajo; pendiente de firmware y
ensayo físico. No libera la placa para fabricación.

## Función

U601 es un TI `TPS3828-33DBVR` (`C20032`) alimentado desde `3V3_CORE`. Supervisa
el rail con umbral nominal de 2,93 V y exige transiciones periódicas en WDI. Su
salida activa a cero y open-drain comparte `STM_NRST`, por lo que puede reiniciar
el STM32 sin entrar en conflicto con el adaptador SWD.

PB4 genera `WATCHDOG_KICK_RAW`. R601=33 Ω lo conecta a WDI y R602=1 kΩ mantiene
WDI a masa si el GPIO queda en alta impedancia. Esto impide el modo de watchdog
deshabilitado que el fabricante define para WDI flotante. El firmware debe crear
flancos de bajada con un periodo menor que el timeout mínimo de 0,9 s; el valor
nominal es 1,6 s y el máximo 2,5 s. Tras un fallo, reset permanece activo entre
120 y 300 ms, 200 ms nominales.

U602 es un `SN74LVC2G08DCTR` (`C352973`) alimentado a 3,3 V. Implementa:

```text
BREW_SLEEP_INTERLOCK = BREW_SLEEP_RAW AND STM_NRST
VALVE_EN_INTERLOCK   = VALVE_EN_RAW   AND STM_NRST
```

R603 y R604, ambos de 10 kΩ, mantienen las órdenes brutas a cero al arrancar.
R506 y R512 conservan además los pull-down junto a cada driver. Mientras
`STM_NRST` está bajo, U602 fuerza ambas salidas a cero aunque el software o un
GPIO fallen en alto. Mantener NRST bajo desde SWD también deshabilita las cargas.

## Límites y pruebas pendientes

- El interlock cubre el motor del grupo y la válvula. El calentador pasa por la
  segunda puerta de U603, la bomba por la primera de U604 y el molinillo, desde
  PB12, por la segunda. U604 está ruteada desde PB11 hasta R714; la segunda
  puerta está en el esquema pero no en la PCB, y PB10 sigue pendiente hasta
  U603.
- Un MOSFET o puente H puede fallar en corto; este circuito no aporta aislamiento
  galvánico ni sustituye fusibles, corte térmico o desconexión de red.
- Medir el tiempo hasta reset, la secuencia de recuperación y los niveles de
  ambas salidas con 12 V y 24 V presentes en cualquier orden.
- Confirmar que el arranque completo llega al primer pulso antes de 0,9 s o
  definir una estrategia de inicialización que mantenga las cargas bloqueadas.
- Inyectar bloqueo del firmware, brownout, PB4 fijo alto/bajo y reset SWD. Cada
  caso debe llevar `BREW_SLEEP_DRV` y `VALVE_EN_DRV` a cero.

Fuentes: [TPS3828/TPS382x de TI](https://www.ti.com/lit/ds/symlink/tps3823.pdf),
[SN74LVC2G08 de TI](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf),
[TPS3828-33DBVR en LCSC](https://www.lcsc.com/product-detail/C20032.html) y
[SN74LVC2G08DCTR en LCSC](https://www.lcsc.com/product-detail/C352973.html).
El 2026-09-19 se observaron 49.065 y 21.000 unidades respectivamente; no son una
reserva de inventario.
