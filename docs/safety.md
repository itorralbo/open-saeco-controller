# Seguridad

**230 VAC. Potencia EXPERIMENTAL, NO VERIFICADA. No conectar este scaffolding a red.**
Riesgos: choque eléctrico, incendio, quemaduras, presión y atrapamiento.
Las pruebas de software no certifican seguridad de la máquina modificada.

## Condiciones antes de potencia
- Revisión independiente cualificada de esquema, PCB, envolvente, cableado y fallos.
- Determinar clase de protección, tierra y dominios reales. No asumir que masa lógica
  o retorno de motor sean seguros al tacto; USB y depuración no deben puentear barreras.
- Dimensionar aislamiento, distancias, fuente y protecciones según condiciones reales
  y requisitos aplicables. Valores, categorías y fusibles permanecen TBD.
- Conservar o reemplazar por solución validada protecciones térmicas independientes.
  Los semiconductores y contactos pueden fallar cerrados.
- Documentar respuesta ante sensores abiertos/cortocircuitados, falta de agua,
  sobretemperatura, motores bloqueados, puerta abierta, reset y pérdida de enlace.

## Requisitos software futuros
Entradas ausentes, inválidas o caducadas impiden operar. Fallos enclavados sin
reanudación automática. Límites de receta subordinados a límites de máquina validados.
Watchdog, timeout real y límite temporal por fase: pendientes; no los implementa esta base.

| Peligro | Mitigación requerida | Cierre |
|---|---|---|
| Red en USB/chasis | Separación/protección verificadas | TBD |
| Calentador pegado | Corte térmico independiente | TBD |
| Marcha en seco | Agua/flujo validados y límites | TBD |
| Movimiento inesperado | Interlocks y recuperación segura | TBD |
| Enlace/ESP caído | Timeout STM32 y salida inactiva | TBD |
| Fuga o presión | Revisión hidráulica y ensayos | TBD |

Rev A funcional requiere evidencias que cierren estos riesgos. No se declara conformidad
normativa ni se dan instrucciones para trabajar con tensión.
