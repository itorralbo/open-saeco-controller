# Frontal Rev A.0 — esquema preliminar

Decisión del propietario, 2026-09-16: reproducir la PCB frontal para conservar
la disposición de botones y montar una pantalla nueva compatible con el hueco.
Se conserva como objetivo la geometría original. El 2026-09-18 se recuperaron por
fotogrametría contorno, taladros y centros de los siete pulsadores (184 × 54,3 mm);
están aceptadas como línea base del layout y aplicadas a la PCB de trabajo. Ver
[registro mecánico](mechanical.md).

## Entregables de esta iteración

- [Esquema KiCad](kicad/front-panel-reva.kicad_sch), con símbolos embebidos.
- [Proyecto KiCad](kicad/front-panel-reva.kicad_pro) y
  [PCB de trabajo](kicad/front-panel-reva.kicad_pcb), con contorno, cuatro taladros
  fresados y 35 huellas sin rutear en zona de staging.
- [Vista nativa de KiCad](validation/front-panel-reva.svg) y
  [validación y límites](../kicad-workflow.md).
- [Vista SVG del circuito](preview/front-panel.svg), generada como ayuda de revisión.
- [BOM candidata](bom-draft.csv) y [conexiones previstas](design-nets.json).
- [Contrato con la principal](../controller/front-panel-interface.md).
- [Registro mecánico fotogramétrico](mechanical.md), [datos](mechanical-source.json)
  y [plano 1:1 imprimible](validation/mechanical-1to1.svg).
- [Selección de componentes y montaje JLCPCB](../assembly/README.md): 35 posiciones
  con MPN/código y stock observado; nueve posiciones mecánicas aún pendientes.

El circuito contiene alimentación externa de 3,3 V, un TCA9534PWR, ocho canales
de pulsadores filtrados y una salida a adaptador de display SPI. Ocho es capacidad
de diseño; la PCB original tiene **siete pulsadores** (PB1–PB8, falta uno).
No hay PCB enrutada; el contorno procede del registro mecánico. El ERC nativo pasa; el DRC no tiene infracciones, pero quedan 70 conexiones
sin rutear y nueve huellas pendientes.
No está listo para fabricar.

## Circuito propuesto

El ESP32 permanece en la controladora principal. Lee botones por I²C y escribe
la pantalla por SPI. El STM32 recibe solicitudes a través del protocolo del
proyecto y conserva la autoridad sobre las cargas.

U1 es un **TCA9534PWR, TSSOP-16**. A0/A1/A2 van a masa, dirección de siete bits
`0x20`. Sus ocho puertos arrancan como entradas; INT es una salida activa a nivel
bajo de drenador abierto. Ver pinout y registros en la
[hoja de datos TI SCPS197D](https://www.ti.com/lit/ds/symlink/tca9534.pdf),
§5, §8.5 y §8.6. El esquema y la BOM se refieren al TCA9534, no al TCA9534A.

Cada canal tiene 10 kΩ a 3,3 V, 100 nF a masa y un pulsador normalmente abierto
a masa a través de 1 kΩ. La resistencia serie limita la corriente si un error
configura el puerto como salida alta. Estimación nominal: 0,30 V pulsado,
0,30 mA por pulsador y constante de subida de 1 ms. El RC reduce ruido;
el antirrebote temporal sigue siendo necesario.

R1/R2 = 4,7 kΩ son las únicas pull-ups I²C previstas. R3 = 10 kΩ polariza INT.
C1 = 100 nF y C2 = 1 µF deben quedar junto a U1; C3 = 10 µF, cerca de J2.
Las huellas 0603 tienen referencias de compra candidatas en la BOM; falta comprobar
capacitancia efectiva, temperatura, corriente y espacio. Se usan X7R para 100 nF
y X5R para 1 µF/10 µF según el catálogo de montaje consultado. Los pulsadores no tienen huella
asignada: altura y mecánica del actuador son determinantes.

J2 lleva alimentación, masa, MOSI, reloj, CS, DC, RESET y BL. CS y RESET
tienen pull-up; BL tiene pull-down para solicitar retroiluminación apagada al
arranque. **BL es una señal lógica**, prevista para un módulo con driver de LED.
No alimentar directamente una retroiluminación desde ese GPIO. El adaptador
deberá corregir orden de pines y añadir driver si lo necesita la pantalla elegida.
No se ha supuesto compatibilidad física de J2 con ningún módulo comercial.

J1 es un cabezal IDC polarizado 2×8 de 2,54 mm, idéntico a J104 de la principal.
El arnés será plano y 1:1; esta elección evita invertir el cable y admite montaje
automatizado THT en JLCPCB. Su posición definitiva depende del contorno del frontal.

## Pantalla reemplazable

> Decisión registrada (2026-09-18): se adopta un **TFT ST7789 2,0"** (240×320, SPI 4 hilos, 3,3 V) sobre frontal nuevo; se descarta reutilizar la PCB OEM. Ver [ADR-0001](../../docs/adr/0001-front-panel-display-st7789.md) y el [subsistema display + UI](../../docs/display-ui.md) (stack LVGL 9 + esp_lcd, SPI 10 MHz, presupuestos y árbol de pantallas). La tabla siguiente se conserva como registro de evaluación de hueco.

La compatibilidad se define por ventana visible, contorno total, altura,
orientación, lógica de 3,3 V, consumo y protocolo. La diagonal sola no basta.
La PCB de botones y el adaptador del display serán diseños independientes,
para cambiar de pantalla sin recolocar los pulsadores.

Referencias para comparar dimensiones, **sin selección ni compra todavía**:

| Módulo candidato | Controlador / resolución | Área visible (mm) | PCB del módulo (mm) |
|---|---|---|---|
| Waveshare 2 inch LCD Module | ST7789VW / 240 × 320 | 30,60 × 40,80 | 58,0 × 35,0 |
| Waveshare 2.4 inch LCD Module | ILI9341 / 240 × 320 | 36,72 × 48,96 | 70,50 × 43,30 |

Fuentes del fabricante consultadas el 2026-09-16:
[módulo 2 pulgadas](https://www.waveshare.com/product/displays/lcd-oled/2inch-lcd-module.htm)
y [módulo 2,4 pulgadas](https://www.waveshare.com/product/2.4inch-lcd-module.htm).
Para el segundo, el fabricante vincula el nivel lógico a la alimentación:
se evaluará alimentado a 3,3 V, no a 5 V.

Estos módulos sirven para evaluar el hueco y prototipar. El diseño final puede
necesitar un panel sin carrier comercial. J2 no incorpora MISO ni táctil:
un display que necesite lectura, touch o interfaz RGB/paralela requiere revisar
el adaptador y las señales disponibles, no solo cambiar el controlador software.

## Comportamiento de firmware previsto

1. Mantener BL bajo y CS alto durante la inicialización. Aplicar el reset y los
   tiempos del display finalmente seleccionado antes de habilitar la imagen.
2. Configurar U1: Configuration (`0x03`) = `0xFF`, Polarity (`0x02`) = `0x00`;
   leer Input (`0x00`). No usar Output (`0x01`) para controlar pulsadores.
3. Leer cada 5 ms como punto de partida y exigir 20 ms de estabilidad.
   INT permite adelantar una lectura; conservar el sondeo para detectar fallos.
   Son objetivos iniciales de firmware, aún no implementados ni ensayados.
4. Tras arranque/reconexión, esperar liberación de todos los botones antes de
   aceptar una pulsación. No convertir una tecla mantenida en START al reiniciar.
5. NACK, lectura caducada o fallo del bus invalidan el teclado: no equivalen a
   «ningún botón pulsado». El frontal no podrá generar nuevas solicitudes START.
   La política del ciclo en curso corresponde al STM32 y queda por definir.

U1 no dispone de reset externo: recuperar I²C y reescribir configuración puede
no bastar tras ciertos fallos de alimentación. La principal incorpora un corte
TPS22918 para `3V3_UI`; quedan por ensayar la secuencia de apagado y la prevención
de alimentación parásita por GPIO con el display y el arnés definitivos.

## Comprobación y edición

`python3 tools/generate_front_panel.py` regenera esquema, SVG, BOM y conexiones.
El generador es la fuente inicial: no ejecutarlo sobre ediciones manuales de KiCad
sin incorporarlas primero. La vista SVG es una representación auxiliar, no una
exportación de KiCad ni evidencia de que su parser acepte el archivo.

`python3 tools/check_front_panel.py` comprueba las conexiones del archivo de
esquema contra requisitos del circuito. `python3 tools/validate_kicad.py` ejecuta
ERC y coteja la netlist nativa de KiCad contra los 44 componentes y 122 pines.
`python3 tools/render_front_panel_mechanics.py` regenera el plano 1:1 y
`python3 tools/apply_front_panel_mechanics.py` aplica contorno, taladros y
referencias a la PCB desde [mechanical-source.json](mechanical-source.json).
Falta elegir J2 y pulsadores, cerrar las comprobaciones de calibre, colocar y rutear.
