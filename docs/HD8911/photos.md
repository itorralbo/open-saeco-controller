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

> **Corregido el 2026-09-24** (ver «Revisión con nonio»): las anchuras de esta
> tabla no son las de las carcasas JST XH, PH ni VH, y JP17 es un TE RAST 5. La
> tabla se conserva como registro de la primera lectura.

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

La placa de trabajo usa cabeceras JST XH verticales para JP13, JP14, JP5 y JP16,
y PH vertical para JP22. Las dimensiones se cotejaron con los catálogos oficiales
[JST XH](https://www.jst-mfg.com/product/index.php?lang=2&series=277) y
[JST PH](https://www.jst-mfg.com/product/index.php?lang=2&series=199).
La marca del fabricante no se ve en las carcasas; la selección sigue siendo
candidata hasta probar físicamente una muestra. Tras la identificación del
Digmesa y el seguimiento visual aportado por el propietario, JP5 queda como
1=señal, 2=GND, 3=VCC. En JP22 los conductores son rojo=VCC, blanco=señal y
negro=GND; la huella se orientará para que correspondan a pines 1, 2 y 3.

## Distribución mecánica de conectores

La vista casi cenital IMG_1098 permite recuperar el orden y la posición con una
incertidumbre estimada de ±1,5 mm. JP21 ocupa la esquina superior izquierda;
JP16 y JP14 entran por el lateral izquierdo; en el borde inferior, de izquierda
a derecha, aparecen JP3, JP22, JP13 y JP5 antes de las conexiones de potencia.
IMG_1101 confirma que las aberturas de JP16 y JP14 miran hacia el exterior.

La PCB nueva sitúa J104, J108, J107, J113, J109, J105 y J106 en esas zonas,
respectivamente. El mapa completo, incluidos los huecos reservados de potencia,
se mantiene en `hardware/controller/mechanical-source.json` y se renderiza como
`hardware/controller/validation/main-connector-map.svg`.

Para los tres conectores de potencia se cotejaron las fotos con el plano oficial
de la serie [JST VH](https://www.jst-mfg.com/product/index.php?series=262):
paso de 3,96 mm, VHR-2N de 7,86 mm y VHR-3N de 11,82 mm de ancho. Se reservan
como referencias de compra B2P-VH(LF)(SN) y B3P-VH(LF)(SN), ambas verticales
(el 2026-09-22 sustituyen a las acodadas S2P-VH/S3P-VH). Esta
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

## Revisión con nonio, 2026-09-24

Se releyó el nonio de cada foto de `photos/Conectores/` y se cotejó con los
planos oficiales de JST ([XH](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf),
[PH](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf),
[VH](https://www.jst-mfg.com/product/pdf/eng/eVH.pdf)). La carcasa XHP-n mide
A + 4,8 mm de ancho; 5,7 mm es su fondo, no su anchura, y de ahí vino la
identificación anterior.

| Conector | Vías | Ancho medido | Carcasa JST supuesta | Lectura |
|---|---:|---:|---|---|
| JP13 | 2 | 5,7 mm | XHP-2, 7,3 mm | no es XH |
| JP14 | 2 | 5,8 mm | XHP-2, 7,3 mm | no es XH |
| JP5 | 3 | 8,3 mm | XHP-3, 9,8 mm | no es XH |
| JP3 | 5 | 13,1 mm | XHP-5, 14,8 mm | no es XH |
| JP16 | 8 | 20,85 mm | XHP-8, 22,3 mm | no es XH |
| JP22 | 3 | 6,1 mm | PHR-3, 7,8 mm | no es PH; paso ≈1,5 mm en IMG_1086 |
| JP24 | 2 | 10,0 mm | VHR-2N, 7,86 mm | no es VH; lengüetas a ≈5 mm |
| JP8 | 3 | 12,9 mm | VHR-3N, 11,82 mm | dudoso; paso ≈3,96 mm |
| JP17 | 3 | 15,0 mm | VHR-3N, 11,82 mm | TE RAST 5, grabado «STOCKO» |

- Los conectores de señal tienen paso de 2,5 mm (o 2,54 mm; las fotos no lo
  distinguen) y una carcasa de ancho ≈ A + 3,3 mm. La familia sigue sin
  identificar; Molex Mini-SPOX 5264 o KK-254 son hipótesis sin confirmar. Las
  huellas XH/PH de la PCB quedan como provisionales.
- JP22 no es PH: en IMG_1086 el paso de sus pines es ≈1,5 mm frente a los 2,5 mm
  de la cabecera de cinco vías vecina. JST ZH es una hipótesis.
- **JP17 queda identificado.** El propietario leyó en la carcasa del mazo la
  referencia TE 2-1241961-7: receptáculo RAST 5, tres vías a 5 mm, polarización
  1b. En IMG_1086 la cabecera de la placa es de la misma familia que JP19, con
  envolvente y lengüetas FASTON. J118 pasa a ser el TE 1971845-3 (LCSC C5169636);
  el cambio de huella y ruteo está en el [layout](../../hardware/controller/layout.md).
- En IMG_1086 todas las cabeceras del borde inferior y del lateral izquierdo son
  acodadas, con el cable entrando por el canto. La PCB usa cabeceras verticales
  por decisión del 2026-09-22; hay que comprobar en la máquina que el mazo llega.
- IMG_1086 muestra una cabecera de tres vías serigrafiada GR.PULSE entre JP22 y
  NTC que no figura en `connectors.csv`. Falta confirmar si la HD8911 la usa.

Para cerrar la familia de los de señal, lo más directo es medir en la placa
original el paso sobre todas las vías, la sección de los pines y el ancho de la
cabecera, o buscar marcas de fabricante. Si no, probar a enchufar una carcasa del
mazo en una muestra de la cabecera candidata.
