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
| JP8, JP17, JP24 | potencia de paso mayor, compatible visualmente con JST VH o equivalente | carcasa, terminal y separación mayores; huella todavía pendiente |

La placa de trabajo usa cabeceras JST acodadas XH para JP13, JP14, JP5 y JP16,
y PH para JP22. Las dimensiones se cotejaron con los catálogos oficiales
[JST XH](https://www.jst-mfg.com/product/index.php?lang=2&series=277) y
[JST PH](https://www.jst-mfg.com/product/index.php?lang=2&series=199).
La marca del fabricante no se ve en las carcasas; la selección sigue siendo
candidata hasta probar físicamente una muestra. Los pines de JP5 y JP22 permanecen
NC aunque ya exista huella: la foto no revela VCC, masa ni señal.
