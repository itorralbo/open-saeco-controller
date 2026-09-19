# Subsistema display + UI — Rev A.0

Estado: contrato de diseño; **sin hardware validado**. Fija el stack de firmware y los
presupuestos del display del frontal nuevo. Números marcados **TBD** siguen sin evidencia.
Decisión de fondo registrada en [ADR-0001](adr/0001-front-panel-display-st7789.md).

Depende de:
[interfaz controladora–frontal](../hardware/controller/front-panel-interface.md) (pinout J_UI y
reserva de GPIO del ESP32) y [frontal Rev A.0](../hardware/front-panel/README.md) (teclado I²C,
adaptador de display). Este documento no sustituye a ninguno; los referencia.

## 1. Display seleccionado

- **Tipo**: TFT color IPS, controlador **ST7789V**, 240 × 320, interfaz **SPI 4 hilos** (sin MISO ni táctil).
- **Motivo de la elección**: encaja el contorno OEM medido y el contrato eléctrico existente
  (SPI + BL lógico, 3,3 V) sin ingeniería inversa. Ver alternativas descartadas en el ADR.
- **Envolvente disponible (medida del módulo OEM)**: **43,3 × 55 mm, 6 mm de fondo**, orientación apaisada.
- **Panel candidato**: 2,0" 240 × 320.
  - Área activa ≈ 30,6 × 40,8 mm (retrato) → **40,8 × 30,6 mm en apaisado**.
  - Contorno de vidrio ≈ 33,6 × 43,4 mm — **TBD: confirmar en el datasheet del MPN concreto** (varía por fabricante).
  - Espesor del panel ≈ 2,0–2,5 mm; deja margen para adaptador y conector dentro de los 6 mm.
- **Consecuencia de UX a cerrar**: la activa (40,8 mm de ancho) es **menor** que la ventana OEM.
  El recorte del bisel del frontal nuevo se diseña a la activa real; igualar el tamaño original
  exigiría panel a medida. **TBD: cota de la ventana visible del OEM** para decidir.
- **Pendiente**: selección de MPN con contorno, activa, espesor, conector (FPC vs cable) y
  código de compra; requisito de adaptador de display (orden de pines, driver de BL).

## 2. Contrato eléctrico (resumen; la fuente es front-panel-interface.md)

Señales sobre J_UI (16 contactos, arnés 1:1), todas lógica 3,3 V:

| Señal | Pin J_UI | GPIO ESP32-S3 (reserva) | Notas |
|---|---|---|---|
| LCD_SCLK | 3 | 12 | Reloj SPI |
| LCD_MOSI | 5 | 11 | Datos a display |
| LCD_CS_N | 7 | 10 | Selección activa baja, pull-up |
| LCD_DC | 8 | 9 | Datos/comando |
| LCD_RST_N | 9 | 8 | Reset, pull-up |
| LCD_BL_PWM | 10 | 7 | **Señal lógica** a driver de BL; pull-down al arranque |
| KEY_SCL | 11 | 5 | I²C teclado (TCA9534) |
| KEY_SDA | 12 | 4 | I²C teclado |
| KEY_INT_N | 13 | 6 | Interrupción teclado, activa baja |

- **Reloj SPI: 10 MHz** (decisión). Elegido por margen de integridad de señal sobre el arnés,
  no por límite del ST7789 (admite mucho más). Revisable al alza solo tras medir flancos con el
  arnés real. Reservar **R serie 22–47 Ω** cerca del ESP32, especialmente en SCLK.
- SPI modo 0 (CPOL=0, CPHA=0), MSB first. **TBD confirmar** contra el panel elegido.
- BL es lógica: **no** alimentar la retroiluminación desde el GPIO; el módulo/adaptador lleva su driver.

## 3. Presupuesto de rendimiento

- Frame completo 240 × 320 RGB565 = 240·320·16 = **1,2288 Mbit**.
  - @10 MHz ≈ **123 ms** por frame completo (solo píxeles, sin comandos).
- LVGL repinta **solo el área sucia**: una actualización típica de menú mueve una fracción de la
  pantalla → decenas de ms o menos. El full-frame a 123 ms es el peor caso (p. ej. cambio de pantalla),
  aceptable para una UI de cafetera.
- Objetivo inicial: transiciones de pantalla percibidas < 200 ms; animaciones limitadas o desactivadas
  si el presupuesto no llega. **No es un objetivo de vídeo fluido.**
- El límite es el enlace SPI sobre el cable, no la CPU del S3. Mantener el arnés de UI separado de
  cableados de potencia (ya recogido en el contrato de la interfaz).

## 4. Presupuesto de memoria (ESP32-S3-WROOM-1U-N8R8)

- Recursos: 512 KB SRAM interna + **8 MB PSRAM** + 8 MB flash. Holgado para esta UI.
- **Draw buffers LVGL**: dos buffers parciales de p. ej. 240 × 40 px × 2 B = 19,2 KB c/u (**≈38 KB**),
  en SRAM interna apta para DMA. Punto de partida; ajustar tamaño por medida.
- Framebuffer completo (150 KB) **opcional** en PSRAM si se adopta rendering full-refresh; no
  necesario para empezar.
- Flash: LVGL + fuentes + assets ≈ 150–400 KB según alcance (**TBD** al cerrar pantallas e iconografía).
- DMA en SPI obligatorio para no bloquear la CPU durante el volcado.

## 5. Stack de firmware

- **ESP-IDF** (versión objetivo **TBD**, fijar LTS al iniciar).
- **`esp_lcd`** con panel driver **`esp_lcd_panel_st7789`** (incluido en IDF) sobre bus SPI.
- **LVGL 9** como componente gestionado (`lvgl/lvgl`) + **`esp_lvgl_port`** para el pegado
  esp_lcd ↔ LVGL (flush, tearing, tick, lock).
- Entrada: **input device tipo keypad** de LVGL alimentado por el teclado I²C (§6).
- Todo por componentes gestionados (`idf_component.yml`); sin forks salvo necesidad justificada.

## 6. Modelo de entrada (teclado)

- Botones del frontal leídos por **TCA9534** (I²C, `0x20`): P0–P6 son las siete teclas y P7 el
  LED de standby (salida, activo a 0); INT drenador abierto. Secuencia: Output `0x01`=`0xFF`,
  Polarity `0x02`=`0x00`, Configuration `0x03`=`0x7F`; Input `0x00` bits 0–6. Mapa bit → tecla
  en el [layout del frontal](../hardware/front-panel/layout.md#teclas-led-y-registros-del-tca9534).
- El firmware expone las teclas a LVGL como **grupo con navegación por foco** (keypad indev):
  las pocas teclas físicas mueven foco y confirman, no hay puntero.
- Muestreo cada 5 ms con exigencia de 20 ms de estabilidad; INT adelanta lectura pero **se conserva
  el sondeo** para detectar fallos de bus. Antirrebote temporal en firmware.
- Tras arranque/reconexión: **esperar liberación de todas las teclas** antes de aceptar pulsación.
  Una tecla mantenida al reiniciar **no** se convierte en START.
- NACK, lectura caducada o fallo de bus **invalidan el teclado** (≠ "ninguna tecla"): el frontal no
  emite nuevas solicitudes START en ese estado.
- **Mapa físico observado (2026-09-18):** la PCB original tiene **siete pulsadores**: tres en cada
  extremo de la placa y PB8 (standby, con LED) abajo en el centro. Posiciones en el
  [registro mecánico del frontal](../hardware/front-panel/mechanical.md). El frontal nuevo
  usa siete canales y dedica el octavo al LED STBY bajo PB8, como el original.
  **TBD: función y etiqueta de cada tecla** en el frontal plástico; se cierran con la UX.

## 7. Árbol de pantallas (propuesta) y mapa a estados del STM32

El STM32 tiene la autoridad; el ESP32 **refleja** estado y **solicita** acciones. Pantallas propuestas:

- **STANDBY** — icono de reposo; una tecla despierta. (STM32: SAFE_IDLE / reposo)
- **SELF-TEST / HOMING** — arranque, no interactiva. (SELF_TEST, HOMING)
- **HOME / READY** — bebidas disponibles y acceso a menú. (READY, HEATING de fondo)
- **PREPARANDO** — fase y progreso de la bebida; STOP visible. (GRINDING, BREWING)
- **AJUSTES** — submenús: bebidas/dosis, agua/dureza, idioma, contadores, mantenimiento.
- **MANTENIMIENTO** — limpieza y descalcificación guiadas por pasos. (CLEANING)
- **AVISOS** — depósito, poso, puerta/cajón, etc. (avisos no bloqueantes)
- **FALLO** — código y estado; no auto-reanuda ciclos. (FAULT)

Reglas: reinicio/reconexión/actualización **no reanudan** ciclos automáticamente; el rearme exige
condiciones válidas y acción explícita. Estas pantallas son un contrato de UX, **no** una máquina
de estados implementada.

## 8. Acoplamiento con el protocolo ESP↔STM32

- Sobre el [protocolo v0](../firmware/common/protocol.md): el ESP solicita, el STM32 decide.
- La UI **consume `STATUS`** para pintar estado/fase y **emite `START_RECIPE`/`STOP`** desde las teclas,
  reflejando `ACK`/`ERROR` y latencia. START se rechaza en el núcleo actual: la UI debe tratar el
  rechazo como normal, no como error de comunicación.
- Enlace caído o STATUS caducado → pantalla de enlace perdido; **no** mostrar datos obsoletos como vivos.
- La política del ciclo en curso ante teclado inválido corresponde al STM32 (**TBD**).

## 9. Arranque, error y robustez

- BL bajo y CS alto durante init; aplicar reset y tiempos del panel antes de habilitar imagen.
- Sin reset externo del TCA9534: prever recuperación de I²C y reescritura de config tras fallo de bus.
- El corte de `3V3_UI` en la principal (TPS22918) permite reinicio limpio del frontal; **TBD** ensayar
  secuencia de apagado y prevención de backfeed por GPIO con display y arnés definitivos.
- Pantalla de FALLO legible sin depender de estados previos; watchdog de la tarea de UI.

## 10. Secuencia de bring-up (orden de trabajo)

1. Bus SPI + `esp_lcd_panel_st7789`: init, orientación apaisada, primer relleno de color. Verificar a 10 MHz.
2. Control de BL (encendido/apagado y, si aplica, PWM lógico) y tiempos de reset.
3. Integrar LVGL 9 + `esp_lvgl_port`: draw buffers, flush con DMA, tick, lock.
4. Keypad indev desde TCA9534: grupo, foco, antirrebote, política de liberación de teclas.
5. Pantalla HOME + una transición; medir tiempos reales de refresco sobre el arnés.
6. Enganche con `STATUS`/`START_RECIPE`; estados de enlace perdido y FALLO.

## 11. Pendientes (TBD) que bloquean el cierre

- MPN del panel: contorno, activa, espesor, conector y código de compra.
- Cota de la ventana visible del OEM (para el recorte del bisel y el tamaño percibido).
- Diseño del adaptador de display (orden de pines, driver de BL, ESD).
- Función y etiqueta de cada uno de los siete botones.
- Versión de ESP-IDF y de LVGL a fijar; parámetros SPI (modo, R serie) por medida.
- Longitud máxima del arnés y validación de integridad de señal a 10 MHz.

## 12. Verificación prevista

- Banco: patrón de color, prueba de rotación, latencia de full-frame y de repintado parcial medidas.
- Teclado: matriz de pulsaciones, rebotes, pérdida de INT, recuperación de bus.
- Integración: inyección de `STATUS` simulados y verificación de que la UI no emite START indebido.
- Regresión de arranque: tecla mantenida al reset **no** dispara ciclo.
