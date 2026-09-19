# Mapa I/O preliminar

**No es todavía un pinout eléctrico.** El diagrama del manual confirma destinos,
número de posiciones y parte del cableado, pero no la numeración física de los pines,
los niveles ni la asignación MCU. Requiere cotejo con PCB y arnés concretos.
Página PDF indica índice desde 1, distinto de la numeración por capítulo.

| Función | Conector documental | Manual, página PDF | Confirmado / pendiente |
|---|---|---|---|
| Bomba | JP24 | 37, 59 | ULKA EP5/S GW, 220–230 V AC, 48 W; driver y transitorios TBD |
| Electroválvula de vapor | JP3 | 37, 59 | OLAB 6000BH/B0DN 24 V DC/10 W; JP3.1 cuadrado=+24 V, JP3.2=retorno; 56,7 Ω y 0,073 V en modo diodo en ambos sentidos; [low-side experimental incorporado](../hardware/power/valve-driver.md) |
| Molino | JP8 | 37, 59 | Motor V3.2, 68 Ω medidos; servicio a 320 V DC; corriente dinámica y driver HV TBD |
| Temperatura | JP13 | 37, 59 | NTC `996530073428`; tabla disponible, R25≈49,9 kΩ/B≈4037 K derivados |
| Caudalímetro | JP5 | 37, 59 | Digmesa 932-9521-B, 3,8–20 V, NPN OC, ≈1925 pulsos/l; vista cenital: 1 señal, 2 GND, 3 VCC |
| Presencia/posición grupo | JP16 | 35–36, 59 | 8 posiciones: motor, puente y dos micros; orden físico y lógica exacta TBD |
| Puerta/cajón | JP14 | 35, 59 | Abierto si falta puerta o cajón; cerrado únicamente con ambos colocados |
| Nivel depósito | JP22 | 34, 59 | Módulo capacitivo V3 `421941306721`; rojo VCC, blanco señal, negro GND; 3,3/5 V, salida TBD |
| Panel frontal original | JP21 | 34, 59 | Multipolar; pines/niveles TBD; sustituido por frontal nuevo con arnés propio |
| Calentador | JP19 | 59 | XS4 220–230 V AC, 1900 W; 4 posiciones/2 cableadas; driver y protecciones TBD |
| Motor grupo | JP16 | 59 | 24 V DC reversible, 54,7 Ω medidos; medida de corriente de compresión para autodosis; DRV8876 experimental incorporado |
| Entrada de red | JP17 | 59 | 3 posiciones, 2 cableadas después del interruptor bipolar; no conectar a Rev A |
| Tierra de protección | JP1 / JP9 | 59 | Caldera / entrada IEC; continuidad y construcción de protección TBD |

Las etiquetas PWR, EARTH, PUMP, GRINDER, NTC, GR.PULSE y TURBO se leen en la copia
JPEG IMG_1085 de la conversación previa; ver [fotos](HD8911/photos.md).
No equipararlas a conectores JP sin trazabilidad. Ninguna etiqueta
demuestra aislamiento ni nivel lógico compatible con un microcontrolador.

Registro editable: [connectors.csv](HD8911/connectors.csv).
Resumen cotejado del diagrama: [electrical-diagram.md](HD8911/electrical-diagram.md).
Requisitos por referencia: [components.md](HD8911/components.md).

La [interfaz nueva del frontal](../hardware/controller/front-panel-interface.md)
tiene su propia numeración J_UI/J1; no reemplaza ni confirma ninguna cavidad de JP21.
