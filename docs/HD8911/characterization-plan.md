# Plan de caracterización de la HD8911

Estado: propuesta del 2026-09-23. Ningún ensayo está hecho. Los resultados se
registran en el [registro de medidas](measurements.md) con el ID de este plan.

La Rev A se diseña hoy con valores supuestos o derivados, y la primera tanda de
prototipos tiene que convertirlos en medidas. El caso más claro es el molinillo:
la etapa se dimensiona a **3 A**, casi la corriente de bloqueo, en vez de
suponer una corriente de marcha (ver
[etapa del molinillo](../../hardware/power/power-architecture.md#etapa-del-molinillo)).
Este plan reúne los ensayos iniciales que caracterizan la cafetera, qué decisión
desbloquea cada uno y con qué criterio se da por bueno el valor supuesto.

## Reglas comunes

- Cada resultado lleva fecha, operador, instrumento con modelo, temperatura
  ambiente y el estado de la máquina, como en el registro actual. Un valor sin
  instrumento se guarda como observación, no como medida.
- Los ensayos se agrupan por nivel de riesgo:
  - **N0**: máquina desenchufada y sin tensión comprobada.
  - **N1**: solo SELV, con fuente de banco aislada y limitada en corriente.
  - **N2**: máquina conectada a red con su placa original o con el prototipo.
    Los hace una persona cualificada, con un procedimiento aparte revisado y
    solo con instrumentos aislados y sin contacto: pinza amperimétrica, sonda
    diferencial homologada para la categoría, termopar fijado antes de conectar.
    Nunca se abre la máquina ni se toca el cableado con tensión.
- Este documento dice qué medir y para qué. No es un procedimiento de trabajo
  bajo tensión, igual que el resto de la documentación
  ([safety.md](../safety.md)).
- Siempre que se pueda, se mide primero con la **placa original**. Así se
  obtiene la referencia de la máquina sana antes de introducir el prototipo, y
  el prototipo se valida después contra ella.
- No se bloquean motores ni se deja el calentador sin agua para medir el peor
  caso. Las corrientes de bloqueo se calculan con la resistencia del devanado.

## Prioridad

| Prioridad | Qué desbloquea | Ensayos |
|---|---|---|
| A | Cerrar la PCB Rev A: corrientes, térmica y fuente | GR-01 a GR-06, BU-01 a BU-04, VA-01 a VA-03, PU-01 a PU-03, PS-01, PS-02, TH-01 |
| B | Límites y calibraciones del firmware | HT, NT, FL, WL, SW, resto de GR, BU y PU |
| C | Reproducir el comportamiento de la original | OR-01 a OR-08 |

## Molinillo (JP8)

Dimensionado de diseño: 3 A. Bloqueo y arranque derivados: 3,4 A eficaces con
68 Ω. Fusible, triac, pistas y reparto con el calentador valen para cualquier
marcha medida. Solo el puente depende de la medida: si GR-03 no pasa de 1,5 A en
ningún ajuste de molido y GR-06 deja el puente por debajo de 100 °C, el KBP410
se queda. Si no, se cambia a cuatro diodos discretos.

| ID | Nivel | Qué se mide | Condiciones | Instrumento | Decide |
|---|---|---|---|---|---|
| GR-01 | N0 | Resistencia e inductancia del motor | Desconectado, en frío y justo tras moler; LCR a 100 Hz y 1 kHz | Multímetro 4 hilos, LCR | Corriente de bloqueo real; di/dt en conmutación |
| GR-02 | N2 | Corriente de marcha sin grano | Tolva vacía, placa original, 5 s; media y eficaz en el cable de JP8 | Pinza DC/AC de efecto Hall | Umbral de «falta de grano» |
| GR-03 | N2 | Corriente de marcha moliendo | Grano, ajustes de molido fino, medio y grueso; 3 repeticiones | Pinza Hall con salida a osciloscopio | Puente KBP410 (umbral 1,5 A) y tiempo máximo de molido |
| GR-04 | N2 | Pico de arranque | Primeros 200 ms, 10 arranques; con la original y con el prototipo (cruce por cero) | Pinza Hall + osciloscopio | Pico real frente a los 4,8 A calculados; puente y triac |
| GR-05 | N2 | Tensión en JP8 y dV/dt en el triac al apagar | Prototipo; captura de apagado | Sonda diferencial de alta tensión | Si Q708 necesita snubber RC |
| GR-06 | N2 | Temperatura de cápsula de Q708 y BR701 | Prototipo; 5 moliendas de 10 s cada 30 s, y luego 10 moliendas seguidas | Termopar tipo K fijado con cinta de Kapton | Térmica del puente al aire y del perfil compartido; criterio: puente < 100 °C |
| GR-07 | N2 | Gramos por segundo | Por ajuste de molido; pesar 3 moliendas de 5 s | Báscula de 0,1 g | Tiempo de molido por dosis |
| GR-08 | N2 | Corriente con muelas casi vacías | Grano acabándose durante la molienda; registro continuo | Pinza Hall + registrador | Separación entre «falta de grano» y marcha normal; decide si hace falta sensor de corriente |
| GR-09 | N0 | Continuidad del mazo de JP8 y aislamiento a PE | Desconectado | Multímetro; medidor de aislamiento a 500 V DC | Integridad del mazo y del motor |

## Grupo de infusión (JP16) y autodosis

El manual define `I0` entre 100 y 300 mA y objetivos de hasta `I0 + 200 mA`.
El límite resistivo derivado es 0,44 A a 24 V.

| ID | Nivel | Qué se mide | Condiciones | Instrumento | Decide |
|---|---|---|---|---|---|
| BU-01 | N0 | Resistencia del motor en varias posiciones del rotor | 5 posiciones, en frío | Multímetro 4 hilos | Variación del límite de bloqueo |
| BU-02 | N1 | Corriente en vacío | Grupo fuera de la máquina, 24 V limitados a 1 A, los dos sentidos | Fuente de banco + pinza o shunt | Rango del shunt y de `I0` |
| BU-03 | N1 | Corriente en carrera completa | Grupo montado, sin café; registro de toda la carrera | Shunt 0,1 Ω + osciloscopio | Perfil de movimiento, tiempos y timeouts |
| BU-04 | N1 | Pico de arranque e inversión | 10 arranques e inversiones | Igual que BU-03 | Límite de corriente del DRV8876 |
| BU-05 | N2 | Corriente de compresión con café | Dosis de 7, 9 y 11 g; aroma 1, 3 y 5 | Telemetría del prototipo (PA3) | Tabla de autodosis |
| BU-06 | N1 | Tiempo de carrera y separación tras el micro | Registro de micros y corriente | Analizador lógico | Algoritmo de homing (1–2 mm tras el micro) |

## Electroválvula (JP3)

| ID | Nivel | Qué se mide | Condiciones | Instrumento | Decide |
|---|---|---|---|---|---|
| VA-01 | N0 | Resistencia en frío y en caliente | Frío; y tras 10 min activada en banco | Multímetro 4 hilos | Corriente mínima de retención en caliente |
| VA-02 | N1 | Corriente de activación y de retención | 24 V; subida de corriente | Shunt + osciloscopio | Fusible F304 y posible PWM de retención |
| VA-03 | N1 | Temperatura de la bobina con servicio continuo | 30 min activada | Termopar | Ciclo de trabajo admisible |
| VA-04 | N1 | Tensión mínima de apertura y de caída | Rampa lenta de tensión | Fuente de banco | Margen ante caída del rail de 24 V |

## Bomba (JP24)

| ID | Nivel | Qué se mide | Condiciones | Instrumento | Decide |
|---|---|---|---|---|---|
| PU-01 | N0 | Diodo en serie y resistencia de la bobina | Desconectada; modo diodo en los dos sentidos | Multímetro | Confirma la semionda y el control por semiciclos |
| PU-02 | N2 | Corriente eficaz y de pico | Placa original; salida libre y contra el café | Pinza Hall + osciloscopio | Supuesto de 0,4 A; fusible |
| PU-03 | N2 | dV/dt al apagar | Prototipo | Sonda diferencial | Si Q704 necesita snubber RC |
| PU-04 | N2 | Caudal en función del salto de semiciclos | 25, 50, 75 y 100 %; agua a taza | Caudalímetro de la máquina + báscula | Tabla de preinfusión y caudal |
| PU-05 | N2 | Presión de salida | Manómetro en la salida de café, con café real | Manómetro 0–16 bar | Límite de presión y perfil |
| PU-06 | N2 | Temperatura del cuerpo de la bomba | Ciclo 2 min ON / 1 min OFF, 3 ciclos | Termopar | Protector térmico de 100 °C y límites de uso |

## Calentador, caldera y NTC (JP19, JP13)

| ID | Nivel | Qué se mide | Condiciones | Instrumento | Decide |
|---|---|---|---|---|---|
| HT-01 | N0 | Resistencia del calentador en frío | 27,5 Ω ya medidos; repetir con temperatura anotada | Multímetro 4 hilos | Confirma 8,4 A |
| HT-02 | N0 | Continuidad de los dos termostatos de 190 °C | Desconectado | Multímetro | Cadena de protección intacta |
| HT-03 | N0 | Aislamiento del calentador a PE | Desconectado | Medidor de aislamiento a 500 V DC | Seguridad del elemento |
| NT-01 | N0 | Curva R-T del NTC | Baño de agua a 25, 40, 60, 80 y 95 °C | Termómetro de referencia + multímetro | Tabla del firmware frente al manual |
| NT-02 | N2 | Calentamiento desde frío | Placa original; NTC y termopar en la caldera, 5 min | Registro de NTC por multímetro aislado + termopar | Constante térmica y tiempo a consigna (manual: 45 s) |
| NT-03 | N2 | Sobreoscilación y caída durante un café | Placa original; café corto y largo | Igual que NT-02 | Parámetros del control |
| NT-04 | N2 | Pérdida en espera | Caldera caliente, calentador apagado, 10 min | Igual que NT-02 | Mantenimiento en espera |
| NT-05 | N2 | Temperatura en taza | Primer café y siguientes; criterio del manual 69–85 °C y 72–85 °C | Termómetro en taza | Consigna de caldera |
| HT-04 | N2 | Temperatura de cápsula de Q703 y del disipador | Prototipo; calentamiento continuo de 5 min | Termopar | Validar los 5 °C/W del perfil |

## Caudalímetro, nivel y contactos (JP5, JP22, JP14, JP16)

| ID | Nivel | Qué se mide | Condiciones | Instrumento | Decide |
|---|---|---|---|---|---|
| FL-01 | N2 | Pulsos por litro | 3 dispensados de 100 ml pesados | Contador del prototipo + báscula | Calibración frente a los 1925 pulsos/l nominales |
| FL-02 | N1 | Forma de la señal | Banco, soplando o con agua por gravedad | Osciloscopio | Filtro de 1 kΩ/10 nF y umbral |
| WL-01 | N1 | Salida del sensor capacitivo | 3,3 V; depósito lleno, a mitad y vacío | Multímetro + osciloscopio | Si es analógica, push-pull o colector abierto |
| WL-02 | N1 | Histéresis y tiempo de respuesta | Vaciado y llenado lentos | Osciloscopio | Filtro y retardo de «falta de agua» |
| SW-01 | N0 | JP16 puente local | Reposo | Multímetro | Confirma el puente |
| SW-02 | N0 | JP16 presencia de grupo | Grupo fuera y dentro | Multímetro | NO/NC de `BU_PRESENT_N` |
| SW-03 | N0 | JP16 posición de trabajo | Fuera y en trabajo | Multímetro | NO/NC de `BU_WORK_N` |
| SW-04 | N1 | Rebotes de micros y puerta | 20 accionamientos | Osciloscopio | Antirrebote del firmware |

## Alimentación y térmica general

| ID | Nivel | Qué se mide | Condiciones | Instrumento | Decide |
|---|---|---|---|---|---|
| PS-01 | N1 | Consumo simultáneo de 24 V | Grupo en movimiento + válvula + lógica, en banco | Fuente de banco con registro | Confirma el IRM-30-24 (31 W) |
| PS-02 | N2 | Consumo de la original en espera y en cada fase | Placa original | Medidor de potencia de enchufe | Presupuesto total y F701 |
| PS-03 | N2 | Corriente de entrada al enchufar | Placa original y prototipo | Pinza Hall + osciloscopio | Fusible F702 e inrush del IRM-30 |
| TH-01 | N2 | Temperatura del aire dentro de la máquina | Junto a la placa, tras 5 cafés seguidos | Termopar | Ambiente para toda la térmica |
| TH-02 | N2 | Temperatura de la placa original | Mismas condiciones que TH-01 | Cámara térmica sin abrir, por rejillas, o termopar fijado antes | Referencia para el prototipo |

## Comportamiento de la placa original

Se registra en el lado SELV y con instrumentos aislados en el de red. Sirve de
referencia para el firmware y para validar el prototipo con el mismo café.

| ID | Nivel | Qué se registra | Cómo | Decide |
|---|---|---|---|---|
| OR-01 | N2 | Secuencia de encendido | Grupo, válvula, calentador y bomba en el tiempo | Máquina de estados de arranque |
| OR-02 | N2 | Ciclo de café completo | Molido, grupo, preinfusión, bomba y expulsión | Tiempos de cada fase |
| OR-03 | N2 | Aclarado al encender y apagar | Duración y volumen | Receta de aclarado |
| OR-04 | N2 | Vapor o agua caliente, si la variante lo permite | Temperatura y tiempos | Modo vapor |
| OR-05 | N2 | Respuesta a falta de agua y cajón abierto | Provocar cada caso con la máquina en reposo | Tabla de fallos del firmware |
| OR-06 | N2 | Autodosis a lo largo de 10 cafés | Tiempo de molido de cada ciclo | Algoritmo de autodosis |
| OR-07 | N2 | Menú de servicio del manual | Ejecutar cada prueba y anotar lo que hace | Modos de servicio del firmware |
| OR-08 | N0 | Código de firmware y versión de la placa original | Etiquetas y marcados visibles | Trazabilidad de la variante |

## Plantilla de resultados

Copiar al [registro de medidas](measurements.md) una fila por medida:

| ID | Fecha/operador | Instrumento | Condiciones | Resultado/unidad | Evidencia | Decisión |
|---|---|---|---|---|---|---|
| GR-03 | | | ajuste medio, grano | | | KBP410: se queda / diodos discretos |
