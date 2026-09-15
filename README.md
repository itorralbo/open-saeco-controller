# Open Saeco Controller

Controladora open-source para sustituir la electrónica de la Saeco Incanto HD8911,
placa objetivo 421941308981/01. Proyecto independiente, sin afiliación a Philips/Saeco.

**Rev A: scaffolding, no hardware validado. Hay 230 VAC. Toda etapa de potencia es
experimental hasta verificación. Este código no permite controlar cargas.**

## Objetivo
Controlar la máquina sin depender de la electrónica original, inicialmente por USB/web.
Conservar mecánica y cableado solo tras verificar compatibilidad. Panel original posterior
a Rev A. STM32 se ocupará del control; ESP32, de interfaz y comunicaciones.

## Documentación
- [Arquitectura](docs/architecture.md)
- [Reverse engineering HD8911](docs/HD8911/README.md)
- [Mapa I/O preliminar](docs/io-map.md)
- [Seguridad](docs/safety.md)
- [Roadmap y validación](docs/roadmap.md)
- [Licencias y fuentes](docs/licensing.md)

## Estructura
```
hardware/controller/  requisitos del futuro diseño KiCad
hardware/power/       requisitos de potencia experimental
firmware/stm32/       núcleo C portable, sin BSP ni pines
firmware/esp32/       proyecto mínimo ESP-IDF
firmware/common/      contrato de comunicaciones propuesto
recipes/              ejemplo de simulación no ejecutable
tests/                pruebas de bloqueo del núcleo
```

## Verificación local
Con Python 3: `python tools/check_scaffold.py`.
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
