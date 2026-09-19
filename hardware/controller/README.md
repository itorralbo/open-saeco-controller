# Controladora lógica

Primer [núcleo lógico en KiCad](core-design.md): STM32G431RBT6 y
ESP32-S3-WROOM-1-N8R8, entrada externa aislada de 12 V, reset, depuración y UART.
Incluye entrada aislada de 12 V protegida, buck de 3,3 V, corte del frontal y
acondicionamiento de NTC, caudalímetro, nivel de agua, tres contactos y un
DRV8876 para el motor del grupo y una etapa low-side para la válvula, alimentados
desde una entrada aislada de 24 V con ramas protegidas por separado.
Un TPS3828 externo supervisa el STM32 y una AND doble bloquea ambas salidas
durante reset o timeout.
123 posiciones; 122 con MPN y código JLC/LCSC, más el puente de cobre J111, y todas con huella importada a la PCB de
trabajo. J105–J109 usan cabeceras JST XH/PH candidatas a partir de las fotos con
calibre; falta comprobar el acoplamiento con una muestra.
Hay [proyecto KiCad, ERC y netlist nativos](../kicad-workflow.md), contorno y
taladros aceptados, sin rutas y con la primera etapa de carga aún sin ensayar. El DRC no
presenta infracciones de reglas; quedan conexiones sin rutear, caracterizar la
salida del nivel de agua y completar las demás etapas de potencia.
El [contrato del frontal](front-panel-interface.md) propone un ESP32-S3-WROOM-1-N8R8
y asigna sus GPIO de pantalla, botones, UART y USB. J110 implementa USB-C de
servicio con ESD y alimentación de banco opcional; fuente AC/DC aislada final,
routing, ensayos y drivers de red/molino siguen pendientes.
Se aplica la [estrategia de suministro y montaje JLCPCB](../assembly/README.md).
Entregables: esquema jerárquico, PCB, BOM trazable, ERC/DRC y planos de montaje.
No trasladar pines de una placa de desarrollo al arnés sin verificación.
