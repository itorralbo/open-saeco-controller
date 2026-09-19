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
- Red, bomba, calentador y molino quedan fuera de la principal de baja tensión
  hasta definir aislamiento, cortes independientes, protección y mecánica.

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
  `mechanical-source.json`, asigna posición y orientación a las 132 huellas y
  conserva MH1–MH3. El script también comprueba que los siete conectores no se
  desplacen al regenerar la PCB.
- JP8, JP19, JP24, JP17, JP1 y JP9 quedan como áreas de regla reservadas: no
  admiten huellas, pads, pistas, vías ni planos hasta incorporar la etapa de
  potencia correspondiente. J110 queda junto a la zona del conector rojo.
- U201 queda junto al borde superior y la zona de exclusión de su antena está
  libre. El DRC detectó las invasiones de la primera iteración y la colocación
  final registrada pasa con 0 infracciones.
- La PCB continúa sin cobre: 307 conexiones pendientes y tres avisos de paridad
  por los taladros mecánicos. La colocación habilita el routing; no libera
  fabricación.
