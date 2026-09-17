# Mapa I/O preliminar

**No es un pinout. Pines, orientación, polaridad, niveles y asignación MCU: TBD.**
Asociaciones documentales del manual local; requieren cotejo con PCB y arnés concretos.
Página PDF indica índice desde 1, distinto de la numeración por capítulo.

| Función | Conector documental | Manual, página PDF | Pendiente |
|---|---|---|---|
| Bomba | JP24 | 37 | Pines, tensión, corriente y driver TBD |
| Electroválvula | JP3 | 37 | Pines, tensión y estado sin energía TBD |
| Molino | JP8 | 37 | Alimentación, arranque y bloqueo TBD |
| Temperatura | JP13 | 37 | Curva sensor, niveles y circuito TBD |
| Caudalímetro | JP5 | 37 | Alimentación, salida y pulsos/ml TBD |
| Presencia/posición grupo | JP16 | 35–36 | Contactos y lógica exacta TBD |
| Puerta/cajón | JP14 | 35 | Contactos y dependencia mecánica TBD |
| Nivel depósito | JP23 | 34 | Interfaz y niveles TBD |
| Panel frontal original | JP21 | 34 | Pines/niveles TBD; sustituido por frontal nuevo con arnés propio |
| Calentador | TBD | TBD | Potencia, conector y protecciones TBD |
| Motor grupo | TBD | TBD | Tensión, driver y conector TBD |
| Entrada red / PE | TBD | Identificación del propietario | Bornes y protección TBD |

Las etiquetas PWR, EARTH, PUMP, GRINDER, NTC, GR.PULSE y TURBO se leen en la copia
JPEG IMG_1085 de la conversación previa; ver [fotos](HD8911/photos.md).
No equipararlas a conectores JP sin trazabilidad. Ninguna etiqueta
demuestra aislamiento ni nivel lógico compatible con un microcontrolador.

Registro editable: [connectors.csv](HD8911/connectors.csv).

La [interfaz nueva del frontal](../hardware/controller/front-panel-interface.md)
tiene su propia numeración J_UI/J1; no reemplaza ni confirma ninguna cavidad de JP21.
