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
de los adaptadores de NTC, caudal, nivel y contactos. Los condensadores del buck
y los componentes de carga de bomba del DRV8876 están en su bloque, pero su
distancia final a cada pad se optimizará durante el routing.

## Barrera red/SELV verificable

La clase `Mains` agrupa L, N, fase tras fusibles y relé, bomba y bus del
molinillo. `controller-core-reva.kicad_dru` exige 8 mm de separación y de
creepage entre cualquier cobre `Mains` y cualquier red SELV, y 2,5 mm entre
pistas de redes `Mains` distintas. La separación de clase entre pads de red se
queda en 1,2 mm porque la fija el paso de 3,96 mm de los VH originales. Los
pines sin uso de conectores de red y los taladros sin red no cuentan como SELV.

Con la regla activa el DRC marca 95 infracciones, todas de la colocación actual:

| Pieza de red | Conflicto SELV | Consecuencia |
|---|---|---|
| F701, F702 | U501, C501, C503 y C504, a menos de 1 mm | el corredor de red del borde derecho no cabe junto al puente H |
| K701 | U601, U603, R601–R603, R802, R403/R404 y C401/C402 | los contactos de fase están en mitad de la zona lógica |
| J115 | C311, C312 y J121 | el bus del molinillo toca la salida del buck de 12 V |

Por tanto, no se rutea todavía ninguna red `Mains`: primero hay que recolocar
fusibles, MOV y relé en un dominio de red contiguo y apartar de él el puente H y
el buck de 12 V.

## Routing del STM32

Cada VSS baja al plano con su propia vía dentro del anillo de pads. Los VDD
(1/64, 13, 19/20, 32 y 48) se unen mediante un anillo de 3V3 en F.Cu bajo el
cuerpo del LQFP, y cada par VDD/VSS tiene su condensador fuera, en una esquina o
junto al par: C105/C111 arriba a la izquierda, C102 a la izquierda, C104 con el
bulk C106 arriba a la derecha, C103/C110 abajo a la derecha y la columna
C107/C109/C108 de VDDA/VREF+ bajo los pines 18–20.

Canales reservados para las señales:

- pines 7–10 (NRST y contactos): salida horizontal a la izquierda;
- pines 14–17 (NTC, caudal, nivel, corriente del grupo): en L escalonadas hacia
  abajo por x = 47,2–48,7 mm;
- pines 21–24 y 27: hacia abajo, a la derecha de la columna de VDDA;
- pines 42–44: a la derecha;
- pines 49–61 (SWD, watchdog, armado y BOOT0): hacia arriba.

El plano GND_UI de B.Cu es provisional: cubre el lado SELV, el filler lo aparta
8 mm de todo cobre de red y se rehará cuando se fije la frontera definitiva.

## Validación

- 155/158 huellas eléctricas colocadas; J115/JP8, J117/JP24 y J118/JP17 ocupan
  ya sus zonas originales. Faltan las huellas de JP19, JP1 y JP9. Contorno
  141,6 × 135,2 mm y MH1–MH3 preservados.
- DRC KiCad 10.0.6: 95 infracciones, todas de la barrera de red/SELV descrita
  arriba; ninguna procede del cobre ruteado ni del plano.
- USB, alimentación y desacoplo del STM32 y plano GND provisional: 93 segmentos y
  18 vías. La impedancia USB se verificará con el stack-up real antes de fabricar.
- 298 conexiones sin rutear y seis diferencias de paridad: los tres taladros
  mecánicos intencionales y los tres conectores aún sin huella.
- El keepout de antena del ESP32 está libre; esta comprobación se hace mediante
  la propia regla del footprint y falló durante la primera iteración hasta mover
  los componentes afectados.

Las referencias se dejan temporalmente en `F.Fab` para que la colocación densa no
genere conflictos de serigrafía. Se añadirán identificadores legibles de
conectores, polaridad, puntos de medida y seguridad después del routing.

## Siguiente paso

La frontera de red/SELV ya es una regla DRC. El siguiente paso es recolocar la
parte de red en un dominio contiguo hasta dejar esa regla sin infracciones,
reservando sitio para las etapas aisladas de calentador, bomba y molino y para
JP19/JP1/JP9. Solo entonces se rutearán la entrada de red y la alimentación
aislada. En paralelo pueden rutearse las señales del STM32 por los canales
reservados. No se generarán Gerbers mientras queden conexiones abiertas o la
revisión de aislamiento pendiente.
