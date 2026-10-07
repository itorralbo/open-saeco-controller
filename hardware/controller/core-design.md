# Principal Rev A — esquema

El esquema tiene 187 posiciones eléctricas en una sola hoja:
[esquema KiCad](kicad/controller-core-reva.kicad_sch),
[vista SVG auxiliar](preview/core.svg) y [BOM](bom-draft.csv). Cubre toda la
placa de sustitución, lógica, 24 V y red, pero nada está ensayado. La
[PCB](layout.md) está colocada y ruteada con DRC limpio; ver
[proyecto y validación](../kicad-workflow.md).

## Alcance del esquema

- U101: STM32G431RBT6, LQFP64; alimentación, desacoplo, NRST, BOOT0 y SWD.
- U201: ESP32-S3-WROOM-1U-N8R8 (LCSC C2980300); alimentación, EN con RC, BOOT y
  UART de programación. Usa antena externa de 2,4 GHz por U.FL: su antena impresa
  y la zona de exclusión del WROOM-1 ocupaban el 10 % de la placa, y ese espacio
  hace falta para la zona de red. La antena y su cable (U.FL/IPEX MHF1) son un
  accesorio del arnés, fuera de la BOM de la PCB. Hay que fijarla lejos de la
  caldera y de chapa, y comprobar la cobertura con la carcasa cerrada.
- UART entre MCU: STM PA9/TX → ESP GPIO2/RX; ESP GPIO42/TX → STM PA10/RX. Van
  por el lado este del módulo, junto a R211/R212 (antes GPIO18/17).
- Conexión J104 al frontal, con el mismo pinout eléctrico que J1 del frontal.
- Resistencias serie candidatas de 33 Ω en las dos salidas UART y seis señales
  del display. Las de la UART van junto a sus emisores; las seis del display,
  en fila bajo J104, a la entrada del cable del frontal.
- Entrada de 12 V DC aislada de banco (J101), protección de entrada, buck de
  3,3 V y corte controlado del rail del frontal.
- Divisor y filtro del NTC JP13 hacia PA3/ADC1_IN4, con diagnóstico de abierto/corto.
- Alimentación a 12 V y entrada open collector del caudalímetro JP5 hacia
  PA2/TIM2_CH3; pinout físico 1=señal, 2=GND y 3=VCC. Desde el 2026-10-07
  (issue #8) la alimentación sale por R413 (390 Ω, anti-surge de 0,66 W) con
  C408 junto al conector. El Digmesa gasta menos de 8 mA y funciona desde
  3,8 V, así que le quedan unos 7,9 V con 11 V en el raíl. Un corto en el mazo
  se queda en 32 mA y 0,4 W, sin hundir `12V_PROTECTED` ni abrir F301.
- Sensor de agua JP22 alimentado a 3,3 V y señal filtrada hacia PC3/ADC12_IN9;
  orden rojo=VCC, blanco=señal y negro=GND. Desde el 2026-10-07 lo alimenta
  U304, otro TPS2553, con R306 = 210 kΩ: 110–150 mA, de sobra para un sensor
  de nivel y lejos del límite de U301.
- Entradas activas a cero para JP14 (PA1) y los micros de presencia (PC2) y
  trabajo (PA0) de JP16, con pull-up, resistencia serie y filtro RC.
- J105 y J106 son HR A2506WV-02P/-03P, identificadas por el propietario;
  J107–J109 usan huellas candidatas JST XH/PH que la revisión con nonio del
  2026-09-24 no confirma. Las vías V1/V2 de JP16 llegan a un DRV8876 para el motor del grupo.
- J110 añade USB-C 2.0 nativo al ESP32, protección ESD, detección de VBUS y
  resistencias CC. J111 permite alimentación limitada de banco y queda abierto.
- J112 recibe 24 V DC aislados para los actuadores y entra por su propio
  fusible F306 (2 A) y Schottky D308; F303/D304/C501 forman la rama protegida
  del motor del grupo y F304/D305 la rama separada de válvula.
- PS701 integra la alimentación de red como módulo IRM-30-24; U303 deriva 12 V,
  y K701 corta de forma general la fase entregada a las cargas peligrosas.
- U501 implementa inversión, PWM, `nSLEEP`, diagnóstico `nFAULT`, límite de
  corriente candidato a 1 A y lectura `IPROPI` hacia el ADC del STM32.
- PA7 gobierna la electroválvula mediante U502, Q501 y una entrada con pull-down.
  J113 reproduce JP3: pin 1 a +24 V, pin 2 al retorno conmutado y 3–5 sin uso.
  D306 proporciona rueda libre externa.
- U601 supervisa 3,3 V y PB4 como watchdog. Su salida open-drain comparte
  `STM_NRST`; U605 (Schmitt) lo cuadra como `STM_NRST_BUF` y U602 solo permite
  activar `nSLEEP` y la válvula mientras reset esté inactivo. R603/R604 mantienen ambas órdenes a cero durante el arranque.
- PF1/ADC2_IN10 y PC1/ADC2_IN7 miden las entradas de 12 V y 24 V mediante
  divisores 200 kΩ/10 kΩ y filtros de 100 nF. J114 expone 3,3 V, 12 V y 24 V
  para medida en banco, cada uno entre dos masas y tras 10 kΩ; no es una
  entrada de alimentación.

- Etapas de calentador (U701/Q703), bomba (U702/Q704) y molinillo
  (U703/Q708/F703/BR701): MOC3083 de cruce por cero y BTA24 tras K701, con el
  LED de cada opto gobernado por un BSS138LT1G desde 12 V. Órdenes PC5, PB11 y PC4
  a través de U603/U604. U704 (TMCS1133B4A) mide la corriente del molinillo en
  la línea + de JP8, cruzando la barrera, y la lleva a PA6 por R412/C407. Detalle
  en [power-architecture.md](../power/power-architecture.md).

JP8 y JP24 son J115 y J117, las LEOCO 3941P03*000 y 5001P020013 identificadas
por el propietario, con huella según el plano del fabricante. JP19 es J116 y JP17
es J118, los TE 1971845-4 y 1971845-3, también con huella según el plano. Los dos
FASTON de PE son J119/J120, TE 63824-1 casados con la foto del propietario.

Los GPIO sin uso llevan NC: no están conectados en el circuito y no equivalen a
ninguna vía del arnés Saeco.

## Alimentación y arranque

J101 usa un JST XH vertical de dos contactos (B2B-XH-A, `C158012`): `12V_BENCH_RAW` y `GND_UI`. Debe
recibir 12 V DC de una fuente AC/DC aislada y certificada; no admite conexión a
red. F305 (1 A) protege su rama y D307 (SS34) bloquea polaridad inversa y la une
a `12V_PROTECTED` en OR con la salida de U303, que llega por F301 y D301. D302
(SMAJ15A) limita transitorios antes del regulador: empieza a conducir entre 16,7 y
18,5 V, por debajo de los 20 V máximos del VDD de U502 y del caudalímetro de J106.
Hasta el 2026-10-05 era un SMAJ18A, que no conduce hasta 20–22,1 V.

En la máquina, PS701 (IRM-30-24) da `24V_INTERNAL_RAW`, que J121, puenteado de
fábrica, une a `24V_ACT_RAW`: de ahí salen el motor del grupo, la válvula, la
bobina de K701 y U303, que baja a 12 V sobre `12V_ISO_RAW`.
En banco, J112 inyecta 24 V limitados con J121 abierto, y J101 12 V para la
lógica sola. Hasta el 2026-10-05 J101 compartía nodo con la salida de U303: sin
24 V, el nodo SW del AP63200 quedaba por encima de su VIN (máximo absoluto
VIN + 0,3 V) y su diodo interno devolvía tensión a `24V_ACT_RAW`. Ahora J101 y
U303 se unen en OR por D307 y D301, y con 24 V presentes manda la tensión más
alta sin que ninguna fuente alimente a la otra.
Ver la [arquitectura de alimentación](../power/power-architecture.md).

U301 es un AP63203WU-7 síncrono de salida fija a 3,3 V/2 A. El circuito implementa
la tabla 2 de su hoja de datos: L301=3,9 µH, C301=10 µF/25 V, C304+C305=2×22 µF/10 V
y C303=100 nF entre BST y SW. C302 y C306 añaden desacoplo de alta frecuencia.
Desde el 2026-10-07 (issue #3) el condensador de entrada que pide la hoja es
C315 (10 µF/50 V X7R 1206, el mismo que C310), justo detrás de C302 entre VIN y
GND. C301 queda como bulk del raíl junto a D301/D307, a unos 30 mm de pista del
conmutador. A 12 V, C315 trabaja al 24 % de su tensión nominal, frente al 48 %
de C301 (25 V X5R 0805). Su capacidad efectiva no se ha leído en la curva de
polarización de Samsung: queda para la medida del rizado de VIN.
`3V3_CORE` alimenta ambos procesadores.

U302 (TPS2553DBVR desde el 2026-10-07, issue #8) genera `3V3_UI` desde
`3V3_CORE`. PB12 del STM32 controla `UI_PWR_EN`; R301=100 kΩ lo mantiene activo
durante reset. R304=49,9 kΩ limita la corriente a 475–565 mA (TI SLVS841F, 7.5),
por debajo de 1,5 A de los contactos WR-MM y del límite de U301. Además, el
TPS2553 tiene apagado térmico. Un corto en el cable del frontal se queda en
U302 y no hunde `3V3_CORE`, así que los dos MCU siguen vivos aunque el reset no
aísle el frontal. El TPS22918 que había no tenía límite de corriente ni apagado
térmico. El TPS2553 no descarga su salida al apagarse: R305=1 kΩ lo hace, como
el QOD del TPS22918, y gasta 3,3 mA con el frontal encendido. Su arranque suave
interno sustituye a C307. FAULT queda sin conectar. Esta rama permite cortar el
frontal y reduce su corriente de arranque. La rampa, descarga y
posible backfeed deben medirse con el display definitivo. `GND_UI` es la masa
lógica común; el aislamiento lo da PS701 (o la fuente de banco de J101/J112).

El símbolo del STM32 sigue la tabla de pads LQFP64 de ST
(`STM32_open_pin_data`, la misma del símbolo oficial de KiCad): VSS/VDD en 15/16
y VSSA/VREF+/VDDA en 27–29. Hasta el 2026-10-01 dibujaba los pads 12–29 con el
orden de la serie F; lo detectó el [modelo de placa](../../sim/README.md).
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

J104 y J1 del frontal usan el Würth WR-MM 690367181672 que el propietario
identificó en el enlace original (16 contactos a 1,27 mm al tresbolillo). El
cable original es plano 1:1 de 16 conductores y su pestillo entra en un taladro de
1,5 mm junto al pin 1, que fija el sentido; el pinout es nuevo, no el de JP21 Saeco.
Las masas intercaladas junto a SCLK y MOSI forman parte del contrato del cable.

## USB de servicio y control en banco

J110 es un HRO TYPE-C-31-D-06 (`C2689964`) USB 2.0 de entrada vertical,
junto a la zona del conector rojo JP21 original. GPIO19 y
GPIO20 del ESP32-S3 implementan D− y D+ a través de R221/R222 de 33 Ω. U203
(USBLC6-2SC6, `C7519`) protege ambas líneas y R223/R224 de 5,1 kΩ anuncian un
dispositivo USB en CC1/CC2. GPIO15 recibe `USB_VBUS_SENSE` mediante 100 kΩ/100 kΩ
y 10 nF, necesario para que un equipo autoalimentado detecte la presencia del host.
La carcasa se une provisionalmente a `GND_UI`; la política EMI/chasis se revisará
con el layout y la envolvente final.

El par D+/D− está ruteado para 90 Ω diferencial (0,29/0,20 mm sobre el plano de
In1.Cu), con U203 junto a J110 y R221/R222 junto al ESP32; ver
[service-usb.md](../../docs/service-usb.md).

La vía de alimentación USB es deliberadamente opcional: F302 limita a 500 mA,
J111 es un puente de soldadura que se fabrica **abierto** y D303 impide retorno
hacia VBUS. Cerrado en banco, inyecta aproximadamente 5 V en la entrada del buck
existente; sirve para firmware y lógica con consumo controlado. No se autoriza
alimentar actuadores, el frontal completo ni la máquina desde el PC. Con J111
abierto, USB sigue disponible para datos cuando J101 alimenta la lógica. El uso
de servicio y el protocolo se detallan en [USB de banco](../../docs/service-usb.md).

## Lo que falta en la principal

| Bloque | Siguiente entrega | Dependencia |
|---|---|---|
| Fuente aislada | Confirmar IRM-30-24 con los consumos reales (PS-01 a PS-03) | Consumos simultáneos, temperatura interior |
| Protección de red | MOV RV701 y filtro EMI (fusibles de red cerrados en la issue #1: 1500 A, F701 de 12 A y F702 de 2 A) | Energía de sobretensión e identificación de L5/L7 de la original |
| Alimentación lógica | Ensayar AP63200/AP63203, térmica, ripple y transitorios; J101 en OR con U303 por D307/D301 | Presupuesto de corriente y prototipo cargado |
| Frontal | Ensayar corte/descarga de 3V3_UI y prevención de backfeed | Display definitivo y comportamiento al apagar UI |
| USB | Comprobar enumeración y consumo de banco | Acceso mecánico y dominio aislado verificado |
| Supervisión | Ensayar el [watchdog e interlock implementados](../power/watchdog-interlock.md) | Firmware PB4, osciloscopio y análisis de fallos |
| Sensores | Caracterizar salida del nivel capacitivo y ensayar adaptadores | Niveles lleno/vacío de JP22 y estados de contactos JP16 |
| Motor del grupo | Ensayar DRV8876, corriente, bloqueo, inversión, frenado, ruido y térmica | Fuente 24 V limitada, motor real y firmware de fallo |
| Electroválvula | Ensayar la [etapa low-side implementada](../power/valve-driver.md), corriente, liberación y transitorios | Fuente 24 V limitada, bobina real y osciloscopio |
| Etapas de red | Ensayar calentador, bomba y molinillo | [Plan de caracterización](../../docs/HD8911/characterization-plan.md) y revisión de aislamiento |
| Mecánica | Comprobación 1:1 y conectores de JP14, JP16 y JP22 | Placa original, mazos y muestras |

### Puente H del motor del grupo

La resistencia medida del motor del grupo es 54,7 Ω. A 24 V equivale a
`24 V / 54,7 Ω = 0,439 A` como estimación resistiva con el rotor parado en la
posición de medida. No se usa como corriente nominal: las escobillas, la posición
del colector, la temperatura y la fuerza contraelectromotriz cambian el valor.

U501 es un
[**DRV8876PWPR**](https://www.ti.com/lit/ds/symlink/drv8876.pdf) (TI, `C575551`), puente H para 4,5–37 V,
3,5 A pico y encapsulado HTSSOP-16 con pad térmico. Integra lectura proporcional
`IPROPI`, regulación de corriente y `nFAULT`, lo que evita un shunt de potencia y
encaja con la autodosis basada en corriente del grupo. La hoja de datos incluye
precisamente un caso de 24 V, 0,5 A RMS y límite de 1 A.

La primera revisión implementa `RIPROPI = 2,4 kΩ`, `RREF1 = 18 kΩ` y
`RREF2 = 49,9 kΩ` desde 3,3 V, los tres Basic en JLCPCB (hasta el 2026-10-01 eran
2,49 kΩ y 16,0 kΩ, que pasaron a Extended). El divisor produce aproximadamente
2,425 V y el límite teórico es aproximadamente 1,01 A. `IPROPI` entregaría unos
1,2 V a 0,5 A y quedaría limitado cerca de 2,43 V, dentro del ADC de 3,3 V. Con
la ganancia de 1 000 µA/A, el firmware convierte con I ≈ V_IPROPI / 2,4 (0,417 A
por voltio). IMODE se
conecta a masa para regulación fixed-off-time con recuperación automática. PB5
mantiene `nSLEEP` a cero durante reset mediante R506; el firmware deberá retirar
`nSLEEP` inmediatamente al detectar `nFAULT`, ya que el modo elegido reintenta
automáticamente tras una sobrecorriente.

PF0 gobierna EN/PWM con TIM1_CH3N, la salida complementaria usada sola.
PC14 da la dirección, PB5 `nSLEEP`, PB6 lee `nFAULT` y PC0 (ADC12_IN6) mide
`IPROPI`. PC14 está en el dominio de respaldo: salida lenta (2 MHz como máximo) y
nunca como fuente de corriente; basta para una entrada lógica. V1/V2 de JP16 son `OUT2/OUT1`. Ese orden, con el DRV8876 girado 270°,
evita que se crucen las pistas del motor; el motor es de continua y el signo de
DIR para cada sentido se fijará en el ensayo del grupo. La numeración física del
conector sigue siendo candidata hasta probar el arnés. C503=100 nF entre VCP y VM y C504=22 nF
entre CPH y CPL siguen la aplicación de referencia de TI. C501=100 µF/35 V es un
bulk inicial, no un dimensionado cerrado. C502=100 nF es el bypass de VM; desde
el 2026-10-07 (issue #5) está a unos 5 mm del pin 11 y no a 11 mm, con su propia
vía de masa.

J112 exige 24 V DC aislados y limitados. Desde el 2026-10-07 (issue #6) entra
por su propio fusible F306 (prosemi 1206TD-2A) y un SS34, D308, antes de unirse
a `24V_ACT_RAW`, igual que J101 por F305/D307. Antes solo las ramas del grupo
(F303/D304) y de la válvula (F304/D305) bloqueaban la polaridad inversa: con el
cable invertido, −24 V llegaban a VIN y EN de U303 (mínimo absoluto −0,3 V) y
polarizaban en directo D701 y el diodo interno de Q701, con solo la limitación
de la fuente como protección. F306 lleva toda la placa en banco: el motor hasta
su ITRIP de 1 A, la válvula (0,42 A) y el buck de 12 V, unos 1,6 A en el peor
caso, así que es de 2 A y no de 1 A como F305. D308 cae unos 0,5 V a 1 A
(≈ 0,5 W en SMA). La fuente interna no pasa por ellos: PS701 se une por J121,
que se sigue abriendo antes de conectar una fuente en J112. La regla
`reverse-polarity` del modelo de placa recorre cada entrada de banco cableada a
mano y falla si un cable invertido alcanza algo más que el ánodo de un diodo
serie. No se ha añadido un TVS al rail de motor: su tensión de trabajo
y energía deben elegirse con la tolerancia y respuesta transitoria de la fuente
real para no superar los 40 V absolutos del DRV8876. El catálogo registra todas
las piezas como candidatas, no liberadas para compra. Se usa la huella estándar
con pad térmico de 3×3 mm, que baja al plano por cuatro vías; la matriz de vías y
el área de cobre que recomienda TI quedan por comprobar antes de fabricar.

### Telemetría de alimentación

R701/R702/R703/C701 y R704/R705/R706/C702 acondicionan `12V_PROTECTED` y
`24V_ACT_RAW`. Cada divisor tiene dos resistencias de 100 kΩ en serie y 10 kΩ a
masa, por lo que `Vin = 21 × Vadc`; a 12 V se esperan 0,571 V y a 24 V, 1,143 V.
La impedancia de Thévenin es 9,52 kΩ y el filtro de 100 nF produce una constante
de tiempo aproximada de 0,95 ms. El firmware usará tiempos de muestreo largos y
calibración con multímetro; estas entradas sirven para diagnóstico y brownout,
no como instrumento de precisión.

J114 es GND, 3,3 V, GND, 12 V protegidos, GND y 24 V de entrada (serigrafía
«G 3V3 G 12 G 24»). Se destina a osciloscopio/multímetro durante el banco; no se
debe alimentar la placa a través de sus pines. Desde el 2026-10-07 (issue #4)
cada raíl llega a su pin por 10 kΩ en 0603 (R723, R724 y R725, junto a la
cabecera) y nunca hay dos raíles contiguos. Antes iban directos y contiguos:
una punta que resbalara ponía 12 V en `3V3_CORE` (2↔3), 24 V en
`12V_PROTECTED` (3↔4) o 24 V en PF1 (4↔5). Ahora un resbalón solo lleva un raíl
a masa por 10 kΩ: 2,4 mA y 58 mW a 24 V, el 58 % de los 100 mW del 0603. Con un
multímetro de 10 MΩ el error es del 0,1 %. Con una sonda de unos 15 pF el polo
cae hacia 1 MHz, así que el rizado de los bucks se mide en sus condensadores y
no en J114. Las dos tensiones ADC salieron de la cabecera: se miden en C701 y
C702. La regla `probe-header` del modelo de placa lo comprueba.

### Driver de la electroválvula

La rama de válvula parte de `24V_ACT_RAW` pero dispone de F304=1 A y D305 propios.
U502 (UCC27517DBVR; pads DBV de TI SLUSAY4D: 1 VDD, 2 GND, 3 IN+, 4 IN−,
5 OUT) recibe PA7 mediante R511=33 Ω y R512=10 kΩ a masa; su salida
de 12 V conduce Q501 (SI2308A, 60 V) a través de R513=33 Ω, con R514=100 kΩ entre
puerta y source. C507=100 nF y C508=1 µF desacoplan el driver. D306 (SS34) queda
en paralelo con la bobina, cátodo a `24V_VALVE` y ánodo a `VALVE_RETURN`.

J113 usa HR A2506WV-05P vertical, LCSC `C382535`, con pin 1 a +24 V y pin 2 al
retorno conmutado; 3–5 quedan NC. La etapa se ha dibujado para probar la bobina
OLAB 6000BH/B0DN. Antes de liberarla deben medirse corriente en caliente, tiempo
de liberación, tensión de drenador y temperatura del MOSFET.

### Watchdog e interlock de actuadores

U601 (TPS3828-33DBVR) monitoriza `3V3_CORE` con umbral nominal de 2,93 V. Su
salida open-drain comparte `STM_NRST`; un timeout de WDI o una caída del rail
reinicia el STM32. PB4 llega por R601=33 Ω a U606 (SN74LVC1G132, NAND Schmitt),
que entrega WDI = NAND(`STM_NRST`, impulso): durante el reset WDI queda en alto y
quieto, porque el TPS3828 enclavaría RESET ante un pulso en WDI con RESET activo.
R602=1 kΩ a masa fija la entrada del impulso si el GPIO queda en alta impedancia.

`STM_NRST` sube por R101 contra C101, unos 0,5 ms/V, y las entradas del
SN74LVC2G08 sin histéresis piden 10 ns/V como mucho: U605 (SN74LVC1G17DBVR,
buffer Schmitt, con C605) entrega a las seis entradas de reset `STM_NRST_BUF`.
U602 (SN74LVC2G08DCTR) combina `STM_NRST_BUF` con `BREW_SLEEP_RAW` y
`VALVE_EN_RAW`. Si reset está activo, fuerza `BREW_SLEEP_INTERLOCK` y
`VALVE_EN_INTERLOCK` a cero independientemente del software. R603/R604 mantienen
las órdenes brutas a cero mientras el MCU arranca. U603 y U604, del mismo tipo,
hacen lo mismo con el armado del relé general (PB7) y las órdenes de calentador
(PC5), bomba (PB11) y molinillo (PC4); R722, R711, R713 y R717 son sus
pull-down. Ver el [diseño y temporización
del supervisor](../power/watchdog-interlock.md).

### Fuente integrada y corte general de cargas

PS701 es un Mean Well IRM-30-24 montado en la propia principal. F701 protege la
entrada completa, F702 separa la rama de la fuente y RV701 limita sobretensiones.
Desde el 2026-10-06 F701 y F702 son Littelfuse 215 de 1500 A a 250 VAC: F701
de 12 A, axial y soldado como el F1 original, y F702 de 2 A, como el F2 original, en pinzas
01110501Z, como F703 en el molinillo (issue #1, [corriente de
defecto supuesta](../power/power-architecture.md#corriente-de-defecto-supuesta-y-fusibles-de-red)).
Sigue abierta la energía del MOV. J121 se entrega puenteado para alimentar `24V_ACT_RAW`
desde PS701 y se abre antes de inyectar 24 V limitados por J112 durante el banco.

U303 (AP63200WU-7) convierte esos 24 V a `12V_ISO_RAW`. La red de aplicación usa
10 µH, 10 µF/50 V en entrada (C310) más 100 nF de alta frecuencia en los pines
(C316, desde el 2026-10-07), dos condensadores de 22 µF/25 V en salida y divisor
330 kΩ/24 kΩ con 56 pF de avance. La tabla de 12 V del fabricante da 249 kΩ/18 kΩ
(11,87 V), pero 249 kΩ es Extended en JLCPCB; el par Basic 330/24 kΩ da
0,8 × (1 + 330/24) = 11,80 V según la ecuación 6 de la hoja, y el avance de 56 pF
queda dentro de los 10–220 pF que admite.

K701 es un relé Omron G5RL-1A-E-TV8 DC24 normalmente abierto. Sus dos pads COM y
sus dos pads NO se mantienen duplicados para repartir corriente. U603 exige a la
vez `STM_NRST` inactivo y `MAINS_ARM_RAW`; Q701 (BSS138LT1G, especificado a
VGS = 2,75 V, porque su puerta sale de los 3,3 V de U603) excita la bobina y D701
absorbe su energía. `LOAD_L_ENABLED` es la única fase que llega a los triacs de calentador,
bomba y molino. El dimensionado final depende aún de medir los motores y revisar
el calentador de 1900 W.

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
```

La cadena completa de la PCB está en [kicad-workflow.md](../kicad-workflow.md#cómo-continuar).

El comprobador propio lee el esquema y verifica alimentación, masas, conexión cruzada
UART, SWD, arranque, reserva PSRAM, enlace frontal y MPN/huella contra catálogo.
Es un parser limitado propio, no KiCad. Adicionalmente,
`python3 tools/validate_kicad.py` ejecuta ERC y coteja una netlist exportada por
KiCad. Las cabeceras de máquina deben probarse con los arneses antes de liberar
la mecánica. Ver [resultados y límites](../kicad-workflow.md). No hay firmware de
placa ni ensayo físico.
