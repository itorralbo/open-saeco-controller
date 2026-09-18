# Etapa candidata para la electroválvula de 24 V

Estado: diseño previo al esquema. No liberar para fabricación ni conectar a la
máquina hasta confirmar el pinout físico de JP3 y ensayar la bobina.

## Datos disponibles

La referencia identificada es `421944029371`, nominal 24 V DC / 10 W. La bobina
desconectada mide 56,7 Ω; la estimación resistiva es `24 / 56,7 = 0,423 A` y
`24² / 56,7 = 10,16 W`. El manual dibuja dos conductores en las dos posiciones
superiores de JP3, pero todavía no fija qué cavidades físicas son ni la polaridad.

JP3 parece JST XH de cinco vías y 2,50 mm. La huella compatible de trabajo es
`JST_XH_S5B-XH-A_1x05_P2.50mm_Horizontal`; la referencia JST disponible
`S5B-XH-A-1(LF)(SN)` (`C163038`) tenía solo 10 unidades observadas, por lo que el
conector no se congela y habrá que refrescar suministro o aprobar un equivalente.

## Topología propuesta

Se propone un interruptor low-side independiente:

- una rama propia desde `24V_BREW_RAW`, con fusible separado de 0,75–1 A;
- JP3: un contacto a `24V_VALVE_FUSED` y el otro al drenador;
- MOSFET N de 60 V `SI2308A` de UMW (`C347491`), SOT-23, 3 A y
  `RDS(on)` máximo publicado de 95 mΩ a 4,5 V;
- diodo SS34 en paralelo con la bobina, cátodo a +24 V y ánodo al drenador;
- driver de puerta TI `UCC27517DBVR` (`C99395`) alimentado desde
  `12V_PROTECTED`, con 100 nF + 1 µF locales, 33 Ω serie en puerta y 100 kΩ
  puerta-source;
- entrada no inversora desde un GPIO STM32 con 10 kΩ a masa. La entrada inversora
  del UCC27517 queda a masa. Con reset, ausencia de 12 V o UVLO, la válvula queda
  desactivada.

El UCC27517 acepta nivel alto de 2,4 V como máximo de umbral y funciona con
4,5–18 V, de modo que separa la compatibilidad lógica de 3,3 V del requisito de
puerta del MOSFET. El SI2308A tiene mucho margen de corriente para los 0,423 A
estimados; con 95 mΩ la pérdida resistiva ideal sería unos 17 mW. Estas cifras no
sustituyen la medida térmica ni la comprobación de corriente en caliente.

Fuentes: [UCC27517 de TI](https://www.ti.com/lit/ds/symlink/ucc27517.pdf),
[UCC27517DBVR en LCSC](https://www.lcsc.com/product-detail/C99395.html) y
[SI2308A en LCSC](https://www.lcsc.com/product-detail/C347491.html). El 2026-09-19
se observaron 27.530 unidades del driver y 546.570 del MOSFET; no constituyen una
reserva.

## Decisiones pendientes antes del esquema

1. Identificar las dos cavidades de JP3 mirando el conector desde la cara de
   componentes y anotar la posición del pad cuadrado/pin 1.
2. Medir la bobina en modo diodo en ambos sentidos. Si aparece una caída de diodo
   integrada, conservar esa polaridad y revisar el diodo externo.
3. Confirmar si el arnés o la válvula incorpora supresión. Dos cables negros no
   demuestran ausencia de polaridad.
4. Medir corriente de activación y corriente estabilizada con fuente de 24 V
   limitada, además del tiempo de liberación.
5. Decidir la supresión: SS34 produce caída lenta y poco ruido; un TVS o zéner
   acelera la liberación a costa de mayor tensión. La función hidráulica decidirá.
6. Recalcular la entrada de 24 V. Motor y válvula suman aproximadamente 0,862 A
   resistivos, demasiado cerca de F303=1 A para autorizar uso simultáneo. Cada
   carga debe tener fusible propio y la fuente/conector común deben dimensionarse
   con arranque, bloqueo y margen térmico.

Hasta cerrar esas medidas, el siguiente commit eléctrico debe limitarse a reservar
GPIO y espacio; no debe asumir polaridad ni numeración de JP3.
