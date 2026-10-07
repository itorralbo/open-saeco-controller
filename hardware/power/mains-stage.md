# Etapa de red y cargas — Rev A

Estado: en el esquema y en la PCB ruteada, con componentes candidatos. Todavía
no es apta para conectar a 230 V ni para pedir una placa montada.

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
JP17 L -- F701 --+-- RV701 a N -- K701 relé general --+-- Q703 -- JP19 calentador
                 |                                    +-- Q704 -- JP24 bomba
                 |                                    +-- Q708 -- F703 -- BR701 -- JP8 molino DC
                 +-- F702 -- PS701 IRM-30-24 -- 24V_SELV
JP17 N ----------------------------------------------- N de cargas, PS701 y BR701
JP9 PE ----------------------------------------------- JP1 PE
```

El filtro EMI (L5/L7 en la original) todavía no está en el esquema.

`K701` permanece abierto sin 24 V y su mando pasa por el interlock hardware. Los
triacs se disparan mediante optotriacs; ninguna red de puerta cruza a la zona
SELV. El puente del molinillo queda después de su interruptor AC, de modo que JP8
recibe polaridad fija y se descarga al apagar. Se incluirá una resistencia de
descarga donde haya capacidad de bus suficiente para retener tensión peligrosa.

## Componentes candidatos con suministro JLC/LCSC

| Función | Candidato | Código | Motivo y estado |
|---|---|---|---|
| Fuente 24 V | Mean Well IRM-30-24 | C6280124 | 85–264 VAC, 24 V/1,3 A, 31 W, encapsulada y aislada; montaje por ola disponible |
| Corte general | Omron G5RL-1A-E-TV8 DC24 | C2896748 | contacto NO, 16 A a 250 VAC, bobina 24 V; montaje por ola |
| Triac calentador | ST BTA24-800BWRG | C15293 | 25 A RMS, 800 V, TO-220AB aislado; requiere disipador calculado |
| Optotriac calentador, bomba y molinillo | Lite-On MOC3083 | C10797 | cruce por cero, 800 V, DIP de 7,62 mm sobre ranura; conmutación completa y salto de semiciclos |
| Fusible molino | Littelfuse 0215004.MXEP | C178840 | T4A, 250 VAC, 5 × 20 mm cerámico axial de 1500 A de poder de corte, de pie junto a Q708; entre Q708 y el puente. Fusible propio por decisión del propietario del 2026-09-23; T4A desde que la etapa se dimensiona a 3 A; sustituye el 2026-10-06 al JDT JFC2410-1400TS (50 A, issue #1) |
| Fusibles de entrada y fuente | Littelfuse 0215012.MXEP / 0215002.MXP | C142789 / C142716 | T12A y T2A, 5 × 20 mm cerámicos de 1500 A a 250 VAC. F701, axial y soldado en horizontal como el F1 original, que también es de 12 A; F702 en dos pinzas Littelfuse 01110501Z (C151075, hasta 10 A), de 2 A como el F2 original |
| Puente molino | MDD KBP410 | C840747 | 4 A, 1000 V, 90 A de pico; a 3 A disipa ≈ 5 W y solo vale para molidos de hasta 10 s con pausa. Un GBU no cabe. Sustituye al GBU8K |

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
equivalente. El molinillo iba a ir al aire, pero desde el 2026-09-23 comparte el
perfil: no quedaba sitio para otro TO-220 de pie. La PCB
reserva ya ese hueco de 40 × 33 mm encima de JP8/JP19/JP24; ver
[colocación](../controller/layout.md). Para bomba y molinillo se calculará la pérdida con corriente medida.

El MOC3083 de cruce por cero sirve al calentador y, desde el 2026-09-22, también
a la bomba: no había en JLC ningún optotriac aleatorio de 800 V en DIP de 400 mil
(ver [etapa de la bomba](power-architecture.md#etapa-de-la-bomba)). Desde el
2026-09-23 también al molinillo, que solo se enciende y apaga; ver
[etapa del molinillo](power-architecture.md#etapa-del-molinillo). No se bajó a
un opto de 600 o 400 V.

## Protección y reglas pendientes de cerrar

- Los tres fusibles de red cortan 1500 A a 250 VAC, la corriente de defecto
  supuesta; ver [corriente de defecto supuesta](power-architecture.md#corriente-de-defecto-supuesta-y-fusibles-de-red),
  con lo que aceptó el propietario para cerrar la issue #1: el puente puede
  perderse en un corto en continua, la selectividad no se exige y el poder de
  corte se acredita con la certificación de los fusibles.
- F701 es un fusible retardado de 5 × 20 mm, Littelfuse 0215012.MXEP (T12AH),
  soldado en horizontal como el F1 original, que también es de 12 A. Se
  revisará después de medir calentador, bomba y molinillo en el peor caso
  permitido. Con
  el molinillo a 3 A la suma llegaría a 11,6 A; el firmware limita el
  calentador al 60 % mientras se muele y el total queda en ≈ 9,7 A (ver
  [reparto de corriente](power-architecture.md#reparto-de-corriente-en-la-fase-de-cargas)).
- F702 protege solo la rama de la fuente: Littelfuse 0215002.MXP (T2AH), de
  2 A como el F2 original. Deja la irrupción estimada del IRM-30 en el 3–4 % de
  su I²t de fusión (ver [F702](power-architecture.md#corriente-de-defecto-supuesta-y-fusibles-de-red)).
- RV701 es un MOV de 275 VAC en disco de 15,5 mm, coordinado con F701; falta
  seleccionar MPN y energía.
- El filtro EMI se copiará funcionalmente, no por aspecto. Falta medir/identificar
  L5/L7 o elegir un choque certificado con corriente suficiente.
- Cobre de 1 oz. Las pistas del calentador y de la fase general se duplican en
  las dos caras con vías de cosido, la opción más barata en JLCPCB (decisión del
  2026-09-19). La entrada de red ya sigue ese criterio. La fase de cargas no lo
  seguía: del carril al triac del calentador era una sola pista de F.Cu, de
  1,5 mm en la tira y 0,9 mm en la bajada. Desde el 2026-09-23 la acompaña un
  bloque de B.Cu bajo el perfil (ver [layout](../controller/layout.md#fase-de-cargas-bajo-el-perfil)).
- Se mantiene una barrera inicial de 8 mm entre red y SELV en todas las capas, con
  ranuras bajo optos o fuente si hacen falta para conservar creepage real.

## Datos que decidirán la liberación

1. Corriente RMS y pico de arranque/bloqueo del molinillo. Rev A se dimensiona
   a 3 A, cerca de los 3,4 A de bloqueo que limitan los 68 Ω del bobinado; la
   medida decide el puente y la detección de bloqueo.
2. Corriente del motor de grupo en movimiento y bloqueo, solo y con válvula.
3. Temperatura ambiente dentro de la máquina y temperatura de triac/disipador.
4. Continuidad de la placa original desde L/N a F1/F2, relé/triacs y cargas.
5. Patrón de patas de los Faston JP1/JP9: cerrado el 2026-09-23 con la foto del
   propietario. Son lengüetas verticales de dos patas en fila, casadas con el
   TE 63824-1 (LCSC C575074): dos taladros de 1,40 mm a 5,08 mm, según el plano
   de TE. Se comprueba con la impresión 1:1. JP19 queda cerrado: el propietario lo
   identificó el 2026-09-22 como TE 1971845-4 (LCSC C2149727), un RAST 5 de
   cuatro lengüetas 6,3 × 0,8 mm a 5 mm, 16 A 250 V, y su huella sigue el plano
   de TE. JP17 queda cerrado el 2026-09-24: la carcasa del mazo es un TE
   2-1241961-7 y la placa lleva su cabecera, el TE 1971845-3 (LCSC C5169636).

Hasta obtenerlos, el esquema puede avanzar con valores conservadores, pero los
Gerbers de la zona de red seguirán marcados como no fabricables.

## Fuentes primarias

- [Mean Well IRM-30](https://www.meanwell.com/Upload/PDF/IRM-30/IRM-30-SPEC.PDF)
- [Omron G5RL](https://components.omron.com/sites/default/files/datasheet_pdf/K132-E1.pdf)
- [ST BTA24](https://www.st.com/resource/en/datasheet/bta24.pdf)
- [Vishay VOT8125](https://www.vishay.com/en/product/84923/)
- [MDD KBP4005–KBP410](https://www.lcsc.com/datasheet/lcsc_datasheet_2407101109_MDD-Microdiode-Semiconductor-KBP410_C840747.pdf)
