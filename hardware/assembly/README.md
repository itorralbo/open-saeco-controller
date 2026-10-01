# Fabricación y montaje — objetivo JLCPCB

Preferencia del propietario, 2026-09-16: fabricar en JLCPCB o equivalente y diseñar
con componentes disponibles. Se adopta desde la selección de componentes; no se
esperará al final del layout para buscar referencias.

## Catálogo trazable

[parts-catalog.json](parts-catalog.json) registra MPN, fabricante, código JLC/LCSC,
huella candidata, categoría, modalidad de montaje, URL y fecha de consulta.
Existencias de la tabla consultadas el **2026-10-01** en la API pública de
búsqueda de JLCPCB con `tools/refresh_jlc_stock.py` (cada pieza lleva su fecha
en el catálogo), sin iniciar sesión ni hacer compras.
Son una instantánea, no una reserva.
`stock_observed` y `available_order_qty_observed` son campos distintos de la web;
un valor `null` significa no observado, no cero ni disponibilidad garantizada.

| Función | Referencia | Código | Stock observado | Cantidad disponible para pedido observada | Montaje |
|---|---|---|---:|---:|---|
| Control principal | STM32G431RBT6 | [C431633](https://jlcpcb.com/partdetail/C431633) | 534 | 436 | Economic / Standard |
| Interfaz y comunicaciones, antena externa U.FL | ESP32-S3-WROOM-1U-N8R8 | [C2980300](https://jlcpcb.com/partdetail/3401552-ESP32_S3_WROOM_1UN8R8/C2980300) | 1.586 | 1.461 | Standard Only |
| Botones frontal | TCA9534PWR | [C783615](https://jlcpcb.com/partdetail/C783615) | 15.246 | 15.123 | Economic / Standard |
| Regulador 3,3 V / 2 A | AP63203WU-7 | [C780769](https://jlcpcb.com/partdetail/C780769) | 17.920 | 14.121 | Economic / Standard |
| Corte alimentación frontal | TPS22918DBVR | [C131941](https://jlcpcb.com/partdetail/TexasInstruments-TPS22918DBVR/C131941) | 12.829 | 12.304 | Economic / Standard |
| Puente H motor del grupo | DRV8876PWPR | [C575551](https://www.lcsc.com/product-detail/C575551.html) | 29.787 | 29.551 | Categoría JLC por verificar |
| Driver de puerta de válvula, candidato | UCC27517DBVR | [C99395](https://www.lcsc.com/product-detail/C99395.html) | 52.624 | 50.166 | Categoría JLC por verificar |
| MOSFET de válvula, candidato | UMW SI2308A, 60 V/3 A | [C347491](https://www.lcsc.com/product-detail/C347491.html) | 517.915 | 515.663 | Categoría JLC por verificar |
| Conector JP3 | HR A2506WV-05P, 5 vías/2,50 mm, vertical | [C382535](https://jlcpcb.com/partdetail/C382535) | 3 | 0 | Extended; categoría JLC por verificar |
| Supervisor/watchdog | TI TPS3828-33DBVR | [C20032](https://www.lcsc.com/product-detail/C20032.html) | 65.909 | 65.838 | Categoría JLC por verificar |
| Interlock doble | TI SN74LVC2G08DCTR | [C352973](https://www.lcsc.com/product-detail/C352973.html) | 34.655 | 34.618 | Categoría JLC por verificar |
| Bulk motor del grupo | Lelon VZH101M1VTR-0607, 100 µF/35 V | [C176683](https://jlcpcb.com/partdetail/Lelon-VZH101M1VTR0607/C176683) | 31.195 | 24.428 | Economic / Standard |
| Bomba de carga DRV8876 | 22 nF/50 V X7R 0603 | [C77571](https://www.lcsc.com/product-detail/C77571.html) | 221.958 | 215.030 | Economic / Standard |
| USB-C de servicio | HRO TYPE-C-31-D-06, vertical | [C2689964](https://jlcpcb.com/partdetail/C2689964) | 2.392 | 2.317 | Categoría JLC por verificar |
| Protección ESD USB | USBLC6-2SC6 | [C7519](https://jlcpcb.com/partdetail/C7519) | 37.284 | 33.977 | Economic / Standard |
| PTC alimentación USB opcional | Littelfuse 1206L050YR | [C163512](https://www.lcsc.com/product-detail/C163512.html) | 20.862 | 20.808 | Categoría JLC por verificar |
| Inductor buck | SRN6028C-3R9M | [C19947652](https://www.lcsc.com/product-detail/C19947652.html) | 208 | 203 | Economic / Standard |
| Salida buck, 2 unidades | 22 µF/10 V X5R 0805 | [C380338](https://jlcpcb.com/partdetail/CCTC-TCC0805X5R226M100FT/C380338) | 278.106 | 271.385 | Economic / Standard |
| Entradas 12 V y 24 V, 2 unidades | JST B2B-XH-A(LF)(SN), vertical | [C158012](https://jlcpcb.com/partdetail/C158012) | 339.944 | 332.527 | Categoría JLC por verificar |
| JP13 | HR A2506WV-02P, 2 vías/2,50 mm, vertical | [C382532](https://jlcpcb.com/partdetail/C382532) | 700 | 698 | Extended; categoría JLC por verificar |
| JP14 | JST B2B-XH-A(LF)(SN), vertical, candidato no confirmado | [C158012](https://jlcpcb.com/partdetail/C158012) | 339.944 | 332.527 | Categoría JLC por verificar |
| JP5 | HR A2506WV-03P, 3 vías/2,50 mm, vertical | [C382533](https://jlcpcb.com/partdetail/C382533) | 0 | 0 | Extended; sin stock |
| JP16 | JST B8B-XH-A(LF)(SN), vertical, candidato no confirmado | [C157972](https://jlcpcb.com/partdetail/C157972) | 12.164 | 11.612 | Categoría JLC por verificar |
| JP22 | JST B3B-PH-K-S(LF)(SN), vertical, candidato no confirmado | [C131339](https://jlcpcb.com/partdetail/C131339) | 142.751 | 130.082 | Categoría JLC por verificar |
| JP24 | LEOCO 5001P020013, 2 vías/5,00 mm, pin cuadrado, vertical | Sin código JLCPCB | — | — | Soldadura manual o pieza aportada |
| JP8 | LEOCO 3941P03*000, 3 vías/3,96 mm, vertical | Sin código JLCPCB | — | — | Soldadura manual o pieza aportada |
| JP17 | TE 1971845-3, RAST 5, 3 lengüetas 6,3 × 0,8 mm, 16 A, vertical | [C5169636](https://jlcpcb.com/partdetail/C5169636) | 233 | 233 | Extended; categoría JLC por verificar |
| Fuente aislada integrada | Mean Well IRM-30-24, 24 V/1,3 A | [C6280124](https://jlcpcb.com/partdetail/MW_MEAN_WELL_Enterprises-IRM_3024/C6280124) | 13.220 | 13.050 | Economic / Standard; ola |
| Relé general de cargas | Omron G5RL-1A-E-TV8 DC24, 16 A | [C2896748](https://jlcpcb.com/partdetail/OmronElectronics-G5RL_1A_E_TV8DC24/C2896748) | 0 | 0 | Economic / Standard; ola; sin stock |
| Buck 24 V → 12 V | Diodes AP63200WU-7, 2 A | [C2071868](https://www.lcsc.com/product-detail/C2071868.html) | 0 | 0 | Categoría JLC por verificar; sin stock |
| Inductor buck 12 V | Bourns SRP7028A-100M, 10 µH/3,5 A | [C2687402](https://www.lcsc.com/product-detail/C2687402.html) | 4.974 | 4.929 | Categoría JLC por verificar |
| Entrada buck 24 V | Samsung CL31B106KBHNNNE, 10 µF/50 V X7R | [C89632](https://jlcpcb.com/partdetail/90812-CL31B106KBHNNNE/C89632) | 146.793 | 85.060 | Economic / Standard; Extended |
| Salida buck 12 V, 2 unidades | CCTC TCC1210X7R226K250MT, 22 µF/25 V X7R | [C49118556](https://jlcpcb.com/partdetail/CCTC-TCC1210X7R226K250MT/C49118556) | 84.548 | 78.350 | Economic / Standard; Extended |
| Triac de potencia, candidato | ST BTA24-800BWRG, 25 A/800 V | [C15293](https://jlcpcb.com/partdetail/Stmicroelectronics-BTA24800BWRG/C15293) | 1.077 | 1.039 | Categoría JLC por verificar |
| Optotriac calentador, bomba y molinillo | Lite-On MOC3083, cruce por cero/800 V | [C10797](https://jlcpcb.com/partdetail/liteon-MOC3083/C10797) | 18.898 | 18.845 | Categoría JLC por verificar |
| SWD/UART, 2 unidades | 1×6 2,54 mm vertical | [C52016393](https://jlcpcb.com/partdetail/C52016393) | 34.356 | 34.222 | Economic / Standard |
| Enlace principal–frontal, 2 unidades | Würth WR-MM 690367181672, 16 contactos 1,27 mm al tresbolillo (identificado por el propietario) | [C19103863](https://jlcpcb.com/partdetail/C19103863) | 0 | 0 | Sin stock el 2026-10-01; tipo PCBA por verificar |

Los integrados y magnéticos figuran como Extended; los pasivos de mayor volumen
se han elegido Basic cuando existe una referencia adecuada. El código
genérico de montaje `C9900171795` no identifica la variante N8R8 del módulo:
no sustituye a `C2980300`. El VOT8125AG de disparo aleatorio que se barajó para
bomba y molinillo no tenía existencias en DIP; se usa el MOC3083 en las tres
cargas.

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

- [Principal](../controller/bom-draft.csv): 187 posiciones. 180 tienen MPN y
  código LCSC; J115 y J117 (LEOCO) tienen MPN pero no código, porque JLCPCB no
  las vende; F701, F702 y RV701 tienen valor provisional y ninguna pieza; J111 y
  J121 son puentes de cobre. J107–J109 (JP14, JP16 y JP22) son cabeceras
  candidatas sin confirmar.
- [Frontal](../front-panel/bom-draft.csv): 42 de 42 posiciones con MPN y código.
  Añadidos el 2026-09-18: pulsador HRO K2-1102SP-A4SC-04 6 × 6 × 4,3 mm (C83916,
  Extended; no hay 6 × 6 SMD Basic), JST B8B-PH-K-S(LF)(SN) vertical (C157974, Extended, sustituye el 2026-09-22 al lateral C157915),
  LED KT-0603R (C2286, Basic) y 470 Ω (C23179, Basic). Paquete JLCPCB candidato en
  [front-panel/fabrication](../front-panel/fabrication/).

Los mismos campos están embebidos en los símbolos de los esquemas; el generador
reutiliza el catálogo y comprueba huellas.

El propietario identificó el 2026-09-29 las cabeceras de JP3, JP5, JP13, JP8 y
JP24. Las tres de señal son HR (Joint Tech) A2506WV y están en JLCPCB, pero con
poco stock: la de cinco vías tenía 3 unidades y la de tres, ninguna (igual el
2026-10-01, con ambas ya reservadas por encima del stock)
(`C9900130733`, la A2506WV-03P blanca de JLCPCB Assembly, tampoco tenía). Habrá
que reservarlas o comprarlas en LCSC antes del pedido. JP8 y JP24 son LEOCO
3941P03*000 y 5001P020013; JLCPCB no tiene LEOCO ni ninguna de las dos series,
así que su línea de la BOM va sin código LCSC y se sueldan a mano o se aportan
a JLCPCB. Para la 3941, el `*` es la opción de pin (V cuadrado, R redondo); la
huella usa el taladro de 1,80 mm del pin cuadrado, que admite los dos. JP8 y
JP24 transportan tensión peligrosa: fijar el conector no libera la arquitectura
eléctrica ni el layout de esos circuitos.

Capacitores de 100 nF y 10 nF: X7R. De 1 µF, 4,7 µF y 10 µF: X5R seleccionados
por suministro. Cerrar temperatura y capacitancia efectiva bajo polarización
antes de liberarlos; no aplicar una sustitución por valor nominal solamente.
Los MPN mecánicos no se elegirán por stock antes de conocer altura, paso y encaje.

## Objetivos de layout

Son decisiones iniciales de diseño, no reglas mínimas publicadas por el fabricante:
- Principal: cuatro capas desde el 2026-09-23 (JLC04161H-7628: planos de GND y
  3,3 V internos solo en el lado SELV), con dominios, retornos y barrera de
  aislamiento controlados. Ver el [perfil de fabricación](../controller/manufacturing.md).
  Frontal: dos capas.
- Componentes SMD preferiblemente en una cara; pasivos 0603 (1608 métrico).
- Encapsulados con patas accesibles: LQFP64 y TSSOP; módulo de RF con conector U.FL
  para antena externa.
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

La principal ya tiene posiciones y ruteo, pero no se generan su CPL ni sus
Gerbers hasta cerrar la revisión (ver [manufacturing.md](../controller/manufacturing.md)).
El frontal ya tiene Gerbers, BOM y CPL generados por
`tools/export_front_panel_fab.py`, pendientes de revisión antes del pedido. Antes de cotizar, refrescar stock y cantidades con merma,
revisar orientaciones en la vista de montaje y cerrar las piezas todavía pendientes.
