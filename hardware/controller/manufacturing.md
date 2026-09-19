# Perfil de fabricación de la controladora

Estado: objetivo de diseño para routing, aún no liberado para fabricar.

La principal se configura como FR-4 de dos capas y 1,6 mm, el mismo espesor
medido en la placa original. La placa
es grande y USB funciona a Full Speed, por lo que dos capas siguen siendo la
opción preferida por coste y plazo. La integración de red exige partición física,
no más capas: se mantendrán dos si la colocación permite planos SELV continuos,
rutas de potencia dimensionadas y una barrera primaria-SELV sin cruces. La
asignación prevista es:

| Capa | Uso principal |
|---|---|
| F.Cu | componentes, señales críticas y potencia local |
| B.Cu | plano de GND solo en SELV; retornos/rutas de potencia separados en la zona de red |

El cobre es de 1 oz. Las pistas de red que llevan la corriente de carga se
duplican en las dos caras con vías de cosido en lugar de pasar a 2 oz, que sale
más caro en JLCPCB. La geometría USB se comprobará con
el espesor real y el calculador del fabricante antes de pedir la placa. La pareja
USB tiene por ahora 0,20 mm de ancho y 0,20 mm de separación como regla de
colocación/routing; no se declara todavía como 90 Ω controlados.

## Reglas de KiCad

`tools/configure_controller_rules.py` mantiene las clases de red:

| Clase | Ancho | Separación | Vía / taladro | Redes |
|---|---:|---:|---:|---|
| Mains | 2,50 mm | 1,20 mm* | 1,60 / 0,80 mm | L, N, fases de carga y bus del molinillo |
| Default | 0,20 mm | 0,20 mm | 0,60 / 0,30 mm | lógica y analógicas |
| USB | 0,20 mm | 0,20 mm | 0,60 / 0,30 mm | D+/D− de puerto, protección y dispositivo |
| Power | 0,50 mm | 0,20 mm | 0,80 / 0,40 mm | 3,3 V, 12 V y VBUS |
| Switching | 0,60 mm | 0,25 mm | 0,80 / 0,40 mm | nodos del buck y charge pump |
| Actuator | 1,00 mm | 0,25 mm | 1,00 / 0,50 mm | 24 V, motor y electroválvula |

\* Entre pads de red la limita el paso de 3,96 mm de los VH originales. El mismo
script escribe `controller-core-reva.kicad_dru`, que exige 2,5 mm entre pistas de
redes `Mains` distintas y 8 mm de separación y creepage entre `Mains` y SELV.

Son valores deliberadamente más conservadores que los mínimos publicados por
JLCPCB para cobre de 1 oz. La tabla de capacidades consultada el 2026-09-19
admite dos capas, placas mayores que 141,6 × 135,2 mm y pistas/espacios mucho
menores que 0,20 mm. La fuente es la
[tabla oficial de capacidades de JLCPCB](https://jlcpcb.com/capabilities/Capab).

Como referencia comercial publicada por JLCPCB en la misma fecha, la producción
por superficie se anuncia desde 56 USD/m² para dos capas y 91 USD/m² para cuatro
capas, con plazos anunciados de 24 horas y cuatro días respectivamente. La
cotización real depende de cantidad, acabado, montaje, promociones y envío; esta
comparación justifica mantener dos capas mientras el DRC y la integridad de
retorno lo permitan.

JP8, JP24 y JP17 ya tienen huellas JST VH candidatas. Las áreas temporales de
JP19, JP1 y JP9 bloquean ambas capas hasta identificar sus huellas. Después se
sustituirán por conectores reales y reglas de alta tensión. La zona de red y bus rectificado no compartirá
relleno, vías ni retornos con el plano GND de SELV. La barrera inicial de 8 mm ya se
comprueba en el DRC y se revisará antes de fabricar.

## Antes de generar Gerbers

- Pedir 1,6 mm (espesor de la original) y 1 oz en la cotización y recalcular la
  geometría USB.
- Validar con JLCPCB material, acabado, ranuras y reglas reales de separación de
  la zona de red; aumentar a cuatro capas solo si el layout demuestra que hace falta.
- Revisar capacidad de corriente y temperatura de las pistas de 24 V con cobre,
  longitud, vías y corriente medidas, incluida la corriente de bloqueo del motor.
- Mantener B.Cu como plano de GND, añadir cosido y revisar cada cruce que lo corte.
- Revisar en 3D alturas (≤ 35 mm, cota comprobada con el disipador original),
  orientación de conectores y acceso al USB.
- Ejecutar ERC, DRC, paridad esquema/PCB y una prueba mecánica 1:1.
