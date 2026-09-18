# Principal Rev A.0 — núcleo lógico y alimentación de baja tensión

Existe una hoja eléctrica parcial con 68 componentes:
[esquema KiCad](kicad/controller-core-reva.kicad_sch),
[vista SVG auxiliar](preview/core.svg) y [BOM](bom-draft.csv).
Es una parte de la futura principal; no es una placa de sustitución terminada.
Ya dispone de [proyecto y PCB de trabajo](../kicad-workflow.md), con 68 huellas,
contorno y tres taladros. ERC nativo superado; la geometría actual no tiene
infracciones DRC, pero quedan 156 conexiones sin rutear.

## Alcance implementado en el borrador

- U101: STM32G431RBT6, LQFP64; alimentación, desacoplo, NRST, BOOT0 y SWD.
- U201: ESP32-S3-WROOM-1-N8R8; alimentación, EN con RC, BOOT y UART de programación.
- UART entre MCU: STM PA9/TX → ESP GPIO18/RX; ESP GPIO17/TX → STM PA10/RX.
- Conexión J104 al frontal, con el mismo pinout eléctrico que J1 del frontal.
- Resistencias serie candidatas de 33 Ω en las dos salidas UART y seis señales
  del display, para colocar cerca de sus respectivos emisores.
- Entrada de 12 V DC aislada, protección de entrada, buck de 3,3 V y corte
  controlado del rail del frontal.
- Divisor y filtro del NTC JP13 hacia PA0/ADC1_IN1, con diagnóstico de abierto/corto.
- Alimentación a 12 V y entrada open collector del caudalímetro JP5 hacia
  PA1/TIM2_CH2; el orden del arnés se resolverá con un adaptador.
- Entradas activas a cero para JP14 y los micros de presencia/trabajo de JP16,
  con pull-up, resistencia serie y filtro RC.
- J105–J109 usan huellas candidatas JST XH/PH cotejadas con fotos y catálogo
  LCSC. JP5, JP22 y las dos vías de motor de JP16 quedan NC hasta cerrar pinouts
  y seleccionar el puente H.

Los GPIO restantes llevan NC en esta hoja parcial. Significa que no están
conectados **en el circuito actual**; se cambiarán al incorporar I/O. No equivale
a una asignación del arnés Saeco. No hay salidas hacia cargas en esta hoja.

## Alimentación y arranque

J101 usa un JST XH lateral de dos contactos: `12V_ISO_RAW` y `GND_UI`. Debe
recibir 12 V DC de una fuente AC/DC aislada y certificada; no admite conexión a
red. F301 (1 A) protege la rama, D301 (SS34) bloquea polaridad inversa y D302
(SMAJ18A) limita transitorios antes del regulador.

La identificación posterior de cargas confirma que el motor del grupo y la
electroválvula necesitan 24 V DC. Por tanto, esta entrada de 12 V solo resuelve el
nucleo lógico actual: antes de congelar Rev A debe decidirse entre añadir un rail
aislado de 24 V separado o migrar J101 a 24 V. La segunda opción obliga a revisar
TVS, fusible, tensión de C301, conector y comportamiento del AP63203; no se puede
aplicar 24 V al circuito dibujado.

U301 es un AP63203WU-7 síncrono de salida fija a 3,3 V/2 A. El circuito implementa
la tabla 2 de su hoja de datos: L301=3,9 µH, C301=10 µF/25 V, C304+C305=2×22 µF/10 V
y C303=100 nF entre BST y SW. C302 y C306 añaden desacoplo de alta frecuencia.
`3V3_CORE` alimenta ambos procesadores.

U302 (TPS22918DBVR) genera `3V3_UI` desde `3V3_CORE`. PB0 del STM32 controla
`UI_PWR_EN`; R301=100 kΩ lo mantiene activo durante reset. C307=1 nF controla la
rampa y QOD queda unido a VOUT para descargar el frontal al apagarlo. Esta rama
permite cortar el frontal y reduce su corriente de arranque. La rampa, descarga y
posible backfeed deben medirse con el display definitivo. `GND_UI` es la masa
lógica común; el aislamiento está en la fuente anterior a J101.

VDDA y VREF+ del STM32 quedan conectados a 3V3_CORE y desacoplados localmente.
VREFBUF interno debe permanecer deshabilitado mientras VREF+ se alimenta así.
Para adquisición de precisión queda pendiente evaluar filtrado y referencia,
junto con la red de sensores. VBAT comparte 3V3_CORE; no hay batería.

Desacoplo inicial STM32: 100 nF por VDD, 4,7 µF común, 10 nF + 1 µF en VDDA y
100 nF + 1 µF en VREF+. EN del ESP usa 10 kΩ + 1 µF; se debe verificar su rampa
con la fuente real. Estas son elecciones para revisión, no un ensayo de arranque.
Fuentes: [ST DS12589, figuras 10 y 16](https://www.st.com/resource/en/datasheet/stm32g431rb.pdf)
y [guía de hardware ESP32-S3, alimentación y reset](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html).

El módulo requiere además cotejar el land pattern y el pad expuesto con su
[hoja de datos](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.html).
El pad 41 está conectado a masa. Los pads 28/29/30, usados por la variante con
PSRAM octal, no se conectan a periféricos externos.

Para el primer BSP se propone HSI interno del STM32 y USART1 AF7 en PA9/PA10.
Faltan la configuración de reloj, tolerancia del enlace y opciones de arranque.
NRST debe conservar función reset: no reconfigurarlo como PG10 de uso general.
J102 y J103 usan cabezales 1×6 de 2,54 mm con numeración propia; el orden no
corresponde al conector Cortex de 10 pines ni a un adaptador USB-serie concreto.
Su pin de 3V3 es referencia para el programador; no se ha diseñado combinación
de fuentes ni alimentación desde USB.

J104 y J1 del frontal usan cabezales IDC polarizados 2×8 de 2,54 mm. El cable es
plano 1:1 de 16 conductores; el saliente rojo original JP21 no comparte pinout.
Las masas intercaladas junto a SCLK y MOSI forman parte del contrato del cable.

## Bloques que faltan en la principal

| Bloque | Siguiente entrega | Dependencia |
|---|---|---|
| Fuente aislada | Definir 24 V para grupo/válvula y alimentación de la lógica | Espacio, temperatura, aislamiento y potencia total |
| Alimentación lógica | Ensayar AP63203, térmica, ripple y transitorios | Presupuesto de corriente y prototipo cargado |
| Frontal | Ensayar corte/descarga de 3V3_UI y prevención de backfeed | Display definitivo y comportamiento al apagar UI |
| USB | USB-C, resistencias CC, protección ESD y política VBUS | Acceso mecánico y dominio aislado verificado |
| Supervisión | Watchdog externo y habilitación independiente de cargas | Arquitectura de drivers y análisis de fallos |
| Sensores | Caracterizar nivel capacitivo y cerrar adaptadores | Pinout de JP5/JP22 y estados de contactos JP16 |
| Potencia | Puente H 24 V, válvula 24 V y dominio de red separado | Medida de corriente de grupo y molino, bloqueo, térmica y corte independiente |
| Layout | Colocación final, conectores y routing | Posición de conectores y cierre de I/O |

La selección del buck sigue la
[hoja de datos Diodes](https://www.diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf)
y el corte del frontal la
[hoja de datos TI](https://www.ti.com/lit/pdf/slvsd76). Las referencias y su
instantánea de existencias están en el [catálogo de montaje](../assembly/parts-catalog.json).

## Validación reproducible

```
python3 tools/generate_controller_core.py
python3 tools/check_controller_core.py
python3 tools/validate_kicad.py
<python de KiCad> tools/sync_controller_pcb.py
```

El comprobador propio lee el esquema y verifica alimentación, masas, conexión cruzada
UART, SWD, arranque, reserva PSRAM, enlace frontal y MPN/huella contra catálogo.
Es un parser limitado propio, no KiCad. Adicionalmente,
`python3 tools/validate_kicad.py` ejecuta ERC y coteja una netlist exportada por
KiCad: 68 componentes y 275 pines. El sincronizador conserva la mecánica, actualiza
redes y mantiene 68 huellas en una colocación provisional. Las cinco cabeceras de
máquina deben ensayarse con los arneses antes de liberar la mecánica.
Ver [resultados y límites](../kicad-workflow.md). No hay routing, firmware de placa
ni ensayo físico.
