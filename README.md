# Open Saeco Controller

Controladora open-source para sustituir la electrónica de la Saeco Incanto HD8911,
placa objetivo 421941308981/01. Proyecto independiente, sin afiliación a Philips/Saeco.

**Rev A: scaffolding, no hardware validado. Hay 230 VAC. Toda etapa de potencia es
experimental hasta verificación. Este código no permite controlar cargas.**

## Objetivo
Controlar la máquina sin depender de la electrónica original, inicialmente por USB/web.
Conservar mecánica y cableado solo tras verificar compatibilidad. Se diseñará un frontal
nuevo que reproduzca la posición de los botones y use una pantalla reemplazable.
STM32 se ocupará del control; ESP32, de interfaz y comunicaciones.

## Documentación
- [Arquitectura](docs/architecture.md)
- [Reverse engineering HD8911](docs/HD8911/README.md)
- [Plan de caracterización de la cafetera](docs/HD8911/characterization-plan.md)
- [Mapa I/O preliminar](docs/io-map.md)
- [Diseño preliminar del frontal y pantalla](hardware/front-panel/README.md)
- [Subsistema display y UI (ST7789 + LVGL)](docs/display-ui.md)
- [Decisión de frontal/display (ADR-0001)](docs/adr/0001-front-panel-display-st7789.md)
- [Núcleo inicial de la principal](hardware/controller/core-design.md)
- [Abrir y editar los proyectos KiCad](hardware/kicad-workflow.md)
- [Componentes y fabricación JLCPCB](hardware/assembly/README.md)
- [Seguridad](docs/safety.md)
- [Roadmap y validación](docs/roadmap.md)
- [Licencias y fuentes](docs/licensing.md)

## Estructura
```
hardware/controller/  esquema parcial del núcleo lógico y BOM candidata
hardware/front-panel/ esquema KiCad preliminar, BOM y mecánica pendiente
hardware/assembly/    catálogo de componentes con códigos JLC y stock observado
hardware/power/       requisitos de potencia experimental
firmware/stm32/       núcleo C portable, sin BSP ni pines
firmware/esp32/       proyecto mínimo ESP-IDF
firmware/common/      contrato de comunicaciones propuesto
recipes/              ejemplo de simulación no ejecutable
tests/                pruebas de bloqueo del núcleo
```

## Verificación local
Con Python 3: `python tools/check_scaffold.py`.
Conexiones del frontal: `python tools/check_front_panel.py` (no sustituye ERC).
Núcleo y suministro: `python tools/check_controller_core.py` (no sustituye ERC/DRC).
ERC y netlist nativos, con KiCad 10: `python3 tools/validate_kicad.py`.
Con CMake >= 3.20 y compilador C:
```
cmake -S firmware/stm32 -B build/host
cmake --build build/host --config Debug
ctest --test-dir build/host -C Debug --output-on-failure
```
El build host no produce firmware STM32 flasheable. USB/web, drivers, protocolos y
calibraciones aún no están implementados. Todos los pinouts y niveles eléctricos
sin evidencia permanecen TBD.

El material original de esta base se publica bajo [MIT](LICENSE). Referencias y
materiales de terceros conservan sus derechos; no se redistribuyen en este paquete.
