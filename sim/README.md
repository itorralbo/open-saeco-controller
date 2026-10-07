# Simulador de la cafetera

Entorno para probar el firmware sin hardware, coherente con las dos PCBs: el
cableado del simulador no se escribe a mano, se genera a partir de los netlists
de KiCad, así que un error de diseño aparece como un fallo de simulación.

| Fase | Contenido | Estado |
|---|---|---|
| F0 | Modelo de las dos placas, contrato de firmware, comprobaciones y `board_pins.h` | Hecha |
| F1 | STM32 en host contra la placa virtual: HAL, modelos de componentes y planta | Hecha; planta con valores supuestos |
| F2 | ESP32 en host: ST7789 y TCA9534 virtuales, protocolo v0 | Hecha; LVGL queda para el puerto ESP-IDF |
| F3 | Panel web local: frontal, pantalla, gráficas, inyección de fallos, VCD | Hecha |
| F4 | Menús y puesta a punto: pruebas de cargas y medidas, cafetera visual en el panel | Hecha; tiempos y corrientes de la planta supuestos |
| F5 | Recetas y máquina de estados completa | Pendiente |

## Entorno (macOS, Windows y Linux)

Hace falta Python 3.10 o posterior (CI usa 3.12). El código del simulador solo
usa la biblioteca estándar; lo único externo es un compilador de C para los dos
firmwares, y [`requirements.txt`](requirements.txt) lo trae con pip (`zig cc`,
paquete `ziglang`): no hacen falta Xcode, MinGW ni Visual Studio.

macOS / Linux:
```
python3 sim/setup_env.py
source .venv/bin/activate
```

Windows (PowerShell):
```
py sim\setup_env.py
.venv\Scripts\Activate.ps1
```

Si PowerShell no deja ejecutar `Activate.ps1`, basta con llamar a
`.venv\Scripts\python` en lugar de `python`.

[`setup_env.py`](setup_env.py) crea `.venv` en la raíz del repositorio, instala
los requisitos, copia [`.env.example`](.env.example) a `sim/.env` si no existe
y compila los dos firmwares para comprobar la cadena. Con el entorno activado,
los comandos de abajo funcionan igual en los tres sistemas.

`sim/.env` (ignorado por git) guarda lo propio de cada máquina, por ejemplo
otro compilador (`CC`) o el SDK de macOS (`SDKROOT`) para un compilador del
sistema; las variables ya definidas en la terminal mandan. Sin `CC`, el
simulador usa `zig cc` si está instalado y si no `cc`, `gcc` o `clang`. CI
pasa los escenarios en Windows y macOS con este entorno, y en Linux con el
`cc` del sistema.

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
| `reverse-polarity` | Entrada de banco cableada a mano (`external_supplies.unkeyed`) que, con el cable invertido, llega por fusibles o bobinas a algo distinto de un diodo serie, un TVS a masa, resistencias, condensadores no polarizados, una bobina de relé o conectores |
| `probe-header` | Cabecera de medida (`probe_headers`) con dos tensiones distintas en pines contiguos o un pin de raíl sin resistencia serie de al menos `min_ohms` |
| `tvs` | TVS que conduciría con el rail en su máximo (VWM) o que no empieza a conducir (VBR máx.) antes del máximo absoluto de lo que protege |
| `resistor-power` | Resistencia que disipa más de su potencia nominal (catálogo o tamaño de huella) en el peor estado; aviso por encima del 60 % |
| `wdi-reset` | Supervisor que enclava RESET ante un pulso en WDI (TPS382x sin A) cuyo WDI cambia, con RESET activo, según PB4 esté en alto, en bajo o liberado |
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

## F2: interfaz, frontal y protocolo

- [`firmware.py`](osc_sim/firmware.py) compila también el núcleo del ESP32
  (`firmware/esp32/core`) con [`hal/hal_esp_sim.c`](hal/hal_esp_sim.c). Sus
  pines entran en el circuito como los del STM32; el I²C y el SPI se resuelven
  al momento en Python.
- [`front.py`](osc_sim/front.py): TCA9534 y ST7789V al otro lado del mazo. Solo
  responden con `3V3_UI` presente; el TCA9534 lee cada tecla como la tensión en
  su pin (pulsador, pull-up y serie del netlist), su INT es una bajada en drenador
  abierto sobre el circuito, y la pantalla descodifica CASET/RASET/RAMWR sobre un
  framebuffer de 320 × 240.
- [`board.py`](osc_sim/board.py) lleva los bytes de la UART entre los dos
  firmwares a 115200 baudios, solo con los dos pines configurados y la línea en
  reposo alto en el receptor, y registra `backfeed` si el ESP32 deja en alto una
  línea del frontal con `3V3_UI` apagado.

Los [escenarios](../tests/sim/test_f2.py): arranque y enlace en las dos
esquinas, STATUS con los rails reales, núcleo FAULT si el ESP32 se cuelga,
pantalla de enlace perdido y recuperación si se cuelga el STM32, START rechazado
como respuesta normal, tecla mantenida al arrancar, rebotes, puerta abierta y
CLEAR_FAULT, standby con el LED, teclado colgado recuperado con un ciclo de
`3V3_UI` sin backfeed, y que el detector de backfeed salta con una línea en alto.

## F3: panel web local

```
python tools/sim_panel.py              # http://127.0.0.1:8765/
python tools/sim_panel.py --speed 5 --corner min
```

[`panel.py`](osc_sim/panel.py) ejecuta los dos firmwares en la placa virtual en
tiempo real (o más rápido) y sirve [`panel/index.html`](panel/index.html), sin
dependencias externas y solo en 127.0.0.1:

- Frontal con las siete teclas en su sitio (mantener pulsado = pulsada), el LED
  STBY y la pantalla tal como la pinta el ST7789V virtual.
- Estado del STM32 y del ESP32, enlace, peticiones y respuestas, `3V3_UI`,
  STATUS, cargas, planta y registro de eventos (watchdog, resets, backfeed).
- Gráficas de caldera, rails y grupo.
- Inyección: puerta, grupo, NTC abierto, nFAULT del DRV8876, STM32, ESP32 o
  teclado colgados, ruido en la UART, rails en sus esquinas, nivel del depósito,
  café en la tolva y sensor de agua (forzado o según el depósito);
  pausa, paso de 100 ms, reinicio y velocidad.
- [VCD](osc_sim/vcd.py) de las señales digitales (órdenes del STM32,
  `STM_NRST`, WDI, enlaces, cargas, teclas, estado del núcleo y pantalla), para
  GTKWave, PulseView o Surfer.

API: `GET /api/state`, `/api/history`, `/api/frame` (RGB565 de 320 × 240),
`/api/vcd`; `POST /api/cmd` con `{"cmd": ...}`. Los
[escenarios](../tests/sim/test_f3.py) la recorren en un puerto efímero.

## F4: menús y puesta a punto

- El ESP32 pinta menús de texto ([`ui.c`](../firmware/esp32/core/ui.c)) y el
  STM32 ejecuta las pruebas de [`service.c`](../firmware/stm32/src/service.c)
  ([protocolo](../firmware/common/protocol.md#pruebas-de-puesta-a-punto)).
- La [planta](osc_sim/plant.py) añade depósito (la bomba se queda sin caudal
  vacío y el sensor JP22 sigue el nivel), tolva y molinillo, el estado de cada
  carga y un arranque del motor con constante de tiempo, que da el pico de
  arranque que mide la prueba del grupo.
- El panel dibuja la cafetera: depósito, bomba, caudalímetro, caldera con el
  calentador y el NTC, válvula, tolva y molinillo, grupo con su posición,
  sentido y corriente, puerta, K701 y los tres triacs. Junto a cada carga, dos
  pilotos: la orden del pin del STM32 y la carga realmente alimentada según el
  netlist; una orden sin carga sale discontinua y una carga sin orden, en rojo.
  El informe de la prueba en curso aparece con sus unidades, y el texto de la
  pantalla también como texto.

Qué mide cada prueba y qué no: la placa mide los rails, la corriente del grupo
(IPROPI), la del molinillo (U704), el NTC, el caudalímetro y los finales de
carrera; las corrientes del calentador, la bomba y la válvula necesitan una
pinza en la sesión de [caracterización](../docs/HD8911/characterization-plan.md),
y las pruebas solo fijan el tiempo y la ventana.

Corriente del molinillo (2026-10-06): U704 entra en el modelo de placa como
dispositivo `hall_current` (su entrada es un conductor de 0,7 mΩ en la línea +
de JP8, su salida VS/2 + 100 mV/A) y la comprobación analógica `hall` exige que
JP8 esté en serie con él y que el rango quepa en el ADC. La planta da la
corriente rectificada de 100 Hz del motor: arranque como rotor bloqueado,
marcha con grano, en vacío y bloqueo (valores supuestos), y una cámara que
recibe el molido y que el grupo vacía al volver a reposo; la corriente al
prensar crece con los gramos. El panel la dibuja junto al molinillo, con dos
fallos nuevos: muelas atascadas y conducto tapado.

Los [escenarios](../tests/sim/test_f4.py) recorren los menús y cada prueba
contra la planta: entradas, ciclo del grupo con I0 en 100-300 mA, válvula,
relé y molinillo sin tocar otras cargas, bomba con calibración del
caudalímetro, bomba sin agua (sin caudal), calentador hasta 90 °C con la
sobreoscilación; molinillo con su corriente, tolva que se vacía a mitad,
sin grano desde el principio y muelas bloqueadas; dosis prensada y conducto
tapado; y que se rechazan con la puerta abierta y se abortan con STOP, con
volver, al abrir la puerta y si se cuelga el ESP32, con todas las cargas a
cero.
