# Controladora lógica

Primer [núcleo lógico en KiCad](core-design.md): STM32G431RBT6 y
ESP32-S3-WROOM-1-N8R8, entrada externa aislada de 12 V, reset, depuración y UART.
Incluye entrada aislada de 12 V protegida, buck de 3,3 V, corte del frontal y
acondicionamiento de NTC, caudalímetro y tres contactos secos.
68 componentes; los 68 con MPN, código JLC/LCSC y huella importada a la PCB de
trabajo. J105–J109 usan cabeceras JST XH/PH candidatas a partir de las fotos con
calibre; falta comprobar el acoplamiento con una muestra.
Hay [proyecto KiCad, ERC y netlist nativos](../kicad-workflow.md), contorno y
taladros aceptados, sin rutas ni etapas de potencia de las cargas. El DRC no
presenta infracciones de reglas; quedan conexiones sin rutear, el nivel de agua y
las etapas de potencia pendientes.
El [contrato del frontal](front-panel-interface.md) propone un ESP32-S3-WROOM-1-N8R8
y reserva sus GPIO de pantalla, botones, UART y USB. La selección es preliminar;
fuente AC/DC aislada, USB, sensores restantes y drivers siguen pendientes.
Se aplica la [estrategia de suministro y montaje JLCPCB](../assembly/README.md).
Entregables: esquema jerárquico, PCB, BOM trazable, ERC/DRC y planos de montaje.
No trasladar pines de una placa de desarrollo al arnés sin verificación.
