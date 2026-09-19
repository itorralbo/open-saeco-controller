# Observaciones fotográficas iniciales

Fecha de revisión inicial: 2026-09-15. Los HEIC se conservan como originales y se
han convertido localmente para inspección sin modificar la fuente.

## Observaciones, no medidas
- IMG_1085.jpeg: etiqueta frontal legible 421941308981/01. Se leen PWR, EARTH,
  PUMP, GRINDER, NTC, GR.PULSE y TURBO. Se ven fusibles, disipadores y transformador.
  La presencia de transformador/optoacopladores no demuestra aislamiento seguro.
- IMG_1091.jpeg: cara de soldaduras y geometría de pistas visibles. No permite
  establecer continuidad ni distancias de aislamiento certificables.
- IMG_1092.jpeg: componentes azules sueltos; se distingue marcado KEKO, 222,
  300~ y Y2. Posiciones originales y estado eléctrico TBD. No se prescribe reposición.

Las fotos no confirman pines, ratings de cargas ni causa de la avería. No usar el
aspecto visual para declarar la placa segura o funcional.

## Segunda revisión, 2026-09-16

Inspección directa de los JPEG IMG_1085, IMG_1086 e IMG_1089 de los adjuntos
originales. IMG_1086 muestra la misma referencia 421941308981/01 sobre una base
cuadriculada; el escalado y la perspectiva no se han calibrado para obtener cotas.

| Zona / etiqueta visible | Observación física | Pendiente para elegir una referencia |
|---|---|---|
| PUMP / GRINDER | Conectores acodados de dos lengüetas planas en carcasa | Ancho/espesor de lengüeta, paso, enclavamiento, huella y rating |
| PWR / AC LOADS | Bloques de varias lengüetas planas en carcasa | Número y función de cada cavidad, dimensiones y codificación |
| EARTH | Dos terminales de lengüeta sin carcasa individual | Dimensiones, fijación y conexión efectiva de protección |
| NTC / GR.PULSE / TURBO | Conectores de señales acodados y polarizados, de una fila | Paso, cavidades, sección de terminal, fabricante y pin 1 |
| JP21, rojo | Conector de dos filas en el borde | Número de posiciones, paso y sistema de acoplamiento |

Estas observaciones distinguen construcción y ubicación. **No identifican una
serie comercial** (JST, TE, Molex u otra); no asignar una huella por parecido.
El conector nuevo de frontal seguirá siendo una selección propia y no una copia
eléctrica de JP21. El pinout del arnés y la identificación de cargas no cambian.

## Fotos dimensionales, 2026-09-17

IMG_1098–IMG_1101 aportan calibre, cuadrícula y vistas cenital/lateral. Se han
extraído contorno y taladros de la principal en el
[registro mecánico](main-board-mechanics.md). Las fotos permiten una plantilla
de encaje provisional. JP21 queda como candidato TE Micro-MaTch y los conectores
blancos pequeños como candidatos JST XH. Se cuentan con claridad JP21=20,
JP24/PUMP=2, JP8/GRINDER=3, JP13/NTC=2, JP5/TURBO=3 y JP14=2 contactos.
La lectura fotográfica que atribuía dos contactos a JP23 era errónea: el diagrama
eléctrico del manual identifica el nivel de agua como JP22, de tres posiciones.
El mismo diagrama confirma ocho posiciones en JP16, aunque en la foto parte queda
ocluida. El resultado consolidado está en
[connectors.csv](connectors.csv). En esa revisión las fotos no cerraban espesor,
alturas ni patrón de anclaje y todavía no se asignaron huellas.

## Conectores desmontados con calibre, 2026-09-18

Las fotos de `photos/Conectores/` muestran las carcasas de cable de frente y con
el calibre en el mismo plano. La anchura, número de vías, paso aparente y forma de
la cara de acoplamiento coinciden con estas familias:

| Conectores | Familia compatible candidata | Evidencia visible |
|---|---|---|
| JP13, JP14 | JST XH, 2 vías, 2,50 mm | cuerpo estrecho ≈5,7 mm y dos cavidades |
| JP5 | JST XH, 3 vías, 2,50 mm | cuerpo ≈8,2 mm y tres cavidades |
| JP3 | JST XH, 5 vías, 2,50 mm | cuerpo ≈13,2 mm y cinco cavidades |
| JP16 | JST XH, 8 vías, 2,50 mm | cuerpo ≈20,7 mm; rojo, azul, negro×2, verde×2, rojo×2 |
| JP22 | JST PH, 3 vías, 2,00 mm | carcasa y conductores menores que JP5; tres cavidades |
| JP8, JP17 | JST VH, 3 vías, 3,96 mm, candidato | dos conductores en carcasa de tres vías; la anchura fotografiada encaja con VHR-3N (11,82 mm) |
| JP24 | JST VH, 2 vías, 3,96 mm, candidato | dos conductores; la anchura fotografiada encaja con VHR-2N (7,86 mm) |

La placa de trabajo usa cabeceras JST acodadas XH para JP13, JP14, JP5 y JP16,
y PH para JP22. Las dimensiones se cotejaron con los catálogos oficiales
[JST XH](https://www.jst-mfg.com/product/index.php?lang=2&series=277) y
[JST PH](https://www.jst-mfg.com/product/index.php?lang=2&series=199).
La marca del fabricante no se ve en las carcasas; la selección sigue siendo
candidata hasta probar físicamente una muestra. Tras la identificación del
Digmesa y el seguimiento visual aportado por el propietario, JP5 queda como
1=señal, 2=GND, 3=VCC. En JP22 los conductores son rojo=VCC, blanco=señal y
negro=GND; la huella se orientará para que correspondan a pines 1, 2 y 3.

Para los tres conectores de potencia se cotejaron las fotos con el plano oficial
de la serie [JST VH](https://www.jst-mfg.com/product/index.php?series=262):
paso de 3,96 mm, VHR-2N de 7,86 mm y VHR-3N de 11,82 mm de ancho. Se reservan
como referencias de compra S2P-VH(LF)(SN) y S3P-VH(LF)(SN), ambas acodadas. Esta
coincidencia dimensional no demuestra el fabricante del arnés existente; hay que
probar una muestra y verificar la retención antes de liberar la PCB. JP19, de
cuatro posiciones con dos cableadas, sigue sin una identificación mecánica fiable.

## Frontal, 2026-09-18

`Frontal_01.HEIC` es una vista casi cenital de la PCB frontal completa con el
display OEM desconectado al lado; `Frontal_02.HEIC` es un detalle a 2× de la zona
central. Con el ancho de 184 mm y el lado estrecho de 52 mm medidos por el
propietario se rectificó la primera y se extrajeron contorno, taladros y centros
de pulsador en el [registro mecánico del frontal](../../hardware/front-panel/mechanical.md).

| Elemento | Observación |
|---|---|
| Identificación | Serigrafía `GIGI KYB_1.9.30.286.00_V03`; etiqueta `421941307291/04 8Y1638 30384` |
| Pulsadores | Siete táctiles SMD 6 × 6 mm: PB1–PB3, PB5, PB7, PB8 y uno tapado por la etiqueta (PB4 o PB6) |
| Lectura de teclas | U1 = 74HCT166 (TI), registro de desplazamiento de carga paralela |
| Indicador | DL1, LED STBY bajo PB8 |
| Display OEM | Marcaje `10107-LED-C-A173-160406-RoHS`; FPC de 18 vías y 0,5 mm a JP2; retroiluminación por cable de 4 hilos a JP1 |
| Arnés | JP3 rojo, 2 × 8 al tresbolillo, 16 contactos, estilo Micro-MaTch, en una pestaña del borde |
| Configuración | JP5 con puentes serigrafiados OTC / AMF / CMF; JP4 sin poblar |

El recuento de 16 contactos en JP3 no coincide con los 20 de JP21: no se deduce
la correspondencia del arnés original. Las funciones de los pulsadores y de los
puentes de JP5 no se infieren de la serigrafía.
