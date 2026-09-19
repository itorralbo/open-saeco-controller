# Mecánica de la PCB principal 421941308981/01

Medición fotogramétrica realizada el 2026-09-17 a partir de IMG_1098–IMG_1101.
El propietario aceptó estas dimensiones el 2026-09-17 como línea base mecánica
de la Rev A para continuar el layout con tolerancias normales de fabricación.
Las fotos originales son 5712 × 4284 px. IMG_1098 e IMG_1099 muestran las dos
dimensiones exteriores sujetas con un calibre de nonio de 0,05 mm; IMG_1098
ofrece además una vista casi normal sobre una cuadrícula de 10 mm. IMG_1100 e
IMG_1101 se utilizaron para comprobar orientación, canto y conectores.

El origen mecánico adoptado es la esquina superior izquierda de IMG_1098, con
la cara de componentes hacia el observador. X crece hacia la derecha e Y hacia
abajo. La orientación se identifica por JP21 rojo arriba a la izquierda y los
conectores de potencia en el borde inferior.

## Cotas recuperadas

| Elemento | X (mm) | Y (mm) | Diámetro (mm) | Incertidumbre | Fuente |
|---|---:|---:|---:|---:|---|
| Contorno | 0…141,6 | 0…135,2 | — | ±0,15 mm | Lectura directa del calibre |
| MH1 | 23,5 | 46,3 | 3,5 | centro ±0,6; diámetro ±0,3 mm | IMG_1098 rectificada |
| MH2 | 37,8 | 112,8 | 3,5 | centro ±0,6; diámetro ±0,3 mm | IMG_1098 rectificada |
| MH3 | 136,5 | 128,8 | 3,5 | centro ±0,6; diámetro ±0,3 mm | IMG_1098 rectificada |

El contorno observado es rectangular y no se distinguen fresados interiores.
Las esquinas parecen rectas; la resolución y los elementos que tapan el borde
no permiten asignar un radio de esquina. La Rev A usa un
rectángulo de 141,6 × 135,2 mm y taladros NPTH de 3,5 mm.

Comprobaciones geométricas útiles:

| Distancia | Valor derivado (mm) |
|---|---:|
| MH1–MH2 | 68,0 |
| MH2–MH3 | 100,7 |
| MH1–MH3 | 139,9 |
| MH3 al borde derecho | 5,1 |
| MH3 al borde inferior | 6,4 |

## Cómo se obtuvo

La lectura del primer calibre coloca el cero del nonio entre 141 y 142 mm y la
coincidencia corresponde aproximadamente a 141,6 mm. En la segunda foto el cero
queda entre 135 y 136 mm, aproximadamente 135,2 mm. No se usa la cuadrícula para
esas dos cotas: sirve como control independiente y para ubicar centros.

Se tomó el cuadrilátero formado por los cuatro bordes y se proyectaron los centros
de los tres taladros a un rectángulo de 141,6 × 135,2 mm. El diámetro se estimó
con la escala local alrededor de cada centro. La dispersión visual entre ejes X/Y
y el desenfoque del canto determinan las incertidumbres indicadas.

## Lo que estas fotos no cierran

- Espesor del laminado: la vista lateral es oblicua y carece de referencia en el
  mismo plano vertical. 1,6 mm sería una elección industrial habitual, no una medida.
- Altura máxima de componentes y disipadores.
- Huellas de conectores: se cuentan cavidades y se distinguen familias mecánicas,
  pero el paso y las dimensiones de retención no alcanzan tolerancia de huella.
- Posición exacta de cada conector: una estimación fotográfica sirve para preparar
  la colocación, pero no para garantizar que encaje el arnés rígido.
- Radio de esquina, tolerancia de fresado y holgura necesaria en la carcasa.

## Posición de conectores recuperada

La sustitución directa exige conservar la llegada de los mazos, por lo que se
adopta una segunda calibración sobre IMG_1098. Se ajustó el borde de la imagen al
rectángulo aceptado y se contrastó en IMG_1101 qué conectores entran por el
lateral izquierdo. Las coordenadas siguientes son orígenes de huella KiCad, no
centros de carcasa:

| Conector original | Referencia Rev A | X (mm) | Y (mm) | Giro | Entrada |
|---|---|---:|---:|---:|---|
| JP21 | J104 | 6,2 | 6,5 | 90° | borde superior |
| JP16 | J108 | 3,0 | 64,5 | 90° | lateral izquierdo |
| JP14 | J107 | 3,0 | 73,5 | 90° | lateral izquierdo |
| JP3 | J113 | 3,5 | 125,3 | 0° | borde inferior |
| JP22 | J109 | 19,0 | 128,2 | 0° | borde inferior |
| JP13 | J105 | 29,0 | 125,3 | 0° | borde inferior |
| JP5 | J106 | 38,5 | 125,3 | 0° | borde inferior |

La incertidumbre asignada es ±1,5 mm, suficiente para congelar el placement de
Rev A y preparar una verificación física 1:1. Los conectores laterales de KiCad
se orientan con la abertura hacia fuera de la placa. El mapa reproducible está en
`hardware/controller/validation/main-connector-map.svg` y las coordenadas
estructuradas en `hardware/controller/mechanical-source.json`.

Se conservan además como zonas reservadas las posiciones de JP8, JP19, JP24,
JP17, JP1 y JP9. Todavía no forman parte del circuito de baja tensión, pero dejar
libre su volumen evita cerrar el camino a una revisión que sustituya también la
etapa conectada a red.

La geometría queda liberada para el layout Rev A. Esta aceptación cierra contorno,
fijaciones y una primera posición de conectores; no libera todavía la PCB
completa, porque alimentación, potencia, rutas y comprobaciones eléctricas siguen
pendientes.

## Familias mecánicas que ya pueden acotarse

- JP21 coincide visual y dimensionalmente con un TE Micro-MaTch Industrial rojo,
  hembra en placa, entrada lateral, dos filas. La variante de 20 posiciones
  [TE 2-338070-0](https://www.te.com/en/product-2-338070-0.html) es el candidato
  más cercano: 2,54 mm entre contactos de una misma fila, filas escalonadas y
  retención por patas deformadas. El recuento y el patrón de soldadura deben
  confirmarse en la cara inferior antes de asignar su huella.
- Los conectores blancos pequeños presentan paso fotográfico cercano a 2,5 mm y
  geometría similar a JST XH de entrada lateral. La
  [especificación XH](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf) confirma
  2,5 mm y PCB nominal de 1,6 mm, pero el color y la silueta no prueban fabricante.
- Las lengüetas de potencia son compatibles en tamaño aparente con FASTON 250:
  6,35 × 0,8 mm. Por ejemplo, TE documenta esas dimensiones para
  [63066-1](https://www.te.com/pt/product-63066-1.html), pero no se ha medido el
  patrón de anclaje de la pieza original y esa referencia no queda seleccionada.

Estas identificaciones reducen la búsqueda de repuestos, pero continúan como
candidatos. La huella se cerrará con una foto ortogonal de soldaduras o una medida
directa entre pines; la disponibilidad JLCPCB se evaluará después de fijar la serie.

Los conectores nuevos J101–J104 no intentan copiar estas piezas de la Saeco.
La Rev A usa JST XH lateral para la entrada aislada de 12 V, cabezales 1×6 para
servicio y un IDC polarizado 2×8 para el frontal nuevo. JP21 conserva valor como
referencia de posición y para documentar la placa original, no como contrato eléctrico.
