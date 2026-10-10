# Perfil de fabricación de la controladora

Estado: perfil aplicado a la PCB ruteada y [paquete JLCPCB candidato](#paquete-jlcpcb-candidato)
generado; aún no liberado para fabricar.

La principal es FR-4 de cuatro capas y 1,6 mm, el mismo espesor medido en la
placa original. Se pasó de dos a cuatro capas el 2026-09-23: con dos, B.Cu era a
la vez plano de GND y capa de saltos, y cada salto troceaba el plano; los
últimos 29 enlaces de señal no cabían sin decenas de vías más, y el 3,3 V
viajaba como una espina de 506 mm con una docena de saltos. El apilado es el
estándar de JLCPCB, JLC04161H-7628, según su
[página de impedancias](https://jlcpcb.com/impedance) (consultada el
2026-09-23):

| Capa | Cobre | Uso |
|---|---|---|
| F.Cu | 1 oz (0,035 mm) | componentes, señales y potencia local |
| preimpregnado 7628 | 0,2104 mm, εr 4,4 | |
| In1.Cu | 0,5 oz (0,0152 mm) | plano GND_UI continuo en el lado SELV, referencia de F.Cu |
| núcleo | 1,065 mm, εr 4,6 | |
| In2.Cu | 0,5 oz (0,0152 mm) | plano 3V3_CORE en el lado SELV |
| preimpregnado 7628 | 0,2104 mm, εr 4,4 | |
| B.Cu | 1 oz (0,035 mm) | señales y saltos, sin plano |

`tools/configure_controller_stackup.py` escribe este apilado en la placa y
`layout_controller_pcb.py` fija las cuatro capas de cobre; las áreas de regla
(barrera, paso de red y ranuras de optos) cubren las cuatro, y la del pie del
disipador todas menos B.Cu.

- Ninguna capa interna lleva cobre en el dominio de red: los dos planos acaban
  en el borde SELV de la banda de barrera y el DRC los mantiene a 8 mm de todo
  cobre `Mains`. Las fases siguen duplicadas en F.Cu y B.Cu.
- In2.Cu solo lleva dos pistas de señal: las subidas de `BREW_SLEEP_INTERLOCK`
  y `WATCHDOG_KICK_RAW` junto al supervisor (33 mm en total), para que el bus
  de sensores cruce esa columna por B.Cu. Son líneas lentas y el plano de
  3,3 V sigue siendo una sola pieza.
- El plano de 3,3 V sustituye la antigua espina: cada condensador de desacoplo
  y cada grupo de pads baja a él con su propia vía.

El cobre exterior es de 1 oz. Las pistas de red que llevan la corriente de
carga se duplican en las dos caras con vías de cosido en lugar de pasar a 2 oz,
que sale más caro en JLCPCB. La pareja USB va en F.Cu sobre el plano de masa de
In1.Cu, a 0,21 mm. Con la calculadora de JLCPCB para este apilado
(2026-09-23), 90 Ω diferenciales piden 0,29 mm de ancho y 0,20 mm de
separación; es la regla de la clase USB y el ancho del tramo acoplado. No se
pide impedancia controlada: el USB es Full Speed y el par es corto (ver
[service-usb.md](../../docs/service-usb.md)).

Rellenos exteriores (2026-09-23): en el lado SELV, F.Cu y B.Cu llevan masa
`GND_UI`, cosida al plano de In1.Cu con vías de 0,6 mm en una rejilla de 5 mm
donde caben. Ayudan a disipar bajo los reguladores y el puente H, apantallan y
equilibran el cobre. Los pads SMD se unen macizos y los de agujero pasante con
alivios. Separación de 0,5 mm alrededor, para no bajar la impedancia del par
USB. En el lado de red no hay relleno: no queda cobre flotante en el dominio
primario, y las reglas de 8 mm mantienen la masa lejos de todo cobre `Mains`.

## Reglas de KiCad

`tools/configure_controller_rules.py` mantiene las clases de red:

| Clase | Ancho | Separación | Vía / taladro | Redes |
|---|---:|---:|---:|---|
| Mains | 2,50 mm | 1,20 mm* | 1,60 / 0,80 mm | L, N, fases de carga y bus del molinillo |
| Default | 0,20 mm | 0,20 mm | 0,60 / 0,30 mm | lógica y analógicas |
| USB | 0,20 mm (par 0,29 / 0,20) | 0,20 mm | 0,60 / 0,30 mm | D+/D− de puerto, protección y dispositivo |
| Power | 0,50 mm | 0,20 mm | 0,80 / 0,40 mm | 3,3 V, 12 V y VBUS |
| Switching | 0,60 mm | 0,25 mm | 0,80 / 0,40 mm | nodos del buck y charge pump |
| Actuator | 1,00 mm | 0,25 mm | 1,00 / 0,50 mm | 24 V, motor y electroválvula |

\* Entre pads de red la limita el paso de 3,96 mm de la cabecera LEOCO 3941 de JP8. El mismo
script escribe `controller-core-reva.kicad_dru`, que exige 2,5 mm entre pistas de
redes `Mains` distintas y 8 mm de separación y creepage entre `Mains` y SELV.

Son valores deliberadamente más conservadores que los mínimos publicados por
JLCPCB para cobre de 1 oz. La tabla de capacidades consultada el 2026-09-19
admite dos capas, placas mayores que 141,6 × 135,2 mm y pistas/espacios mucho
menores que 0,20 mm. La fuente es la
[tabla oficial de capacidades de JLCPCB](https://jlcpcb.com/capabilities/Capab).

Como referencia comercial publicada por JLCPCB el 2026-09-19, la producción
por superficie se anuncia desde 56 USD/m² para dos capas y 91 USD/m² para cuatro
capas, con plazos anunciados de 24 horas y cuatro días respectivamente. La
cotización real depende de cantidad, acabado, montaje, promociones y envío. El
sobrecoste se acepta a cambio de planos continuos y de un ruteo cerrado sin
trocear la masa.

JP8 y JP24 son las LEOCO 3941P03*000 y 5001P020013; JLCPCB no las monta, así
que van a mano o como piezas aportadas. JP19 y JP17 son los TE 1971845-4 y 1971845-3 y
JP1/JP9 son TE 63824-1. La zona de red y bus rectificado no comparte relleno,
vías ni retornos con el plano GND de SELV. La barrera inicial de 8 mm ya se
comprueba en el DRC y se revisará antes de fabricar.

## Paquete JLCPCB candidato

`tools/export_controller_fab.py` lo escribe en [fabrication/](fabrication/) desde
la PCB y la [BOM](bom-draft.csv). No es una liberación: el script lista al final
lo que sigue abierto (hoy nada) y saca de la BOM de JLCPCB lo que no tenía stock
en la última consulta (`tools/refresh_jlc_stock.py`): hoy J104 (Würth WR-MM),
J106 (HR A2506WV-03P) y J108 (HR A2506WV-08P), THT, que se compran aparte y se
sueldan a mano. Los de J106 y J108 pueden salir de la placa original, que lleva
las mismas cabeceras.

| Archivo | Contenido |
|---|---|
| [controller-core-reva-gerbers.zip](fabrication/controller-core-reva-gerbers.zip) | Gerber de 4 capas (extensiones Protel, máscara restada de la serigrafía), trabajo `.gbrjob` con el apilado, Excellon en mm con PTH y NPTH separados, y mapas de taladros |
| [controller-core-reva-bom-jlcpcb.csv](fabrication/controller-core-reva-bom-jlcpcb.csv) | 70 líneas / 210 posiciones: Comment, Designator, Footprint, LCSC Part # |
| [controller-core-reva-cpl-jlcpcb.csv](fabrication/controller-core-reva-cpl-jlcpcb.csv) | Designator, Mid X, Mid Y, Layer, Rotation (todas Top) |
| [controller-core-reva-not-assembled.csv](fabrication/controller-core-reva-not-assembled.csv) | Lo que JLCPCB no monta y por qué |

Los PTH y NPTH van en ficheros separados: en uno solo, únicamente los comentarios
del Excellon dicen qué agujero se metaliza. JLCPCB no monta:

- J111 (DNP) y J121: puentes de soldadura, cobre sin pieza.
- R415 y R416 (DNP): polarización de JP22, a la espera de WL-01 (issue #7).
- C705, R727, C706 y R728 (DNP, cara inferior): snubbers RC de Q704 y Q708, a
  la espera de PU-03 y GR-05.
- C708 (DNP, cara inferior): supresión del molinillo, a la espera de EM-01.

C707, el X2 de entrada, es la única pieza montada en la cara inferior. Con él en
el CPL el pedido es de montaje a doble cara; si sale más barato, se quita del
CPL y se suelda a mano (2220).
- J115 y J117 (LEOCO de JP8 y JP24): sin código JLCPCB, se sueldan a mano o se aportan.
- RV701: sin pieza hasta elegir el MOV.

Opciones del pedido: 4 capas, 1,6 mm, apilado JLC04161H-7628 (1 oz exterior,
0,5 oz interior), sin impedancia controlada. Montaje en la cara superior; hay
piezas THT y el ESP32 es «Standard Only», así que va en montaje Standard.
`check_controller_core.py` falla en CI si la BOM o el CPL dejan de coincidir con
la BOM de diseño; no comprueba los Gerbers, que hay que regenerar tras cada
cambio de la PCB.

En la vista previa de JLCPCB, antes de confirmar: pin 1 de U101, U201 y de cada
integrado; polaridad de diodos, puentes rectificadores y electrolíticos; y la
boca de cada conector hacia el borde. Las rotaciones del CPL son las de KiCad;
si una pieza sale girada, se corrige allí y se anota aquí.

La huella de KiCad del ESP32-S3-WROOM-1U lleva 12 vías de 0,2 mm en el pad de
masa central, sin tapar. Confirmar con JLCPCB el taladro de 0,2 mm y si la
soldadura se escapa por ellas.

## Antes de pedir

- Pedir JLC04161H-7628 (1,6 mm, 1 oz exterior y 0,5 oz interior). La
  geometría USB ya está calculada con ese apilado.
- Validar con JLCPCB material, acabado, ranuras y reglas reales de separación de
  la zona de red, también entre capas internas y externas.
- Revisar capacidad de corriente y temperatura de las pistas de 24 V con cobre,
  longitud, vías y corriente medidas, incluida la corriente de bloqueo del motor.
- Revisar las dos ranuras de In2.Cu bajo el supervisor (los rellenos
  exteriores ya están decididos).
- Revisar en 3D alturas (≤ 35 mm, cota comprobada con el disipador original),
  orientación de conectores y acceso al USB.
- Ejecutar ERC, DRC, paridad esquema/PCB y la prueba mecánica 1:1 con
  `preview/controller-top-1to1.pdf` impreso al 100 %.
- Refrescar stock (`tools/refresh_jlc_stock.py`), regenerar el paquete y
  revisarlo en el visor de Gerbers de JLCPCB.
