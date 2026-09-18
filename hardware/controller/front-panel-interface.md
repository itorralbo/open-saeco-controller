# Interfaz propuesta controladora–frontal, Rev A.0

Estado: contrato de diseño nuevo; no es el pinout de JP21 Saeco.
Compatible con el [esquema preliminar del frontal](../front-panel/README.md).
Display seleccionado (ST7789 2,0") y presupuestos en el [subsistema display + UI](../../docs/display-ui.md).

## Distribución de funciones

STM32: sensores, interlocks, control y única autoridad sobre actuadores.
ESP32: USB/web, menús, display SPI y teclado I²C. Ambos siguen en la principal.
Frontal: botones, expansor de entradas y adaptador de pantalla reemplazable.
Así la definición del frontal puede avanzar mientras se caracterizan las cargas.

## J_UI en principal ↔ J1 en frontal

Numeración eléctrica de 16 contactos, arnés nuevo 1:1. Se selecciona un cabezal
IDC polarizado 2×8 de 2,54 mm en ambos extremos, candidato Megastar
ZX-IDC2.54-2-8PZZ / JLC C7501244. No es una vista del lado del cable y no autoriza
reutilizar el arnés Saeco existente.

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
la masa lógica propuesta; su nombre no demuestra separación de red. Su unión a
la principal depende del diseño de alimentación y aislamiento todavía pendiente.
J1/J2 están dentro del mismo dominio lógico; no hay aislamiento en el frontal.

## Reserva candidata ESP32-S3-WROOM-1-N8R8

Selección de trabajo del módulo, instanciada en el [núcleo inicial](core-design.md).
No hay BSP; USB ya está conectado en el esquema principal y queda por rutear y ensayar. No usar números de un DevKit.
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
| UART_TX hacia STM32 | 17 | 10 |
| UART_RX desde STM32 | 18 | 11 |
| USB D− / D+ | 19 / 20 | 13 / 14 |
| USB VBUS sense | 21 | 23 |

Esta asignación evita pines de arranque 0/3/45/46 y, para la variante con PSRAM
octal N8R8, 35/36/37. Quedan por cerrar el layout USB, alimentación final, depuración,
antena y enlace STM32. La tabla reserva recursos, no completa esos circuitos.

## Condiciones eléctricas pendientes de cierre

- Reservar protección de corriente y posible corte de `3V3_UI` en la principal;
  calcular el rail con consumo máximo e inrush del display elegido, caída del
  cable y consumo del resto de electrónica. No hay presupuesto de corriente cerrado.
- Pull-ups de SCL/SDA/INT en el frontal; no duplicarlas inadvertidamente.
  Al apagar el frontal, poner sus señales en alta impedancia y revisar caminos
  de backfeed. Fuente, corte y protección ESD todavía sin componente seleccionado.
- I²C: arrancar en banco a 100 kHz. Con 4,7 kΩ, el modelo RC
  `tr ≈ 0,8473 × R × C` da aproximadamente 1 µs a 250 pF. Medir capacitancia y
  flancos del arnés completo; no se declara una longitud máxima admisible.
- SPI: **reloj de partida 10 MHz** (decisión; ver
  [subsistema display + UI](../../docs/display-ui.md)) con resistencias serie candidatas de
  22–47 Ω cerca del ESP32, especialmente en reloj. Revisable al alza solo por medida
  de flancos con el arnés real; la frecuencia no garantiza por sí sola integridad de señal.
- Un frame 240 × 320 RGB565 (1,2288 Mbit) tarda ≈ 123 ms a 10 MHz (≈ 1,23 s a 1 MHz),
  sin contar comandos. LVGL repinta solo el área sucia, así que el full-frame es el
  peor caso, no un objetivo de interfaz fluida. Evaluar actualización parcial y
  velocidad final con el arnés real.
- Separar el arnés de UI de cableados de potencia en el diseño mecánico.
  Si el recorrido no permite SPI/I²C fiables, revisar la ubicación del ESP32
  o introducir un controlador local; no congelar conectores antes de medirlo.

## Continuación de la principal

| Bloque | Avance permitido ahora | Dato que falta para cerrarlo |
|---|---|---|
| ESP32 y frontal | Módulo, alimentación con corte, J104/J1 IDC y contrato eléctrico implementados | Longitud de arnés, EMC y dimensiones del frontal |
| STM32G431RBT6 | Primer núcleo LQFP64 con UART, reset y SWD | Asignación de I/O y acondicionamiento de sensores |
| Sensores | Definir requisitos de diagnóstico abierto/corto | Pinouts, niveles y curva NTC de la unidad |
| Potencia | Separar control lógico, drivers y corte independiente | Ratings de cargas, topología y protecciones |
| PCB principal | Registrar zonas y restricciones mecánicas | Cotas, taladros, posición y orientación de conectores |

No derivar fuentes de motor ni referencias de driver de cifras no verificadas
en conversaciones anteriores. El frontal nuevo elimina la dependencia del
protocolo del display original, pero no la caracterización de la máquina.
