# Diagrama de interconexión del manual

Fuente cotejada visualmente el 2026-09-18: manual de servicio HD8911/01,
página PDF 59, capítulo 10 «ELECTRICAL DIAGRAM», hoja 1/1. Es un diagrama de
cableado entre conjuntos; no muestra los componentes ni las pistas de la PCB.
La orientación y las posiciones descritas son las del dibujo, no una vista del
lado del cable ni una numeración garantizada del conector físico.

## Información confirmada

| Ref. principal | Posiciones dibujadas | Conductores usados | Destino |
|---|---:|---:|---|
| JP17 | 3 | 2 | Red después del interruptor general: negro y azul |
| JP1 / JP9 | 1 + 1 | 1 + 1 | Tierra de caldera / tierra desde IEC |
| JP19 | 4 | 2 | Calentador de la caldera, con protecciones térmicas externas en serie |
| JP24 | 2 | 2 | Bomba |
| JP8 | 3 | 2 | Motor de molinillo; blanco a `+`, centro libre, negro a `-` en el dibujo |
| JP3 | 5 | 2 | Electroválvula; se usan las dos posiciones superiores del dibujo |
| JP5 | 3 | 3 | Caudalímetro |
| JP13 | 2 | 2 | Sensor de temperatura de la caldera |
| JP22 | 3 | 3 | Sensor de nivel del depósito |
| JP16 | 8 | 8 | Motor de grupo, puente local y dos microinterruptores |
| JP14 | 2 | 2 | Microinterruptor de puerta/cajón |
| JP21 | multipolar | multipolar | Placa de interfaz original |
| JP2 | no indicado | 0 | Marcado expresamente `NOT CONNECT` |
| PROG. | multipolar | multipolar | Programador; protocolo sin identificar |

En JP16, de izquierda a derecha en la hoja: rojo al `+` del motor, azul al `-`,
dos negros unidos por un puente local, dos verdes para presencia del grupo y dos
rojos para posición de trabajo. Esta secuencia se registra como posición visual
`V1..V8`; todavía no se denomina pin 1..8 de la pieza física.

## Consecuencias para la Rev A

- Corrige el nivel de agua a **JP22 de tres vías**. La asociación anterior con
  JP23 y dos vías era incorrecta.
- Permite reservar dos entradas de sensor de tres hilos (JP5 y JP22), una entrada
  analógica de dos hilos para JP13 y tres pares de contactos: JP14 y los dos de JP16.
- JP16 mezcla motor y contactos en un mismo conector. El acondicionamiento lógico
  y la etapa del motor deben mantenerse diferenciados aunque compartan carcasa.
- JP17 introduce red y JP19 conduce el circuito del calentador. La controladora
  actual solo acepta 12 V DC aislados por J101; este documento no autoriza conectar
  JP17 o JP19 al subconjunto de baja tensión actual ni selecciona por sí solo los
  drivers de potencia. Ambos conectores y sus etapas sí son obligatorios en la
  principal completa.
- JP2 debe permanecer sin uso hasta encontrar documentación que contradiga de
  forma verificable la indicación `NOT CONNECT`.

## Datos eléctricos añadidos por referencias y modo de servicio

La identificación de componentes y otras secciones del manual cierran tensiones,
potencia del calentador y bomba, curva NTC y características del caudalímetro. El
resultado se mantiene en [components.md](components.md).

Siguen sin conocerse corrientes dinámicas de motores, pinout del sensor capacitivo,
COM/NO/NC de los dos micros de JP16, pinout de JP21 o PROG. y referencias completas
de las carcasas. Estos datos requieren continuidad sin tensión y ensayos específicos
antes de cerrar las etapas eléctricas.
