# Simulador de la cafetera

Entorno para probar el firmware sin hardware, coherente con las dos PCBs: el
cableado del simulador no se escribe a mano, se genera a partir de los netlists
de KiCad, así que un error de diseño aparece como un fallo de simulación.

| Fase | Contenido | Estado |
|---|---|---|
| F0 | Modelo de las dos placas, contrato de firmware, comprobaciones y `board_pins.h` | Hecha |
| F1 | STM32 en host contra la placa virtual: HAL, modelos de componentes y planta | Hecha; planta con valores supuestos |
| F2 | ESP32 en host: LVGL, ST7789 y TCA9534 virtuales, protocolo v0 | Pendiente |
| F3 | Panel web local: frontal, pantalla, gráficas, inyección de fallos, VCD | Pendiente |
| F4 | Recetas y máquina de estados completa | Pendiente |

## F0: modelo de placa

```
python tools/build_board_model.py           # regenera las salidas
python tools/build_board_model.py --check   # falla con errores de diseño o salidas viejas
python tools/build_board_model.py --as-if-fixed
python -m unittest discover -s tests/sim
```

`--as-if-fixed` repite las comprobaciones como si cada símbolo siguiera ya su
pinout de referencia: muestra lo que seguiría mal tras corregir los símbolos.
Los netlists se leen de `hardware/*/validation/netlist.xml`; tras editar un
esquema hay que regenerarlos con `tools/validate_kicad.py`.

Entradas:
- [Contrato de firmware](../firmware/common/signals.json): cada señal que usa el
  firmware (red, función, nivel activo, nivel en reset, a qué conector debe
  llegar y si va enclavada por el watchdog), el mazo entre placas, los rails y
  el teclado.
- [Pinouts de referencia](reference/pinouts.json) de cada CI activo, transcritos
  del fabricante con la fuente anotada.
- [Capacidades de los MCU](reference/mcus.json): funciones alternativas, canales
  ADC, pines reservados y estado tras reset. Un pin sin fila falla hasta que se
  añade desde la fuente.
- [Límites eléctricos](reference/devices.json) de cada CI y transistor (F1),
  con la hoja de datos de cada uno: VIH/VIL, VOH, VGS a la que se especifica
  RDS(on), IFT del opto, tensión de cierre del relé y tiempos del TPS3828.

Salidas (generadas, no editar):
- [Informe](board-report.md) con hallazgos, tabla de señales y entradas analógicas.
- `board-model.json`: componentes, redes globales y señales resueltas; es la
  entrada del simulador de F1.
- `firmware/stm32/include/board_pins.h` y `firmware/esp32/main/board_pins.h`:
  puerto, pin, AF y canal ADC de cada señal según los pads físicos.

## Qué comprueba

| Regla | Qué detecta |
|---|---|
| `symbol-pinout` | Símbolo cuyos pads no coinciden con el pinout del fabricante |
| `supply-pad`, `ground-pad`, `output-on-rail` | Alimentación o masa del CI real en una red de señal, o una salida unida a un rail |
| `pin-shift`, `signal-pad` | Señal que en el componente real cae en otro pin o en un pad de alimentación |
| `pin-caps`, `reserved-pin`, `strapping-pin` | Pin sin el periférico pedido (AF, ADC, USB) o reservado (SWD, BOOT0, flash/PSRAM) |
| `signal-path` | Orden que no llega a su carga o entrada que no viene de su conector, atravesando resistencias, puertas, drivers, optos, triacs, relé y mazo |
| `interlock` | Orden de carga que no pasa por una AND con `STM_NRST` (watchdog) |
| `reset-level` | Nivel de cada orden con el MCU en reset (pines en alta impedancia, pull internos de depuración) |
| `pull` | Entrada sin el pull-up o pull-down que requiere |
| `analog` | Divisores, NTC (ventana y °C/LSB) y límite de corriente del DRV8876 resueltos por análisis nodal |
| `harness` | Pines del mazo J104 ↔ J1 con redes distintas a cada lado |
| `keypad` | Dirección I²C del TCA9534, bus, mapa bit → tecla y LED |
| `uart-pair`, `unclaimed-net`, `power-domain` | TX con RX, redes del MCU que el firmware no usa, pull-ups en otro dominio |
| `drive` | Orden que no mueve su carga en el peor caso: activa, inactiva, con el MCU en reset y, si va enclavada, con `STM_NRST` bajo y el pin aún activo, con los rails al mínimo y al máximo |
| `drive-current` | Salida del MCU o de una puerta que entrega más corriente de la que garantiza su VOH/VOL |
| `drive-limit` | IF del opto, tensión de bobina o VDS por encima del máximo |
| `slow-edge` | Entrada lógica sin histéresis en una red RC más lenta que su Δt/Δv máximo |
| `back-feed` | Entrada de alimentación externa que llega al nodo de conmutación de un buck por bobinas o fusibles, sin cruzar otro rail |
| `tvs` | TVS que conduciría con el rail en su máximo (VWM) o que no empieza a conducir (VBR máx.) antes del máximo absoluto de lo que protege |
| `pin-voltage` | Pin de un MCU por encima de su máximo absoluto en algún estado, con los rails y VBUS al máximo |
| `input-level` | Entrada digital activa a cero que, con su contacto cerrado (50 Ω) o abierto, no pasa de VIL o VIH en las dos esquinas |

El modelo usa los pads físicos: cuando un símbolo no sigue su pinout de
referencia, el modelo se comporta como la placa que se fabricaría, no como el
dibujo. Representa el flujo de control y la red en continua por conmutación, no
transitorios, la red de 230 V más allá de quién tiene fase, ni la PWM más allá de
su nivel; no sustituye a ERC, DRC, ni a ensayos de integridad de señal, EMI o
aislamiento.

Las [pruebas de mutación](../tests/sim/test_board_model.py) parten de los
netlists con los símbolos corregidos, rompen una cosa cada vez y exigen que la
regla correspondiente la detecte.

## F1: placa virtual y firmware en host

```
python -m unittest discover -s tests/sim    # F0, F1 y escenarios del firmware
```

- [`circuit.py`](osc_sim/circuit.py): modelo DC por conmutación de las dos
  placas sacado de los netlists. Resistencias, salidas como fuentes de Thevenin,
  LED como caída directa, canales MOSFET como RDS(on), relé por la tensión de
  bobina y triacs por el opto que los dispara. Solo se fía de los puntos que
  garantiza el fabricante; entre ellos el dispositivo queda indefinido y todo lo
  que alimenta también. Cada punto se resuelve dos veces (indefinidos abiertos y
  cerrados) y solo es definido si ambas coinciden.
- [`drive.py`](osc_sim/drive.py): la regla `drive` y la tabla de márgenes del
  [informe](board-report.md). Las esquinas de los rails y las cargas de prueba
  están en el contrato (`rail_range`, `loads`, `drive` de cada orden).
- [`firmware.py`](osc_sim/firmware.py): compila `firmware/stm32` (controlador,
  BSP y bucle principal) con [`hal/hal_sim.c`](hal/hal_sim.c) como biblioteca y
  la carga con ctypes. Usa `$CC` (por defecto `cc`) y `$SDKROOT` si está
  definido; en macOS con las Command Line Tools rotas, el `clang` de Xcode.
- [`board.py`](osc_sim/board.py): pasos de 1 ms. Los pines que el firmware
  configura pasan a la red, U601 vigila WDI y gobierna `STM_NRST`, el STM32 se
  resetea y arranca según ese nivel, y los niveles, códigos ADC y flancos vuelven
  al firmware. Tras el reset los pines están en analógico y UCPD1 deja su Rd de
  5,1 kΩ en PB4/PB6 hasta que el BSP lo quita. U601 usa el extremo de cada rango
  que pone a prueba el caso: time-out de 0,9 s para el firmware sano, 2,5 s para
  el colgado, y 300 ms de reset al arrancar.
- [`plant.py`](osc_sim/plant.py): caldera y NTC, bomba y caudalímetro, grupo con
  sus micros, puerta, válvula y sensor de agua en los pines de los conectores.
  Los valores medidos llevan su fuente; los marcados *ASSUMED* (masa térmica,
  caudal, recorrido del grupo, salida de JP22) esperan a la caracterización.

Los [escenarios](../tests/sim/test_f1.py) comprueban el arranque en las dos
esquinas, que el firmware mantiene callado el watchdog, que un núcleo colgado se
resetea, que el interlock corta las órdenes de un núcleo desbocado en el mismo
paso en que U601 baja `STM_NRST`, que olvidar el *dead battery* de UCPD deja
`nFAULT` indefinido, y la caldera/NTC, el grupo/IPROPI y los flancos del
caudalímetro.
