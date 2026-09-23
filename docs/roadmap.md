# Roadmap y validación

| Hito | Entregable | Aceptación |
|---|---|---|
| A0 | Documentación y scaffolding | Estructura y pruebas de bloqueo |
| A1 | Reverse engineering | Pines, niveles, orientación y evidencia revisados |
| A2 | Banco lógico | BSP, simulación de sensores y fallos, protocolo probado |
| A3 | Hardware | Esquema, BOM, PCB y revisión independiente |
| A4 | Ensayos potencia | Plan revisado, resultados y riesgos cerrados |
| A5 | Rev A funcional | Ciclo USB/web sin electrónica original y fallos validados |

Prioridades: variante exacta, conectores, alimentación de motores, protecciones,
calibraciones, aislamiento, selección MCU, interfaz, protocolo y límites de receta.
El frontal nuevo entra en el diseño: copia mecánica de botones y pantalla reemplazable,
con [primer esquema y BOM candidata](../hardware/front-panel/README.md).
La integración física requiere cotas y selección del display. La reutilización de la
electrónica del panel original deja de ser objetivo. OTA y MQTT quedan para después.

Principal: [primer núcleo STM32 + ESP32](../hardware/controller/core-design.md)
con conexiones de depuración/UART, USB-C de servicio, fuente de baja tensión,
entradas de NTC, caudalímetro, nivel de agua y contactos. El primer bloque de
carga es un DRV8876 para el motor del grupo y la válvula dispone de una etapa
low-side, ambos desde una entrada de 24 V de banco con fusibles separados.
Calentador, bomba y molino tienen ya su etapa en el esquema y en la PCB; ninguna
carga está ensayada.
El [watchdog e interlock hardware](../hardware/power/watchdog-interlock.md) ya
reinicia el STM32 y bloquea motor/válvula ante timeout o reset; falta implementar
el pulso periódico en PB4 y validar la temporización real.
La [arquitectura de alimentación Rev A](../hardware/power/power-architecture.md)
mantiene dos fuentes DC externas aisladas para el banco, pero la principal final
integra en la misma PCB la entrada de red, la fuente aislada, calentador, bomba y
molino. El interlock hardware cubre ya todas las cargas, y sus órdenes están
ruteadas desde el STM32. Desde el 2026-09-23 la PCB es de cuatro capas y todas
sus redes están conectadas (DRC sin infracciones); faltan los rellenos
exteriores, la serigrafía y la revisión de aislamiento antes de fabricar.
La principal ya mide ambos rails en PF1/PC1 y expone J114 para correlacionar la
telemetría USB con el multímetro durante los ensayos.
Las 135 huellas actuales tienen ya una [colocación funcional](../hardware/controller/layout.md)
reproducible y con DRC limpio; JP8, JP24 y JP17 ya ocupan sus posiciones originales.
JP19 usa ya la pieza identificada, TE 1971845-4; los FASTON de PE esperan una muestra.
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
JP8/JP17 y JP24 tienen ya candidatos JST VH de 3 y 2 vías, respectivamente,
pendientes solo de una prueba física de acoplamiento antes de fijar sus huellas.
Esto avanza el esquema de A3; no cierra A1, A2 ni la aceptación de A3.

## Verificaciones
- Python: enlaces locales y receta no ejecutable.
- Frontal: comprobación de conexiones del esquema frente al pinout previsto;
  ERC nativo y netlist cotejados. Huellas mecánicas y layout pendientes.
- Principal y frontal: proyectos KiCad con PCB de trabajo; [DRC con incidencias
  pendientes](../hardware/kicad-workflow.md), no fabricables.
- Host C/CTest: arranque inactivo, START bloqueado, fallo enclavado y STOP sin rearme.
- ESP-IDF: build pendiente de SDK disponible y versión fijada.
- Futuro banco: timeout real, parser corrupto, duplicados, reset, brownout y
  watchdog externo con corte observado en las salidas.
- Potencia bloqueada hasta A3 y plan aprobado. Ningún build prueba seguridad eléctrica.
