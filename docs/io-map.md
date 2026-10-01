# Mapa I/O preliminar

Destino, pieza y pin del MCU de cada conector en la Rev A. El diagrama del manual
confirma destinos, número de posiciones y el color de cada hilo; los pinouts de
JP3, JP5 y JP22 los trazó el propietario. La numeración física de JP14 y JP16
sigue sin confirmar: requiere cotejo con la placa y el arnés.
Página PDF indica índice desde 1, distinto de la numeración por capítulo.

| Función | Conector documental | Manual, página PDF | Confirmado / pendiente |
|---|---|---|---|
| Bomba | JP24 | 37, 59 | ULKA EP5/S GW, 220–230 V AC, 48 W; LEOCO 5001P020013, 2 vías a 5,00 mm (no disponible en JLCPCB); BTA24 + MOC3083 (Q704/U702), orden PB11 vía U604; dV/dt por medir |
| Electroválvula de vapor | JP3 | 37, 59 | OLAB 6000BH/B0DN 24 V DC/10 W; HR A2506WV-05P; JP3.1 cuadrado=+24 V, JP3.2=retorno; 56,7 Ω y 0,073 V en modo diodo en ambos sentidos; [low-side experimental incorporado](../hardware/power/valve-driver.md), orden PA7 vía U602 |
| Molino | JP8 | 37, 59 | Motor V3.2, 68 Ω medidos; servicio a 320 V DC; LEOCO 3941P03*000, 3 vías a 3,96 mm (no disponible en JLCPCB); BTA24 + MOC3083 + T4A + KBP410 (Q708/U703/F703/BR701), orden PC4 vía U604; dimensionado a 3 A, marcha por medir |
| Temperatura | JP13 | 37, 59 | NTC `996530073428`; HR A2506WV-02P; tabla disponible, R25≈49,9 kΩ/B≈4037 K derivados; PA3 (ADC1_IN4) |
| Caudalímetro | JP5 | 37, 59 | Digmesa 932-9521-B, 3,8–20 V, NPN OC, ≈1925 pulsos/l; HR A2506WV-03P; vista cenital: 1 señal, 2 GND, 3 VCC; PA2 (TIM2_CH3) |
| Presencia/posición grupo | JP16 | 35–36, 59 | 8 posiciones: motor, puente y dos micros; presencia en PC2 y trabajo en PA0; orden físico, NO/NC y carcasa TBD |
| Puerta/cajón | JP14 | 35, 59 | Abierto si falta puerta o cajón; cerrado únicamente con ambos colocados; PA1; carcasa TBD |
| Nivel depósito | JP22 | 34, 59 | Módulo capacitivo V3 `421941306721`; rojo VCC, blanco señal, negro GND; 3,3 V elegidos; PC3 (ADC12_IN9); tipo de salida y carcasa TBD |
| Panel frontal original | JP21 | 34, 59 | Würth WR-MM 690367181672 de 16 contactos (propietario, 2026-10-01); pinout original TBD; J104 usa la misma pieza con el pinout nuevo del frontal |
| Calentador | JP19 | 59 | XS4 220–230 V AC, 1900 W, 27,5 Ω medidos; TE RAST 5 1971845-4, 4 lengüetas/2 cableadas; BTA24 + MOC3083 (Q703/U701), orden PC5 vía U603 |
| Motor grupo | JP16 | 59 | 24 V DC reversible, 54,7 Ω medidos; DRV8876 (U501): PWM PF0, dirección PC14, nSLEEP PB5 vía U602, nFAULT PB6, corriente PC0; medida de corriente de compresión para autodosis |
| Entrada de red | JP17 | 59 | TE RAST 5 1971845-3, 3 lengüetas (carcasa del mazo TE 2-1241961-7), 2 cableadas después del interruptor bipolar; F701, RV701 y relé general K701 (armado por PB7 vía U603) |
| Tierra de protección | JP1 / JP9 | 59 | Caldera / entrada IEC; lengüetas TE 63824-1 unidas en la placa; continuidad y construcción de protección por comprobar |

Las etiquetas PWR, EARTH, PUMP, GRINDER, NTC, GR.PULSE y TURBO se leen en la copia
JPEG IMG_1085 de la conversación previa; ver [fotos](HD8911/photos.md).
No equipararlas a conectores JP sin trazabilidad. Ninguna etiqueta
demuestra aislamiento ni nivel lógico compatible con un microcontrolador.

Registro editable: [connectors.csv](HD8911/connectors.csv).
Resumen cotejado del diagrama: [electrical-diagram.md](HD8911/electrical-diagram.md).
Requisitos por referencia: [components.md](HD8911/components.md).

La [interfaz nueva del frontal](../hardware/controller/front-panel-interface.md)
tiene su propia numeración J_UI/J1; no reemplaza ni confirma ninguna cavidad de JP21.
