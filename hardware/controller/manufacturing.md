# Perfil de fabricación de la controladora

Estado: objetivo de diseño para routing, aún no liberado para fabricar.

La principal se configura como FR-4 de cuatro capas y 1,6 mm. La asignación
prevista es:

| Capa | Uso principal |
|---|---|
| F.Cu | componentes, señales críticas y potencia local |
| In1.Cu | plano continuo de GND |
| In2.Cu | distribución de 3,3/12/24 V y señales lentas donde sea necesario |
| B.Cu | señales secundarias y relleno de GND |

El cobre de 1 oz es la referencia inicial. El stack-up exacto y la geometría de
USB se elegirán en la calculadora de impedancia del fabricante antes de pedir la
placa. La pareja USB tiene por ahora 0,20 mm de ancho y 0,20 mm de separación
como regla de colocación/routing; no se declara todavía como 90 Ω controlados.

## Reglas de KiCad

`tools/configure_controller_rules.py` mantiene las clases de red:

| Clase | Ancho | Separación | Vía / taladro | Redes |
|---|---:|---:|---:|---|
| Default | 0,20 mm | 0,20 mm | 0,60 / 0,30 mm | lógica y analógicas |
| USB | 0,20 mm | 0,20 mm | 0,60 / 0,30 mm | D+/D− de puerto, protección y dispositivo |
| Power | 0,50 mm | 0,20 mm | 0,80 / 0,40 mm | 3,3 V, 12 V y VBUS |
| Switching | 0,60 mm | 0,25 mm | 0,80 / 0,40 mm | nodos del buck y charge pump |
| Actuator | 1,00 mm | 0,25 mm | 1,00 / 0,50 mm | 24 V, motor y electroválvula |

Son valores deliberadamente más conservadores que los mínimos publicados por
JLCPCB para cobre de 1 oz. La tabla de capacidades consultada el 2026-09-19
admite cuatro capas, placas mayores que 141,6 × 135,2 mm y pistas/espacios mucho
menores que 0,20 mm. La fuente es la
[tabla oficial de capacidades de JLCPCB](https://jlcpcb.com/capabilities/Capab).

Las áreas de JP8, JP19, JP24, JP17, JP1 y JP9 bloquean todas las capas de cobre.
Aunque esas conexiones no están implementadas, no se deben cruzar con pistas ni
planos: quedan reservadas para mantener la mecánica de sustitución y para no
comprometer una futura revisión de potencia.

## Antes de generar Gerbers

- Elegir en la cotización un stack-up real de cuatro capas y recalcular USB.
- Revisar capacidad de corriente y temperatura de las pistas de 24 V con cobre,
  longitud, vías y corriente medidas, incluida la corriente de bloqueo del motor.
- Añadir planos, cosido de GND y reglas de retorno después de fijar rutas críticas.
- Revisar en 3D alturas, orientación de conectores y acceso al USB.
- Ejecutar ERC, DRC, paridad esquema/PCB y una prueba mecánica 1:1.
