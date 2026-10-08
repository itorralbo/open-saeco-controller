# Verificación de esta base

2026-09-15, Windows, Visual Studio 2022 / MSVC 19.34:
- Comprobación Python de enlaces y receta inactiva: PASS.
- Configuración CMake y compilación host Debug: PASS.
- CTest controller_lockout: 1/1 PASS.
- Páginas PDF 34–37 del manual renderizadas y cotejadas visualmente.
- Fotografías JPEG de la conversación revisadas según docs/HD8911/photos.md.

ESP-IDF no está disponible como comando en esta sesión: build ESP32 no ejecutado.
No se ha compilado para STM32, flasheado placas ni ensayado hardware.
La CI se incluye pero no se ha ejecutado en GitHub.

## Iteración de hardware, 2026-09-16

macOS / AppleClang 21.0.0:
- `python3 tools/check_scaffold.py`: PASS.
- `python3 tools/check_front_panel.py`: PASS; 44 componentes (hoy 42: siete teclas y LED), pinout del TCA9534,
  conectores, filtros, polarización y correspondencia con BOM/netlist prevista.
- CMake/build/CTest: PASS, `controller_lockout` 1/1.
- `git diff --check`: PASS.

El SDK seleccionado por defecto (CommandLineTools/MacOSX27.0) no era compatible
con el linker de Xcode activo. La compilación pasó seleccionando explícitamente
el SDK de ese Xcode, sin cambiar la configuración global del equipo:

```
cmake -S firmware/stm32 -B build/host -DCMAKE_OSX_SYSROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.4.sdk
cmake --build build/host
ctest --test-dir build/host --output-on-failure
```

El comprobador del frontal lee las conexiones del archivo `.kicad_sch` usando
un parser limitado propio. No acredita que el archivo haya sido abierto por
KiCad ni sustituye su ERC. En esa iteración no se había localizado KiCad/kicad-cli; apertura,
exportación nativa de netlist y ERC quedan pendientes. No hay PCB ni DRC.
El SVG auxiliar se revisó como ayuda visual; no es un render nativo de KiCad.
No se ha montado, alimentado o ensayado el circuito.

## Núcleo principal y suministro, 2026-09-16

- Primera hoja de la principal: 32 componentes, STM32G431RBT6 + ESP32-S3-WROOM-1-N8R8.
- `python3 tools/check_controller_core.py`: PASS. Comprueba conexiones de
  alimentación, depuración, arranque, UART y frontal leyendo el esquema generado.
- Coincidencia MPN/código/huella con el catálogo: 28/32 posiciones de la hoja
  principal y 34/44 del frontal. Las restantes son mecánicas sin seleccionar.
- Catálogo: 14 referencias con stock observado en la web renderizada de JLCPCB;
  incluye AP63203 como candidato aún no instanciado. Fecha y fuente por referencia.
- `python3 tools/check_front_panel.py`, enlaces locales y `git diff --check`: PASS.
- Vista SVG auxiliar del núcleo renderizada y revisada. No es exportación de KiCad.

Sigue sin ejecutarse ERC/DRC nativo. No se han generado archivos de fabricación,
hecho pedidos ni reservado componentes. No se repitieron las pruebas del firmware,
que no ha cambiado respecto a la verificación anterior.

## Validación nativa y proyectos KiCad, 2026-09-16 (posterior)

Esta revisión sustituye el estado pendiente de KiCad de los apartados anteriores.
Se ha localizado KiCad 10.0.6 en `/Applications/KiCad`; no estaba en PATH.

- Proyectos `.kicad_pro`, bibliotecas locales y PCB `.kicad_pcb` creados.
- ERC nativo de ambos esquemas: 0 errores y 0 avisos, sin exclusiones añadidas.
  Se documentan los controles opcionales desactivados por defecto.
- Se corrigieron extremos fuera de rejilla, biblioteca ausente y declaración
  de las fuentes externas. La revisión del SVG nativo detectó y corrigió
  etiquetas izquierdas que invadían los símbolos.
- Netlist nativa XML frente a conexiones previstas: 32 componentes / 188 pines
  principal y 44 / 122 frontal, coincidencia completa.
- PCB guardadas y recargadas con `pcbnew`: 28 y 34 huellas respectivamente;
  numeración de pads y conexiones verificadas. Posiciones de trabajo, sin rutas.
- DRC nativo **no aprobado**: principal 60 conexiones, 4 huellas, contorno y 12
  taladros pendientes; frontal 58 conexiones, 10 huellas y contorno pendientes.
  [Detalle e informes](../hardware/kicad-workflow.md).
- El CLI DRC dentro del sandbox abortaba al registrar la aplicación en macOS;
  fuera del sandbox se ejecutó y produjo los informes. No era un DRC aprobado.
- Fotografías IMG_1085/1086/1089 revisadas directamente; tipos constructivos
  registrados, sin asignar referencias comerciales ni cotas a partir de perspectiva.

## Mecánica recuperada de IMG_1098–IMG_1101, 2026-09-17

- Calibre: contorno principal 141,6 × 135,2 mm, incertidumbre estimada ±0,15 mm.
- Fotogrametría calibrada: tres taladros NPTH de aproximadamente 3,5 mm; centros
  registrados con ±0,6 mm en [mecánica de la principal](HD8911/main-board-mechanics.md).
- Contorno y taladros incorporados al `.kicad_pcb`; archivo guardado y recargado
  para verificar las coordenadas. La vista mecánica SVG fue renderizada y revisada.
- DRC posterior: ya no informa contorno ausente. Conserva 12 taladros del pad
  térmico ESP32 fuera de regla, 60 conexiones sin ruta, cuatro conectores sin
  huella y tres huellas mecánicas adicionales al esquema.
- Las fotos no proporcionan espesor o alturas fiables ni tolerancia suficiente
  para fabricar huellas de conectores. Esos campos continúan pendientes.
- El propietario aceptó el 2026-09-17 el contorno y los centros de taladro como
  línea base mecánica de Rev A. La aceptación no libera el resto del diseño.

Sin ampliación de firmware ni ensayos eléctricos. Supervisión, sensores y potencia
de cargas siguen pendientes en el esquema principal.

## Alimentación de baja tensión y conectores internos, 2026-09-17

- La principal pasa de 32 a 48 componentes; los 48 tienen MPN, código JLC/LCSC y huella.
- Entrada J101 de 12 V DC aislados con fusible 1 A, bloqueo de polaridad SS34 y
  TVS SMAJ18A. La fuente AC/DC aislada y certificada aún no está seleccionada.
- U301 AP63203WU-7 implementado a 3,3 V/2 A con 3,9 µH, 10 µF de entrada,
  2×22 µF de salida y bootstrap de 100 nF según la tabla 2 del fabricante.
- U302 TPS22918DBVR implementado para `3V3_UI`, controlado por PB0, con pull-up,
  CT de 1 nF y descarga QOD. Falta medirlo con el display definitivo.
- Existencias observadas y registradas para las nuevas referencias; el inductor
  seleccionado tiene 3,3 A nominales y 3,9 A de saturación.
- Comprobador propio: PASS. ERC KiCad 10.0.6: 0 infracciones; netlist nativa:
  48 componentes y 227 pines, coincidencia completa.
- J101 seleccionado como JST XH lateral de 2 vías; J102/J103 como 1×6 de 2,54 mm;
  J104 y J1 frontal como IDC polarizado 2×8 de 2,54 mm. Stock observado y registrado.
- PCB principal: 48 huellas eléctricas, 16 nuevas de alimentación y cuatro
  conectores colocados provisionalmente;
  contorno y los tres taladros aceptados conservados y verificados tras recargar.
- DRC de la principal: 0 infracciones geométricas/de reglas, 122 conexiones sin
  rutear y 3 avisos de paridad esperados (MH1–MH3 adicionales al esquema).
- PCB frontal: J1 incorporado; 35 huellas, 70 conexiones sin rutear. El DRC solo
  marca el contorno ausente y las nueve huellas mecánicas aún pendientes.
- El mínimo de taladro se fija en 0,20 mm para las vías térmicas del ESP32, valor
  preferido publicado por JLCPCB. No equivale a liberar el stack-up ni la fabricación.

## Diagrama de interconexión del manual, 2026-09-18

- La página PDF 59, capítulo 10, hoja 1/1, se renderizó y cotejó visualmente con
  la transcripción aportada por el propietario. Es un diagrama de interconexión,
  no un esquema de la electrónica interna de la placa.
- Se corrigió el nivel de agua de JP23/2 a **JP22/3**.
- Se confirmaron JP17 (entrada de red), JP1/JP9 (PE), JP19 (calentador), JP24
  (bomba), JP3 (válvula), JP8 (molino), JP13 (temperatura), JP5 (caudalímetro),
  JP16 (motor del grupo y dos micros), JP14 (puerta/cajón) y JP21 (interfaz original).
- JP16 tiene ocho posiciones: dos para motor, dos unidas por puente y dos pares
  para los micros de presencia y posición de trabajo. JP2 aparece expresamente
  sin conectar.
- La comprobación no determina niveles, corrientes, curvas, estados de contactos,
  numeración física ni familias comerciales. Esos datos siguen bloqueando la
  selección final de drivers y huellas del arnés de máquina.

## Identificación de cargas y sensores, 2026-09-18

- Las referencias aportadas se cotejaron con el manual y el despiece HD8911.
  Quedan confirmados: calentador 220–230 V/1900 W, bomba 220–230 V/48 W,
  electroválvula 24 V DC, motor de grupo 24 V DC y molino accionado a 320 V DC
  según el modo de servicio.
- `996530059843` se identificó con el Digmesa FHKSC `932-9521-B`: alimentación
  3,8–20 V, salida NPN de colector abierto y aproximadamente 1925 pulsos/litro.
- La tabla NTC se ajustó únicamente como ayuda de diseño: R25≈49,9 kΩ y B≈4037 K.
  El firmware deberá usar tabla/interpolación y tolerancias del manual.
- Se aclaró que el ajuste de dosis usa la corriente de compresión del motor del
  grupo: I0=100–300 mA y objetivos I0+55/100/200 mA. La corriente del molino se
  mide por separado para detectar falta de grano y bloqueo.
- El módulo capacitivo `421941306721`, el orden de los conectores, los estados de
  micros y las corrientes de bloqueo siguen necesitando caracterización física.

## Entradas pasivas de la principal, 2026-09-18

- La principal pasa de 48 a 68 componentes. Hay 63 posiciones con MPN, código
  JLC/LCSC y huella; J105–J109 quedan sin huella hasta identificar las carcasas.
- JP13 usa un pull-up de 4,7 kΩ, 1 kΩ serie y 100 nF hacia PA0/ADC1_IN1.
- El adaptador de JP5 alimenta el caudalímetro desde `12V_PROTECTED` y acondiciona
  su colector abierto con pull-up a 3,3 V, 1 kΩ serie y 10 nF hacia PA1/TIM2_CH2.
  Esta alimentación solo es válida mientras la entrada lógica siga siendo 12 V.
- JP14 y los dos contactos de JP16 usan entradas activas a cero con 10 kΩ,
  1 kΩ y 100 nF hacia PC0, PC1 y PC2. La secuencia V1–V8 de JP16 procede de la
  vista del manual y no se presenta como numeración física confirmada.
- JP22 y las vías de motor de JP16 se marcan NC explícitamente. No se aplica una
  tensión desconocida al sensor capacitivo ni se anticipa el puente H.
- Comprobador propio: PASS. ERC KiCad 10.0.6: 0 infracciones; netlist nativa:
  68 componentes y 275 pines, coincidencia completa.
- La PCB contiene 63 huellas eléctricas y conserva el contorno y los tres taladros.
  DRC: 0 infracciones geométricas/de reglas, 147 conexiones sin rutear y 8 avisos
  de paridad: J105–J109 y MH1–MH3.

## Medidas de cargas y conectores, 2026-09-18

- Resistencias aportadas por el propietario: molino 68 Ω, electroválvula 56,7 Ω
  y motor del grupo 54,7 Ω. A sus tensiones documentadas dan límites resistivos
  derivados de 4,71 A a 320 V, 0,423 A a 24 V y 0,439 A a 24 V, respectivamente.
  No se presentan como corrientes nominales de los motores.
- JP14 queda abierto si falta puerta o cajón y cerrado únicamente con ambos
  colocados. La red se renombra `DOOR_CLOSED_N`: nivel bajo significa cierre.
- Las fotos con calibre encajan con JST XH 2,50 mm para JP13/JP14/JP5/JP16 y
  JST PH 2,00 mm para JP22. Se seleccionaron cabeceras acodadas genuinas con stock
  LCSC observado, manteniendo el estado candidato hasta probar el acoplamiento.
- La principal incorpora las cinco huellas: 68/68 componentes con MPN, código
  LCSC y huella. JP5 y JP22 permanecen NC por pinout eléctrico desconocido.
- ERC: 0 infracciones, 68 componentes/275 pines. DRC: 0 infracciones geométricas,
  156 conexiones sin rutear y 3 diferencias de paridad correspondientes a MH1–MH3.

## Pinout de caudal y nivel de agua, 2026-09-18

- El propietario confirmó el Digmesa `932-9521-B` y el seguimiento físico de JP5:
  vista cenital, pad cuadrado/pin 1 izquierdo=señal, pin 2=GND y pin 3=VCC.
- La hoja oficial de Digmesa confirma 3,8–20 V, menos de 8 mA y salida NPN de
  colector abierto. JP5 queda alimentado a 12 V y su señal se eleva a 3,3 V antes
  de PA1/TIM2_CH2.
- JP22 usa rojo=VCC, blanco=señal y negro=GND. Se selecciona alimentación a 3,3 V
  y entrada PA2/ADC1_IN3 mediante 1 kΩ/10 nF; la forma de salida y los niveles
  lleno/vacío todavía requieren medida.
- La principal pasa a 70 componentes/279 pines y 70 huellas eléctricas. Comprobador
  propio y ERC nativo: PASS, 0 infracciones. DRC: 0 infracciones geométricas,
  165 conexiones sin rutear y 3 diferencias de paridad correspondientes a MH1–MH3.

## USB-C de servicio, 2026-09-19

- J110 implementa USB 2.0 nativo del ESP32-S3: GPIO19=D−, GPIO20=D+ y GPIO21
  detecta VBUS mediante 100 kΩ/100 kΩ y 10 nF.
- Se seleccionan HRO TYPE-C-31-M-12 (`C165948`), USBLC6-2SC6 (`C7519`), dos
  resistencias CC de 5,1 kΩ y 33 Ω serie en cada línea de datos.
- La alimentación de banco pasa por PTC de 500 mA, puente J111 abierto por defecto
  y SS34 hacia la entrada del buck. No está destinada a cargas ni autoriza conectar
  USB mientras no se haya verificado el aislamiento de la máquina.
- La principal pasa a 83 componentes/324 pines y 83 huellas eléctricas. Comprobador
  propio y ERC KiCad 10.0.6: PASS, 0 infracciones. DRC: 0 infracciones geométricas,
  198 conexiones sin rutear y 3 diferencias de paridad correspondientes a MH1–MH3.
- Las huellas quedan colocadas provisionalmente; el par de 90 Ω, el retorno de masa,
  la envolvente mecánica del conector y la política de pantalla/chasis siguen pendientes
  del routing y revisión física.

## Puente H del motor del grupo, 2026-09-19

- JP16 V1/V2 se asignan a `OUT1/OUT2` de un DRV8876PWPR. PA8 gobierna PWM,
  PA6 dirección, PB5 `nSLEEP`, PB6 `nFAULT` y PA3 adquiere `IPROPI`.
- J112 introduce 24 V DC aislados para pruebas; F303=1 A, D304=SS34 y
  C501=100 µF/35 V forman la entrada provisional. Este rail no se une a J101.
- R510=2,49 kΩ y el divisor R508/R509=16 kΩ/49,9 kΩ producen un límite teórico
  cercano a 1,00 A. IMODE a masa activa recuperación automática; el firmware
  deberá retirar `nSLEEP` al detectar `nFAULT`.
- Comprobador propio y ERC KiCad 10.0.6: PASS, 0 infracciones, 103 componentes y
  379 pines. La PCB contiene 103 huellas; DRC: 0 infracciones geométricas,
  243 conexiones sin rutear y 3 diferencias de paridad por MH1–MH3.
- No se libera la etapa: faltan una fuente de 24 V limitada, medida de corriente
  de marcha/arranque/bloqueo, inversión, frenado, ruido, térmica, bulk y TVS.

## Estudio de la electroválvula, 2026-09-19

- La bobina de 56,7 Ω implica 0,423 A y 10,16 W resistivos a 24 V, coherente con
  la referencia nominal de 10 W.
- Se documenta una [etapa low-side candidata](../hardware/power/valve-driver.md)
  con UCC27517DBVR, MOSFET SI2308A de 60 V, rueda libre y fusible propio.
- El propietario confirma JP3.1 (pad cuadrado) a solenoide.1/+24 V y JP3.2 a
  solenoide.2/retorno 0 V; JP3.3–5 y el terminal GND separado quedan sin conectar.
  La bobina se identifica como OLAB 6000BH/B0DN, 24 V DC/10 W, y mide 0,073 V
  en modo diodo en ambos sentidos: no se detecta supresión interna polarizada.
- Motor y válvula sumarían unos 0,862 A resistivos; F303=1 A no se considera una
  protección común válida sin medir transitorios, arranque y temperatura.

## Etapa de la electroválvula incorporada, 2026-09-19

- J113 reproduce JP3 con JST S5B-XH-A(LF)(SN), `C263757`: pin 1 a +24 V, pin 2
  al retorno conmutado y pines 3–5 NC. Se observaron 8.885 unidades en LCSC.
- F304=1 A y D305 separan la rama desde `24V_ACT_RAW`. D306=SS34 queda como
  rueda libre, con cátodo a +24 V y ánodo al drenador.
- PA7 controla U502 UCC27517DBVR; Q501 SI2308A conmuta el retorno. Las entradas
  y la puerta tienen pull-down, y el driver dispone de 100 nF + 1 µF locales.
- Comprobador propio y ERC KiCad 10.0.6: PASS, 0 infracciones, 115 componentes y
  410 pines. La PCB contiene 115 huellas; DRC: 0 infracciones geométricas,
  265 conexiones sin rutear y 3 diferencias de paridad por MH1–MH3.
- La etapa continúa sin liberar: faltan corriente en caliente, liberación,
  sobretensión de drenador, ruido y térmica con la bobina real y fuente limitada.

## Watchdog e interlock de actuadores, 2026-09-19

- U601 TPS3828-33DBVR (`C20032`) supervisa `3V3_CORE` a 2,93 V nominal y PB4/WDI.
  Su salida open-drain comparte `STM_NRST`; timeout nominal 1,6 s y reset nominal
  200 ms, con límites de hoja de datos de 0,9–2,5 s y 120–300 ms.
- R602=1 kΩ evita que WDI flotante desactive el watchdog. U602 SN74LVC2G08DCTR
  (`C352973`) combina `STM_NRST` con las órdenes de `nSLEEP` y válvula; R603/R604
  mantienen las órdenes inactivas durante reset.
- Existencias observadas: 49.065 unidades de C20032 y 21.000 de C352973. La
  categoría exacta de montaje JLCPCB queda por verificar.
- Comprobador propio y ERC KiCad 10.0.6: PASS, 0 infracciones, 123 componentes y
  435 pines. La PCB contiene 123 huellas; DRC: 0 infracciones geométricas,
  287 conexiones sin rutear y 3 diferencias de paridad por MH1–MH3.
- Falta implementar PB4 en firmware y comprobar con osciloscopio arranque,
  brownout, timeout, rearme y corte efectivo de ambas cargas.

## Candidatos JST VH de potencia, 2026-09-19

- Las fotos con calibre de JP24 encajan con JST VHR-2N: dos vías, paso 3,96 mm
  y 7,86 mm de ancho según el plano oficial. Se reserva S2P-VH(LF)(SN), C160355;
  se observaron 4.955 unidades en LCSC.
- JP8 y JP17 usan dos conductores dentro de una carcasa de tres vías cuya anchura
  encaja con VHR-3N: 11,82 mm. Se reserva S3P-VH(LF)(SN), C264986; JLCPCB mostraba
  4.721 unidades en stock y 4.697 disponibles para pedido.
- Las referencias están en el catálogo pero no en el esquema ni en la BOM. La
  liberación exige probar el arnés real, confirmar retención y cerrar el diseño
  de alta tensión. JP19 permanece sin identificar mecánicamente.

## Arquitectura de alimentación Rev A, 2026-09-19

- Se mantienen J101=12 V y J112=24 V como dos entradas DC externas aisladas y
  limitadas para el banco; USB puede alimentar únicamente lógica mediante el
  puente J111, abierto por defecto.
- Motor y válvula suman 0,862 A/20,69 W según sus resistencias medidas. El límite
  de 1 A del puente H eleva el peor caso provisional de ambas ramas a 1,423 A;
  se especifica una fuente de banco de al menos 1,5 A, preferiblemente 2 A para
  margen de medida, empezando siempre con un límite inferior.
- La carga completa de 3,3 V equivale aproximadamente a 0,65 A desde 12 V si el
  buck entrega 2 A con una eficiencia conservadora del 85 %. Falta medir ESP32,
  frontal y retroiluminación para validar F301 y la térmica.
- El esquema actual sigue siendo el subconjunto de baja tensión. La principal
  final integrará red, bomba, calentador y molino con aislamiento, protección y
  cortes independientes en la misma PCB.

## Telemetría de rails, 2026-09-19

- PA4/ADC2_IN17 mide `12V_PROTECTED` y PA5/ADC2_IN13 mide `24V_ACT_RAW`; ambas
  funciones se cotejaron con la tabla de pines LQFP64 del STM32G431.
- Cada entrada usa 200 kΩ sobre 10 kΩ y 100 nF: factor 21, 0,571 V nominal para
  12 V y 1,143 V nominal para 24 V. El rango teórico hasta 3,3 V alcanza 69,3 V,
  dejando margen de diagnóstico sin depender de los diodos internos del MCU.
- J114 expone GND, 3,3 V, ambos rails y ambas señales ADC para comparar firmware
  y multímetro. Es una cabecera de medida, no de alimentación.

## Colocación mecánica de conectores de la principal, 2026-09-19

- IMG_1098 se ajustó al contorno aceptado de 141,6 × 135,2 mm e IMG_1101 confirmó
  la entrada por el lateral izquierdo. J104/J108/J107/J113/J109/J105/J106 ocupan
  respectivamente las zonas originales de JP21/JP16/JP14/JP3/JP22/JP13/JP5,
  con incertidumbre fotográfica asignada de ±1,5 mm.
- `tools/layout_controller_pcb.py` consume esas coordenadas desde
  `mechanical-source.json`, asigna posición y orientación a las huellas y
  conserva MH1–MH3. El script también comprueba que los siete conectores no se
  desplacen al regenerar la PCB.
- JP8, JP24 y JP17 ya tienen huellas JST VH candidatas en sus posiciones
  originales. JP19, JP1 y JP9 conservan áreas temporales hasta identificar sus
  huellas. J110 queda junto a la zona del conector rojo.
- U201 queda junto al borde superior y la zona de exclusión de su antena está
  libre. El DRC detectó las invasiones de la primera iteración y la colocación
  final registrada pasa con 0 infracciones.
- El primer routing USB contiene 39 segmentos y 7 vías. Quedan 299 conexiones
  pendientes y tres avisos de paridad por los taladros mecánicos; no libera
  fabricación.

## Reglas de fabricación y routing de la principal, 2026-09-19

- Se evaluaron cuatro capas, pero la Rev A se mantiene en dos para reducir coste
  y plazo: F.Cu concentra señales/potencia y B.Cu se reserva como plano de GND
  casi continuo. El tamaño disponible y USB Full Speed hacen viable esta opción.
- `tools/configure_controller_rules.py` instala cinco clases: Default 0,20 mm,
  USB 0,20/0,20 mm, Power 0,50 mm, Switching 0,60 mm y Actuator 1,00 mm. Las
  vías aumentan de 0,60/0,30 a 1,00/0,50 mm según corriente.
- Se asignaron 26 redes explícitas. USB sigue como geometría provisional hasta
  elegir stack-up y recalcular 90 Ω en la herramienta del fabricante.
- Las áreas temporales de los seis conectores de potencia obligatorios y el keepout de antena
  de U201 se aplican a ambas capas de cobre.
- KiCad 10.0.6: DRC 0 infracciones, 299 conexiones abiertas y seis diferencias
  de paridad: MH1–MH3 y J116/J119/J120 sin huella. Las reglas preparan el routing,
  no liberan fabricación.

## Barrera red/SELV, distribución de red y ESP32-1U, 2026-09-19

- `configure_controller_rules.py` añade la clase `Mains` y escribe
  `controller-core-reva.kicad_dru`: 8 mm de separación y creepage entre red y
  SELV, y 2,5 mm entre pistas de redes de red distintas. Sobre la colocación
  anterior detectó 95 infracciones: fusibles junto al puente H, K701 en la zona
  lógica y J115 junto al buck de 12 V.
- Primer routing del STM32: anillo de VDD bajo el LQFP, una vía por VSS y
  desacoplo en cada par. El plano GND_UI de B.Cu se queda en el lado SELV.
- Fotos IMG_1098/1100/1101: el disipador original ocupa 40 × 33 mm en planta,
  mide 35 mm de alto, lleva dos TO-220 y está encima de JP8/JP19. El propietario
  midió 1,6 mm de espesor de placa y confirmó 35 mm de altura libre.
- U201 pasa a ESP32-S3-WROOM-1U-N8R8 (JLCPCB C2980300; 2.091 en stock y 1.984
  disponibles para pedido, observados hoy). Tiene el mismo pinout y libera la
  zona de exclusión de la antena, unos 1 990 mm².
- La placa se reorganiza con la distribución de la original. La barrera en L es
  una banda de 8 mm sin cobre, el hueco del disipador está reservado y PS701 está
  en vertical junto a J118. `sync_controller_pcb.py` admite ahora cambios de
  huella declarados.
- KiCad 10.0.6: ERC 0; netlist nativa 158 componentes / 528 pines coincidente.
  DRC con todas las severidades: 0 infracciones, 297 conexiones abiertas y seis
  diferencias de paridad (MH1–MH3 y J116/J119/J120 sin huella). No libera
  fabricación ni conexión a red.

## Entrada de red y salida de 24 V, 2026-09-19

- Rutadas la fase J118 → F701, la rama F702 → PS701, la fase protegida hacia
  RV701 y los dos pares de contactos de K701, y el neutro hacia PS701 y RV701.
  L_IN y PSU_L van anidados por el paso junto a PS701 y N cruza por B.Cu.
- Rutados PS701 → J121 y `24V_ACT_RAW` hasta J112, el buck de 12 V, F303, R704,
  J114, K701, D701 y F304. Retoques: F701/F702 intercambiados, J121 girado, y
  C307 y Q701 desplazados.
- KiCad 10.0.6, todas las severidades: 0 infracciones, incluidos 2,5 mm entre
  redes de red, 8 mm y creepage hasta SELV y la banda de barrera. Quedan 273
  conexiones abiertas; las redes de red y de 24 V están completas. Las fases
  van a 3 mm con 1 oz, anchura provisional hasta dimensionar el calentador.

- Decisión del propietario: cobre de 1 oz con las fases de carga duplicadas en
  las dos caras. L_IN hasta y = 77 mm, la fase protegida y el par NO de K701 van
  duplicados, con siete vías de 1,6/0,8 mm. DRC: 0 infracciones (152 segmentos,
  23 vías).

## Prueba de autorrutado y cambio en JP16, 2026-09-19

- Freerouting v2.4.1 sobre las redes SELV, con el cobre revisado fijo y el
  dominio de red vetado. El DRC de KiCad no encontró infracciones de separación,
  pero hubo 17 conexiones abiertas, 62 pistas de 0,15 mm y 2,3 m de pista en
  B.Cu. Resultado descartado y no incorporado a la placa.
- JP16/J108: V1 pasa a `BREW_OUT2` y V2 a `BREW_OUT1` para rutear el motor sin
  cruces. ERC 0, netlist coincidente y comprobador del núcleo correcto.

## Conectores de entrada vertical, 2026-09-22

- Decisión del propietario: todos los conectores de mazo, de entrada vertical.
  Las JST laterales S-series pasan a B-series: B2B-XH-A (`C158012`) en J101,
  J105, J107 y J112; B3B-XH-A (`C144394`) en J106; B5B-XH-A (`C157991`) en J113;
  B8B-XH-A (`C157972`) en J108; B3B-PH-K-S (`C131339`) en J109; B2P-VH
  (`C160315`) en J117; B3P-VH (`C160316`) en J115 y J118; B8B-PH-K-S
  (`C157974`) en J2 del frontal. Existencias leídas de la API de JLCPCB; queda
  por confirmar el tipo de montaje.
- Las huellas KiCad de ambas series tienen pads, paso y taladro idénticos, así que
  el cobre no cambia. J118 baja 0,8 mm para despejar PS701, y se ajustan sus
  tres arranques de pista.
- ERC 0 en las dos placas y netlist coincidente. DRC de la principal: 0
  infracciones, los dos avisos intencionales de extremo suelto, 77 conexiones
  abiertas y tres diferencias de paridad (MH1–MH3), como antes. DRC del frontal
  con todas las severidades, tras rellenar zonas: 0 infracciones.
- El propietario confirma que no hay problema de altura y pide también J110
  vertical. Se elige HRO TYPE-C-31-D-06 (`C2689964`, 3.265 en stock), USB 2.0,
  16 contactos. La huella (`OpenSaeco.pretty`) partió del footprint LCSC/EasyEDA
  y se cotejó con el layout recomendado del plano HRO (rev. A, 2020-11-02).
  Coinciden paso, filas, patas de carcasa y tetones. Se corrigieron dos cosas:
  los pads de señal miden 0,87 mm (de 0,43 a 1,30 mm del eje), no 0,90 mm, y el
  tetón este es un coliso de 0,72 × 0,52 mm, no un taladro redondo de 0,72 mm.
- El plano recomienda PCB de 0,8 ± 0,1 mm y las patas de carcasa miden 0,95 mm;
  en la placa de 1,6 mm no asoman por la cara inferior. Hay que confirmar con
  JLCPCB o con una muestra que la soldadura por reflujo de las patas basta.
- Se rehízo el fanout de J110 con cruce del par por B.Cu bajo el conector, y se
  acercaron R223/R224. El puerto queda completo: VBUS en las cuatro patas,
  CC1/CC2 hasta sus 5,1 kΩ y las masas a la carcasa. DRC: 0 infracciones, los
  dos avisos intencionales, 74 conexiones abiertas (antes 77) y las mismas tres
  diferencias de paridad.

## Etapa del molinillo en la PCB, 2026-09-23

- Decisiones del propietario: 1 A de marcha supuesto hasta medir, fusible T2A
  propio y permiso para mover piezas ya ruteadas. F703 es un JDT
  JFC2410-1200TS (`C136382`, 18 992 en stock), de acción retardada, en una
  huella 2410 nueva hecha con el patrón recomendado de su hoja.
- Los tres optos comparten la barrera vertical: U701 sube a y = 88 mm, U703
  entra en y = 100,72 mm y U702 no se mueve. Los tres triacs van en la cara sur
  del perfil, molinillo, calentador y bomba de oeste a este. Para hacer sitio se
  movieron D701, la troncal de 24 V bajo la bobina de K701, el filtro del
  caudalímetro y la vía de masa de C401. BR701 queda entre J115 y el borde.
- KiCad 10.0.6: ERC 0; netlist nativa 187 componentes / 612 pines
  coincidente. DRC con todas las severidades: 0 infracciones, el mismo aviso
  de extremo suelto de antes, 67 conexiones abiertas (66 antes, más PB12 hasta
  U604) y las tres diferencias de paridad de MH1–MH3. No libera fabricación ni
  conexión a red.

## Rellenos, serigrafía, optos, USB y FASTON, 2026-09-23

- Rellenos: masa `GND_UI` en F.Cu y B.Cu en el lado SELV, cosida al plano de
  In1.Cu con 156 vías de 0,6 mm; sin relleno en el lado de red (decisión
  delegada por el propietario).
- Serigrafía: logo del propietario, título, nombre de los 21 conectores con su
  JP original, polaridad de JP8 y JP17 y aviso de red. Copia 1:1 en
  `hardware/controller/preview/controller-top-1to1.pdf`, con regla de 100 mm.
- Optos: las áreas de paso y de ranura se nombran por pieza y cada una tiene su
  regla; la regla compartida dejaba pasar pares de piezas distintas. Se corrigió
  el único caso real (bajada de B.Cu a Q708). Ranura: ≈ 9 mm de camino
  superficial, 6,02 mm de aire entre filas.
- USB: calculadora de JLCPCB para JLC04161H-7628: 90 Ω diferenciales con
  0,29 / 0,20 mm (0,20 / 0,20 daba ≈ 104 Ω). Tramo U203–R221/R222 acoplado así;
  el ESP32-S3 es Full Speed y el par mide unos 30 mm.
- JP1/JP9: la foto del propietario muestra lengüetas verticales de dos patas;
  se toma el TE 63824-1 (C575074, 11 205 en stock), con dos taladros de 1,40 mm a
  5,08 mm según el plano de TE. Pendiente de comprobar en papel 1:1.
- KiCad 10.0.6: ERC 0; netlist nativa 187 componentes / 612 pines coincidente.
  DRC con todas las severidades: 0 infracciones, 0 conexiones abiertas y las
  tres diferencias de paridad de MH1–MH3. No libera fabricación ni conexión a
  red.

## Molinillo a 3 A y fase de cargas duplicada, 2026-09-23

- Decisión del propietario: la etapa del molinillo se dimensiona a 3 A en vez
  del 1 A de marcha supuesto. F703 pasa a JDT JFC2410-1400TS, T4A
  (`C136386`, 19 798 en stock), en la misma huella. BR701 se queda en KBP410,
  solo para molidos de hasta 10 s.
- La fase de cargas era una sola pista de F.Cu del carril al triac del
  calentador (1,5 mm en la franja, 0,9 mm en la bajada). Ahora el carril va a
  3,3 mm, la franja a 1,7 mm y las bajadas a 1,9 mm, con un bloque de B.Cu bajo
  el pie del disipador unido por 13 vías. El área del pie ya no incluye B.Cu. La
  puerta del calentador cruza bajo el carril en y = 85,6 mm y baja a Q703 por el
  este del bloque. Las pistas del molinillo pasan a 1,9 y 1,2 mm.
- Regla de reparto en el núcleo C: con el molinillo encendido, el calentador
  conduce 3 de cada 5 ciclos; molido de 10 s como máximo.
  `osc_heater_cycles_allowed()` tiene su prueba en CTest.
- KiCad 10.0.6: ERC 0; netlist nativa 187 componentes / 612 pines coincidente.
  DRC con todas las severidades: 0 infracciones, 0 conexiones abiertas y las
  tres diferencias de paridad de MH1–MH3. CTest: 1/1. No libera fabricación ni
  conexión a red.

## Órdenes a las cargas y salidas de U602, 2026-09-23

- Cambio de pin: `GRINDER_EN_RAW` pasa de PB12 (pin 34) a PC4 (pin 25), junto
  a PA7 en la fila sur de U101. El firmware aún no asigna pines. KiCad 10.0.6:
  ERC 0; netlist nativa 187 componentes / 612 pines coincidente.
- PA7, PB10, PB11 y PC4 llegan a sus puertas como un bus de cuatro carriles en
  B.Cu por el borde sur del plano, con dos vías por orden. PB11 conserva sus
  vías; su tramo en B.Cu se rehízo como primer carril. El salto de PB7 bajo la
  troncal de 24 V subió a y = 53,25 mm, la vía oeste del salto de 3,3 V pasó a
  x = 44,75 mm y C602 comparte la vía de masa de R604.
- U602: reset del pin 6 al 2, `BREW_SLEEP_INTERLOCK` hasta R505.1 y
  `VALVE_EN_INTERLOCK` hasta R511.1, con dos y cuatro vías.
- DRC con todas las severidades: 0 infracciones, el aviso intencional de
  extremo suelto en PA3, 44 conexiones abiertas (50 antes) y las tres
  diferencias de paridad de MH1–MH3. El relleno de GND_UI queda en las mismas
  seis piezas que antes. No libera fabricación ni conexión a red.

## Lado este del STM32, puente H y telemetría, 2026-09-23

- Cambios de pin, comprobados contra las funciones alternativas del
  STM32G431RBTx en la librería de KiCad 10: `UI_PWR_EN` PB0→PB12,
  `BREW_DIR_RAW` PA6→PC14, `BREW_PWM_RAW` PA8→PF0 (TIM1_CH3N), `RAIL_12V_ADC`
  PA4→PF1 (ADC2_IN10), `BREW_CURRENT_ADC` PA3→PC0 (ADC12_IN6) y
  `DOOR_CLOSED_N` PC0→PC3. ERC 0; netlist nativa 187 componentes / 612 pines
  coincidente; `check_controller_core.py` actualizado.
- R701–R706, C701 y C702 pasan al hueco bajo J114, con entradas desde J114.3 y
  la rama de 24 V y salidas a J114.5/J114.6.
- Ruteados la UART, BOOT0, el reset hasta J102.5, el corte del frontal, la
  dirección y el PWM del puente H, su corriente, las dos telemetrías y los
  divisores.
- DRC con todas las severidades: 0 infracciones y ningún aviso (desaparece el
  extremo suelto de PA3), 29 conexiones abiertas (44 antes) y las tres
  diferencias de paridad de MH1–MH3. El relleno de GND_UI queda en las mismas
  seis piezas. No libera fabricación ni conexión a red.

## Cuatro capas y ruteo completo, 2026-09-23

- Apilado JLC04161H-7628 (`configure_controller_stackup.py`): GND_UI pasa de
  B.Cu a In1.Cu y un plano 3V3_CORE en In2.Cu sustituye la espina de 3,3 V
  (506 → 143 mm de pista). Ninguna capa interna entra en el dominio de red; las
  áreas de regla se rehacen en las cuatro capas.
- Cambios de pin del STM32, comprobados contra el símbolo STM32G431RBTx:
  `RAIL_24V_ADC` PA5→PC1 (ADC2_IN7), `WATER_LEVEL` PA2→PC3 (ADC12_IN9),
  `BU_PRESENT_N` PC1→PC2, `BU_WORK_N` PC2→PA0, `DOOR_CLOSED_N` PC3→PA1,
  `FLOW_TIM` PA1→PA2 (TIM2_CH3) y `NTC_ADC` PA0→PA3 (ADC1_IN4).
- Cambios de pin del ESP32-S3: `ESP_TX_RAW` IO17→IO42, `STM_TO_ESP`
  IO18→IO2 y `USB_VBUS_SENSE` IO21→IO15. R213–R218 pasan a una fila bajo J104.
- Ruteados el bus de sensores y todo el ESP32 con el frontal. Las subidas de
  `BREW_SLEEP_INTERLOCK` y `WATCHDOG_KICK_RAW` junto al supervisor pasan a
  In2.Cu. Se quitan los saltos que solo cruzaban la espina de 3,3 V.
- ERC 0; netlist nativa 187 componentes / 612 pines coincidente;
  `check_controller_core.py` actualizado. DRC con todas las severidades:
  0 infracciones, 0 conexiones abiertas y las tres diferencias de paridad de
  MH1–MH3. 1 244 segmentos y 274 vías. No libera fabricación ni conexión a red.

## JP17 RAST 5 y revisión de conectores, 2026-09-24

- Relectura con nonio de las fotos de `photos/Conectores/` frente a los planos
  JST: ninguna carcasa de señal tiene el ancho de XH ni de PH, JP24 mide 10,0 mm
  (VHR-2N 7,86 mm) y JP8 12,9 mm (VHR-3N 11,82 mm). Sus huellas quedan como
  provisionales; detalle en [photos.md](HD8911/photos.md).
- JP17: el propietario identificó la carcasa del mazo como TE 2-1241961-7 (RAST 5,
  tres vías, polarización 1b). J118 pasa de JST B3P-VH a TE 1971845-3 (LCSC
  C5169636, 233 en JLCPCB), con huella nueva según el plano C-1971845 rev. B10,
  a ras del borde en (107,5; 126,55). Se rehacen la fase, el neutro hacia JP24,
  JP19 y PS701 y la serigrafía de la zona.
- ERC 0; netlist 187 componentes / 612 pines coincidente. DRC con todas las
  severidades: 0 infracciones, 0 conexiones abiertas y las tres diferencias de
  paridad de MH1–MH3. 1 268 segmentos y 441 vías. Pendiente: comprobar con una
  muestra la codificación 1C/2D contra la carcasa del mazo. No libera
  fabricación ni conexión a red.

## Conectores de JP3, JP5, JP13, JP8 y JP24, 2026-09-29

- El propietario identificó las cabeceras: HR A2506WV-05P, -03P y -02P para JP3,
  JP5 y JP13 (C382535, C382533 y C382532) y LEOCO 3941P03*000 y 5001P020013 para
  JP8 y JP24, que JLCPCB no tiene. Stock JLCPCB consultado el mismo día por la
  API de lista de componentes, solo lectura: 3, 0 y 700 unidades.
- Cinco huellas nuevas en `OpenSaeco.pretty`, desde los planos A2506WV-XP
  rev. B5, 394105S rev. F y 500101S rev. D. El pad 1 queda en el circuito 1 de
  cada plano; en las LEOCO se lee del alzado en tercer diedro.
- J105, J113 y J115 conservan su origen y su cobre. J106 se corre 0,3 mm al oeste
  para despejar el courtyard de U702. J117 pasa a 5 mm entre pines, centrado
  0,5 mm al este del JP24 fotografiado; el neutro sale de la mitad sur de su
  pad 2 para quedar a 2,5 mm de la fase. La marca L de JP17 pasa al este de la
  lengüeta 1.
- `check_controller_core.py` admite piezas del propietario sin stock o sin código
  JLCPCB, siempre con su estado explícito en el catálogo. La comprobación de
  frescura del stock falla hoy en piezas no tocadas (consultas del 2026-09-16 al
  2026-09-22, más de 7 días); con esa fecha fijada al 2026-09-23 pasa todo lo
  demás.
- ERC 0; netlist 187 componentes / 612 pines coincidente. DRC con todas las
  severidades: 0 infracciones, 0 conexiones abiertas y las tres diferencias de
  paridad de MH1–MH3. 1 268 segmentos y 441 vías. Pendiente: probar cada mazo
  en su cabecera, sobre todo el sentido del gancho de JP8, que fija la
  polaridad del molinillo. No libera fabricación ni conexión a red.

## Revisión de la documentación, 2026-09-29

Relectura de todos los documentos contra el esquema, la BOM, la PCB y los
informes de validación. Se corrigieron, entre otros:

- Estados anteriores al ruteo: 135–159 huellas, conexiones sin rutear, «esquema
  parcial», etapas de red «sin dibujar», rellenos y serigrafía pendientes. La
  principal tiene 187 posiciones y está ruteada con DRC limpio.
- Pines: el caudalímetro va a PA2 (TIM2_CH3) y el nivel de agua a PC3
  (ADC12_IN9), no a PA1/PA2; la UART del ESP32 va en IO42/IO2 y la detección de
  VBUS en IO15, no en IO17/IO18/IO21; la corriente del grupo se lee en PC0.
  `connectors.csv` e `io-map.md` recogen ya el pin de cada conector.
- Notas del propio esquema («borrador parcial», módulo de red «sin
  seleccionar») y el texto que `validate_kicad.py` escribe en los README de
  validación, que ahora toma el recuento de ruteo de `routing.json`.
- Código del ESP32 en el catálogo de montaje (C2980300), optotriac VOT8125
  descartado, BOM (180 de 187 con código LCSC) y medida de 27,5 Ω del calentador,
  que faltaba en el registro de medidas.
- Se confirmó con la hoja de Mean Well que la IRM-30-24 da 1,3 A y 31,2 W.

Hallazgo de diseño, sin cambiar: J101 comparte nodo con la salida de U303 sin
diodo ni selector, así que usar J101 con o sin 24 V presentes queda por revisar.
ERC 0; netlist 187/612 coincidente; enlaces de la documentación comprobados.

## Conector del frontal Würth WR-MM, 2026-10-01

El propietario identificó el conector del enlace entre la principal y el frontal
como Würth WR-MM 690367181672 (16 contactos a 1,27 mm al tresbolillo), el mismo
en las dos placas, con el cable original plano 1:1 de 16 hilos. El pestillo del
cable entra en un taladro de 1,5 mm junto al pin 1. Sustituye al IDC 2×8 en J104 y J1.

- Huella `OpenSaeco:Wurth_WR-MM_690367181672_2x08_P1.27mm_Vertical` del plano Würth
  rev 002.000, en las dos bibliotecas, con modelo 3D simplificado (22,32 × 5 ×
  6,1 mm). Catálogo: JLC C19103863, Extended, sin stock el 2026-10-01.
- Principal: J104 gira 180° con el pin 1 en (6,2; 6,5); los impares no se mueven y
  los pares van 1,27 mm al este. Se reencaminan 3V3_UI (al oeste del taladro del
  pestillo), DC, BL, SDA, SCL e INT. 1 315 segmentos y 439 vías.
- Frontal: J1 se centra en la zona del JP3 original; C3 sigue junto al pin 1.
  Freerouting: 297 segmentos y 192 vías. Gerber, BOM y CPL regenerados.
- ERC 0 en las dos placas; netlists 187/612 y 42/118 coincidentes. DRC con todas
  las severidades: principal 0 infracciones, 0 sin conectar y paridad solo MH1–MH3;
  frontal 0/0/0.
- El recuento fotográfico de 20 contactos en JP21 era un error. Pendiente:
  presentar el cable y comprobar que el pestillo entra en el taladro de las dos
  placas nuevas.

## Resistencias Basic para el límite del puente H, 2026-10-01

R510 (IPROPI) pasa de 2,49 kΩ (C22908) a 2,4 kΩ (C22940) y R508 (VREF, lado alto)
de 16 kΩ (C4210) a 18 kΩ (C25810, la misma de R303). Las dos anteriores pasaron a
Extended en JLCPCB; las nuevas son Basic y R509 sigue en 49,9 kΩ.

- VREF = 3,3 × 49,9 / 67,9 ≈ 2,425 V (antes 2,498 V); con 1 000 µA/A,
  I_TRIP ≈ 2,425 / 2,4 ≈ 1,01 A (antes 1,00 A). IPROPI ≈ 1,2 V a 0,5 A.
- Misma huella 0603: colocación y ruteo intactos; solo cambian valor y campos.
- ERC 0; netlist 187/612; DRC con todas las severidades: 0 infracciones,
  0 sin conectar y paridad solo MH1–MH3. El límite sigue pendiente de medir.

## Divisor Basic del buck de 12 V, 2026-10-01

Revisión de todas las resistencias Extended del catálogo. Solo quedaban dos:

- R302/R303 (realimentación de U303, AP63200): 249 kΩ (C22918, Extended)/18 kΩ
  pasan a 330 kΩ (C23137)/24 kΩ (C23352), ambas Basic. Ecuación 6 de la hoja Diodes:
  V_OUT = 0,8 × (1 + 330/24) = 11,80 V, frente a 11,87 V. C314 sigue en 56 pF,
  dentro de los 10–220 pF admitidos para el condensador de avance.
- R710, R712 y R721 (puertas de los triacs, lado de red) siguen como Panasonic
  ERJ-P08J391V Extended: necesitan 500 V de tensión límite y pulsos de 0,83 A, y
  las 1206 Basic son de película gruesa normal de unos 200 V.

Misma huella 0603: colocación y ruteo intactos. La salida de 12 V queda
pendiente de medir en banco, como antes.


## Pinout del STM32 y del UCC27517, pull-down del relé general, 2026-10-01

El [modelo de placa](../sim/README.md) (`tools/build_board_model.py`) comparó cada
símbolo con el pinout del fabricante y encontró tres errores en la principal:

- **U101, STM32G431RBT6**: los pads 12–29 seguían el LQFP64 de la serie F. El
  G431 tiene PA0–PA2 en 12–14, VSS/VDD en 15/16 y VSSA/VREF+/VDDA en 27–29
  (`STM32_open_pin_data` de ST, idéntico al símbolo `STM32G431R_6-8-B_Tx` de
  KiCad 10). En la placa ruteada VSS caía en `DOOR_CLOSED_N`, VDD en `FLOW_TIM` y
  VSSA, VREF+ y VDDA quedaban sin conectar.
- **U502, UCC27517DBVR**: el DBV es 1 VDD, 2 GND, 3 IN+, 4 IN−, 5 OUT (TI
  SLUSAY4D); el símbolo ponía la salida en el pad de VDD, unida al rail de 12 V.
- **`MAINS_ARM_RAW`** (PB7 → U603.1A) no tenía pull-down, a diferencia de las
  otras cinco órdenes. Se añade R722 = 10 kΩ (C25804, Basic).

Corrección:

- Las funciones del firmware no cambian salvo una: PA0 trabajo, PA1 puerta,
  PA2 caudal (TIM2_CH3), PA3 NTC, PA7 válvula y PC4 molinillo. El calentador pasa
  de PB10 (pin 30) a PC5 (pin 23) para dejar sitio a C107 junto a VREF+/VDDA.
- Ruteo: escapes de PA0–PA2 alrededor de VSS15/VDD16; VSS15, VSSA27 y VSS31 a
  vías interiores; VDD16 y VREF+/VDDA al anillo; C107 (10 nF) bajo los pads
  28/29; vía del nivel de agua desplazada; bajadas de PA7/PC4/PC5 al bus de
  órdenes; U502 reconectado (VDD desde C507/C508, IN+ desde R511/R512, OUT a
  R513); R722 junto a U603.1 con la vía de masa de C603.
- C102 queda al oeste de los escapes y desacopla VDD16 a través de los planos,
  y C109/C108 siguen en su columna como bulk analógico. Es menos local que antes:
  revisar en la comprobación 1:1.
- `check_controller_core.py` tenía la misma tabla errónea de la serie F y se
  corrige con la de ST.

Resultado: ERC 0 en las dos placas; netlist 188/614; DRC con todas las
severidades: 0 infracciones, 0 sin conectar y paridad solo MH1–MH3; modelo de
placa 0 errores y 0 avisos. Sin hardware fabricado ni ensayado.

## Simulador F1 y MOSFET del relé y de los optos, 2026-10-05

F1 del [simulador](../sim/README.md): modelo DC por conmutación de las dos placas
desde los netlists, con los límites de cada CI y transistor en
`sim/reference/devices.json` (fuente por pieza), la regla `drive` en el peor caso
de los rails y el firmware del STM32 (controlador, BSP y bucle principal nuevos
sobre `osc_hal.h`) ejecutado en host contra la placa virtual, con U601 y una
planta sencilla.

Su primera pasada encontró un error en la principal:

- **Q701, Q705, Q706 y Q707** (relé K701 y LED de U701–U703) eran SI2308A con la
  puerta a 3,3 V desde U603/U604. UMW solo especifica RDS(on) a VGS = 4,5 V y
  10 V, y VGS(th) llega a 3 V a 250 µA: con 3,2 V de puerta no está garantizado
  que conduzcan los 17 mA de la bobina ni los 10 mA del LED (IFT 5 mA). Con los
  rails al mínimo, las cuatro órdenes de red quedaban indefinidas.

Corrección: los cuatro pasan a **BSS138LT1G** de onsemi (C82045, Extended; 550.029
en stock hoy): VGS(th) 0,5–1,5 V, 10 Ω como máximo a VGS = 2,75 V con ID < 200 mA
y 50 V de VDS para los 28 V del relé. Misma huella SOT-23 y mismo pinout
(1 G, 2 S, 3 D): colocación y ruteo intactos. Q501, la válvula, conserva el
SI2308A porque el UCC27517 le da 12 V de puerta. Márgenes en el peor caso: VGS
3,20 V ≥ 2,75 V, IF de los optos 9,5 mA ≥ 5 mA, bobina de K701 a 21,5 V ≥ 16,8 V.

Escenarios de F1 en verde: arranque en las dos esquinas, watchdog sin resets con
time-out de 0,9 s, reset de un núcleo colgado antes de 2,5 s, corte por el
interlock de las órdenes de un núcleo desbocado en el mismo paso, *dead battery*
de UCPD, caldera/NTC, grupo/IPROPI (2,4 V/A) y flancos del caudalímetro. La planta
usa valores supuestos donde falta caracterización.

Resultado: ERC 0 en las dos placas; netlist 188/614; DRC: 0 infracciones,
0 sin conectar y paridad solo MH1–MH3; modelo de placa 0 errores y 0 avisos;
tests de `tests/sim` 33/33 (24 de modelo y mutación, 9 de F1); CTest 2/2. Sin
hardware fabricado ni ensayado.

## Buffer Schmitt para el reset de los interlocks, 2026-10-05

La regla nueva `slow-edge` del simulador comprueba que las entradas lógicas sin
histéresis no cuelguen de una red RC lenta. Encontró un error en la principal:

- Las seis entradas de reset de U602–U604 (SN74LVC2G08) estaban en `STM_NRST`,
  que sube por R101 (10 kΩ ‖ el pull-up interno del STM32) contra C101 (100 nF):
  8,5 kΩ × 100 nF dan unos 530 µs/V en la transición. TI SCES198N pide como
  mucho 10 ns/V a 3,3 V y la entrada no tiene histéresis. Con una orden activa,
  el flanco de bajada de un reset de watchdog puede hacer oscilar la salida de
  la AND antes de quedar a cero. Ningún SN74LVC2G08 equivalente con entradas
  Schmitt cabe en la huella SM-8.

Corrección: **U605, SN74LVC1G17DBVR** (TI, C7836, Extended; 57.737 en stock hoy)
con C605 = 100 nF. Toma `STM_NRST` y entrega `STM_NRST_BUF` a las seis entradas;
VT+ ≤ 1,92 V y VT− ≥ 0,89 V a 3 V, sin límite de Δt/Δv. U601, R101, C101, el
STM32 y J102 siguen en `STM_NRST`. En la PCB, U605 va en el bolsillo bajo R603,
la columna del reset se corta en y = 61 mm y baja a B.Cu hasta la entrada de
U605; la salida retoma la columna hacia U602, U603 y U604. C605 queda al sur de
la orden del calentador. El chequeo de interlock acepta ahora `STM_NRST` a
través de buffers no inversores. Dos tests de mutación nuevos cubren la regla y
el interlock a través del buffer.

Resultado: ERC 0 en las dos placas; netlist 190/621; DRC con todas las
severidades: 0 infracciones, 0 sin conectar y paridad solo MH1–MH3 (1326
segmentos y 445 vías, 153 de cosido); modelo de placa 0 errores y 0 avisos;
`tests/sim` 35/35. Serigrafía, PDF 1:1 y render regenerados. Sin hardware
fabricado ni ensayado.

## J101 en OR con U303 y tres reglas nuevas del simulador, 2026-10-05

Reglas nuevas del modelo de placa: `back-feed` (una entrada de alimentación
externa no puede llegar por bobinas o fusibles al nodo de conmutación de un
buck), `pin-voltage` (ningún pin de MCU por encima de su máximo absoluto, con
los rails y VBUS al máximo) e `input-level` (cada entrada activa a cero lee sus
dos estados en las dos esquinas). Las dos últimas pasan sin cambios; la primera
encontró un error en la principal:

- **J101** estaba en `12V_ISO_RAW`, el nodo de salida de U303 (AP63200). Con la
  placa alimentada por J101 sin 24 V, L302 lleva esos 12 V al nodo SW con VIN
  sin alimentar: Diodes limita VSW a VIN + 0,3 V y el diodo interno del MOSFET
  alto devolvía tensión a `24V_ACT_RAW`. La documentación lo tenía como
  pregunta abierta.

Corrección: J101 pasa a `12V_BENCH_RAW` y entra a `12V_PROTECTED` por su propio
fusible F305 (1 A/72 V, el de F301) y Schottky D307 (SS34, el de D301), en OR con
U303 por F301/D301. D307 también bloquea la polaridad inversa. En la PCB, J101.1
pasa en B.Cu bajo la salida del buck hasta F305, y D307 llega al pad de C301;
las dos redes nuevas están en la clase Power.

Resultado: ERC 0 en las dos placas; netlist 192/625; DRC con todas las
severidades: 0 infracciones, 0 sin conectar y paridad solo MH1–MH3 (1333
segmentos y 443 vías, 150 de cosido); modelo de placa 0 errores y 0 avisos;
`tests/sim` 38/38. Sin hardware fabricado ni ensayado.

## TVS del rail de 12 V, 2026-10-05

La regla nueva `tvs` del modelo de placa compara cada TVS con su rail: VWM por
encima del máximo estable (`rail_range`) y VBR máxima por debajo del máximo
absoluto de cada pin de alimentación del rail (`abs_max` en
`sim/reference/devices.json`) y de las cargas externas (`external_limits`).
Encontró un error:

- **D302, SMAJ18A** en `12V_PROTECTED`: VBR de 20,0 a 22,1 V. El VDD de U502
  (UCC27517) admite 20 V como máximo absoluto (TI SLUSAY4D, 8.1) y el Digmesa de
  J106.3 se alimenta de 3,8 a 20 V; un transitorio entre 20 y 22 V no lo frenaba.

Corrección: **SMAJ15A** de Littelfuse (C148216, Extended; 5.699 en stock hoy):
VWM 15 V, por encima de los 12,5 V máximos del rail; VBR de 16,7 a 18,5 V y
VC 24,4 V a 16,4 A. A plena corriente de pico la pinza sigue pasando de 20 V; el
rail solo lo alimentan U303 y una fuente de banco certificada por J101, y la
pinza protege frente a los transitorios de baja energía del enchufe en caliente.
Misma huella SMA. La entrada `RAIL_12V` del contrato pasa a 15 V de fondo.

Resultado: ERC 0; netlist 192/625; DRC 0 infracciones y 0 sin conectar, paridad
solo MH1–MH3; modelo de placa 0 errores y 0 avisos; `tests/sim` 39/39.

## Potencia de las resistencias de LED de los optos, 2026-10-05

La regla nueva `resistor-power` compara la potencia de cada resistencia en el
peor estado (rails al máximo; órdenes activas, inactivas y en reset) con la
nominal de su pieza del catálogo o, si no la tiene, de su tamaño de huella, y
avisa por encima del 60 %. Encontró un error:

- **R709, R716 y R720** (1 kΩ en serie con el LED de U701–U703 desde
  `12V_PROTECTED`) eran UNI-ROYAL 0603WAF1001T5E de 100 mW y disipan hasta
  120 mW con 12,5 V.

Corrección: **ROHM ESR03EZPF1001** (C2653986, 1 kΩ 1 %, 0603 anti-sobretensión
de 250 mW, Extended; 68.914 en stock hoy). Misma huella; la PCB solo cambia de
campos. La corriente de los LED no cambia (9,5–11,5 mA). Las demás resistencias
quedan por debajo del 60 %.

Resultado: ERC 0; netlist 192/625; DRC 0 infracciones y 0 sin conectar, paridad
solo MH1–MH3; modelo de placa 0 errores y 0 avisos; `tests/sim` 40/40.

## U302 junto a J104, 2026-10-05

Se recupera el cambio que estaba sin commit en el árbol de trabajo antes de
traer `d059fb0` (guardado ese día en un stash): U302 (TPS22918) pasa del
bolsillo junto a PS701 a justo debajo de J104 (4,5 / 17 mm, girado 90°), con
C307, C308, C309 y R301 a su alrededor. `3V3_UI`, la alimentación conmutada del
frontal, pasa de unos 144 mm de 0,4 mm por el borde superior de la placa a unos
13 mm de 0,5 mm en F.Cu; lo que cruza ahora la placa es la orden lenta de PB12,
en B.Cu por y = 27,25 mm con dos vías. Sobre el ruteo actual, PB12 pasa además
al sur de las vías interiores de VSS27/VSS31 (y = 44,65 mm), que aparecieron con
la corrección del pinout del STM32.

Resultado: ERC 0; netlist 192/625; DRC con todas las severidades: 0 infracciones,
0 sin conectar y paridad solo MH1–MH3 (1318 segmentos y 444 vías, 149 de
cosido); modelo de placa 0 errores y 0 avisos. Serigrafía, PDF 1:1 y render
regenerados.

## Simulador F2, VREFINT y puerta del WDI, 2026-10-05

F2 del [simulador](../sim/README.md#f2-interfaz-frontal-y-protocolo):
[protocolo v0](../firmware/common/protocol.md) implementado y compartido por los
dos firmwares; núcleo portable del ESP32 (`firmware/esp32/core`: TCA9534 con
antirrebote, ST7789V no bloqueante, enlace y pantallas) sobre su HAL; el STM32
atiende el enlace y solo llega a SAFE_IDLE con él vivo; TCA9534 y ST7789V
virtuales en el frontal, que responden desde las tensiones del otro lado del
mazo; UART entre firmwares y detector de backfeed.

Encontró dos errores, uno de firmware y otro de circuito:

- **Medida de los rails**: el firmware escalaba con VREF = 3,3 V supuestos; con
  VDDA en 3,4 V (esquina alta del AP63203 más rizado) leía 12,13 V en un rail de
  12,5 V. Ahora mide VDDA contra VREFINT (ADC1_IN18) y su valor de fábrica a
  3,0 V (DS12589, 3.18.2).
- **U601 y el reset enclavado**: el TPS3828 sin sufijo A deja RESET en bajo para
  siempre si WDI recibe un pulso con RESET activo (TI SLVS165O, 7.3.4). Con WDI
  unido a PB4 y R602 a masa, un núcleo colgado con PB4 en alto o una bajada de
  tensión daban ese pulso al entrar el STM32 en reset: el escenario del watchdog
  quedaba en reset permanente. Corrección: **U606, SN74LVC1G132DBVR** (TI,
  C403723, Extended; 30.058 en stock hoy) y C606, con WDI = NAND(`STM_NRST`,
  impulso): durante el reset WDI queda en alto pase lo que pase en PB4. La versión
  A del supervisor no sirve porque su salida es push-pull y NRST necesita drenador
  abierto. Regla nueva `wdi-reset` con su test de mutación, y escenario de núcleo
  colgado con PB4 en alto y en bajo.

Resultado: ERC 0 en las dos placas; netlist 194/632; DRC con todas las
severidades: 0 infracciones, 0 sin conectar y paridad solo MH1–MH3 (1334
segmentos y 448 vías, 149 de cosido); modelo de placa 0 errores y 0 avisos;
`tests/sim` 53/53; CTest 3/3 (con el protocolo). Serigrafía, PDF 1:1 y render
regenerados. Sin hardware fabricado ni ensayado.

## Simulador F3: panel web local, 2026-10-05

`tools/sim_panel.py` sirve en 127.0.0.1 un panel de la máquina virtual con los
dos firmwares en tiempo real: frontal con teclas, LED y pantalla del ST7789V
virtual, estado de los dos núcleos, STATUS, cargas, planta, gráficas, registro
de eventos, inyección de fallos (puerta, grupo, NTC, nFAULT, cuelgues, teclado,
ruido UART, esquinas de los rails, sensor de agua) y VCD de las señales
digitales. Probado en el navegador integrado: arranque a SAFE_IDLE, puerta
abierta a FALLO en rojo, gráficas y descarga del VCD. Con un 5 % de bytes
corruptos en la UART el enlace llega a caer y el núcleo queda en FAULT hasta
CLEAR_FAULT, como prevé el protocolo. `tests/sim` 59/59. Sin hardware.

## Simulador F4: menús y puesta a punto, 2026-10-05

El ESP32 tiene menús de texto (inicio, MENU, puesta a punto, información) con
una fuente 5×7 propia, y el STM32 ejecuta siete pruebas de puesta a punto
(`firmware/stm32/src/service.c`) pedidas con TEST e informadas con TEST_REPORT:
entradas y sensores, ciclo del grupo (tiempo de ida, I0, pico de arranque,
corriente al tope, vuelta, fallos del DRV8876), válvula, relé K701, bomba con
calibración del caudalímetro, calentador hasta una consigna con la
sobreoscilación, y molinillo. STATUS crece a 18 bytes con la temperatura de la
caldera. El panel dibuja la cafetera con la orden de cada pin y la carga
realmente alimentada según el netlist.

Lo que el simulador encontró en el firmware nuevo, corregido con su escenario:

- Con la puerta abierta a mitad de prueba el núcleo pasaba a FAULT antes que
  la prueba y el informe decía "estado" en vez de "puerta". Ahora el motivo es
  la causa que vio el núcleo (puerta o nFAULT).
- El ciclo del grupo tardaba ~5 s con el rail de 24 V en su mínimo (planta
  supuesta) frente a 6 s de tiempo máximo: margen del 20 %. Ahora 10 s; a rotor
  bloqueado el motor consume V/R ≈ 0,44 A, por debajo del I_TRIP de ~1 A.
- La bomba tenía 10 s como máximo, por debajo de los 20 s de 100 ml a 5 ml/s:
  ahora 30 s. Textos de más de 26 caracteres en la pantalla y un `snprintf` que
  GCC marcaba como truncable, corregidos.

No apareció ningún error de circuito: con las pruebas moviendo cada carga, las
reglas del modelo (accionamiento, back-feed, potencias, niveles) siguen a cero.

Medidas que la placa no puede hacer: las corrientes de red (calentador, bomba,
molinillo) y la de la válvula. Las pruebas fijan tiempo y ventana para medirlas
con pinza en la caracterización.

Resultado: modelo de placa 0 errores y 0 avisos; `tests/sim` 71/71 (12 de F4);
CTest 3/3; GCC 15 con `-Wall -Wextra -Werror -pedantic` sin avisos. Probado en
el navegador integrado: ciclo del grupo y bomba con K701, triac, caudal y el
informe en vivo. Sin hardware.

## Corriente del molinillo y prueba de dosis, 2026-10-06

A petición del propietario, la placa mide la corriente del molinillo para
saber cuándo falta grano (el motor gira en vacío) o se bloquean las muelas.
Detalle en [power-architecture.md](../hardware/power/power-architecture.md#corriente-del-molinillo)
y [layout.md](../hardware/controller/layout.md#corriente-del-molinillo).

- **U704**, TI TMCS1133B4AQDVGR (C36873216, Extended, 163 en stock hoy;
  alternativa TMCS1123B4AQDVGR, C30955591): Hall con aislamiento reforzado de
  5 kVrms en la línea + de JP8, 100 mV/A sobre VS/2. Cruza la barrera bajo
  U702 con el patrón HV de TI (8,1 mm entre filas). Para que su patio de
  11,9 mm cupiera, J106 (JP5) pasa 1,2 mm al oeste, J105 (JP13) 0,25 mm y
  BR701 0,75 mm al este; J106 queda a 1,5 mm de la foto, dentro de la
  incertidumbre asignada.
- La salida llega a **PA6** (ADC2_IN3, de la tabla 13 de DS12589) por R412 y
  C407 (1,6 kHz) junto al STM32: unos 150 mm y dos vías, rodeando por el
  oeste el bus de órdenes y el tronco de 24 V, que cierran el sur del MCU.
- Firmware: muestreo cada 1 ms y media por tick; cero con el motor parado;
  bloqueo por encima de 2 A, falta de grano por debajo de 550 mA o del 75 %
  de la corriente con carga. Nueva prueba **Dosis**: muele, prensa con el
  grupo y comprueba que la corriente al prensar sube al menos 40 mA sobre I0
  (manual: +55 a 200 mA). Umbrales supuestos hasta GR-02/03/08 y BU-05.
  STATUS pasa a 20 bytes con la corriente del molinillo.

Lo que encontraron las comprobaciones, corregido con su prueba:

- El modelo de placa dio `GRINDER_EN no llega a J115.1` en cuanto U704 se
  puso en la línea: el modelo no sabía que su entrada es un conductor. Ahora
  `hall_current` lo une, y la comprobación `hall` falla si JP8 no está en
  serie con el sensor o si VS no tiene alimentación (dos pruebas de mutación).
- Los motivos de la pantalla de prueba se cortaban a 18 caracteres tras
  «Motivo: »: «límite de temperatura» ya salía truncado. Acortados, con una
  prueba que los mide.
- La comprobación de dosis medía I0 sobre todo el recorrido, prensado
  incluido, y con 3 s de molido (3,6 g) la subida quedaba en 41 mA frente a
  15 mA sin café. Ahora I0 sale del primer segundo y la prueba muele 6 s por
  defecto: 107 mA con café frente a 21 mA sin él.

Resultado: ERC 0; netlist 198 componentes y 648 pines; DRC con todas las
severidades: 0 infracciones, 0 sin conectar y paridad solo MH1–MH3 (1360
segmentos y 452 vías, 147 de cosido); modelo de placa 0 errores y 0 avisos;
`tests/sim` 83/83; CTest 3/3; GCC 15 sin avisos. Serigrafía, PDF 1:1 y render
regenerados. Panel probado en el navegador integrado con la prueba de dosis.
Sin hardware.

## Poder de corte de los fusibles de red, 2026-10-06

Corrección de la [issue #1](https://github.com/itorralbo/open-saeco-controller/issues/1),
con los matices de la revisión del propietario. F703, el fusible del
molinillo, era un JDT JFC2410-1400TS con 50 A de poder de corte a 250 V, y lo
que tiene que despejar es un diodo de BR701 en corto, un camino de baja
impedancia entre fase y neutro a través de Q708. En un cortocircuito el
fusible más pequeño del lazo abre primero y tiene que interrumpir solo la
corriente: F701 aguas arriba no lo sustituye. F702 tenía el mismo problema en
la entrada de PS701, y F701 no tenía pieza.

Corrección:

- **Hipótesis de corriente de defecto**: 1500 A a 250 VAC, el nivel «H» de
  IEC 60127-2, en `mains.prospective_fault` del contrato. No es un máximo
  medido ni normalizado y queda para la revisión de seguridad.
- **F703**: Littelfuse 0215004.MXEP (C178840, 974 en stock hoy), T4A de
  5 × 20 mm cerámico axial, 1500 A a 250 VAC (hoja 215, rev. 01/12/17). Va de
  pie con una huella nueva, `Fuse_Littelfuse_0215_5x20mm_Axial_Vertical_P5.08mm`,
  porque entre Q708 y J115 solo quedaban 4,65 mm. J115 baja 1,35 mm, BR701
  1,2 mm, la puerta de la bomba pasa a y = 117,2 mm y la etiqueta de JP8
  1,7 mm.
- **F701 y F702**: Littelfuse 0215010.MXP (C142733) y 0215001.MXP (C142715),
  1500 A a 250 VAC, cada uno en dos pinzas Littelfuse 01110501Z (C151075, «hasta
  10 A»). Huella sin cambios.
- **Regla nueva `fuse-breaking`** del modelo de placa: recorre fase y neutro a
  través de fusibles, contactos, triacs, puentes y el conductor de U704, y
  falla si un fusible de ese lado corta menos de la corriente supuesta o no
  tiene su poder de corte en `sim/reference/devices.json`. Dos pruebas de
  mutación: F703 de vuelta al JFC2410 y F701 sin pieza.

Lo que no queda demostrado y sigue abierto en la issue:

- **Protección del puente**: el I²t de fusión nominal de F703 (46,96 A²s a
  10 In) supera los 35 A²s del KBP410; un corto en el lado de continua puede
  destruir el puente antes de que abra el fusible. Para el BTA24 (340 A²s) falta
  el I²t de despeje.
- **Selectividad F703/F701**: los I²t de fusión nominales están en 1 : 7,1, pero
  el I²t de despeje a la corriente de fallo no está publicado.
- **Valor de F702** frente a la irrupción del IRM-30 (PS-03). El **margen de
  carga de F701**, con pinzas de 10 A frente a 8,4–9,2 A solo del calentador,
  se cerró el mismo día (ver abajo).
- **Ensayo de interrupción** (PS-04, en laboratorio). El propietario confirmó el
  mismo día que el mazo de JP8 llega de sobra 1,35 mm más al sur.

Las fotos de la original (F1 y F2 de clase H, sin fusible del molinillo y con un
puente de 1N400x) respaldan la hipótesis de 1500 A y que se acepte el requisito 2
como en la original; ver [fotos](HD8911/photos.md#fusibles-y-puente-del-molinillo-2026-10-06).

Resultado: ERC 0 en las dos placas; netlist 198 componentes y 648 pines; DRC
con todas las severidades: 0 infracciones, 0 sin conectar y paridad solo
MH1–MH3; modelo de placa 0 errores y 0 avisos; `tests/sim` 85/85. Serigrafía,
modelos 3D, PDF 1:1, mapa de conectores y render regenerados. Sin hardware
fabricado ni ensayado.

## F701 de 12 A como el F1 original, 2026-10-06

El propietario leyó «12AH250V» en el F1 de la placa original, que tuvo que
desmontar, y «T2AH250…» en F2 ([fotos](HD8911/photos.md#lectura-del-propietario-sobre-la-pieza-2026-10-06)).
El fabricante dio 12 A al mismo calentador, y el F701 de 10 A en pinzas de 10 A
no dejaba margen sobre sus 8,4–9,2 A.

- **F701**: Littelfuse **0215012.MXEP** (C142789, 556 en stock hoy), T12AH, de
  1500 A a 250 VAC. Como pasa de los 10 A de las pinzas Littelfuse 111 501, va
  soldado en horizontal con patillas axiales, igual que el F1 original, con la
  huella nueva `Fuse_Littelfuse_0215_5x20mm_Axial_Horizontal_P27.50mm`. El pad 1
  cae en el extremo de la subida de fase, en (96,5; 74), y el pad 2, a 0,4 mm
  del courtyard de K701, llega a la fase protegida. Desaparece el tramo de unos
  10 mm de fase solo en F.Cu hasta las pinzas; quedan 3 mm. El 0215010.MXP pasa
  a sustituido en el catálogo.
- Con el reparto de molido la carga ronda 9,7 A a 230 V, el 81 % de F701. La
  relación de I²t de fusión nominales con F703 sube de 7,1 a 11; la
  selectividad sigue sin demostrar por falta del I²t de despeje.

Resultado: ERC 0 en las dos placas; netlist 198 componentes y 648 pines; DRC
con todas las severidades: 0 infracciones, 0 sin conectar y paridad solo
MH1–MH3; modelo de placa 0 errores y 0 avisos; `tests/sim` 85/85; CTest 3/3.
Modelos 3D, PDF 1:1, mapa de conectores y render regenerados. Sin hardware.

## F702 de 2 A y cierre de la issue #1, 2026-10-07

El propietario decidió los puntos que quedaban abiertos de la issue #1 (ver
[corriente de defecto supuesta](../hardware/power/power-architecture.md#corriente-de-defecto-supuesta-y-fusibles-de-red)):

- **Hipótesis de 1500 A aceptada** como base de diseño. Es la clase H de los
  fusibles de la original, y la impedancia de bucle de una vivienda la deja
  por debajo de 1500 A salvo junto al cuadro (ITC-BT-17: 4,5 kA en el
  interruptor general). Por encima, el automático de 16 A respalda en su zona
  magnética. Medir la impedancia de bucle fase-neutro del enchufe queda como
  confirmación opcional.
- **Requisito 2 aceptado** (2026-10-06): un corto en continua puede destruir
  BR701 antes de que abra F703, como en la original.
- **Requisito 1** acreditado con la certificación IEC 60127-2 de cada
  referencia (Semko 1517218 de 0,125 a 12 A; VDE 40013521 de 0,2 a 8 A), no
  con un ensayo propio. **Selectividad F703/F701 no exigida**: la original no
  la tenía. PS-04 pasa a ensayo opcional.
- **F702**: Littelfuse **0215002.MXP** (C142716, 1819 en stock hoy), T2AH de
  1500 A a 250 VAC, como el F2 original, en las mismas pinzas 01110501Z. La
  irrupción del IRM-30 (45 A típicos, duración sin publicar) se estima en
  0,3–0,5 A²s, el 3–4 % de sus 11,68 A²s de fusión nominal, frente al 20–33 %
  del 0215001.MXP de 1 A, que pasa a sustituido. PS-03 queda como
  confirmación.

Resultado: ERC 0 en las dos placas; netlist 198 componentes y 648 pines; DRC
con todas las severidades: 0 infracciones, 0 sin conectar y paridad solo
MH1–MH3; modelo de placa 0 errores y 0 avisos (la regla `fuse-breaking` lee
el nuevo F702); `tests/sim` 85/85; CTest 3/3. Solo cambian valor y pieza de
F702; huella y ruteo, igual. Sin hardware.

## Polaridad inversa en J112, 2026-10-07

Issue #6: J112.1 iba directo a `24V_ACT_RAW`. Con el cable de banco invertido,
−24 V llegaban a VIN y EN de U303 (AP63200, mínimo absoluto −0,3 V) y
polarizaban en directo D701 y el diodo interno de Q701; solo F303/D304 y
F304/D305 protegían sus ramas.

- **F306** (prosemi 1206TD-2A, C2838912) y **D308** (SS34, C2909963) entre
  J112.1 y `24V_ACT_RAW`, como F305/D307 en J101. F306 es de 2 A porque en banco
  lleva toda la placa (motor hasta 1 A de ITRIP, válvula 0,42 A y buck de
  12 V). PS701 sigue entrando por J121, que se abre antes de usar J112.
- **PCB**: los dos van de pie en la columna de 24 V de x = 112,5 mm, bajo J112.
  U303 y C310 toman el raíl por debajo de D308 y suben por B.Cu en
  x = 115,6 mm.
- **Regla `reverse-polarity`** en el modelo de placa: desde cada entrada de banco
  cableada a mano (`external_supplies.unkeyed`: J101.1 y J112.1) sigue
  fusibles y bobinas y falla si el cable invertido alcanza algo más que el ánodo
  de un diodo serie, un TVS a masa, resistencias, condensadores no polarizados,
  una bobina de relé o conectores. Sobre el diseño anterior señalaba D701.K,
  U303.EN y U303.VIN. Dos pruebas de mutación: J112 directo al raíl y D308
  invertido.
- **PS-05** nuevo en el plan de caracterización: inversión en banco con la
  fuente limitada y J121 abierto.

Resultado: ERC 0 en las dos placas; netlist 200 componentes y 652 pines; DRC
con todas las severidades: 0 infracciones, 0 sin conectar y paridad solo
MH1–MH3; modelo de placa 0 errores y 0 avisos; `tests/sim` 87/87; CTest 3/3.
PDF 1:1 y render regenerados. Sin hardware.

## J114 a prueba de resbalones, 2026-10-07

Issue #4: J114 llevaba GND, 3,3 V, 12 V, 24 V y los dos nodos ADC en pines
contiguos y sin resistencia. Un resbalón de la punta ponía 12 V en `3V3_CORE`
(2↔3), 24 V en `12V_PROTECTED` contra el SMAJ15A (3↔4) o 24 V en PF1 (4↔5).

- **Nuevo orden**: GND, sonda de 3,3 V, GND, sonda de 12 V, GND y sonda de
  24 V, con la serigrafía «G 3V3 G 12 G 24». Cada raíl llega por 10 kΩ en 0603
  (R723, R724 y R725, catálogo `R:10k`): un resbalón a masa son 2,4 mA y 58 mW
  a 24 V. Los nodos ADC se miden en C701 y C702.
- **PCB**: misma huella y posición. El 12 V se une en una vía sobre la cabecera
  y baja entre J114.3 y J114.4 a R701 y R724; PF1 baja entre J114.4 y J114.5;
  PC1 rodea J114.6 por B.Cu; la rama de 24 V termina en R725. De paso, J114 deja
  de solapar a C603 en el esquema.
- **Regla `probe-header`** en el modelo de placa (`probe_headers` del contrato:
  J114, 1 kΩ mínimo): falla si dos pines contiguos llevan tensiones distintas o
  si un pin de raíl llega a algo sin una resistencia serie suficiente. Sobre el
  diseño anterior señala los cuatro pares contiguos y los seis pines directos.
  Tres pruebas de mutación. La telemetría del contrato pasa a seguirse desde
  R701.1 y R704.1 en lugar de J114.5/J114.6.

Resultado: ERC 0 en las dos placas; netlist 203 componentes y 658 pines; DRC
con todas las severidades: 0 infracciones, 0 sin conectar y paridad solo
MH1–MH3; modelo de placa 0 errores y 0 avisos; `tests/sim` 90/90; CTest 3/3.
PDF 1:1 y render regenerados. Sin hardware.

## Condensadores de entrada de los bucks, 2026-10-07

Issue #3: el bulk de entrada de U301, C301, estaba a unos 30 mm de pista de VIN,
y U303 tenía un solo condensador, C310, a 8,3 mm, con la masa por dos vías y el
plano. Diodes (DS41326) pide los condensadores de VIN tan cerca del integrado
como sea posible.

- **U301**: **C315** nuevo, 10 µF/50 V X7R 1206 (`C:10uF_50V_1206`, el mismo
  que C310), justo detrás de C302, a unos 5 mm de pista de VIN, con la vía de
  masa al este de su pad. C301 sigue como bulk del raíl junto a D301/D307.
- **U303**: **C316** nuevo, 100 nF/50 V, entre los pines 3 y 4 a 1,7 mm, y C310
  bajo él a unos 4 mm. La troncal entra primero en C310, después en C316 y
  luego en los pines. Las masas vuelven al pin 4 por F.Cu, con una sola vía al
  plano pasado C310.
- **`tools/check_controller_pcb.py`**: comprobación geométrica nueva que se
  ejecuta con el Python de KiCad. Para U301 y U303 exige un condensador de bulk
  (≥ 4,7 µF) a menos de 5 mm de VIN y de GND, y uno de alta frecuencia
  (≤ 1 µF) a menos de 3 mm, medidos en línea recta de pin a pad. Con
  `--self-test` mueve C315, C316 y C310 en memoria y comprueba que cada caso
  falla. Sobre la placa anterior señalaba C301 a 16,5 mm de U301 y U303 sin
  condensador de alta frecuencia.
- **Pendiente**: la capacidad efectiva a 12 V y 24 V no se ha leído en la curva
  de polarización de Samsung, y el rizado de VIN en los pines durante el
  arranque y los escalones de carga está sin medir. Un DRC limpio no valida
  estabilidad ni EMI.

Resultado: ERC 0 en las dos placas; netlist 205 componentes y 662 pines; DRC
con todas las severidades: 0 infracciones, 0 sin conectar y paridad solo
MH1–MH3; `check_controller_pcb.py --self-test` pasa; modelo de placa 0 errores y
0 avisos; `tests/sim` 90/90; CTest 3/3. Sin hardware.

## Bypass de VM del DRV8876, 2026-10-07

Issue #5: C502 (100 nF, bypass de VM) estaba a 11,2 mm de cobre del pin 11 y su
masa volvía al plano por una vía en (38,2; 48,0). El lazo encerraba unos
6 × 8 mm. TI (SLVSDS7, §10.1) pide el bypass de VM tan cerca del integrado como
sea posible.

- Bajo el pin 11 no cabe un condensador: OUT2, VM, VCP, CPH y CPL salen de
  pines contiguos a 0,65 mm, y la bomba de carga (C503 a 3,6 mm y C504 a
  5,5 mm) ya ocupa el hueco inmediato. Como pedía la revisión, se conservan sus
  lazos.
- **C502** pasa a (31,85; 44,9), colgado del nodo de VM bajo C503: unos 5,4 mm
  de cobre desde el pin 11. Su masa baja al plano por una vía propia a 1,1 mm
  del pad. El lazo queda en unos 3 × 4,5 mm. OUT2 gira primero al oeste por
  y = 41,9 mm para dejarle sitio.
- **VM** sale con el ancho del pad (0,3 mm) y pasa a 0,5 mm en cuanto deja la
  fila. Como señalaba la revisión, ensanchar hasta el propio pin invadiría la
  separación con VCP (clase Switching, 0,25 mm).
- **`check_controller_pcb.py`** gana U501: un condensador de ≤ 1 µF entre VM y
  PGND a menos de 6 mm de los pines 11 y 9. La prueba propia devuelve C502 a su
  sitio anterior y espera el fallo.
- **Pendiente**: VM en arranque, inversión y frenado y la limitación de
  corriente con el motor real (BU-0x), y si el bulk absorbe la energía que D304
  no deja volver a la fuente.

Resultado: ERC 0 en las dos placas; DRC con todas las severidades: 0
infracciones, 0 sin conectar y paridad solo MH1–MH3; `check_controller_pcb.py
--self-test` pasa; modelo de placa 0 errores y 0 avisos; `tests/sim` 90/90;
CTest 3/3. Sin hardware.

## Límite de corriente en las alimentaciones que salen de la placa, 2026-10-07

Issue #8: J109.1 (JP22) salía directo de `3V3_CORE`, J106.3 (JP5) de
`12V_PROTECTED` y J104.1 (frontal) de U302, un TPS22918 sin límite de corriente
ni apagado térmico. Un corto en un mazo hundía el raíl de los dos MCU o podía
abrir F301, que no se rearma, y el reset no aislaba el frontal porque R301 lo
mantiene encendido.

- **J104.1**: U302 pasa a **TPS2553DBVR** (C55266). R304 = 49,9 kΩ fija
  475–565 mA (TI SLVS841F, 7.5), por debajo de 1,5 A del WR-MM y del límite de
  U301, con apagado térmico. R305 = 1 kΩ descarga `3V3_UI` como hacía el QOD
  del TPS22918 y gasta 3,3 mA. El arranque suave interno sustituye a C307, que
  se retira. FAULT queda sin conectar.
- **J109.1**: **U304**, otro TPS2553, con R306 = 210 kΩ (110–150 mA), C409 en
  la entrada y C410 junto al conector, bajo J113. El consumo del sensor sigue
  sin medir (WL-01); 110 mA es el mínimo garantizado.
- **J106.3**: **R413**, 390 Ω anti-surge de 0,66 W (`R:390_1206_500V`), con
  C408. Con menos de 8 mA, al Digmesa le quedan unos 7,9 V de los 3,8 V que
  necesita; un corto se queda en 32 mA y 0,4 W. Se descartó un regulador de
  corriente NSI45015: con 100 mm² de cobre (600 °C/W) un corto lo calentaba
  unos 135 °C. La rama de 12 V del LED de la bomba termina ahora en R413 y no en
  el pad de JP5.
- **Regla `offboard-supply`** en el modelo de placa (`offboard_supplies` del
  contrato: J104.1, J106.3 y J109.1, 100 Ω mínimo): cada salida debe venir de un
  interruptor con `current_limited` en `devices.json` o solo a través de
  resistencias suficientes. Tres pruebas de mutación: J106.3 y J109.1 de vuelta
  a sus raíles y U302 de vuelta al TPS22918. El simulador acepta ahora los dos
  juegos de nombres de pin de un interruptor de carga (VIN/ON/VOUT e IN/EN/OUT).
- **PS-08** nuevo: cortos de 5 s en cada salida, comprobando que los raíles no
  caen, que ningún MCU se reinicia y que F301 sigue entero.

Resultado: ERC 0 en las dos placas; netlist 212 componentes y 680 pines; DRC
con todas las severidades: 0 infracciones, 0 sin conectar y paridad solo
MH1–MH3; `check_controller_pcb.py --self-test` pasa; modelo de placa 0 errores y
0 avisos; `tests/sim` 94/94; CTest 3/3. Sin hardware.

## Disipador de los triacs y limitación térmica del calentador, 2026-10-07

Issue #2: el diseño pedía ≈ 5 °C/W al disipador, pero el perfil reservado
(33 × 21 × 35 mm) solo da del orden de 6–8 °C/W. Con 8 °C/W, Q703 llega a 125 °C
en continuo con 39 °C de aire a 253 V. El propietario decidió mantener el
volumen y limitar el calentador por temperatura.

- **Clase del perfil**: ≈ 8 °C/W. El Fischer SK 657 de 37,5 mm (36,8 × 25 mm,
  algo mayor que el hueco) da 7,75 K/W anodizado en negro y vertical. La
  referencia exacta queda para la mecánica.
- **RT701** (Murata NCP18XH103F03RB, C13564), R726 (10 kΩ) y C704 (100 nF) en el
  borde SELV de la barrera, sobre la columna del disipador, hacia **PB14**
  (ADC1_IN5, añadido a `sim/reference/mcus.json` desde el XML de pines de ST).
  No toca el perfil, que solo está separado de la red por el aislamiento de los
  triacs. Señal `HEATSINK_AIR` en el contrato: el modelo de placa da
  0,03–0,07 °C/LSB entre 40 y 80 °C y 2,44–0,20 V entre 0 y 120 °C.
- **Firmware**: `osc_heatsink_step()` integra un modelo de primer orden del
  perfil (8 °C/W, 30 J/K) con la potencia de cada triac.
  `osc_heater_cycles_thermal()` quita ciclos al calentador por encima de 105 °C
  de unión estimada, hasta ninguno a 120 °C; con RT701 fuera de su ventana se
  supone aire a 70 °C. Las pruebas de CTest cubren un calentamiento corto en
  frío (sin limitar), una hora con aire a 60 °C y bomba (limitado, nunca
  apagado, por debajo del corte), el sensor caído y el corte. Simulado con aire
  a 25, 40, 50 y 60 °C, el ciclo en régimen es del 88, 70, 60 y 45 %, y la
  primera reducción llega a los 8,6, 4,4, 3 y 2 minutos.
- **TH-03** nuevo: descalcificación y vapor con termopares en Q703, el perfil,
  RT701 y PS701 (carcasa y aire local) para fijar las constantes.

Resultado: ERC 0 en las dos placas; netlist 215 componentes y 686 pines; DRC
con todas las severidades: 0 infracciones, 0 sin conectar y paridad solo
MH1–MH3; `check_controller_pcb.py --self-test` pasa; modelo de placa 0 errores y
0 avisos; `tests/sim` 94/94; CTest 3/3. Sin hardware.

## C310 a 1210 por la polarización DC, 2026-10-07

Curvas de polarización DC del Component Library de Samsung (25 °C, 1 Vrms,
1 kHz), leídas con el navegador el 2026-10-07:

| Pieza | Uso | 0 V | 12 V | 24 V |
|---|---|---:|---:|---:|
| CL31B106KBHNNNE (10 µF/50 V X7R 1206) | C315; C310 hasta ahora | 10,8 µF | 5,0 µF | 2,27 µF |
| CL21A106KAYNNNE (10 µF/25 V X5R 0805) | C301 | 10,9 µF | 2,0 µF | — |
| CL10B104KB8NNNE (100 nF/50 V X7R 0603, equivalente de C316) | — | 102 nF | 95 nF | 76 nF |
| CL32B106KBJNNNE (10 µF/50 V X7R 1210) | C310 desde hoy | 10,8 µF | 7,9 µF | 4,8 µF |

- **C310** pasa a **CL32B106KBJNNNE** (C138687): duplica la capacidad
  efectiva en la entrada de U303. Va en (122,5; 9,85), con el ruteo y la vía de
  masa ajustados, y el logo de la serigrafía baja 0,5 mm para dejarle sitio.
- **C315** se queda en 1206: a 12 V da 5,0 µF, 2,5 veces lo que daba C301.
  Corrige lo dicho en la issue #3: trabajar al 24 % de la tensión nominal no
  evita perder la mitad.
- Las curvas son típicas; el rizado de VIN en los pines sigue pendiente de
  PS-07.

Resultado: ERC 0 en las dos placas; DRC con todas las severidades: 0
infracciones, 0 sin conectar y paridad solo MH1–MH3; `check_controller_pcb.py
--self-test` pasa; modelo de placa 0 errores y 0 avisos; `tests/sim` 94/94;
CTest 3/3. Sin hardware.

## Huellas DNP para polarizar JP22, 2026-10-07

Issue #7: con JP22 desconectado o un hilo roto, PC3 queda al aire. El valor
depende de la salida del sensor, que WL-01 todavía no ha medido, así que se
reservan las dos opciones sin montar:

- **R415**, 100 kΩ de `WATER_VCC` a `WATER_RAW` (pull-up, para una salida de
  colector abierto), y **R416**, 100 kΩ de `WATER_RAW` a GND (pull-down, para
  que una salida push-pull desconectada lea cero). 0603, en línea sobre J109.
- El generador admite `dnp=True`; la huella lleva el atributo DNP y KiCad lo
  marca en el netlist. El simulador deja fuera los componentes DNP, con una
  prueba que falla si los vuelve a cargar.
- `check_controller_core.py` comprueba sus redes; el paquete JLCPCB los lista
  como no montados.

La issue #7 sigue abierta: falta elegir cuál se monta y su valor tras WL-01, y
la comprobación de firmware del nivel «ausente».

Resultado: ERC 0 en las dos placas; netlist 217 componentes y 690 pines; DRC
con todas las severidades: 0 infracciones, 0 sin conectar y paridad solo
MH1–MH3; `check_controller_pcb.py --self-test` pasa; modelo de placa 0 errores y
0 avisos; `tests/sim` 95/95. Sin hardware.

## Huellas DNP para los snubbers de Q704 y Q708, 2026-10-07

Los dos triacs se dejaron sin snubber RC a la espera de medir el dV/dt en el
apagado (PU-03, GR-05). Si hiciera falta, no había sitio para añadirlo sin
rehacer la placa. Ahora las dos posiciones tienen huella sin montar entre A1 y
A2, en la cara inferior y bajo el pie del perfil, sin pieza elegida:

- **Q704**: C705 (1812, para un condensador de 1 kV o X2) y R727 (2512), sobre
  el triac, donde B.Cu estaba libre.
- **Q708**: C706 y R728, en un recorte de la esquina suroeste del bloque de
  `LOAD_L_ENABLED` en B.Cu. El calentador sigue bajando por x = 70,5–77,6 mm;
  se estima que unos 2 A de los 8,4 A pasan ahora por F.Cu al oeste del recorte.
  La termografía del primer ensayo con carga ya estaba prevista.
- Las redes `PUMP_SNUBBER` y `GRINDER_SNUBBER` son de clase `Mains`, así que
  el DRC aplica los 2,5 mm entre pistas de red y los 8 mm a SELV.
- `layout_controller_pcb.py` admite huellas en la cara inferior.
  `check_controller_core.py` comprueba las redes de las cuatro piezas, y el
  exportador no las cuenta como pendientes del pedido.

Resultado: ERC 0 en las dos placas; netlist 221 componentes y 698 pines; DRC
con todas las severidades: 0 infracciones, 0 sin conectar y paridad solo
MH1–MH3; `check_controller_pcb.py --self-test` pasa; modelo de placa 0 errores y
0 avisos; `tests/sim` 95/95. Sin hardware.

## Filtro EMI de la Rev A, 2026-10-08

La original filtra en tres sitios (IMG_1085): L5, un choque toroidal de modo
común en la entrada general; un choque de modo común («2030R5») con el X C83 en
la rama de su flyback; y L1/L2, choques de barra en serie con el molinillo. En
la principal nueva:

- La fuente es el IRM-30-24, que cumple la EN 55032 clase B, conducida y
  radiada, sin componentes externos (hoja IRM-30-SPEC de Mean Well). No hace
  falta el equivalente del filtro de la flyback.
- Los triacs se disparan en el cruce por cero (MOC3083). El ruido que queda es
  sobre todo el de las escobillas del molinillo.
- Un choque de modo común de 10 A en stock en JLCPCB, el TDK B82724V2103U040
  (C3211917; 3,3 mH, 9,2 mΩ, nominal a +70 °C), mide 33 × 23 × 30 mm. No hay
  sitio en el lado de red: donde la original tenía L5 está ahora el IRM-30, y el
  resto lo ocupan F701/F702, RV701, K701, el pie del perfil y los conectores.

Decisión del propietario: en la Rev A, un X2 en la entrada; el choque, en la
Rev B si la emisión conducida del prototipo lo pide.

- **C707**, Murata GA355XR7GB563KW06L (C161105): 56 nF, X2 de 250 VAC, 2220,
  entre `MAINS_L_FUSED` y `MAINS_N`, en la cara inferior bajo F701. Un X2
  radial de 7,5 mm (KNSCHA MPX104K31B3KN20600) no cabía junto a RV701 a 2,5 mm
  de la fase de entrada. Con 56 nF no hace falta resistencia de descarga: la
  EN 60335-1 solo la pide por encima de 0,1 µF.
- **C708**, DNP, 2220, sobre los bornes del motor del molinillo (J115.1 y
  J115.3), en la cara inferior bajo JP8, sin pieza elegida.
- EM-01 y EM-02 en el plan de caracterización: emisión conducida con LISN del
  prototipo y de la original. Deciden C708 y el choque de la Rev B.
- C707 es la única pieza montada en la cara inferior: el exportador lo avisa,
  porque obliga a pedir montaje a doble cara o a soldarla a mano.
- La serigrafía ya no trata los pads SMD de la cara inferior como obstáculos
  de la superior; las etiquetas no cambian.

Resultado: ERC 0 en las dos placas; netlist 223 componentes y 702 pines; DRC
con todas las severidades: 0 infracciones, 0 sin conectar y paridad solo
MH1–MH3; `check_controller_pcb.py --self-test` pasa; modelo de placa 0 errores y
0 avisos; `tests/sim` 95/95. Sin hardware.

## Suministro para el pedido y RV701, 2026-10-08

Stock refrescado para las 83 piezas del catálogo (`tools/refresh_jlc_stock.py`).
Sin stock en JLCPCB: U303, K701, J104/J1 (Würth WR-MM) y J106 (HR A2506WV-03P);
J113 (A2506WV-05P) tenía 3 y F702 9. LCSC tampoco tenía el relé ni las A2506,
y ya no vende la WR-MM.

- **U303** pasa a **AP63301WU-7** (C2158003, 5107 en stock): la versión de 3 A y
  PWM fijo de la familia del AP63200, con el mismo TSOT-23-6, el mismo patillaje
  (FB, EN, VIN, GND, SW, BST) y la misma referencia de 0,8 V, así que el divisor
  330 k/24 k sigue dando 11,80 V. Su límite de pico es 4,5 A típico y 4,9 A
  máximo (frente a 2,8/3,1 A), por debajo de los 6 A de saturación de L302
  (SRP7028A-100M). Máximos absolutos iguales: VIN y EN a 35 V.
- **K701** pasa a **G5RL-1A-E-HR DC24** (C397236, 639 en stock). Omron da a
  G5RL-1A-E, -E-LN, -E-HR y -E-TV8 el mismo plano y los mismos taladros. -E-HR
  y -E-TV8 son sus dos modelos de alta corriente de arranque, con la misma tabla
  de bobina (24 V, 1440 Ω, 70 % para operar); solo cambia el listado UL TV-8.
  El simulador lo detectó: con la referencia nueva no encontraba el modelo del
  relé y daba por paradas las cuatro órdenes de carga. Se actualizó
  `sim/reference/devices.json`.
- **RV701** es un **TDK B72214S0271K101** (S14K275, C7502584): 275 VAC,
  4,5 kA, 71 J, homologado UL, CSA y VDE. Su contorno (paso de 7,5 mm, disco de
  15,5 mm, 5,0 mm de grueso) es la huella que ya tenía la placa.
- Los dos exportadores sacan de la BOM y el CPL las piezas sin stock en la
  última consulta y las listan en `*-not-assembled.csv` para comprarlas aparte:
  hoy J104 y J106 en la principal y J1 en el frontal, todos THT. La CI falla si
  el paquete no sigue al stock; se probó devolviendo stock a J106.

Resultado: ERC 0 en las dos placas; DRC con todas las severidades: 0
infracciones, 0 sin conectar y paridad solo MH1–MH3; `check_controller_pcb.py
--self-test` pasa; modelo de placa 0 errores y 0 avisos; `tests/sim` 95/95.
Sin hardware.
