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
Panel original, OTA y MQTT quedan para después.

## Verificaciones
- Python: enlaces locales y receta no ejecutable.
- Host C/CTest: arranque inactivo, START bloqueado, fallo enclavado y STOP sin rearme.
- ESP-IDF: build pendiente de SDK disponible y versión fijada.
- Futuro banco: timeout real, parser corrupto, duplicados, reset, brownout y watchdog.
- Potencia bloqueada hasta A3 y plan aprobado. Ningún build prueba seguridad eléctrica.
