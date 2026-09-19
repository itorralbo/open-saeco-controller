# Colocación de la principal Rev A

Estado: colocación mecánica de conectores y colocación funcional inicial, con
la fuente AC/DC y el corte general ya integrados, pero aún no fabricable. La fuente de verdad mecánica es
`mechanical-source.json`; `tools/layout_controller_pcb.py` consume sus
coordenadas, coloca las 155 huellas actuales y comprueba que los tres taladros aceptados
no se muevan.

![Vista superior de la colocación](preview/pcb-staging-top.png)

![Mapa mecánico de conectores](validation/main-connector-map.svg)

## Sustitución física de la placa original

La posición de los mazos ya no se decide por conveniencia eléctrica. Se ha
rectificado IMG_1098 con el contorno aceptado de 141,6 × 135,2 mm y se ha usado
IMG_1101 para confirmar el sentido de entrada lateral. Se fija esta relación:

| Original | Rev A | Borde | Origen de huella X/Y (mm) | Giro |
|---|---|---|---:|---:|
| JP21 | J104, enlace del frontal nuevo | superior | 6,2 / 6,5 | 90° |
| JP16 | J108, grupo y micros | izquierdo | 3,0 / 64,5 | 90° |
| JP14 | J107, puerta/cajón | izquierdo | 3,0 / 73,5 | 90° |
| JP3 | J113, electroválvula | inferior | 3,5 / 125,3 | 0° |
| JP22 | J109, nivel de agua | inferior | 19,0 / 128,2 | 0° |
| JP13 | J105, NTC | inferior | 29,0 / 125,3 | 0° |
| JP5 | J106, caudalímetro | inferior | 38,5 / 125,3 | 0° |

La incertidumbre de posición asignada es ±1,5 mm. J104 ocupa la zona de JP21,
pero no reproduce su interfaz: el IDC 2×8 nuevo es algo más ancho y enlaza con la
nueva placa frontal. J110 queda inmediatamente a su derecha, accesible desde el
mismo borde superior para las pruebas por ordenador.

JP8, JP19, JP24, JP17 y los dos FASTON de tierra son conectores obligatorios de
la principal completa. JP8, JP24 y JP17 ya tienen huella; las envolventes de
JP19 y los FASTON se protegen mediante áreas de regla hasta cerrar su geometría.
No son reservas para otra placa: forman parte de esta misma PCB de sustitución.

## Zonas funcionales

- Borde superior izquierdo: enlace al frontal en la zona de JP21, USB-C a su
  derecha y protección ESD.
- Parte superior: ESP32 con la antena orientada hacia el borde y toda la zona de
  exclusión del footprint libre de componentes y cobre.
- Superior central: lógica y regulación SELV; las entradas de 12/24 V se
  conservan como puntos de banco y J121 permite separar los 24 V internos.
- Borde derecho: corredor de entrada de red con los dos fusibles y el MOV.
- Cuadrante inferior derecho: módulo aislado IRM-30-24; sus pines AC miran al
  corredor de red y sus salidas de 24 V miran a la zona SELV.
- Centro e izquierda: STM32, desacoplo, reset, watchdog, relé general e
  interlock hardware. El buck AP63200 genera 12 V desde los 24 V internos.
- Lateral izquierdo: JP16 del grupo y JP14 de puerta/cajón en sus zonas originales.
- Borde inferior izquierdo: JP3, JP22, JP13 y JP5, con el mismo orden y sentido
  de entrada observados en la placa original.
- Zona inferior central: conectores originales de potencia. Se preservan las
  envolventes aún pendientes de JP19 y los dos FASTON de protección.

La frontera entre primario/red y SELV se trazará en la PCB antes de rutear más
señales. USB, frontal, sensores, STM32, ESP32 y depuración permanecerán íntegramente
en SELV. Las órdenes hacia las cargas de red cruzarán la frontera únicamente por
componentes de aislamiento y ningún plano de masa la atravesará.

La colocación mantiene separadas las redes conmutadas del puente H y la válvula
de los adaptadores de NTC, caudal, nivel y contactos. Los condensadores del buck,
los desacoplos de MCU y los componentes de carga de bomba del DRV8876 están en su
bloque, pero su distancia final a cada pad se optimizará durante el routing.

## Validación

- 155/158 huellas eléctricas colocadas; J115/JP8, J117/JP24 y J118/JP17 ocupan
  ya sus zonas originales. Faltan las huellas de JP19, JP1 y JP9. Contorno
  141,6 × 135,2 mm y MH1–MH3 preservados.
- DRC KiCad 10.0.6: 0 infracciones geométricas/de reglas.
- El bloque USB tiene 39 segmentos y 7 vías, sin infracciones DRC; su impedancia
  se verificará con el stack-up real antes de fabricar.
- 349 conexiones sin rutear y seis diferencias de paridad: los tres taladros
  mecánicos intencionales y los tres conectores aún sin huella.
- El keepout de antena del ESP32 está libre; esta comprobación se hace mediante
  la propia regla del footprint y falló durante la primera iteración hasta mover
  los componentes afectados.

Las referencias se dejan temporalmente en `F.Fab` para que la colocación densa no
genere conflictos de serigrafía. Se añadirán identificadores legibles de
conectores, polaridad, puntos de medida y seguridad después del routing.

## Siguiente paso

El siguiente paso es incorporar las etapas aisladas de calentador, bomba y
molino, cerrar las huellas de JP19/JP1/JP9 y convertir la frontera de red/SELV en
reglas y áreas de exclusión verificables. Después se podrán rutear primero la
entrada de red y la alimentación aislada. No se generarán Gerbers mientras
queden conexiones abiertas o la revisión de aislamiento pendiente.
