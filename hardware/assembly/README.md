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
| Interfaz y comunicaciones | ESP32-S3-WROOM-1-N8R8 | [C2913201](https://jlcpcb.com/partdetail/C2913201) | 2.995 | No observado | Standard Only |
| Botones frontal | TCA9534PWR | [C783615](https://jlcpcb.com/partdetail/C783615) | 2.103 | 2.055 | Economic / Standard |
| Regulador 3,3 V / 2 A | AP63203WU-7 | [C780769](https://jlcpcb.com/partdetail/C780769) | 26.107 | 21.974 | Economic / Standard |
| Corte alimentación frontal | TPS22918DBVR | [C131941](https://jlcpcb.com/partdetail/TexasInstruments-TPS22918DBVR/C131941) | 1.849 | 1.767 | Economic / Standard |
| Puente H motor del grupo | DRV8876PWPR | [C575551](https://www.lcsc.com/product-detail/C575551.html) | 30.138 | No observado | Categoría JLC por verificar |
| Bulk motor del grupo | Lelon VZH101M1VTR-0607, 100 µF/35 V | [C176683](https://jlcpcb.com/partdetail/Lelon-VZH101M1VTR0607/C176683) | 48.395 | 48.395 | Economic / Standard |
| Bomba de carga DRV8876 | 22 nF/50 V X7R 0603 | [C77571](https://www.lcsc.com/product-detail/C77571.html) | 231.200 | 231.200 | Economic / Standard |
| USB-C de servicio | HRO TYPE-C-31-M-12 | [C165948](https://jlcpcb.com/partdetail/C165948) | 219.670 | No observado | Economic / Standard |
| Protección ESD USB | USBLC6-2SC6 | [C7519](https://jlcpcb.com/partdetail/C7519) | 32.360 | No observado | Economic / Standard |
| PTC alimentación USB opcional | Littelfuse 1206L050YR | [C163512](https://www.lcsc.com/product-detail/C163512.html) | 21.680 | No observado | Categoría JLC por verificar |
| Inductor buck | SRN6028C-3R9M | [C19947652](https://www.lcsc.com/product-detail/C19947652.html) | 227 | 227 | Economic / Standard |
| Salida buck, 2 unidades | 22 µF/10 V X5R 0805 | [C380338](https://jlcpcb.com/partdetail/CCTC-TCC0805X5R226M100FT/C380338) | 270.440 | 270.440 | Economic / Standard |
| Entrada 12 V | JST S2B-XH-A-1(LF)(SN) | [C163035](https://www.lcsc.com/product-detail/C163035.html) | 100.630 | 100.630 | Economic / Standard |
| JP13/JP14, 2 unidades | JST S2B-XH-A-1(LF)(SN) | [C163035](https://www.lcsc.com/product-detail/C163035.html) | 100.630 | 100.630 | Economic / Standard |
| JP5 | JST S3B-XH-A(LF)(SN) | [C157928](https://www.lcsc.com/product-detail/C157928.html) | 139.550 | 139.550 | Economic / Standard |
| JP16 | JST S8B-XH-A(LF)(SN) | [C157914](https://www.lcsc.com/product-detail/C157914.html) | 17.350 | 17.350 | Economic / Standard |
| JP22 | JST S3B-PH-K(LF)(SN) | [C545716](https://www.lcsc.com/product-detail/C545716.html) | 14.715 | 14.715 | Economic / Standard |
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

La principal se orienta a **Standard PCBA** por el módulo ESP32 seleccionado. El
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
  102 de 103 posiciones actuales con MPN, código y huella; J111 es un puente de
  cobre abierto y no requiere pieza. Las cabeceras de máquina
  son candidatas mecánicas; faltan caracterizar la salida de JP22, ensayar el
  puente H y completar las etapas de válvula/red/molino.
- [Frontal](../front-panel/bom-draft.csv): 42 de 42 posiciones con MPN y código.
  Añadidos el 2026-09-18: pulsador HRO K2-1102SP-A4SC-04 6 × 6 × 4,3 mm (C83916,
  Extended; no hay 6 × 6 SMD Basic), JST S8B-PH-K-S(LF)(SN) (C157915, Extended),
  LED KT-0603R (C2286, Basic) y 470 Ω (C23179, Basic). Paquete JLCPCB candidato en
  [front-panel/fabrication](../front-panel/fabrication/).

Los mismos campos están embebidos en los símbolos de los esquemas; el generador
reutiliza el catálogo y comprueba huellas. La BOM de la principal incluye la
protección de entrada DC, el buck, el corte del frontal, sensores de baja tensión,
USB de servicio y el driver del motor del grupo. **No incluye** fuentes AC/DC
aisladas ni drivers de válvula, calentador, bomba o molino. El porcentaje anterior
solo describe la hoja actual, no el avance de toda la máquina.

Capacitores de 100 nF y 10 nF: X7R. De 1 µF, 4,7 µF y 10 µF: X5R seleccionados
por suministro. Cerrar temperatura y capacitancia efectiva bajo polarización
antes de liberarlos; no aplicar una sustitución por valor nominal solamente.
Los MPN mecánicos no se elegirán por stock antes de conocer altura, paso y encaje.

## Objetivos de layout

Son decisiones iniciales de diseño, no reglas mínimas publicadas por el fabricante:
- Principal: estudiar cuatro capas para retornos, desacoplo y coexistencia de los
  MCU con los drivers. Frontal: dos capas si la mecánica lo permite.
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
