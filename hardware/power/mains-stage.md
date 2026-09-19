# Etapa de red y cargas — Rev A

Estado: arquitectura y componentes candidatos. Todavía no es apta para conectar
a 230 V ni para pedir una placa montada.

## Lo que muestran las fotos de la original

La inspección de `docs/HD8911/photos/IMG_1085.HEIC` a `IMG_1089.HEIC` permite
identificar la topología general sin asumir valores que no se leen:

- `F1` y `F2`: dos fusibles cilíndricos de 5 × 20 mm;
- `L5` y `L7`: filtrado de modo común/diferencial de la entrada;
- `DB1`, `U4` y `TR1`: fuente flyback aislada con transformador de ferrita;
- `ISO1` a `ISO7`: barrera optoaislada entre control y red;
- tres semiconductores de potencia junto a disipadores en la zona `AC_LOADS`;
- `D17`, `D22`, `D16` y `D23`: puente de diodos discreto situado junto a JP8,
  coherente con alimentar el molinillo con red rectificada;
- JP17, JP24, JP19, JP8, JP1 y JP9 sobre el mismo borde que los arneses originales.

Esto confirma que la sustituta debe integrar entrada de red, fuente aislada y
salidas de potencia en la misma tarjeta. Las referencias anteriores describen la
placa fotografiada; la asignación exacta de cada opto y triac a una carga se
confirmará por continuidad antes de copiar detalles del circuito.

## Arquitectura de Rev A

```text
JP17 L -- F1 -- MOV/filtro -- K701 relé general --+-- QH -- JP19 calentador
                                                   +-- QP -- JP24 bomba
                                                   +-- QG -- BR701 -- JP8 molino DC
JP17 N --------------------------------------------+---------------------------
             +-- F2 electrónica -- PS701 IRM-30-24 -- 24V_SELV
JP9 PE ------------------------------------------------------- JP1 PE
```

`K701` permanece abierto sin 24 V y su mando pasa por el interlock hardware. Los
triacs se disparan mediante optotriacs; ninguna red de puerta cruza a la zona
SELV. El puente del molinillo queda después de su interruptor AC, de modo que JP8
recibe polaridad fija y se descarga al apagar. Se incluirá una resistencia de
descarga donde haya capacidad de bus suficiente para retener tensión peligrosa.

## Componentes candidatos con suministro JLC/LCSC

| Funcón | Candidato | Código | Motivo y estado |
|---|---|---|---|
| Fuente 24 V | Mean Well IRM-30-24 | C6280124 | 85–264 VAC, 24 V/1,3 A, 31 W, encapsulada y aislada; montaje por ola disponible |
| Corte general | Omron G5RL-1A-E-TV8 DC24 | C2896748 | contacto NO, 16 A a 250 VAC, bobina 24 V; montaje por ola |
| Triac calentador | ST BTA24-800BWRG | C15293 | 25 A RMS, 800 V, TO-220AB aislado; requiere disipador calculado |
| Optotriac calentador | Lite-On MOC3083 | C10797 | cruce por cero, 800 V; adecuado para conmutación completa del calentador |
| Optotriac motor | Vishay VOT8125AG | C6925370 | disparo aleatorio, 800 V, separación ancha; suministro/montaje por confirmar |
| Puente molino | Vishay GBU8K o equivalente de marca | por cerrar | 8 A, 1000 V; validar corriente de arranque y stock antes de fijar MPN |

El mismo BTA24 es candidato provisional para bomba y molinillo para reducir
variantes y conservar margen ante cargas inductivas. Esa unificación no libera
la térmica: para el calentador, una caída cercana a 1,5 V a 8,3 A implica del
orden de 12 W en el semiconductor y exige un disipador similar al de la placa
original, que mide 40 mm de ancho y 35 mm de alto sobre la placa.

IMG_1098, IMG_1100 e IMG_1101 muestran ese disipador: un perfil extruido negro
colocado de pie, con la extrusión perpendicular a la placa. En planta ocupa unos
40 × 33 mm, estimados sobre IMG_1098 con la escala del calibre. Tiene dos canales
con un TO-220 atornillado en cada uno, y la cara de soldaduras (IMG_1091) muestra
dos anclajes soldados. Está centrado en x ≈ 72 mm e y ≈ 97 mm de la placa
original, justo encima de JP8 y AC_LOADS/JP19. El tercer semiconductor, un
BTA208-800B, está de pie y sin disipador junto a un relé beige, en el centro-
izquierda. Rev A seguirá el mismo esquema: calentador y bomba en un disipador
equivalente y molinillo en TO-220 al aire, tras comprobar su pérdida. La PCB
reserva ya ese hueco de 40 × 33 mm encima de JP8/JP19/JP24; ver
[colocación](../controller/layout.md). Para bomba y molinillo se calculará la pérdida con corriente medida.

El MOC3083 de cruce por cero se reserva al calentador. La bomba y el molinillo
mantienen optotriac de disparo aleatorio para no cerrar prematuramente la opción
de control de fase. Si `VOT8125AG` no puede suministrarse para el lote, se
rediseñará esa interfaz; no se bajará silenciosamente a 400 V.

## Protección y reglas pendientes de cerrar

- F1 será un fusible retardado reemplazable, inicialmente 10 A/250 V, ajustado
  después de medir calentador, bomba y molinillo en el peor caso permitido.
- F2 protegerá solo la rama de fuente/electrónica y se dimensionará con el pico de
  entrada del IRM-30 y su recomendación de fabricante.
- El MOV será de 275 VAC y se coordinará con F1; falta seleccionar MPN, energía y
  disposición térmica.
- El filtro EMI se copiará funcionalmente, no por aspecto. Falta medir/identificar
  L5/L7 o elegir un choque certificado con corriente suficiente.
- Las pistas del calentador se resolverán con vertidos anchos en ambas caras y
  cosido de vías. Se calculará el cobre con 1 oz y 2 oz antes de cotizar.
- Se mantiene una barrera inicial de 8 mm entre red y SELV en las dos capas, con
  ranuras bajo optos o fuente si hacen falta para conservar creepage real.

## Datos que decidirán la liberación

1. Corriente RMS y pico de arranque/bloqueo del molinillo.
2. Corriente del motor de grupo en movimiento y bloqueo, solo y con válvula.
3. Temperatura ambiente dentro de la máquina y temperatura de triac/disipador.
4. Continuidad de la placa original desde L/N a F1/F2, relé/triacs y cargas.
5. Familia exacta y pinout mecánico de JP19 y de los Faston JP1/JP9.

Hasta obtenerlos, el esquema puede avanzar con valores conservadores, pero los
Gerbers de la zona de red seguirán marcados como no fabricables.

## Fuentes primarias

- [Mean Well IRM-30](https://www.meanwell.com/Upload/PDF/IRM-30/IRM-30-SPEC.PDF)
- [Omron G5RL](https://components.omron.com/sites/default/files/datasheet_pdf/K132-E1.pdf)
- [ST BTA24](https://www.st.com/resource/en/datasheet/bta24.pdf)
- [Vishay VOT8125](https://www.vishay.com/en/product/84923/)
- [Vishay GBU8](https://www.vishay.com/en/product/88616/)
