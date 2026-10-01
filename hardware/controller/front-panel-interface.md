# Interfaz propuesta controladora–frontal, Rev A.0

Estado: contrato de diseño nuevo; no es el pinout de JP21 Saeco.
Compatible con el [frontal Rev A](../front-panel/README.md).
Display seleccionado (ST7789 2,0") y presupuestos en el [subsistema display + UI](../../docs/display-ui.md).

## Distribución de funciones

STM32: sensores, interlocks, control y única autoridad sobre actuadores.
ESP32: USB/web, menús, display SPI y teclado I²C. Ambos siguen en la principal.
Frontal: botones, expansor de entradas y adaptador de pantalla reemplazable.
Así la definición del frontal puede avanzar mientras se caracterizan las cargas.

## J_UI en principal ↔ J1 en frontal

Numeración eléctrica de 16 contactos, cable plano 1:1. Los dos extremos llevan el
conector que el propietario identificó el 2026-10-01 en el enlace original con el
frontal: Würth WR-MM 690367181672 (hembra de placa compatible Micro-MaTch,
16 contactos a 1,27 mm al tresbolillo, 2,54 mm por fila, THT vertical, 1,5 A por
contacto; JLC C19103863, sin stock el 2026-10-01). La huella sigue el plano Würth
rev 002.000. La tabla es la numeración del fabricante, no una vista del lado del
cable. El cable original es plano, de 16 hilos y 1:1 (propietario, 2026-10-01).
El pestillo de su conector entra en un taladro de 1,5 mm junto al pin 1, que lo
retiene y solo deja enchufarlo en un sentido. Como las dos placas llevan la misma
huella, el pin 1 llega al pin 1. El pinout es nuevo, no el de Saeco.

| Pin | Red | Dirección desde principal | Función |
|---|---|---|---|
| 1 | 3V3_UI | Alimentación | Rail regulado para frontal y display |
| 2 | GND_UI | Retorno | Masa |
| 3 | LCD_SCLK | Salida | Reloj SPI |
| 4 | GND_UI | Retorno | Masa junto a reloj |
| 5 | LCD_MOSI | Salida | Datos a display |
| 6 | GND_UI | Retorno | Masa junto a datos |
| 7 | LCD_CS_N | Salida | Selección activa baja |
| 8 | LCD_DC | Salida | Datos/comando |
| 9 | LCD_RST_N | Salida | Reset del display |
| 10 | LCD_BL_PWM | Salida | Control lógico de retroiluminación |
| 11 | KEY_SCL | Drenador abierto | Reloj I²C |
| 12 | KEY_SDA | Bidireccional, drenador abierto | Datos I²C |
| 13 | KEY_INT_N | Entrada | Interrupción del teclado |
| 14 | GND_UI | Retorno | Masa |
| 15 | GND_UI | Retorno | Masa |
| 16 | NC | Sin conexión | Reserva, sin tensión asignada |

Todas las señales de esta interfaz se diseñan para lógica de 3,3 V. `GND_UI` es
la masa lógica de la principal, aislada de red por la fuente IRM-30-24; su nombre
no demuestra por sí solo esa separación, que queda por verificar en la revisión
de aislamiento.
J1/J2 están dentro del mismo dominio lógico; no hay aislamiento en el frontal.

## Pines del ESP32-S3-WROOM-1U-N8R8

Módulo del [esquema de la principal](core-design.md).
La variante 1U tiene el mismo pinout que la WROOM-1 y sustituye la antena impresa
por un conector U.FL para antena externa.
No hay BSP; USB está conectado y ruteado, pendiente de ensayo. No usar números de un DevKit.
Tabla cotejada con la sección de pines de la
[hoja de datos Espressif del módulo](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.html).

| Red | GPIO ESP32 | Pad del módulo |
|---|---|---|
| LCD_SCLK | 12 | 20 |
| LCD_MOSI | 11 | 19 |
| LCD_CS_N | 10 | 18 |
| LCD_DC | 9 | 17 |
| LCD_RST_N | 8 | 12 |
| LCD_BL_PWM | 7 | 7 |
| KEY_SCL | 5 | 5 |
| KEY_SDA | 4 | 4 |
| KEY_INT_N | 6 | 6 |
| UART_TX hacia STM32 | 42 | 35 |
| UART_RX desde STM32 | 2 | 38 |
| USB D− / D+ | 19 / 20 | 13 / 14 |
| USB VBUS sense | 15 | 8 |
| UART de depuración TX / RX (J103) | 43 / 44 | 37 / 36 |
| BOOT (J103) | 0 | 27 |

Salvo GPIO0, que solo sirve para forzar el arranque desde J103, la asignación
evita los pines de arranque 0/3/45/46 y, para la variante con PSRAM octal N8R8,
35/36/37. La UART pasó el 2026-09-23 de IO17/IO18 a IO42/IO2 y la detección de
VBUS de IO21 a IO15, para acortar el ruteo (ver
[layout.md](layout.md#esp32-y-frontal)). Quedan por ensayar el USB, la antena y el
enlace con el STM32.

## Condiciones eléctricas pendientes de cierre

- `3V3_UI` sale de U302 (TPS22918, 2 A, con rampa por C307 y descarga QOD).
  Falta calcular el rail con consumo máximo e inrush del display elegido, caída
  del cable y consumo del resto de electrónica. No hay presupuesto de corriente cerrado.
  `3V3_UI` va por un solo contacto (pin 1) y el WR-MM admite 1,5 A por contacto,
  menos que los 2 A de U302: el consumo del frontal debe quedar por debajo.
- Pull-ups de SCL/SDA/INT en el frontal; no duplicarlas inadvertidamente.
  Al apagar el frontal, poner sus señales en alta impedancia y revisar caminos
  de backfeed. La protección ESD del arnés sigue sin componente seleccionado.
- I²C: arrancar en banco a 100 kHz. Con 4,7 kΩ, el modelo RC
  `tr ≈ 0,8473 × R × C` da aproximadamente 1 µs a 250 pF. Medir capacitancia y
  flancos del arnés completo; no se declara una longitud máxima admisible.
- SPI: **reloj de partida 10 MHz** (decisión; ver
  [subsistema display + UI](../../docs/display-ui.md)). R213–R218, de 33 Ω, van en
  serie con las seis señales del display, en una fila junto a J104, a la entrada
  del cable. Revisable al alza solo por medida de flancos con el arnés real; la
  frecuencia no garantiza por sí sola integridad de señal.
- Un frame 240 × 320 RGB565 (1,2288 Mbit) tarda ≈ 123 ms a 10 MHz (≈ 1,23 s a 1 MHz),
  sin contar comandos. LVGL repinta solo el área sucia, así que el full-frame es el
  peor caso, no un objetivo de interfaz fluida. Evaluar actualización parcial y
  velocidad final con el arnés real.
- Separar el arnés de UI de cableados de potencia en el diseño mecánico.
  Si el recorrido no permite SPI/I²C fiables, revisar la ubicación del ESP32
  o introducir un controlador local; no congelar conectores antes de medirlo.

## Continuación de la principal

| Bloque | Hecho | Lo que falta para cerrarlo |
|---|---|---|
| ESP32 y frontal | Módulo, alimentación con corte, J104/J1 WR-MM y contrato eléctrico, ruteados | Longitud de arnés, EMC y MPN del display |
| STM32G431RBT6 | Todas las E/S asignadas y ruteadas | BSP y ensayo |
| Sensores | Acondicionamiento con diagnóstico de abierto/corto | Salida de JP22, NO/NC de JP16 y conectores de JP14/JP16/JP22 |
| Potencia | Etapas de 24 V y de red con corte general e interlock | Medidas de las cargas, fusibles, MOV, filtro EMI y ensayos |
| PCB principal | Colocación y ruteo completos, DRC limpio | Comprobación 1:1 y revisión de aislamiento |

No derivar fuentes de motor ni referencias de driver de cifras no verificadas
en conversaciones anteriores. El frontal nuevo elimina la dependencia del
protocolo del display original, pero no la caracterización de la máquina.
