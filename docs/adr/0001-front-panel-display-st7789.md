# ADR-0001: Frontal nuevo con display ST7789 2,0"; descartada la reutilización de la PCB OEM

**Estado:** Aceptada
**Fecha:** 2026-09-18
**Deciders:** Propietario del proyecto (Ignacio)

## Contexto

El frontal OEM de la Saeco Incanto (placa `GIGI KYB_1.9.30.286.00_V03`) integra los pulsadores,
un LED de standby y el display gráfico monocromo `10107-LED-C-A173`. Análisis de las fotos de la
placa (una sola cara, todo visible):

- **U1 = 74HCT166**: registro de desplazamiento parallel-in/serial-out. Los botones se leen por
  *scan* serie, no por I²C ni matriz.
- **No hay MCU ni controlador de display discreto**: el display es **COG** (controlador en el vidrio)
  y se pilota **directamente desde la placa principal** a través del flex (JP2) y el mazo (JP3, 2×8).
- Config por straps `OTC/AMF/CMF`; drivers de LED/backlight con transistores y zeners.
- **Sin datasheet público** del módulo `10107-LED-C-A173`: controlador, bus, niveles, VLCD y el
  pinout de JP3 son desconocidos y solo se obtendrían por ingeniería inversa en banco.

El proyecto ya había decidido (2026-09-16) un **frontal nuevo** que reproduce la disposición de
botones, con teclado por **TCA9534 (I²C)** y display **SPI 3,3 V** reemplazable
([front-panel README](../../hardware/front-panel/README.md),
[interfaz](../../hardware/controller/front-panel-interface.md)). Envolvente medida del hueco del
display: **43,3 × 55 mm, 6 mm de fondo**, apaisado.

Fuerzas en juego: evitar depender de una pantalla sin documentar; mantener el dominio lógico 3,3 V del
contrato; encajar en la envolvente mecánica; minimizar coste de firmware; conservar la geometría de
botones. Restricción de integridad de señal: el display cuelga de la principal por un arnés, lo que
acota la frecuencia SPI utilizable.

## Decisión

1. **No reutilizar** la PCB frontal OEM como electrónica del proyecto. Se conserva **solo como patrón
   dimensional** (centros de pulsador, contorno, taladros, ventana del display).
2. Diseñar el **frontal nuevo** ya acordado (teclado I²C + adaptador de display SPI).
3. Adoptar un **TFT color 2,0" 240 × 320, ST7789V, SPI 4 hilos, 3,3 V** como display de referencia.
4. Fijar el **reloj SPI en 10 MHz** como punto de partida, por margen de integridad de señal sobre
   el arnés (revisable al alza solo tras medida).

Detalle de firmware y presupuestos en [Subsistema display + UI](../display-ui.md).

## Opciones consideradas

### Opción A — Reutilizar la PCB OEM y su display

| Dimensión | Valoración |
|---|---|
| Complejidad | Alta (ingeniería inversa del bus COG y del pinout JP3) |
| Coste | Bajo en HW, **alto e incierto** en caracterización |
| Riesgo | Alto: display sin datasheet; posible dominio 5 V (repoblar U1 o adaptar nivel) |
| Encaje contrato | Malo: 74HCT166 y bus COG en vez de I²C + SPI TFT |
| Familiaridad | Baja: driver de display propietario a deducir |

**Pros:** encaje mecánico y visual exactos; cero rediseño de frontal; reaprovecha el registro de botones.
**Contras:** atado a una pantalla no documentada; RE de riesgo abierto; choca con el contrato 3,3 V/I²C/SPI;
mono en vez de color.

### Opción B — Frontal nuevo + TFT 2,4" ILI9341 240 × 320 SPI

| Dimensión | Valoración |
|---|---|
| Complejidad | Baja (driver estándar) |
| Coste | Bajo |
| Encaje contrato | Bueno (SPI 3,3 V) |
| Encaje mecánico | **Malo** |

**Pros:** activa mayor (36,7 × 49,0 mm), eléctricamente ideal.
**Contras:** contorno de vidrio ≈ 42,7 × **60,3** mm → excede los **55 mm** de la envolvente. Descartada por mecánica.

### Opción C — Frontal nuevo + TFT 2,0" ST7789 240 × 320 SPI (elegida)

| Dimensión | Valoración |
|---|---|
| Complejidad | Baja (driver `esp_lcd` de serie + LVGL) |
| Coste | Bajo (panel ubicuo) |
| Encaje contrato | Bueno (SPI 4 hilos, 3,3 V, sin MISO/touch) |
| Encaje mecánico | Bueno (contorno ≈ 33,6 × 43,4 mm en 43,3 × 55; fondo ≈ 2–2,5 mm en 6) |

**Pros:** cabe con margen; color; stack de firmware trivial; coherente con el contrato.
**Contras:** activa (40,8 × 30,6 mm) **menor** que la ventana OEM → recorte de bisel a la activa real;
el aspecto exacto del contorno depende del MPN (**a confirmar en datasheet**).

### Opción D — Frontal nuevo + display monocromo transflectivo (ST7565/UC1701), SPI

| Dimensión | Valoración |
|---|---|
| Complejidad | Baja–media |
| Coste | Bajo |
| Encaje contrato | Bueno (SPI 3,3 V) |
| Encaje mecánico | Verosímil (contorno a confirmar por MPN) |

**Pros:** legible a plena luz, consumo bajo, estética próxima al original.
**Contras:** monocromo y baja resolución; UI de menús/iconografía más limitada; sourcing de un contorno
exacto menos inmediato.

## Análisis de trade-offs

El único valor real de la Opción A era conservar *ese* display exacto; al aceptar una pantalla nueva,
ese valor desaparece y solo quedan sus costes (RE del bus COG, dominio de tensión, pinout JP3). La B es
la mejor eléctricamente pero **no cabe** (60,3 > 55 mm). Entre C y D, ambas cumplen el contrato y la
mecánica; la elección se reduce a **UI color con menús ricos (C)** frente a **legibilidad a la luz y
consumo (D)**. El proyecto prioriza una UI moderna con menús, y la C tiene el stack de firmware más
trillado (LVGL + `esp_lcd`). El coste de programación de la UI no depende del ST7789 (driver de serie),
sino de la UX y de que el SPI llegue limpio por el arnés — mitigado bajando el reloj a 10 MHz.

## Consecuencias

**Más fácil:**
- Firmware de display: driver estándar en ESP-IDF; LVGL 9 para menús y navegación por foco.
- Cumplimiento del contrato eléctrico existente sin ingeniería inversa.
- Avanzar el frontal en paralelo a la caracterización de la máquina.

**Más difícil / a vigilar:**
- Integridad de señal del SPI sobre el arnés: 10 MHz de partida, R serie 22–47 Ω, medida obligada.
- El tamaño percibido del display baja respecto al original; el bisel del frontal se rediseña a la activa.
- Sourcing: cerrar MPN con contorno/activa/espesor/conector reales.

**A revisar más adelante:**
- Subir el reloj SPI si la medida de flancos lo permite.
- Reconsiderar un panel a medida si igualar el tamaño visual original resulta prioritario.
- La PCB OEM permanece como referencia mecánica hasta capturar cotas en `mechanical.md`.

## Acciones

1. [ ] Capturar cotas del OEM (ventana visible, centros de pulsador, contorno, taladros) → `mechanical.md`.
2. [ ] Cerrar MPN del panel 2,0" ST7789 (contorno, activa, espesor, conector, código de compra).
3. [ ] Definir el adaptador de display (orden de pines, driver de BL, ESD).
4. [ ] Fijar versión de ESP-IDF y de LVGL; parámetros SPI (modo, R serie) por medir.
5. [ ] Esqueleto `esp_lcd` + LVGL con pantalla de prueba a 10 MHz (bring-up §10 del design doc).
