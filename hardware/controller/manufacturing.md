# Perfil de fabricación de la controladora

Estado: objetivo de diseño para routing, aún no liberado para fabricar.

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

\* Entre pads de red la limita el paso de 3,96 mm de los conectores de JP8 y JP24. El mismo
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

JP8 y JP24 tienen huellas JST VH candidatas, pendientes de identificar (sus
carcasas miden más que las VH). JP19 y JP17 son los TE 1971845-4 y 1971845-3 y
JP1/JP9 son TE 63824-1. La zona de red y bus rectificado no comparte relleno,
vías ni retornos con el plano GND de SELV. La barrera inicial de 8 mm ya se
comprueba en el DRC y se revisará antes de fabricar.

## Antes de generar Gerbers

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
