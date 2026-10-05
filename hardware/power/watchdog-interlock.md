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

U603 y U604, del mismo tipo, aplican la misma regla al resto:

```text
MAINS_RELAY_EN         = MAINS_ARM_RAW  AND STM_NRST   (U603, relé K701)
HEATER_EN_INTERLOCK    = HEATER_EN_RAW  AND STM_NRST   (U603)
PUMP_EN_INTERLOCK      = PUMP_EN_RAW    AND STM_NRST   (U604)
GRINDER_EN_INTERLOCK   = GRINDER_EN_RAW AND STM_NRST   (U604)
```

R603 y R604, ambos de 10 kΩ, mantienen las órdenes brutas a cero al arrancar;
R711, R713, R717 y R722 hacen lo mismo con calentador, bomba, molinillo y el
armado del relé general. R722 se añadió el 2026-10-01: sin él, la entrada 1A de
U603 quedaba flotante entre el fin del reset y la configuración de PB7.
R506 y R512 conservan además los pull-down junto a cada driver. Mientras
`STM_NRST` está bajo, U602 fuerza ambas salidas a cero aunque el software o un
GPIO fallen en alto. Mantener NRST bajo desde SWD también deshabilita las cargas.

## Límites y pruebas pendientes

- El interlock cubre el motor del grupo y la válvula. El calentador pasa por la
  segunda puerta de U603, la bomba por la primera de U604 y el molinillo, desde
  PC4, por la segunda. Las tres órdenes y la de la válvula están ruteadas desde
  el STM32 hasta sus puertas, igual que las dos salidas de U602.
- Un MOSFET o puente H puede fallar en corto; este circuito no aporta aislamiento
  galvánico ni sustituye fusibles, corte térmico o desconexión de red.
- Medir el tiempo hasta reset, la secuencia de recuperación y los niveles de
  ambas salidas con 12 V y 24 V presentes en cualquier orden.
- Confirmar que el arranque completo llega al primer pulso antes de 0,9 s o
  definir una estrategia de inicialización que mantenga las cargas bloqueadas.
- Inyectar bloqueo del firmware, brownout, PB4 fijo alto/bajo y reset SWD. Cada
  caso debe llevar a cero `BREW_SLEEP_DRV`, `VALVE_EN_DRV`, el relé K701 y las
  tres órdenes de red.

El [simulador](../../sim/README.md) (F1) ejecuta el bucle del firmware contra
este circuito con los tiempos del extremo desfavorable: el firmware sano no
provoca resets con un time-out de 0,9 s, un núcleo colgado se resetea antes de
2,5 s y las órdenes que un núcleo desbocado deja activas caen en el mismo paso en
que U601 baja `STM_NRST`. También modela que el TPS3828 sin sufijo A deja RESET
enclavado si WDI recibe flancos mientras está activo; con el STM32 en reset PB4
queda en alta impedancia y R602 lo mantiene bajo, así que no ocurre. No sustituye
al ensayo anterior.

Fuentes: [TPS3828/TPS382x de TI](https://www.ti.com/lit/ds/symlink/tps3823.pdf),
[SN74LVC2G08 de TI](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf),
[TPS3828-33DBVR en LCSC](https://www.lcsc.com/product-detail/C20032.html) y
[SN74LVC2G08DCTR en LCSC](https://www.lcsc.com/product-detail/C352973.html).
El 2026-09-19 se observaron 49.065 y 21.000 unidades respectivamente; no son una
reserva de inventario.
