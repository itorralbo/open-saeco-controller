# Colocación de la principal Rev A

Estado: colocación mecánica de conectores y colocación funcional con la
distribución de la placa original, dominio de red contiguo, reserva del disipador
y barrera red/SELV comprobada por DRC; aún no fabricable. La fuente de verdad mecánica es
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

La distribución sigue la de la placa original: lógica arriba y a la izquierda,
red en el cuadrante inferior central y derecho, y el disipador de las cargas
encima de JP8/JP19/JP24.

- Borde superior izquierdo: enlace al frontal en la zona de JP21, USB-C a su
  derecha con la protección ESD, y el ESP32-S3-WROOM-1U junto a ambos. El
  conector U.FL del módulo queda arriba, hacia el borde.
- Superior central: STM32 con su desacoplo, reset y SWD, y debajo J114, F303/D304,
  el divisor de 24 V y las series del LCD. Más a la derecha, el buck de 3,3 V y el
  corte del frontal.
- Esquina superior derecha: entradas de banco J101/J112, buck AP63200 de 24 V a
  12 V y, debajo, el puente H DRV8876 con su columna de fallo, VREF e IPROPI.
- Lateral izquierdo: JP16 y JP14 en sus zonas originales, sus filtros, las
  cabeceras de depuración, el watchdog e interlock (U601/U602) y el mando del
  relé (U603, Q701, D701).
- Borde inferior izquierdo: JP3, JP22, JP13 y JP5 con su acondicionamiento y la
  etapa de válvula, en el mismo orden y sentido que en la original.
- Dominio de red, por debajo y a la derecha de la barrera: K701 con los contactos
  a la derecha de la barrera; F701, F702 y RV701 encima del disipador; y PS701 en
  vertical en el borde derecho, con las salidas de 24 V arriba (SELV) y los pines
  AC abajo, junto a J118. El paso de 6 mm entre el disipador y PS701 lleva L y
  PSU_L entre J118, los fusibles y PS701.
- Borde inferior central y derecho: conectores originales de potencia y las
  envolventes aún pendientes de JP19 y de los dos FASTON de protección.

USB, frontal, sensores, STM32, ESP32 y depuración permanecen íntegramente en
SELV. Las órdenes hacia las cargas de red cruzarán la frontera únicamente por
componentes de aislamiento y ningún plano de masa la atravesará.

## Barrera red/SELV verificable

La clase `Mains` agrupa L, N, fase tras fusibles y relé, bomba y bus del
molinillo. `controller-core-reva.kicad_dru` exige 8 mm de separación y de
creepage entre cualquier cobre `Mains` y cualquier red SELV, y 2,5 mm entre
pistas de redes `Mains` distintas. La separación de clase entre pads de red se
queda en 1,2 mm porque la fija el paso de 3,96 mm de los VH originales. Los
pines sin uso de conectores de red y los taladros sin red no cuentan como SELV.

`layout_controller_pcb.py` fija además la línea central de la barrera
(`MAINS_BARRIER`), que es una L: sube desde el borde inferior en x = 51 mm, entre
J106 y J115, hasta y = 60 mm, y cruza hacia el borde derecho por encima de
PS701. Alrededor de ella hay una banda de 8 mm en ambas capas sin pistas, vías,
pads ni rellenos. K701, PS701 y los futuros optoacopladores pueden atravesarla
porque su propio aislamiento cubre ese tramo. Un opto DIP-6 estándar tiene las
filas a 7,62 mm y el DRC lo rechazará: hará falta una versión de patillas anchas
o una ranura.

La primera versión de la regla detectó 95 infracciones en la colocación inicial:
fusibles junto al puente H, contactos de K701 entre la lógica y el bus del
molinillo junto al buck de 12 V. La colocación actual no tiene ninguna.

## Disipador de calentador y bomba

El disipador original (IMG_1098, IMG_1100 e IMG_1101) es un perfil de pie de
40 × 33 mm en planta y 35 mm de alto, con un TO-220 en cada canal. Se reserva
el mismo sitio: `HEATSINK_AREA` (x = 55–95, y = 84,5–117,5 mm), justo encima de
JP8, JP19 y JP24, como un área de regla que solo prohíbe huellas. Por eso se
cambió el ESP32 por la variante 1U de antena externa: la zona de exclusión de
la antena impresa ocupaba unos 1 990 mm², el 10 % de la placa, y sin ese espacio
no cabían a la vez el disipador, los fusibles, el MOV y K701.

El triac del molinillo irá en TO-220 de pie sin disipador, como el BTA208 de la
original, tras comprobar su pérdida. Su puente rectificador, los optos y los
snubbers ocuparán el hueco entre K701/RV701 y el disipador y el paso junto a
PS701.

## Routing del STM32

Todo el bloque del STM32 se desplaza junto con U101: la colocación lo define
respecto a `U101_AT` y el routing aplica a sus pistas el desplazamiento de U101.
Cada VSS baja al plano con su propia vía dentro del anillo de pads. Los VDD
(1/64, 13, 19/20, 32 y 48) se unen mediante un anillo de 3V3 en F.Cu bajo el
cuerpo del LQFP, y cada par VDD/VSS tiene su condensador fuera, en una esquina o
junto al par: C105/C111 arriba a la izquierda, C102 a la izquierda, C104 con el
bulk C106 arriba a la derecha, C103/C110 abajo a la derecha y la columna
C107/C109/C108 de VDDA/VREF+ bajo los pines 18–20.

Canales reservados para las señales:

- pines 7–10 (NRST y contactos): salida horizontal a la izquierda;
- pines 14–17 (NTC, caudal, nivel, corriente del grupo): en L escalonadas hacia
  abajo, a 6,3–7,8 mm a la izquierda del centro de U101;
- pines 21–24 y 27: hacia abajo, a la derecha de la columna de VDDA;
- pines 42–44: a la derecha;
- pines 49–61 (SWD, watchdog, armado y BOOT0): hacia arriba.

El plano GND_UI de B.Cu cubre el lado SELV hasta el borde de la banda de
barrera; además, el filler lo aparta 8 mm de todo cobre de red.

## USB

El puerto (J110 → U203) conserva su fanout. Del lado del dispositivo, la pareja
rodea U203 por la izquierda hasta R221/R222 y llega a los pads 13/14 del ESP32,
a unos 15 mm. Como sale de U203 en sentido opuesto al módulo, DM cruza una vez a
DP por B.Cu justo antes de los pads.

## Validación

- 155/158 huellas eléctricas colocadas; J115/JP8, J117/JP24 y J118/JP17 ocupan
  ya sus zonas originales. Faltan las huellas de JP19, JP1 y JP9. Contorno
  141,6 × 135,2 mm y MH1–MH3 preservados.
- DRC KiCad 10.0.6 con todas las severidades: 0 infracciones, incluidas la
  barrera de 8 mm, la reserva del disipador y los solapes de courtyard.
- USB, alimentación y desacoplo del STM32 y plano GND: 86 segmentos y 16 vías.
  La impedancia USB se verificará con el stack-up real antes de fabricar.
- 297 conexiones sin rutear y seis diferencias de paridad: los tres taladros
  mecánicos intencionales y los tres conectores aún sin huella.

Las referencias se dejan temporalmente en `F.Fab` para que la colocación densa no
genere conflictos de serigrafía. Se añadirán identificadores legibles de
conectores, polaridad, puntos de medida y seguridad después del routing.

## Siguiente paso

Pueden rutearse ya la entrada de red (J118 → F701 → RV701, F702 → PS701 y K701),
los 24 V de PS701 hacia J121 y las señales del STM32 por los canales reservados.
Las etapas de calentador, bomba y molinillo esperan a elegir el disipador y a las
huellas de JP19/JP1/JP9. No se generarán Gerbers mientras queden conexiones
abiertas o la revisión de aislamiento pendiente.
