# Principal Rev A.0 — núcleo lógico y alimentación de baja tensión

Existe una hoja eléctrica parcial con 83 posiciones eléctricas:
[esquema KiCad](kicad/controller-core-reva.kicad_sch),
[vista SVG auxiliar](preview/core.svg) y [BOM](bom-draft.csv).
Es una parte de la futura principal; no es una placa de sustitución terminada.
Ya dispone de [proyecto y PCB de trabajo](../kicad-workflow.md), con 83 huellas,
contorno y tres taladros. ERC nativo superado; la geometría actual no tiene
infracciones DRC, pero quedan 198 conexiones sin rutear.

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
  PA1/TIM2_CH2; pinout físico 1=señal, 2=GND y 3=VCC.
- Sensor de agua JP22 alimentado a 3,3 V y señal filtrada hacia PA2/ADC1_IN3;
  orden rojo=VCC, blanco=señal y negro=GND.
- Entradas activas a cero para JP14 y los micros de presencia/trabajo de JP16,
  con pull-up, resistencia serie y filtro RC.
- J105–J109 usan huellas candidatas JST XH/PH cotejadas con fotos y catálogo
  LCSC. Las dos vías de motor de JP16 quedan NC hasta seleccionar el puente H.
- J110 añade USB-C 2.0 nativo al ESP32, protección ESD, detección de VBUS y
  resistencias CC. J111 permite alimentación limitada de banco y queda abierto.

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
Su pin de 3V3 es referencia para el programador; no se alimenta desde él.

J104 y J1 del frontal usan cabezales IDC polarizados 2×8 de 2,54 mm. El cable es
plano 1:1 de 16 conductores; el saliente rojo original JP21 no comparte pinout.
Las masas intercaladas junto a SCLK y MOSI forman parte del contrato del cable.

## USB de servicio y control en banco

J110 es un HRO TYPE-C-31-M-12 (`C165948`) USB 2.0 colocado provisionalmente en
el borde superior, junto a la zona del conector rojo JP21 original. GPIO19 y
GPIO20 del ESP32-S3 implementan D− y D+ a través de R221/R222 de 33 Ω. U203
(USBLC6-2SC6, `C7519`) protege ambas líneas y R223/R224 de 5,1 kΩ anuncian un
dispositivo USB en CC1/CC2. GPIO21 recibe `USB_VBUS_SENSE` mediante 100 kΩ/100 kΩ
y 10 nF, necesario para que un equipo autoalimentado detecte la presencia del host.
La carcasa se une provisionalmente a `GND_UI`; la política EMI/chasis se revisará
con el layout y la envolvente final.

El layout deberá mantener D+/D− a 90 Ω diferencial ±10 %, longitudes igualadas,
plano de masa continuo y el mínimo de vías. U203 irá junto a J110 y R221/R222 junto
al ESP32. Son requisitos de colocación/routing; el PCB actual solo coloca huellas.

La vía de alimentación USB es deliberadamente opcional: F302 limita a 500 mA,
J111 es un puente de soldadura que se fabrica **abierto** y D303 impide retorno
hacia VBUS. Cerrado en banco, inyecta aproximadamente 5 V en la entrada del buck
existente; sirve para firmware y lógica con consumo controlado. No se autoriza
alimentar actuadores, el frontal completo ni la máquina desde el PC. Con J111
abierto, USB sigue disponible para datos cuando J101 alimenta la lógica. El uso
de servicio y el protocolo se detallan en [USB de banco](../../docs/service-usb.md).

## Bloques que faltan en la principal

| Bloque | Siguiente entrega | Dependencia |
|---|---|---|
| Fuente aislada | Definir 24 V para grupo/válvula y alimentación de la lógica | Espacio, temperatura, aislamiento y potencia total |
| Alimentación lógica | Ensayar AP63203, térmica, ripple y transitorios | Presupuesto de corriente y prototipo cargado |
| Frontal | Ensayar corte/descarga de 3V3_UI y prevención de backfeed | Display definitivo y comportamiento al apagar UI |
| USB | Rutear el par, comprobar enumeración y consumo de banco | Impedancia del stack-up, acceso mecánico y dominio aislado verificado |
| Supervisión | Watchdog externo y habilitación independiente de cargas | Arquitectura de drivers y análisis de fallos |
| Sensores | Caracterizar salida del nivel capacitivo y ensayar adaptadores | Niveles lleno/vacío de JP22 y estados de contactos JP16 |
| Potencia | Puente H 24 V, válvula 24 V y dominio de red separado | Medida de corriente de grupo y molino, bloqueo, térmica y corte independiente |
| Layout | Colocación final, conectores y routing | Posición de conectores y cierre de I/O |

### Candidato para el motor del grupo

La resistencia medida del motor del grupo es 54,7 Ω. A 24 V equivale a
`24 V / 54,7 Ω = 0,439 A` como estimación resistiva con el rotor parado en la
posición de medida. No se usa como corriente nominal: las escobillas, la posición
del colector, la temperatura y la fuerza contraelectromotriz cambian el valor.

El candidato de trabajo es
[**DRV8876PWPR**](https://www.ti.com/lit/ds/symlink/drv8876.pdf) (TI, `C575551`), puente H para 4,5–37 V,
3,5 A pico y encapsulado HTSSOP-16 con pad térmico. Integra lectura proporcional
`IPROPI`, regulación de corriente y `nFAULT`, lo que evita un shunt de potencia y
encaja con la autodosis basada en corriente del grupo. La hoja de datos incluye
precisamente un caso de 24 V, 0,5 A RMS y límite de 1 A.

Para la primera revisión se propone `RIPROPI = 2,49 kΩ`, `RREF1 = 16,0 kΩ` y
`RREF2 = 49,9 kΩ` desde 3,3 V. El divisor produce aproximadamente 2,498 V y el
límite teórico es aproximadamente 1,00 A. `IPROPI` entregaría unos 1,245 V a
0,5 A y quedaría limitado cerca de 2,5 V, dentro del ADC de 3,3 V. IMODE se
plantea a masa para regulación fixed-off-time con recuperación automática; la
elección debe revisarse junto con la estrategia de fallo del firmware.

Todavía no se incorpora al esquema: faltan confirmar los dos hilos de motor y los
dos contactos de JP16, cerrar el rail de 24 V, dimensionar capacidad bulk y
validar corriente, inversión, frenado, ruido y temperatura con una fuente de
laboratorio limitada. El catálogo registra la pieza como candidata y no como
liberada para compra. La huella de catálogo representa el pad térmico de 3×3 mm;
antes del esquema final se derivará una huella local con la matriz de vías y el
área de cobre recomendadas por TI.

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
KiCad: 83 componentes y 324 pines. El sincronizador conserva la mecánica, actualiza
redes y mantiene 83 huellas en una colocación provisional. Las cinco cabeceras de
máquina deben ensayarse con los arneses antes de liberar la mecánica.
Ver [resultados y límites](../kicad-workflow.md). No hay routing, firmware de placa
ni ensayo físico.
