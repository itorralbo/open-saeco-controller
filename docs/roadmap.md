# Roadmap y validación

| Hito | Entregable | Aceptación |
|---|---|---|
| A0 | Documentación y scaffolding | Estructura y pruebas de bloqueo |
| A1 | Reverse engineering | Pines, niveles, orientación y evidencia revisados |
| A2 | Banco lógico | BSP, simulación de sensores y fallos, protocolo probado |
| A3 | Hardware | Esquema, BOM, PCB y revisión independiente |
| A4 | Ensayos potencia | Plan revisado, resultados y riesgos cerrados |
| A5 | Rev A funcional | Ciclo USB/web sin electrónica original y fallos validados |

Prioridades: comprobar la principal en papel 1:1 contra la placa y los mazos,
comprobar el acoplamiento de las cabeceras con los mazos, medir las
cargas y la emisión conducida (ver el plan de caracterización), revisión de aislamiento, BSP, protocolo
y límites de receta.
El frontal nuevo copia la mecánica de botones y usa una pantalla reemplazable:
[PCB ruteada y paquete JLCPCB candidato](../hardware/front-panel/README.md), con
la geometría recuperada por fotogrametría y un ST7789 2,0" como display de
referencia. Falta cerrar el MPN del panel y el adaptador. La reutilización de la
electrónica del panel original deja de ser objetivo. OTA y MQTT quedan para después.

Principal: [STM32 + ESP32](../hardware/controller/core-design.md)
con conexiones de depuración/UART, USB-C de servicio, fuente de baja tensión,
entradas de NTC, caudalímetro, nivel de agua y contactos. El motor del grupo
tiene un DRV8876 y la válvula una etapa low-side, las dos desde el rail de 24 V
con fusibles separados.
Calentador, bomba y molino tienen ya su etapa en el esquema y en la PCB; ninguna
carga está ensayada.
El [watchdog e interlock hardware](../hardware/power/watchdog-interlock.md) ya
reinicia el STM32 y anula todas las órdenes de carga ante timeout o reset; falta
implementar el pulso periódico en PB4 y validar la temporización real.
La [arquitectura de alimentación Rev A](../hardware/power/power-architecture.md)
mantiene dos fuentes DC externas aisladas para el banco, pero la principal final
integra en la misma PCB la entrada de red, la fuente aislada, calentador, bomba y
molino. El interlock hardware cubre ya todas las cargas, y sus órdenes están
ruteadas desde el STM32. Desde el 2026-09-23 la PCB es de cuatro capas y todas
sus redes están conectadas (DRC sin infracciones). Desde el mismo día tiene
rellenos de masa exteriores en el lado SELV, serigrafía con el nombre de cada
conector y el par USB calculado a 90 Ω; falta la comprobación en papel 1:1
antes de fabricar.
La principal ya mide ambos rails en PF1/PC1 y expone J114 para correlacionar la
telemetría USB con el multímetro durante los ensayos.
Las 187 huellas eléctricas tienen [colocación y ruteo](../hardware/controller/layout.md)
reproducibles y con DRC limpio; JP8, JP24 y JP17 ocupan sus posiciones originales.
JP19 usa ya la pieza identificada, TE 1971845-4; los FASTON de PE son TE 63824-1,
casados con la foto del propietario.
La [etapa low-side candidata para la válvula](../hardware/power/valve-driver.md)
ya está incorporada al esquema y a la PCB de trabajo. JP3.1=+24 V y JP3.2=retorno están
confirmados; 0,073 V en modo diodo en ambos sentidos descarta una supresión
interna polarizada detectable y permite dibujar la rueda libre externa.
El manual ya permite dibujar las envolventes de
conectores y separar sensores de cargas. Ya están documentadas las tensiones
principales, la curva NTC y el caudalímetro; siguen pendientes la salida del nivel
capacitivo y las corrientes de marcha, arranque y bloqueo del grupo y del molino.
El molinillo se dimensiona a 3 A, casi su corriente de bloqueo, y el firmware
limita el calentador mientras muele; esas medidas y el resto de la
caracterización están en el [plan de caracterización](HD8911/characterization-plan.md),
priorizadas por lo que desbloquean.
El contorno de 141,6 × 135,2 mm y los tres taladros quedan aceptados como línea
base mecánica de la Rev A; ya no bloquean la colocación de la principal.
Suministro: [catálogo JLCPCB](../hardware/assembly/README.md), con consulta fechada.
JP17 es un TE RAST 5 1971845-3, identificado por el propietario. El
2026-09-29 identificó también JP3, JP5 y JP13 (HR A2506WV, en JLCPCB) y JP8 y
JP24 (LEOCO 3941P03*000 y 5001P020013, que JLCPCB no tiene: se sueldan a mano
o se aportan). El 2026-10-10 identificó JP14 y JP16 (HR A2506WV-02P y -08P) y
JP22 (JST ZH B3B-ZR): ya no queda ningún conector sin identificar.
Esto avanza el esquema de A3; no cierra A1, A2 ni la aceptación de A3.

## Verificaciones
- Python: enlaces locales y receta no ejecutable.
- Frontal: comprobación de conexiones del esquema frente al pinout previsto;
  ERC nativo y netlist cotejados; PCB ruteada con DRC limpio y paquete JLCPCB
  candidato, sin pedir.
- Principal: ERC y [DRC](../hardware/kicad-workflow.md) sin infracciones ni
  conexiones abiertas; no fabricable hasta cerrar las prioridades anteriores.
- `check_controller_core.py` exige consultas de stock de menos de 7 días: hay
  que refrescar el catálogo antes de cada pedido (y para que pase la CI).
- Host C/CTest: arranque inactivo, START bloqueado, fallo enclavado y STOP sin rearme.
- ESP-IDF: build pendiente de SDK disponible y versión fijada.
- Futuro banco: timeout real, parser corrupto, duplicados, reset, brownout y
  watchdog externo con corte observado en las salidas.
- Potencia bloqueada hasta A3 y plan aprobado. Ningún build prueba seguridad eléctrica.
