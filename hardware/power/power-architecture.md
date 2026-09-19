# Arquitectura de alimentación y separación — Rev A

Estado: decisión de diseño para prototipo, no liberada para fabricar ni conectar
a red. El objetivo es poder desarrollar y medir la controladora sin introducir
todavía 230 V AC ni el bus rectificado del molino en la PCB principal.

## Decisión para la Rev A de banco

La controladora mantiene dos entradas DC procedentes de fuentes externas,
aisladas y limitadas en corriente:

| Entrada | Uso | Protección presente | Límite actual |
|---|---|---|---|
| J101, 12 V DC | buck de 3,3 V, lógica, frontal, caudalímetro y driver de puerta | F301 1 A, inversión y TVS | no alimentar actuadores |
| J112, 24 V DC | motor del grupo y electroválvula | ramas F303/F304 de 1 A e inversión independientes | fuente de laboratorio limitada |
| J110, USB-C 5 V | datos y alimentación opcional de lógica en banco | PTC 500 mA, diodo y puente J111 abierto | J111 solo se cierra expresamente en banco |

J101 y J112 comparten la masa lógica en la controladora. Por ello ambas fuentes
deben ser salidas SELV aisladas de red; no se conectará el negativo a un nodo de
potencia de la máquina. La entrada USB solo se conecta cuando todo el montaje
alimentado pertenece al dominio aislado de banco.

Esta decisión permite cerrar y rutear la zona de baja tensión. La fuente final
integrada se elegirá después de medir consumo, temperatura y espacio. No es
necesario esperar a esa elección para probar firmware, sensores, motor del grupo
y electroválvula.

La principal mide ambos rails con divisores 200 kΩ/10 kΩ: PA4/ADC2_IN17 recibe
`12V_PROTECTED` y PA5/ADC2_IN13 recibe `24V_ACT_RAW`. J114 expone rails y señales
ADC para contrastarlas con el multímetro durante las pruebas por USB.

## Presupuesto provisional de 24 V

Las resistencias medidas permiten calcular un punto de partida, no la corriente
nominal de los motores:

| Carga | Dato | Corriente resistiva | Potencia resistiva |
|---|---:|---:|---:|
| Motor del grupo | 54,7 Ω | 0,439 A | 10,53 W |
| Electroválvula | 56,7 Ω | 0,423 A | 10,16 W |
| Ambas | — | 0,862 A | 20,69 W |

El DRV8876 limita inicialmente el motor a aproximadamente 1 A. El peor caso de
diseño de las dos ramas activas es por tanto 1,423 A, antes de tolerancias y
transitorios. Para las primeras pruebas se requiere una fuente ajustable de
24 V capaz de al menos 1,5 A, configurada al principio con un límite mucho menor
y aumentado de forma controlada. Una fuente de 2 A aporta margen para observar
el arranque sin convertir esa cifra en la especificación final.

F303 y F304 protegen las ramas por separado; no se presupone que un fusible de
1 A común pueda distinguir un bloqueo del motor del funcionamiento simultáneo.
El valor y la curva de los fusibles se revisarán con las formas de onda reales.

## Presupuesto provisional de 12 V

El AP63203 puede entregar hasta 2 A a 3,3 V. A plena carga serían 6,6 W de salida;
con una eficiencia conservadora del 85 %, la entrada demandaría unos 0,65 A a
12 V. El caudalímetro añade menos de 8 mA y el driver de puerta de la válvula una
carga pequeña frente al buck. F301 de 1 A deja margen provisional, pero no valida
el consumo del display ni el arranque simultáneo de los radios.

El ensayo debe registrar corriente media y pico con STM32, ESP32, Wi-Fi, display
y retroiluminación activos. Si el conjunto supera el margen térmico del buck o
del fusible, se corrige la arquitectura antes de elegir la fuente final.

## Potencia de red y molino

JP17 (red), JP24 (bomba), JP19 (calentador) y JP8 (molino a 320 V DC de servicio)
quedan fuera del dominio de baja tensión de esta revisión. Sus conectores pueden
identificarse y reservarse, pero no se colocan ni se cablean en la principal de
banco.

El siguiente diseño de potencia debe incluir, como bloque revisable por separado:

- corte seguro de calentador, bomba y molino en reset, watchdog y fallo;
- aislamiento de sus órdenes y retornos respecto de USB, sensores y usuario;
- protección de sobrecorriente y sobretensión dimensionada con medidas reales;
- corte térmico independiente del firmware para el calentador;
- separación física, ranuras, stack-up, materiales y envolvente definidos antes
  de fijar reglas de aislamiento;
- puesta a tierra y unión de pantallas/chasis verificadas en el conjunto mecánico.

Hasta cerrar esos puntos, el banco usa cargas DC aisladas y no energiza los
conectores de red. Esta limitación se aplica aunque ERC y DRC resulten limpios.

## Secuencia de validación

1. Alimentar solo J101 con límite de corriente; comprobar 3,3 V, reset, USB y
   consumo con el frontal apagado y encendido.
2. Conectar J112 sin cargas y verificar que motor y válvula permanecen apagados
   durante arranque, reset y timeout del watchdog.
3. Probar la electroválvula con límite bajo; medir corriente, drenador, liberación
   y temperatura antes de aumentar el tiempo activado.
4. Probar el motor del grupo sin carga y después en la máquina; registrar arranque,
   inversión, frenado, bloqueo, `IPROPI`, `nFAULT` y temperatura.
5. Recalcular fuente, fusibles, bulk y TVS a partir de los máximos observados.

La incorporación de cualquier etapa conectada a red requiere su propio esquema,
reglas de PCB, revisión y plan de ensayo; no se deduce de este documento.
