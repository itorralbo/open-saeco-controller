# Etapa candidata para la electroválvula de 24 V

Estado: pinout de JP3 confirmado; etapa incorporada al esquema y PCB de trabajo. No liberar para
fabricación ni conectar a la máquina hasta ensayar la bobina.

## Datos disponibles

La referencia identificada es `421944029371` y la bobina es OLAB
`6000BH/B0DN`, nominal 24 V DC / 10 W. El catálogo oficial indica tolerancia de
tensión DC ±5 %; la familia 6000BH usa aislamiento clase H (180 °C). La bobina
desconectada mide 56,7 Ω; la estimación resistiva es `24 / 56,7 = 0,423 A` y
`24² / 56,7 = 10,16 W`. El propietario ha seguido el arnés: visto desde arriba,
JP3.1 es el pad cuadrado y llega al pin 1 del solenoide, +24 V; JP3.2 llega al pin 2,
retorno de 0 V. JP3.3–5 no se usan. El terminal GND separado del solenoide no está
conectado.

En modo diodo se miden 0,073 V en ambos sentidos. Esa simetría, junto con los
56,7 Ω, indica que el instrumento está leyendo el devanado y no una unión de diodo
en paralelo. No se ha detectado supresión interna accesible desde los terminales;
la rueda libre externa forma parte necesaria del driver.

JP3 parece JST XH de cinco vías y 2,50 mm. La huella compatible de trabajo es
`JST_XH_S5B-XH-A_1x05_P2.50mm_Horizontal`; se selecciona
`S5B-XH-A(LF)(SN)` (`C263757`), con 8.885 unidades LCSC observadas el 2026-09-19.
La referencia continúa siendo candidata hasta probar el acoplamiento físico.

## Topología propuesta

El esquema implementa un interruptor low-side independiente:

- una rama propia desde `24V_ACT_RAW`, con F304 de 1 A separado;
- D305 bloquea polaridad inversa; JP3.1 va a `24V_VALVE` y JP3.2 al drenador
  como retorno conmutado;
- MOSFET N de 60 V `SI2308A` de UMW (`C347491`), SOT-23, 3 A y
  `RDS(on)` máximo publicado de 95 mΩ a 4,5 V;
- diodo SS34 en paralelo con la bobina, cátodo a +24 V y ánodo al drenador;
- driver de puerta TI `UCC27517DBVR` (`C99395`) alimentado desde
  `12V_PROTECTED`, con 100 nF + 1 µF locales, 33 Ω serie en puerta y 100 kΩ
  puerta-source;
- entrada no inversora desde un GPIO STM32 con 10 kΩ a masa. La entrada inversora
  del UCC27517 queda a masa. Con reset, ausencia de 12 V o UVLO, la válvula queda
  desactivada.

PA7 del STM32 es `VALVE_EN_RAW`. R512 mantiene baja la entrada no inversora de
U502 durante reset y R514 mantiene baja la puerta de Q501; la entrada inversora
queda a masa.

El UCC27517 acepta nivel alto de 2,4 V como máximo de umbral y funciona con
4,5–18 V, de modo que separa la compatibilidad lógica de 3,3 V del requisito de
puerta del MOSFET. El SI2308A tiene mucho margen de corriente para los 0,423 A
estimados; con 95 mΩ la pérdida resistiva ideal sería unos 17 mW. Estas cifras no
sustituyen la medida térmica ni la comprobación de corriente en caliente.

Fuentes: [bobina 6000BH de OLAB](https://www.olabitaly.com/products/fluid-control/direct-indirect-and-mixed-action-solenoid-valves/direct-action-solenoid-valves/coils_211.html),
[UCC27517 de TI](https://www.ti.com/lit/ds/symlink/ucc27517.pdf),
[UCC27517DBVR en LCSC](https://www.lcsc.com/product-detail/C99395.html) y
[SI2308A en LCSC](https://www.lcsc.com/product-detail/C347491.html). El 2026-09-19
se observaron 27.530 unidades del driver y 546.570 del MOSFET; no constituyen una
reserva.

## Ensayos pendientes antes de liberar la etapa

1. Medir corriente de activación y corriente estabilizada con fuente de 24 V
   limitada, además del tiempo de liberación.
2. Comparar el tiempo de liberación con SS34: produce caída lenta y poco ruido;
   un TVS o zéner
   acelera la liberación a costa de mayor tensión. La función hidráulica decidirá.
3. Dimensionar la fuente y J112. Motor y válvula suman aproximadamente 0,862 A
   resistivos. F303 y F304 protegen ahora cada rama por separado, pero la fuente y
   el conector común deben dimensionarse con arranque, bloqueo y margen térmico.
4. Verificar con osciloscopio `VALVE_RETURN`, la tensión máxima de Q501 y el
   comportamiento al conectar/desconectar 12 V y 24 V en cualquier orden.

ERC y DRC geométrico pasan sin infracciones. La PCB principal sigue sin rutear;
esta validación comprueba coherencia del diseño, no el funcionamiento con la carga.
