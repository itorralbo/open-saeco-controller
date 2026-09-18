# Registro mecánico del frontal

Estado: **cotas fotogramétricas aceptadas por el propietario el 2026-09-18 como
línea base del layout Rev A** y aplicadas a la
[PCB de trabajo](kicad/front-panel-reva.kicad_pcb) con
`python3 tools/apply_front_panel_mechanics.py`.
Fuente de datos: [mechanical-source.json](mechanical-source.json). Plano imprimible
1:1: [validation/mechanical-1to1.svg](validation/mechanical-1to1.svg). Superposición
sobre la foto rectificada: [validation/photo-rectified-overlay.jpg](validation/photo-rectified-overlay.jpg).
Quedan liberadas para layout, no para fabricación: antes hay que cerrar las
comprobaciones de calibre y superposición de más abajo.

## Placa original

- Serigrafía `GIGI KYB_1.9.30.286.00_V03`; etiqueta `421941307291/04 8Y1638 30384`.
- Siete pulsadores táctiles SMD de 6 × 6 mm en la cara de componentes: PB1–PB3
  a la izquierda, PB7, PB5 y un tercero con la serigrafía tapada (PB4 o PB6) a la
  derecha, y PB8 (standby) en el centro, girado 90°. DL1 (LED STBY) está debajo de PB8.
- U1 = 74HCT166 (TI, SOIC-16): los botones se leen por registro de desplazamiento.
- JP1: cabecera blanca de 4 vías, cable de retroiluminación del display OEM.
  JP2: FPC de 18 vías y 0,5 mm, display OEM `10107-LED-C-A173-160406`.
  JP3: conector rojo de 2 × 8 al tresbolillo, **16 contactos**, estilo Micro-MaTch,
  en una pestaña del borde inferior derecho. JP21 de la principal tiene 20, así que
  la continuidad del arnés original sigue sin verificar.
- JP5: puentes serigrafiados OTC / AMF / CMF. JP4: huella sin poblar.
- El display OEM no va montado sobre esta PCB: cuelga del FPC y del cable.

## Convención

Vista desde la cara de componentes (pulsadores hacia el observador, serigrafía
legible). Origen en la esquina superior izquierda; +X a la derecha, +Y hacia abajo,
en mm. La pestaña de JP3 queda abajo a la derecha. La orientación de montaje en la
máquina no se ha comprobado.

## Cotas recuperadas

| Elemento | Valor | Incertidumbre | Fuente |
|---|---|---|---|
| Ancho total | 184,0 | — | Medida del propietario |
| Alto del lado estrecho (x 0…30,7) | 52,0 | — | Medida del propietario; la foto da 52,2 |
| Alto del cuerpo (x 30,7…184) | 54,3 | ±0,3 | Frontal_01 rectificada |
| Escalón inferior izquierdo | x = 30,7; 2,3 de alto | ±0,3 | Frontal_01 rectificada |
| Pestaña de JP3 | x 125,7…171,6, hasta y = 62,3 | ±0,3 | Frontal_01 rectificada |
| Esquinas | vivas a la resolución de la foto | radio < 0,5 no resuelto | Frontal_01 |
| MH1–MH4 (NPTH Ø8,4) | (51,9; 8,7) (134,0; 8,7) (51,9; 43,7) (134,0; 43,7) | centro ±0,3; Ø ±0,2 | Ajuste de círculo |
| SP1–SP3 (cuadrado 4,9) | (6,7; 10,9) (6,7; 39,0) (177,9; 28,2) | ±0,3 | Frontal_01 rectificada |

Contorno, recorriendo en sentido horario desde el origen:
(0; 0) → (184; 0) → (184; 54,3) → (171,6; 54,3) → (171,6; 62,3) → (125,7; 62,3)
→ (125,7; 54,3) → (30,7; 54,3) → (30,7; 52,0) → (0; 52,0).

SP1–SP3 son cuadrados de cobre expuesto con un anillo central de ≈3,4 mm. A
través de ellos no se ve el papel, así que no son taladros abiertos. Su función
(masa o ESD, apoyo, centrado) queda **TBD**: mirar la cara de soldaduras y la carcasa.

### Pulsadores

Centro = centro del patrón de pads, a nivel de PCB. El capuchón rojo aparece
desplazado hasta ~1,6 mm por paralaje y no se usa para situar el centro.

| Original | X | Y | Patas |
|---|---:|---:|---|
| PB1 | 19,2 | 9,9 | arriba/abajo |
| PB2 | 19,2 | 25,6 | arriba/abajo |
| PB3 | 19,2 | 41,2 | arriba/abajo |
| PB7 | 164,6 | 9,9 | arriba/abajo |
| PB5 | 164,6 | 25,6 | arriba/abajo |
| PB4/PB6 (tapado) | 164,6 | 41,2 | arriba/abajo |
| PB8 (STBY) | 91,7 | 43,5 | izquierda/derecha |
| DL1 (LED STBY) | 91,8 | 48,5 | — |

Incertidumbre de centro: ±0,3 mm. Huella común: patas a 4,5 mm y 11,2 mm de
extremo a extremo de pads. Las columnas son simétricas respecto a x ≈ 91,9; los
taladros lo son respecto a x ≈ 93,0 (diferencia de 1 mm, que se ve en ambas filas).

Como referencia, sin valor de huella (el cuerpo incluye paralaje): JP1 ≈ (77,6; 4,4),
JP2 ≈ (92,0; 6,4) y JP3 ocupa x 143…166, y 51,5…59,3 (±1 mm).

## Cómo se obtuvo

Frontal_01 (iPhone 17, 5712 × 4284 px, 26 mm equivalente, cámara a ≈19 cm) es
casi cenital. Se segmentó el verde de la PCB y se ajustaron con precisión
subpíxel los diez tramos rectos del borde (residuo 0,1–1,8 px). Con las rectas
superior, izquierda, derecha e inferior del cuerpo se calculó una homografía a un
rectángulo de 184 mm de ancho. El alto se obtuvo de la distancia focal del EXIF,
exigiendo ejes ortogonales y escala igual en X e Y: sale 54,26 mm, prácticamente
independiente de la focal en ±5 %. Frontal_02 (detalle a 2×) solo sirvió para
identificar componentes.

La foto tiene una guiñada de ≈2,4° y un cabeceo de ≈1,6°: el extremo izquierdo
está más cerca de la cámara. Por eso, sin rectificar, el alto aparente del lado
izquierdo es ~3 % mayor del que le corresponde con 184 mm de ancho.

Comprobaciones independientes tras rectificar:

- Paso de U1 (SOIC-16): 1,273 mm frente a 1,27 nominal (+0,2 %).
- Lado estrecho: 52,2 mm fotogramétrico frente a 52 mm medido por el propietario.
- Los cuatro taladros salen redondos (Ø8,37–8,52 en ambos ejes) e iguales.
- Los seis pulsadores laterales dan la misma huella a izquierda y derecha
  (paso 4,45–4,52; alcance 11,20–11,29). Sin rectificar diferían un 8 % en X y
  un 4 % en Y, como corresponde a la guiñada.
- Dispersión entre centros que deberían estar alineados: ≤0,27 mm.

## Cómo quedan en KiCad

- Contorno: diez segmentos en Edge.Cuts.
- MH1–MH4: círculos de Ø8,4 en Edge.Cuts, es decir, agujeros fresados sin cobre.
  No se usa `MountingHole_8.4mm_M8` porque reserva la zona de cabeza de un
  tornillo M8, en torno al doble del diámetro del agujero, y aquí no hay tornillos.
- Pulsadores, DL1, SP1–SP3 y zona de JP3: solo referencias en Dwgs.User.
  SW1–SW8 siguen sin huella hasta conocer la altura del actuador.
- J1 y U1 pasan a la zona de staging fuera de la placa; la colocación sigue pendiente.

## Lo que estas fotos no cierran

- Espesor de la PCB y altura del actuador de los pulsadores sobre la PCB
  (determina la carrera con los botones de la carcasa).
- Función de SP1–SP3 y posible taladro bajo el anillo.
- Posición y ventana del display respecto a la PCB y al frontal plástico.
- Recorrido y longitud del arnés hacia JP21; pinout de JP3.
- Radio de esquina y tolerancias de fresado.

## Criterios para cerrar el layout

- Imprimir [mechanical-1to1.svg](validation/mechanical-1to1.svg) al 100 %,
  comprobar la barra de 100 mm y superponerlo a la PCB original: contorno,
  taladros y centros de pulsador deben coincidir dentro de ±0,3 mm.
- Medir con calibre el alto del cuerpo (54,3), la pestaña (62,3) y la distancia
  entre taladros (82,1 × 35,0).
- Comprobar conjunto carcasa–actuador–pulsador, incluyendo tolerancias y carrera.
- Presentar pantalla y adaptador en el hueco; verificar imagen visible sin recortes.
- Evitar que tornillos, flex o nervios carguen sobre el vidrio o componentes.
- Confirmar conector polarizado, pin 1 y vista de ambos extremos del nuevo arnés.
- Elegir stack-up, cobre, acabado y protección ambiental después de esta revisión.

La nueva PCB puede repetir la mecánica y contactos de la original sin reutilizar
su electrónica activa. JP21 no se considera compatible con J1: pinout y niveles
del arnés original continúan sin verificar.
