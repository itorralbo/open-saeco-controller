# Núcleo STM32

C99 portable sin HAL. CMake compila para host; no es firmware flasheable.
MCU definitivo, BSP, startup, linker script, pines y proyecto CubeMX TBD.
El adaptador futuro calculará interlocks y vigencia real del enlace; aquí son booleanos
simulados. No usar este scaffolding como supervisor de seguridad.
Ningún estado actual autoriza cargas.
`osc_heater_cycles_allowed()` fija ya la regla de reparto de la fase de cargas
(calentador a 3 de cada 5 ciclos mientras muele el molinillo); ver
[power-architecture.md](../../hardware/power/power-architecture.md#reparto-de-corriente-en-la-fase-de-cargas).
