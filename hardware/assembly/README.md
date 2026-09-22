# Fabricación y montaje — objetivo JLCPCB

Preferencia del propietario, 2026-09-16: fabricar en JLCPCB o equivalente y diseñar
con componentes disponibles. Se adopta desde la selección de componentes; no se
esperará al final del layout para buscar referencias.

## Catálogo trazable

[parts-catalog.json](parts-catalog.json) registra MPN, fabricante, código JLC/LCSC,
huella candidata, categoría, modalidad de montaje, URL y fecha de consulta.
Existencias verificadas en las páginas renderizadas de JLCPCB/LCSC el **2026-09-16/19**,
sin iniciar sesión ni hacer compras. Son una instantánea, no una reserva.
`stock_observed` y `available_order_qty_observed` son campos distintos de la web;
un valor `null` significa no observado, no cero ni disponibilidad garantizada.

| Función | Referencia | Código | Stock observado | Cantidad disponible para pedido observada | Montaje |
|---|---|---|---:|---:|---|
| Control principal | STM32G431RBT6 | [C431633](https://jlcpcb.com/partdetail/C431633) | 387 | 242 | Economic / Standard |
| Interfaz y comunicaciones, antena externa U.FL | ESP32-S3-WROOM-1U-N8R8 | [C2980300](https://jlcpcb.com/partdetail/3401552-ESP32_S3_WROOM_1UN8R8/C2980300) | 2.091 | 1.984 | Standard Only |
| Botones frontal | TCA9534PWR | [C783615](https://jlcpcb.com/partdetail/C783615) | 2.103 | 2.055 | Economic / Standard |
| Regulador 3,3 V / 2 A | AP63203WU-7 | [C780769](https://jlcpcb.com/partdetail/C780769) | 26.107 | 21.974 | Economic / Standard |
| Corte alimentación frontal | TPS22918DBVR | [C131941](https://jlcpcb.com/partdetail/TexasInstruments-TPS22918DBVR/C131941) | 1.849 | 1.767 | Economic / Standard |
| Puente H motor del grupo | DRV8876PWPR | [C575551](https://www.lcsc.com/product-detail/C575551.html) | 30.138 | No observado | Categoría JLC por verificar |
| Driver de puerta de válvula, candidato | UCC27517DBVR | [C99395](https://www.lcsc.com/product-detail/C99395.html) | 27.530 | 27.530 | Categoría JLC por verificar |
| MOSFET de válvula, candidato | UMW SI2308A, 60 V/3 A | [C347491](https://www.lcsc.com/product-detail/C347491.html) | 546.570 | 546.570 | Categoría JLC por verificar |
| Conector JP3 | JST B5B-XH-A(LF)(SN), vertical | [C157991](https://jlcpcb.com/partdetail/C157991) | 63.729 | No observado | Categoría JLC por verificar |
| Supervisor/watchdog | TI TPS3828-33DBVR | [C20032](https://www.lcsc.com/product-detail/C20032.html) | 49.065 | 49.065 | Categoría JLC por verificar |
| Interlock doble | TI SN74LVC2G08DCTR | [C352973](https://www.lcsc.com/product-detail/C352973.html) | 21.000 | 21.000 | Categoría JLC por verificar |
| Bulk motor del grupo | Lelon VZH101M1VTR-0607, 100 µF/35 V | [C176683](https://jlcpcb.com/partdetail/Lelon-VZH101M1VTR0607/C176683) | 48.395 | 48.395 | Economic / Standard |
| Bomba de carga DRV8876 | 22 nF/50 V X7R 0603 | [C77571](https://www.lcsc.com/product-detail/C77571.html) | 231.200 | 231.200 | Economic / Standard |
| USB-C de servicio | HRO TYPE-C-31-M-12 | [C165948](https://jlcpcb.com/partdetail/C165948) | 219.670 | No observado | Economic / Standard |
| Protección ESD USB | USBLC6-2SC6 | [C7519](https://jlcpcb.com/partdetail/C7519) | 32.360 | No observado | Economic / Standard |
| PTC alimentación USB opcional | Littelfuse 1206L050YR | [C163512](https://www.lcsc.com/product-detail/C163512.html) | 21.680 | No observado | Categoría JLC por verificar |
| Inductor buck | SRN6028C-3R9M | [C19947652](https://www.lcsc.com/product-detail/C19947652.html) | 227 | 227 | Economic / Standard |
| Salida buck, 2 unidades | 22 µF/10 V X5R 0805 | [C380338](https://jlcpcb.com/partdetail/CCTC-TCC0805X5R226M100FT/C380338) | 270.440 | 270.440 | Economic / Standard |
| Entradas 12 V y 24 V, 2 unidades | JST B2B-XH-A(LF)(SN), vertical | [C158012](https://jlcpcb.com/partdetail/C158012) | 364.229 | No observado | Categoría JLC por verificar |
| JP13/JP14, 2 unidades | JST B2B-XH-A(LF)(SN), vertical | [C158012](https://jlcpcb.com/partdetail/C158012) | 364.229 | No observado | Categoría JLC por verificar |
| JP5 | JST B3B-XH-A(LF)(SN), vertical | [C144394](https://jlcpcb.com/partdetail/C144394) | 213.419 | No observado | Categoría JLC por verificar |
| JP16 | JST B8B-XH-A(LF)(SN), vertical | [C157972](https://jlcpcb.com/partdetail/C157972) | 11.697 | No observado | Categoría JLC por verificar |
| JP22 | JST B3B-PH-K-S(LF)(SN), vertical | [C131339](https://jlcpcb.com/partdetail/C131339) | 153.612 | No observado | Categoría JLC por verificar |
| JP24 | JST B2P-VH(LF)(SN), 2 vías/3,96 mm, vertical | [C160315](https://jlcpcb.com/partdetail/C160315) | 328.397 | No observado | Categoría JLC por verificar |
| JP8/JP17 | JST B3P-VH(LF)(SN), 3 vías/3,96 mm, vertical | [C160316](https://jlcpcb.com/partdetail/C160316) | 39.334 | No observado | Categoría JLC por verificar |
| Fuente aislada integrada | Mean Well IRM-30-24, 24 V/1,3 A | [C6280124](https://jlcpcb.com/partdetail/MW_MEAN_WELL_Enterprises-IRM_3024/C6280124) | 2.161 | No observado | Economic / Standard; ola |
| Relé general de cargas | Omron G5RL-1A-E-TV8 DC24, 16 A | [C2896748](https://jlcpcb.com/partdetail/OmronElectronics-G5RL_1A_E_TV8DC24/C2896748) | No observado | No observado | Economic / Standard; ola |
| Buck 24 V → 12 V | Diodes AP63200WU-7, 2 A | [C2071868](https://www.lcsc.com/product-detail/C2071868.html) | 30.090 | No observado | Categoría JLC por verificar |
| Inductor buck 12 V | Bourns SRP7028A-100M, 10 µH/3,5 A | [C2687402](https://www.lcsc.com/product-detail/C2687402.html) | No observado | No observado | Categoría JLC por verificar |
| Entrada buck 24 V | Samsung CL31B106KBHNNNE, 10 µF/50 V X7R | [C89632](https://jlcpcb.com/partdetail/90812-CL31B106KBHNNNE/C89632) | 231.690 | 174.742 | Economic / Standard; Extended |
| Salida buck 12 V, 2 unidades | CCTC TCC1210X7R226K250MT, 22 µF/25 V X7R | [C49118556](https://jlcpcb.com/partdetail/CCTC-TCC1210X7R226K250MT/C49118556) | 46.369 | 42.198 | Economic / Standard; Extended |
| Triac de potencia, candidato | ST BTA24-800BWRG, 25 A/800 V | [C15293](https://jlcpcb.com/partdetail/Stmicroelectronics-BTA24800BWRG/C15293) | 1.051 | No observado | Categoría JLC por verificar |
| Optotriac calentador | Lite-On MOC3083, cruce por cero/800 V | [C10797](https://jlcpcb.com/partdetail/liteon-MOC3083/C10797) | 11.916 | No observado | Categoría JLC por verificar |
| Optotriac motores, candidato | Vishay VOT8125AG-V, aleatorio/800 V | C6925370 | No observado | No observado | Suministro y montaje por verificar |
| SWD/UART, 2 unidades | 1×6 2,54 mm vertical | [C52016393](https://jlcpcb.com/partdetail/C52016393) | 35.363 | 35.210 | Economic / Standard |
| Enlace principal–frontal, 2 unidades | IDC polarizado 2×8 2,54 mm | [C7501244](https://jlcpcb.com/partdetail/Megastar-ZX_IDC2_54_28PZZ/C7501244) | 1.643 | 1.603 | Economic / Standard |

Los integrados y magnéticos figuran como Extended; los pasivos de mayor volumen
se han elegido Basic cuando existe una referencia adecuada. El código
genérico de montaje `C9900171795` no identifica la variante N8R8 del módulo:
no sustituye a `C2913201`.

El DRV8876 figura en LCSC con stock, pero aún no se ha verificado su categoría ni
su disponibilidad dentro del selector de montaje de JLCPCB. Ya forma parte del
esquema y de la BOM candidata junto con el bulk, la bomba de carga y la red de
medida; sigue sin estar liberado para compra hasta validar el motor y la térmica.

La principal se orienta a **Standard PCBA** por el módulo ESP32 seleccionado y
requerirá montaje mixto/reflow más ola para módulo AC/DC, relé y conectores. El
frontal podría cotizarse aparte en Economic, sujeto a los conectores/pulsadores
que se elijan. No hay presupuesto de montaje calculado; las categorías no bastan
para deducir el precio total de un pedido.

## Decisión STM32

Para el núcleo de Rev A se selecciona como referencia de trabajo STM32G431RBT6,
LQFP64, 128 KB Flash / 32 KB RAM. Los menús, red y pantalla viven en el ESP32;
el control queda en el STM32. El margen real de firmware debe comprobarse al
añadir BSP, protocolo y adquisición: no se ha demostrado aún su capacidad final.

Se compararon también, sin seleccionarlos:
- [STM32G474RET6 / C521608](https://jlcpcb.com/partdetail/C521608): la página
  mostraba 52 en stock y acción «Pre-order»; 13,3943 USD estimados por unidad.
- [STM32G474VET6 / C431632](https://jlcpcb.com/partdetail/C431632): cero en stock,
  LQFP100. No se adopta como alternativa disponible.

G431RBT6 mostraba 4,9501 USD para una unidad; precios de la consulta, sin impuestos,
montaje ni transporte. No son presupuesto. No se aprueba ninguna sustitución
G431/G474 automáticamente: hay que revisar pinout, periféricos, memoria y firmware.

## BOM de cada placa

- [Principal, lógica, alimentación y sensores](../controller/bom-draft.csv):
  150 de 158 posiciones actuales tienen MPN y código LCSC; J111 y
  J121 son puentes de cobre y no requieren pieza. J116/J119/J120 aún no tienen huella ni referencia
  comprable. Las cabeceras de máquina
  son candidatas mecánicas; faltan caracterizar la salida de JP22, ensayar el
  puente H y la válvula, y completar las etapas de calentador, bomba y molino.
  La fuente IRM-30, el relé, el buck de 12 V y la protección de entrada ya se
  contabilizan en la BOM; fusibles, MOV y tres pasivos del buck siguen abiertos.
- [Frontal](../front-panel/bom-draft.csv): 42 de 42 posiciones con MPN y código.
  Añadidos el 2026-09-18: pulsador HRO K2-1102SP-A4SC-04 6 × 6 × 4,3 mm (C83916,
  Extended; no hay 6 × 6 SMD Basic), JST B8B-PH-K-S(LF)(SN) vertical (C157974, Extended, sustituye el 2026-09-22 al lateral C157915),
  LED KT-0603R (C2286, Basic) y 470 Ω (C23179, Basic). Paquete JLCPCB candidato en
  [front-panel/fabrication](../front-panel/fabrication/).

Los mismos campos están embebidos en los símbolos de los esquemas; el generador
reutiliza el catálogo y comprueba huellas. La BOM de la principal incluye la
protección de entrada DC, el buck, el corte del frontal, sensores de baja tensión,
  USB de servicio, telemetría de 12/24 V, el driver del motor del grupo, la etapa
  de válvula, la fuente IRM-30, el relé general y el watchdog con interlock
  hardware. **Todavía no incluye en el esquema** los drivers de calentador,
  bomba o molino.
El porcentaje anterior
solo describe la hoja actual, no el avance de toda la máquina.

Las referencias JST VH se incorporan al catálogo para reservar una opción
fabricable, pero todavía no aparecen en el esquema ni en la BOM de la principal.
Las fotos y las cotas encajan; falta una prueba física de acoplamiento. Además,
JP8 y JP17 transportan tensión peligrosa, por lo que elegir la carcasa no libera
la arquitectura eléctrica ni el layout de esos circuitos.

Capacitores de 100 nF y 10 nF: X7R. De 1 µF, 4,7 µF y 10 µF: X5R seleccionados
por suministro. Cerrar temperatura y capacitancia efectiva bajo polarización
antes de liberarlos; no aplicar una sustitución por valor nominal solamente.
Los MPN mecánicos no se elegirán por stock antes de conocer altura, paso y encaje.

## Objetivos de layout

Son decisiones iniciales de diseño, no reglas mínimas publicadas por el fabricante:
- Principal: dos capas como primera opción, con dominios, retornos y barrera de
  aislamiento controlados. Solo se pasará a cuatro si el layout o la EMC lo exige.
  Frontal: dos capas.
- Componentes SMD preferiblemente en una cara; pasivos 0603 (1608 métrico).
- Encapsulados con patas accesibles: LQFP64 y TSSOP; módulo de RF con antena integrada.
- En señales lógicas, comenzar con pistas/espacios de 0,20 mm y vías 0,60/0,30 mm;
  revisar con stack-up y cotización. Estas cifras **no** dimensionan aislamiento
  de red, pistas de potencia, térmica ni impedancia USB.
- Comprobar huellas contra planos del fabricante y pin 1, no contra la foto de catálogo.
- Conectores de potencia, elementos térmicos y THT pueden necesitar montaje mixto;
  documentar qué monta fábrica y qué se monta después.

## Paquete de fabricación futuro

Cuando haya PCB revisada: Gerbers y taladros, BOM de montaje, CPL de posiciones,
planos de ensamblaje, exclusiones DNP, revisión de fabricación y registro de ERC/DRC.
La [guía oficial de BOM](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly)
identifica Comment, Designator y Footprint. Añadiremos el código de componente
para evitar coincidencias ambiguas. Las referencias de BOM y CPL deben coincidir;
ver [guía de preparación](https://jlcpcb.com/help/article/advice-for-bom-and-cpl-files-preparation).

La BOM de la principal es de diseño: no hay CPL sin posiciones reales, ni Gerbers sin
contorno y routing. El frontal ya tiene Gerbers, BOM y CPL generados por
`tools/export_front_panel_fab.py`, pendientes de revisión antes del pedido. Antes de cotizar, refrescar stock y cantidades con merma,
revisar orientaciones en la vista de montaje y cerrar las piezas todavía pendientes.
