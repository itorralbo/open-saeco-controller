# Colocación de la principal Rev A

Estado: colocación mecánica de conectores y colocación funcional con la
distribución de la placa original, dominio de red contiguo, reserva del disipador
y barrera red/SELV comprobada por DRC. El puente H, el supervisor y sus
interlocks, la válvula, los sensores y el buck de 12 V ya están ruteados a mano;
aún no fabricable. La fuente de verdad mecánica es
`mechanical-source.json`; `tools/layout_controller_pcb.py` consume sus
coordenadas, coloca las 159 huellas actuales y comprueba que los tres taladros aceptados
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

Todos los conectores de mazo entran en vertical (decisión del propietario,
2026-09-22). J101, J105–J109, J112–J113, J115, J117 y J118 pasan de las JST
S-series laterales a las B-series verticales. Los pads, el paso y el taladro son
los mismos, así que las huellas conservan origen y giro y el cobre no cambia.
Solo J118 baja 0,8 mm, a y = 122,1 mm, dentro de la tolerancia de ±1,5 mm: la
carcasa VH vertical sobresale 4,2 mm al norte de los pines y chocaba 0,6 mm con
el courtyard de PS701. Los courtyards liberan unos 750 mm². La franja útil está
en x = 7–12,7 mm junto a J107/J108 y en y = 10–15,7 mm bajo J101/J112. En la fila
inferior se libera y ≈ 129–135 mm junto al borde. J110 (USB-C) también pasa a
vertical, con el HRO TYPE-C-31-D-06 (ver «USB»). J102–J104, J114, J116 y los
FASTON ya eran verticales.

JP8, JP19, JP24, JP17 y los dos FASTON de tierra son conectores obligatorios de
la principal completa, y ya tienen huella los seis. No son reservas para otra
placa: forman parte de esta misma PCB de sustitución.

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
- Borde inferior central y derecho: conectores originales de potencia, JP19
  (TE 1971845-4) y los dos FASTON de protección.

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
PS701. Alrededor de ella hay una banda de 8 mm en ambas capas sin pistas, vías
ni rellenos. K701, PS701 y los optoacopladores pueden atravesarla porque su
propio aislamiento cubre ese tramo. La banda admite pads porque los optos, DIP-6
estándar de 7,62 mm, meten los suyos 0,8 mm dentro. La regla de 8 mm del DRC los
sigue cubriendo.

Los optos se montan sobre una ranura fresada de 2 mm entre filas, que sobresale
3,5 mm de los pines extremos y va dibujada en la propia huella
(`OpenSaeco:DIP-6_W7.62mm_BarrierSlot`). Entre pads quedan 6,02 mm de aire. El
camino por la superficie rodea la ranura y supera los 8 mm: sin ella el DRC de
creepage da 6,02 mm y lo rechaza. Solo el aire se relaja, con la regla
`optocoupler_barrier_slot` (6 mm), y únicamente entre objetos contenidos por
completo en el área `optocoupler barrier slot` de cada opto: los pads y los
tramos de 0,75–1 mm que entran en ellos. Todo lo que sale de esas áreas
mantiene 8 mm.

La primera versión de la regla detectó 95 infracciones en la colocación inicial:
fusibles junto al puente H, contactos de K701 entre la lógica y el bus del
molinillo junto al buck de 12 V. La colocación actual no tiene ninguna.

## Disipador de calentador, bomba y molinillo

El disipador original (IMG_1098, IMG_1100 e IMG_1101) es un perfil de pie de
40 mm de ancho y 35 mm de alto, con un TO-220 en cada canal, pegado justo detrás
de AC_LOADS (JP19). Se reserva el mismo sitio: `HEATSINK_AREA` (x = 55–95,
y = 84,5–113 mm), como un área de regla que solo prohíbe huellas. Se toma un
fondo de 28,5 mm, el espacio entre la fila de K701/RV701 y la carcasa de JP19;
los 33 mm leídos en la foto cenital incluyen las aletas abiertas de arriba.
JP19 es un TE 1971845-4 de 22,3 × 14,9 × 12,8 mm, con 4 lengüetas FASTON
6,3 × 0,8 mm a 5 mm de paso, a ras del borde inferior. Por eso se
cambió el ESP32 por la variante 1U de antena externa: la zona de exclusión de
la antena impresa ocupaba unos 1 990 mm², el 10 % de la placa, y sin ese espacio
no cabían a la vez el disipador, los fusibles, el MOV y K701.

Desde el 2026-09-23 el triac del molinillo también va en el perfil. Se había
previsto al aire, como el BTA208 de la original, pero no quedaba en la zona de
red ningún hueco para un TO-220 de pie con su puente, y en el perfil gana margen
térmico ante un bloqueo. Los tres TO-220 ocupan la cara sur: molinillo,
calentador y bomba, de oeste a este, con 0,6 mm entre courtyards. Hay que
comprobar con el perfil real que caben tres tornillos y tres láminas aislantes.
Ver la [etapa del molinillo](#etapa-del-molinillo-jp8).

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

J110 es el receptáculo vertical HRO TYPE-C-31-D-06, centrado en (36; 5) con la
fila A al norte. Es SMD, así que B.Cu queda libre bajo el cuerpo. A6 y A7 bajan
por vías justo al norte de la fila y cruzan por debajo. D+ se une a B6 en la vía
bajo ese pad; D− vuelve a F.Cu bajo B7 y sigue por esa cara hasta U203. D+ salta
por B.Cu el tramo de masa de U203, como antes. Cada columna de VBUS une sus dos
filas por el hueco entre ellas. La columna este sube a una vía y cruza por B.Cu
al norte y por el oeste del conector hasta la vía de VBUS de (31; 11). Las masas
van cada una a su pata de carcasa, que está en el plano. R223 y R224 se acercan
al puerto: CC1 sale hacia el norte por encima de la pata de carcasa, y CC2 por la
fila sur, al este del par. El puerto queda completo.

Del lado del dispositivo, la pareja
rodea U203 por la izquierda hasta R221/R222 y llega a los pads 13/14 del ESP32,
a unos 15 mm. Como sale de U203 en sentido opuesto al módulo, DM cruza una vez a
DP por B.Cu justo antes de los pads.

## Entrada de red

- Fase: J118.1 sube por el paso entre el disipador y PS701 hasta F701 (3 mm en
  cada cara). PSU_L baja desde F702 por el mismo paso hasta PS701.1 (1 mm). Las dos
  pistas van anidadas y separadas 2,5 mm; por eso F702 está encima de F701.
- Fase protegida: une las dos pinzas de F701 y F702, RV701 y los dos pads COM
  de K701. El par COM de K701 se une por B.Cu para dejar sitio a la unión del par
  NO (`LOAD_L_ENABLED`), que espera a las etapas de carga.
- Neutro: J118.3 → PS701.2 en F.Cu y, desde ahí, hasta RV701 por B.Cu, por
  debajo de las dos fases. En el lado de red no hay plano, así que B.Cu está libre.
- Todo el cobre de red mantiene 2,5 mm entre redes distintas y 8 mm hasta SELV,
  comprobados por el DRC. La salida de J118.1 se estrecha a 2,2 mm para respetar
  1,2 mm hasta el pin central libre del VH.

Las fases que llevan la corriente de carga (unos 10 A) van duplicadas: 3 mm en
F.Cu y 3 mm en B.Cu, unidas por pads THT y vías de cosido de 1,6/0,8 mm. Son unos
6 mm de cobre de 1 oz, frente a los ≈4,7 mm que pide IPC-2221 para 10 A con 20 °C
de calentamiento. Se decidió así el 2026-09-19 porque sale más barato en JLCPCB
que pasar a 2 oz. El tramo corto que une las pinzas de F701 y la curva superior,
unos 10 mm, quedan solo en F.Cu, porque el neutro cruza por B.Cu justo encima.

## Salida de 24 V

- PS701.4 → J121 (`24V_INTERNAL_RAW`), junto al extremo SELV del módulo.
- `24V_ACT_RAW` sale de J121 por dos caminos:
  - un carril de 0,8 mm en x = 107,85 mm, entre el buck de 3,3 V y las
    resistencias del DRV8876, hasta J112 y el buck de 12 V;
  - una troncal de 1 mm por el borde SELV de la banda de barrera (y = 55,1 mm)
    que baja por x = 46 mm, a la izquierda de la banda, hasta la bobina de
    K701. De ella salen F303 (rama del grupo), el divisor R704, J114.4 y la
    bobina. Desde el pin 1 de la bobina sigue por x = 43 mm, pasa por D701 y
    gira al oeste en y = 93 mm hacia la rama de la válvula (F304). Hasta el
    2026-09-23 bajaba por x = 46 mm, justo donde ahora está el opto del
    calentador.
- Para esos recorridos se giró J121 y se movieron C307 y Q701.

## Validación

- 159/159 huellas eléctricas colocadas; J115/JP8, J117/JP24 y J118/JP17 ocupan
  ya sus zonas originales. JP19 es el TE 1971845-4; JP1 y JP9, lengüetas con
  patrón de patas provisional. Contorno
  141,6 × 135,2 mm y MH1–MH3 preservados.
- DRC KiCad 10.0.6 con todas las severidades: 0 infracciones, incluidas la
  barrera de 8 mm, la reserva del disipador y los solapes de courtyard.
- 843 segmentos y 170 vías. 2 559 mm de pista en F.Cu y 588 mm en B.Cu: el
  cruce del par USB, los saltos cortos bajo troncales de potencia y los carriles
  de escape del STM32.
  La impedancia USB se verificará con el stack-up real antes de fabricar.
- 66 conexiones sin rutear y tres diferencias de paridad, los taladros
  mecánicos MH1–MH3, que son intencionales.
- Un aviso de extremo suelto, intencional: la fila de corriente del puente H
  termina donde entrará PA3.

Las referencias se dejan temporalmente en `F.Fab` para que la colocación densa no
genere conflictos de serigrafía. Se añadirán identificadores legibles de
conectores, polaridad, puntos de medida y seguridad después del routing.

## Bloques ruteados a mano

El plan acordado el 2026-09-19 se ha ejecutado y ampliado. Cada bloque está
escrito en `route_controller_pcb.py` y se comprueba con DRC completo después de
añadirlo.

### Puente H del grupo

U501 se ha girado 270° y llevado al hueco que dejó J102, encima de MH1 y junto a
JP16 (centro 35/37 mm). Debajo quedan la bomba de carga (C503/C504), el bulk
C501 y el desacoplo C502; F303 y D304 entran en el mismo bloque. Las seis
señales de control salen en filas de 1,6 mm hacia el este, cada pareja
serie/pull-down unida por un salto sobre el pad de masa. OUT1 y OUT2, de 0,8 mm,
bajan por la izquierda a x = 28 y 29,2 mm y entran en J108 a y = 62 y 64,5 mm,
entre las filas de filtros. El pad expuesto baja al plano por cuatro vías.

J102 y J103 ya no están en el hueco del puente H ni en la esquina superior
derecha: J102 queda justo encima del STM32 (74,5/31 mm), en la salida natural de
los pines 49–61, y J103 al lado del ESP32 (75/10 mm), cerca de sus pines de
depuración.

### Supervisor, interlocks y mando del relé

R601 y R602 se han metido debajo de U601 para dejar libre el canal entre los
integrados y la columna de condensadores; por él sube la espina de 3V3 que
alimenta U601, C601, U602 y C602. El canal de 1,35 mm que queda al oeste de
U601/U602, entre ellos y C501, se deja vacío a propósito: es el único acceso a
los pines de STM_NRST y a las órdenes en bruto, y se rutea en la pasada de
señales. Por eso este bloque deja abiertos esos pines en lugar de taparlos.

U603 se ha girado 180° para que su salida mire a las resistencias de puerta. La
cadena del relé va de U603 a R801, R802 y Q701, y de ahí a la bobina de K701 y
al diodo D701. El retorno de bobina pasa al oeste de los pines de bobina, porque
el corredor este lo ocupa la alimentación de 24 V de K701.1. D701 se movió el
2026-09-23 a x = 40,6 mm, entre ese retorno y la troncal, para dejar sitio al
opto del calentador.

U603 no tenía condensador de desacoplo propio. Se ha añadido C603, un 100 nF
igual que C601 y C602, entre U603 y Q701: la puerta que arma la red no debe
tomar una caída de alimentación por un nivel alto válido.

### Válvula

F304, D305, D306, U502, Q501 y sus resistencias están ruteados. El par de 24 V y
el retorno conmutado bajan por el borde izquierdo y por y = 121 mm hasta JP3,
de modo que la cadena de puerta no tiene que cruzarlos. La rama de 24 V baja a
B.Cu durante 2,6 mm para pasar por debajo de la troncal de 24 V de y = 93 mm;
el plano pierde solo esa ranura.

### Sensores

NTC, caudalímetro, nivel de agua, puerta y los dos contactos del grupo llegan
desde sus conectores a sus filas de pull-up, serie y filtro. El filtro del
caudalímetro (R403, R404 y C402) bajó el 2026-09-23 a la columna al oeste de
MH2, para dejar su sitio junto a U703 al driver del molinillo; la señal en bruto
sube desde JP5 por el oeste de MH2. Los pines 3 y 4 de
JP16 quedan puenteados. El contacto de trabajo sube por el este de MH1 y C501
para no cruzar la fila del contacto de presencia. Cada condensador de filtro
baja al plano por su propia vía.

### Buck de 24 V a 12 V

Nodo de conmutación corto entre U303, C313 y L302; banco de salida al otro lado
de la bobina. Los dos condensadores 1210 comparten la columna x = 139 mm con un
pad de masa entre medias, así que el raíl los rodea por dentro, a x = 136 mm.

El divisor de realimentación estaba debajo del conmutador, a y = 10 mm, y desde
ahí no tenía camino: la troncal de 24 V rodea C310 por y = 7,3 mm para llegar a
los pines de entrada, y el único hueco que quedaba era el canal de 0,95 mm por
debajo del integrado, entre sus pads de entrada y el nodo de conmutación. Se ha
movido R302, R303 y C314 al borde superior, al noroeste del conmutador. Ahora
una sola línea a y = 3,4 mm recoge las tres piezas y entra en el pin 1 sin
cruzarse con nada, porque la troncal se mantiene a y ≥ 5 mm en todo su rodeo a
C310. El extremo alto del divisor vuelve al pad de la bobina por una línea de
sensado, sin corriente, pegada al borde superior.

### Buck de 12 V a 3,3 V

C302, el condensador de entrada de alta frecuencia, estaba a 8 mm del
conmutador, junto al bulk C301. Se ha llevado debajo del encapsulado, puenteando
los pines de entrada con el de masa, que es donde cierra el lazo que conmuta. La
masa del conmutador llega al plano a través del pad de ese condensador, así que
el lazo se cierra en cobre antes de pasar por una vía.

12V_FUSED cruza por encima de D301 y 12V_PROTECTED sale por debajo, de modo que
sobre los pads de los diodos no pasa ninguna pista ajena. La línea de sensado de
3,3 V vuelve al pin 1 por el norte del conmutador, a y = 31,5 mm, por encima del
nodo de conmutación y del arranque.

La troncal de 24 V subía a x = 107,85 mm, justo entre la bobina y la columna de
condensadores de salida, así que todos los enlaces de 3,3 V la cruzaban. Se ha
llevado a la columna vacía de x = 112,5 mm, al este de esos condensadores, y
baja a J112 por un ramal corto. Los condensadores de salida se quedan junto a la
bobina, que es donde deben estar.

La telemetría de 12 V queda ruteada: R702 girado 270° para que el nodo medio
mire a R701 y el nodo filtrado siga en línea recta hasta R703 y C701.

### Corte del frontal

La huella de PS701 cierra este hueco por el este a x = 101,25 mm, así que todo
lo que estaba al este de U302 se ha pasado al oeste o al norte. C307, que fija
el tiempo de subida, estaba a 8 mm de su pin 4 y ahora está pegado a él; C308
desacopla la entrada junto al pin 1 y C309 sostiene la salida conmutada. El raíl
de 3,3 V entra al hueco por y = 43 mm y baja por la columna libre de
x = 91,6 mm, al oeste de la pila de condensadores.

### Distribución de 3,3 V

Una sola línea sale del buck por y = 43 mm y se parte en dos.

La rama norte sube por el hueco de 1,1 mm que queda entre F301 y D301, cruza por
encima del ESP32 a y = 2,5 mm y baja a sus pines de alimentación, a sus dos
resistencias de estado y a la cabecera de UART. Para dejarle ese hueco libre,
F301 se ha movido 3 mm al oeste y el enlace de 12 V fusionado pasa por debajo
del cuerpo de D301 en B.Cu en vez de rodearlo por arriba. De la misma rama
cuelgan el pull-up de reset del STM32 y la cabecera SWD.

La rama oeste corre por el hueco de 1,1 mm entre los condensadores del
supervisor y la troncal de 24 V que pasa por debajo. Dos ramales de 24 V suben
cruzando su camino, el de x = 46,4 mm hacia el fusible del grupo y el de
x = 62,5 mm hacia la cabecera de medida, así que pasa por debajo de cada uno en
B.Cu. De ella salen la cabecera de medida, el bloque del supervisor, la puerta
que arma la red y, tras otro salto bajo las dos salidas del motor, los pull-up
de los contactos y el de la puerta.

R405 se ha girado 270° para que su pad de 3,3 V mire al norte: la red del mazo
de la puerta ocupa el carril de y = 71,8 mm y no dejaba alimentarlo por abajo.

Siguen sin alimentar los pull-up de la fila inferior (NTC y caudalímetro), J109
y las resistencias de fallo y VREF del puente H. Los primeros necesitan cruzar
el ramal de 24 V de la válvula, que atraviesa la placa a y = 93 mm; las
segundas están encerradas entre las envolventes de fallo y de corriente.

### Árbol de reset

R101 y C101 estaban al este del STM32, pero su pin de reset es el 7, del lado
oeste, así que la pareja se ha llevado al propio carril del reset, junto al
supervisor que lo gobierna. El pin sale en horizontal, porque los pads del oeste
van a 0,5 mm de paso y cualquier diagonal toca el vecino, baja a y = 50,5 mm y
cruza hacia el oeste por debajo de los dos ramales de 24 V hasta el canal de
1,35 mm que se había dejado libre junto a C501. De ahí alimenta U601, U602 y
U603.

Quedan dos puntos de reset abiertos. El pin 6 de U602, su segunda entrada, solo
se puede alcanzar por el hueco de 0,87 mm al este del encapsulado, que ya usan
la orden de la válvula y el ramal de 3,3 V. Y el pin de reset de la cabecera
SWD, que tendría que cruzar el enlace de desacoplo que pasa por el norte del
microcontrolador. Ninguno de los dos impide depurar ni arrancar.

### Raíl del USB de servicio

VBUS baja del conector al divisor de medida, al fusible rearmable y al puente de
alimentación de banco. El pin de VBUS del protector ESD es el central de su lado
oeste y el par protegido sale a ambos lados de él, así que se alcanza por B.Cu
desde el conector en vez de intentar colarlo por su propio abanico. R202 se ha
girado 270° para que su pad de 3,3 V mire al norte y la orden de arranque del
ESP32 salga por debajo sin cruzarlo.

### JP19, JP1 y JP9

Datos del propietario (2026-09-20): de JP19 solo están cableadas las lengüetas 1
y 3, que son los dos extremos del mismo resistor del boiler, así que da igual
cuál es cuál. El elemento mide 27,5 Ω y declara 1900 W, o sea 8,4 A a 230 V, que
es justo lo que ya soporta el cobre de fase duplicado. JP1 y JP9 son tomas de
tierra, del cuerpo del boiler y de la entrada de red.

Con eso ya tienen huella las tres. Las tomas de tierra usan una lengüeta
suelta dibujada en `OpenSaeco.pretty`, **provisional en el patrón de patas**:
las medidas dan la lengüeta, no cómo suelda, así que lleva un taladro redondo
de 1,6 mm. Hay que cotejarla con una muestra antes de pedir la placa.

El propietario identificó JP19 el 2026-09-22: es el **TE 1971845-4** (LCSC
C2149727, Extended en JLCPCB, soldadura por ola), un RAST 5 de cuatro
lengüetas con 16 A y 250 V. Su huella,
`TE_RAST5_1971845-4_1x04_P5.00mm_Vertical`, sigue la disposición recomendada
del plano de TE C-1971845 (rev. A25), redibujada desde la cara de componentes y
girada para que las lengüetas queden en columna:

- cada lengüeta suelda con **dos patas a 5 mm**, en taladros de 1,30 +0,10 mm
  (se usan 1,35 mm con pads de 2,4 mm);
- las patas se escalonan: las lengüetas impares a −1,25 y +3,75 mm del eje y
  las pares a −3,75 y +1,25 mm;
- un taladro sin metalizar de 2,5 mm recibe el poste de polarización, a +6,4 mm
  del eje y entre las lengüetas 3 y 4.

La carcasa se centra en (80,5; 124,05) para quedar a ras del borde inferior.
La lengüeta 3 es la de uso más cercana al borde y toma el retorno de neutro,
ruteado desde JP17 por debajo de la fila de conectores y duplicado en las dos
caras; sube a la fila de patas antes de llegar al taladro del poste y une las
dos patas. La lengüeta 1 recibe el vivo conmutado del triac en sus dos patas.
Las lengüetas 2 y 4 no se usan, pero cada una une sus dos patas para que la
pieza metálica flotante sea un solo nodo.

Queda por comprobar en la máquina que el poste y el cierre del conector aéreo
casan con esta orientación. Si no, se gira J116 180° y se rehacen las dos
entradas: las lengüetas 1 y 3 son los dos extremos del mismo elemento y el
orden no importa.

El puente de tierra entre JP1 y JP9 va duplicado en las dos caras como una fase
de carga, porque tiene que llevar corriente de defecto hasta que abra la
protección de aguas arriba. `PROTECTIVE_EARTH` se ha metido en la clase `Mains`:
el conductor de protección pertenece al dominio primario a efectos de
separación y mantiene los mismos 8 mm respecto de cualquier red SELV.

Con las tres huellas puestas desaparecen las áreas temporales que las
reservaban, y la paridad esquema/PCB baja de seis diferencias a tres: solo
quedan los taladros mecánicos MH1–MH3, que son intencionales.

### Etapa del calentador y disipador

Disipador elegido: perfil extruido estándar de 33 × 21 mm de pie y 35 mm de
alto, aletas verticales, en x = 62–95, y = 84,5–105,5 mm. Se queda en 33 mm y no
en 40 porque la fase conmutada tiene que bajar de K701 a los triacs y el único
paso es un carril de 5 mm al oeste del perfil: al este sube la fase de entrada
junto a PS701. El pie prohíbe ahora cobre además de huellas, porque la base del
perfil apoya en la placa. Los taladros de sujeción se añadirán con la pieza
concreta. Con ese volumen se espera del orden de 6–8 °C/W: suficiente para el
ciclo real del termobloque, justo para calentamiento continuo. Hay que medirlo en
una descalcificación.

Colocados: el triac del calentador Q703 contra la cara sur del perfil, el opto
U701 cruzando la barrera y R710, la resistencia de puerta, en el carril.
**Recolocado el 2026-09-23** para hacer sitio al molinillo: U701 sube a
y = 88 mm, justo bajo K701, y es el primero de la pila de tres optos. R710
queda encima, en el carril, con un pad sobre la fase. Q703 pasa al centro de la
cara sur (x = 75,26 mm).
**Corregido el 2026-09-22:** el MOC3083 de Lite-On del catálogo (C10797) es el
DIP de 7,62 mm; el de 10,16 mm es el MOC3083M y JLC solo tenía 3 unidades. U701
pasa a la huella con ranura descrita en la barrera, centrada en x = 51 mm.

Ruteado: bucle del LED desde 12 V con Q705, la fase conmutada por el carril, la
puerta por B.Cu (en el dominio de red no hay plano) y la salida del triac hasta
la lengüeta 1 de JP19. Los pines 4 y 6 del opto son intercambiables: la
alimentación de puerta sale por el 6, al norte hacia R710, y la puerta por el 4.
La puerta AND libre de U603 hace de enclavamiento del calentador con el reset.

Desde el 2026-09-23:

- Ánodo y retorno del LED pasan bajo la troncal de 24 V y D701 por B.Cu, en dos
  diagonales paralelas, y suben junto a los stubs del opto.
- La fase baja por el carril a 2,6 mm, en x = 60,6 mm, para dejar 1,2 mm con
  los pads de alimentación de R710 y R721. Al pie del perfil gira por una
  franja de 1,5 mm (antes 0,9 mm) de la que bajan los tres terminales
  centrales.
- La puerta baja por B.Cu en x = 59,3 mm, bajo la fase y a 2,5 mm de los stubs
  del opto del molinillo, y va por y = 107,1 mm hasta Q703. Pasa por encima
  de los pines de Q708, así que no cruza la puerta del molinillo, que va por
  debajo de ellos.

Dos áreas con nombre, `mains device pitch`, bajan la separación entre redes de
red a 0,6 mm solo sobre los pines del lado de red del opto y del triac, cuyo
paso de 2,54 mm lo impone el encapsulado. El hueco entre las dos filas del opto
conserva los 8 mm.

Enclavamiento ruteado: HEATER_EN_RAW entra en el pin 5 de U603 y llega a la
bajada R711 saltando a B.Cu bajo el ramal de 3,3 V. La salida, en el pin 3,
queda cercada por el ramal de tierra del pin 4 y el lazo de reset del pin 2;
el lazo se ha desplazado a x = 37,2 mm para que quepa una vía dentro, y desde
ella HEATER_EN_INTERLOCK baja por B.Cu, bajo el retorno del relé y los 12 V,
hasta R707. La entrada de reset del pin 6 sale al oeste a un hueco que deja
libre la orden del relé, ahora recta hacia el oeste antes de subir a R801, y
llega por B.Cu a la vía de reset al norte del encapsulado.

R710 es ya una ERJ-P08J391V (390 Ω, 1206, 500 V de tensión límite), en la
misma huella 1206.

Pendiente: el tramo desde el STM32 (PB10) con el resto de señales del
microcontrolador.

### Etapa de la bomba (JP24)

Es gemela de la del calentador y usa las mismas piezas: MOC3083 (U702), BTA24
(Q704), una ERJ-P08 de 390 Ω como resistencia de puerta (R712) y un SI2308A
(Q706) para el LED desde 12 V. Por qué el mismo opto de cruce por cero, y no uno
de disparo aleatorio, se explica en
[power-architecture.md](../power/power-architecture.md#etapa-de-la-bomba).

Colocación:

- U702 cruza la barrera en y = 113,46 mm, sobre su propia ranura, al pie de la
  pila de tres optos. Queda lo bastante alto para no tocar J115.
- Q704 ocupa el extremo este de la cara sur del perfil (x = 86,46 mm).
- R712 va al pie del carril y toma la fase conmutada de su final.
- El driver del LED (R714–R716 y Q706) ocupa la franja entre U702 y MH2.
- U604, la puerta de reset de la bomba, va bajo Q701 con C604 y la bajada R713,
  en la misma orientación que U603. Así tiene cerca `STM_NRST` y 3,3 V, y solo
  su salida baja hasta R714, como hace el calentador.

Ruteado:

- El 12 V llega de JP5.3 por B.Cu pegado al borde del plano.
- La fase conmutada sigue por la franja bajo el pie del disipador hasta el
  terminal central de Q704, a 0,9 mm.
- La puerta es la única red que hace los 35 mm hasta el triac. Va por B.Cu, al
  sur de la puerta del calentador y al norte de la lengüeta 1 de JP19, con
  2,5 mm a las dos.
- La salida de la bomba y su neutro, 0,4 A, van a 1,2 mm hasta JP24.1 y desde
  JP24.2 hasta el neutro de JP19. Con 1,2 mm quedan 2,5 mm entre las dos pistas
  en los pads de 3,96 mm, y la salida termina en el borde norte de su pad para
  respetar esos 2,5 mm con el neutro.
- Q704 tiene su propia área `mains device pitch`, igual que Q703.

Enclavamiento ruteado:

- Los pines de U604 salen a mano:
  - la orden en bruto, al oeste hasta R713;
  - el reset, al norte por entre las dos filas de pads;
  - 3,3 V, al este hasta C604;
  - la salida, al este y luego al sur;
  - las masas, cada una a su vía.
- Los tramos largos se buscaron con un A* en rejilla de 0,25 mm que prima F.Cu
  y se fijaron después en `route_pump_enable`.
- PB11 es el primer pin del lado este de U101:
  - baja junto a los desacoplos de la esquina inferior derecha;
  - pasa a B.Cu bajo el codo de los 24 V y va hacia el oeste por el borde sur
    del plano de masa, que casi no recorta;
  - sube junto a U602 hasta Q701, en paralelo a la pista del enclavamiento del
    calentador.
- 3,3 V llega desde C603 y el reset desde la vía junto a U603, los dos saltando
  por B.Cu bajo Q701.
- La salida cruza bajo la rama de 24 V de y = 93 mm por B.Cu y, desde el
  2026-09-23, sigue por B.Cu junto al driver del molinillo y llega a R714 por
  el oeste.
- El paso hacia U603 queda libre para PB10: la misma búsqueda encuentra camino
  de 64 mm con todo esto ya ruteado.

No hay snubber RC en el triac; ver la nota de la etapa.

### Cabecera SWD

PA13 (SWDIO) y PA14 (SWCLK) son los dos pines más al este de la fila norte, pero
llegan a J102 cruzados. SWCLK sigue en F.Cu por y = 32,3 mm, bajo J102.3, y
SWDIO baja a B.Cu justo al este de su pad y vuelve hacia el oeste por debajo.
SWO (PB3) sube entre J102.1 y J102.2 y llega al pin 6 por encima de la
cabecera. El pin de reset de J102 sigue abierto.

### Órdenes al supervisor

PB4 (watchdog), PB5 (sleep), PB6 (fallo) y PB7 (armado de red) salen de la fila
norte hacia el oeste, pero la alimentación del pin 64 cierra en F.Cu la esquina
noroeste. Por eso salen por B.Cu:

- PB6 sube, pasa a B.Cu entre la fila y J102 y cruza bajo J102.1 hasta
  x = 70,8 mm, donde vuelve a F.Cu y se une a la fila de fallo del puente H.
- PB7, PB5 y PB4 bajan a vías en la banda que queda entre las puntas de los pads
  y el anillo de 3,3 V, y vuelven hacia el oeste bajo la fila norte en carriles
  a 0,62 mm. De sur a norte van en el mismo orden que sus destinos, así que no
  se vuelven a cruzar. Cada carril sube a F.Cu en una vía escalonada al oeste
  del encapsulado.
- Los tramos largos se buscaron con un A* en rejilla de 0,05 mm que prima F.Cu
  y se fijaron en `route_supervisor_orders`. Pasan entre los pines de J114 y
  saltan por B.Cu bajo los ramales de 24 V. PB5 termina en R603 y cruza el
  corredor del reset una sola vez hasta U602.1.

### Etapa del molinillo (JP8)

Colocada y ruteada el 2026-09-23, sobre 1 A de marcha supuesto; ver
[power-architecture.md](../power/power-architecture.md#etapa-del-molinillo).
Las piezas son las del calentador y la bomba: MOC3083 (U703), BTA24 (Q708), una
ERJ-P08 de 390 Ω (R721) y un SI2308A (Q707). Además lleva el puente KBP410
(BR701) y el fusible T2A (F703).

Colocación:

- Tres optos en la barrera vertical, de K701 a J106: calentador, molinillo y
  bomba. Sobran 0,7 mm. U703 queda en medio, en y = 100,72 mm, con R721 en el
  carril a su altura.
- Q708 en el extremo oeste de la cara sur del perfil. La salida baja a F703,
  justo debajo, y la salida del fusible rodea J115 por el este hasta el puente.
- BR701 entre J115 y el borde inferior. El + (pin 1) sube a JP8.1 y el −
  (pin 4) a JP8.3. Son los dos pines exteriores, así que el cableado conserva la
  polaridad: blanco +, negro −.
- El driver del LED ocupa el sitio del filtro del caudalímetro, al oeste de
  U703: R720 junto al ánodo, Q707 debajo y R718/R719 a su oeste.
- R717, la bajada de la orden en bruto, va junto al pin 5 de U604.

Ruteado:

- Puerta por B.Cu en x = 56,5 mm, pegada a la barrera, y bajo la fila de
  triacs en y = 111,85 mm hasta el pin 3 de Q708. Queda a 2,5 mm de la puerta
  del calentador, que baja por el otro lado del carril.
- La fase con fusible baja por el pasillo entre J115 y JP19 y entra al pin 2
  del puente por encima. El neutro sale de la cola oeste de la lengüeta 3 de
  JP19 y entra al pin 3. El − sube por B.Cu bajo los dos.
- Anchuras: 1 mm hasta el fusible y 0,8 mm después. Con 3,4 A de bloqueo durante
  segundos sobra en 1 oz.
- 12 V para R720 desde la alimentación B.Cu de la bomba, junto a R716.
- La salida de la segunda puerta de U604 (pin 3) mira al oeste. Baja a B.Cu
  junto al pin, rodea las vías de masa y la pata B.Cu del enclavamiento del
  calentador por el oeste, sube junto a R401 y va por y = 103 mm, encima de la
  fila del NTC, hasta R718. La vía de masa de C401 pasó al este para dejarle
  sitio.
- El reset entra al pin 6 por debajo del encapsulado. PB12, la orden desde
  el STM32, espera con el resto de señales del microcontrolador, como PB10.

Nuevas áreas `mains device pitch` en el carril (R710, R721 y R712) y una por
triac. Tampoco hay snubber en Q708.

## Verificación de huellas

Se comprobó contra la hoja de datos que el SN74LVC2G08 en encapsulado DCT lleva
2Y en el pin 3, GND en el 4, 2A en el 5 y 2B en el 6. No coincide con el DCU de
ocho patillas, que sería 2A en el 3, 2B en el 5 y 2Y en el 6. El símbolo del
generador usa la asignación DCT, que es la correcta para el SN74LVC2G08DCTR
elegido. Si alguna vez se sustituye por la variante DCU, hay que cambiar también
el símbolo.

## Siguiente paso

1. Cerrar la distribución de 3,3 V: fila inferior de sensores, J109 y las
   resistencias de fallo y VREF del puente H. Y el raíl de 12 V desde el buck
   hasta J101 y F301.
2. Resto de señales del STM32: sensores (fila oeste), puente H (PA3, PA6,
   PA8), UART con el ESP32, BOOT0, telemetría de raíles, PA7 hasta U602 y
   PB0 hasta el corte del frontal.
3. PB10 hasta U603 y PB12 hasta U604 por el mismo pasillo que PB11.

Se probó Freerouting (`tools/autoroute_controller_pcb.py`, experimental y no
usado por la cadena). No dejó infracciones de separación, pero puso 2,3 m de
pista y 220 vías en B.Cu, troceó el plano de GND, estrechó pistas a 0,15 mm y no
consiguió rutear el puente H. Se descartó a favor del ruteo manual.

Las etapas de calentador, bomba y molinillo están colocadas y ruteadas; faltan
las huellas de JP1/JP9 y los taladros del perfil. No se generarán Gerbers
mientras queden conexiones abiertas o la revisión de aislamiento pendiente.
