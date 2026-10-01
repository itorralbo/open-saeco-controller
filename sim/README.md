# Simulador de la cafetera

Entorno para probar el firmware sin hardware, coherente con las dos PCBs: el
cableado del simulador no se escribe a mano, se genera a partir de los netlists
de KiCad, así que un error de diseño aparece como un fallo de simulación.

| Fase | Contenido | Estado |
|---|---|---|
| F0 | Modelo de las dos placas, contrato de firmware, comprobaciones y `board_pins.h` | Hecha |
| F1 | STM32 en host contra la placa virtual: HAL, modelos de componentes y planta | Pendiente |
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

El modelo usa los pads físicos: cuando un símbolo no sigue su pinout de
referencia, el modelo se comporta como la placa que se fabricaría, no como el
dibujo. Solo representa el flujo de control y la red resistiva en continua; no
sustituye a ERC, DRC, ni a ensayos de integridad de señal, EMI o aislamiento.

Las [pruebas de mutación](../tests/sim/test_board_model.py) parten de los
netlists con los símbolos corregidos, rompen una cosa cada vez y exigen que la
regla correspondiente la detecte.
