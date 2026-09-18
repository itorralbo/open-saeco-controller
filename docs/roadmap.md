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
con conexiones de depuración/UART, USB-C de servicio, fuente de baja tensión y
entradas de NTC, caudalímetro, nivel de agua y contactos, todavía sin potencia de cargas.
El manual ya permite dibujar las envolventes de
conectores y separar sensores de cargas. Ya están documentadas las tensiones
principales, la curva NTC y el caudalímetro; siguen pendientes orden de pines,
salida del nivel capacitivo y corrientes de arranque/bloqueo.
El contorno de 141,6 × 135,2 mm y los tres taladros quedan aceptados como línea
base mecánica de la Rev A; ya no bloquean la colocación de la principal.
Suministro: [catálogo JLCPCB](../hardware/assembly/README.md), con consulta fechada.
Esto avanza el esquema de A3; no cierra A1, A2 ni la aceptación de A3.

## Verificaciones
- Python: enlaces locales y receta no ejecutable.
- Frontal: comprobación de conexiones del esquema frente al pinout previsto;
  ERC nativo y netlist cotejados. Huellas mecánicas y layout pendientes.
- Principal y frontal: proyectos KiCad con PCB de trabajo; [DRC con incidencias
  pendientes](../hardware/kicad-workflow.md), no fabricables.
- Host C/CTest: arranque inactivo, START bloqueado, fallo enclavado y STOP sin rearme.
- ESP-IDF: build pendiente de SDK disponible y versión fijada.
- Futuro banco: timeout real, parser corrupto, duplicados, reset, brownout y watchdog.
- Potencia bloqueada hasta A3 y plan aprobado. Ningún build prueba seguridad eléctrica.
