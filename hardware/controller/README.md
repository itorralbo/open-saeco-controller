# Controladora lógica

Primer [núcleo lógico en KiCad](core-design.md): STM32G431RBT6 y
ESP32-S3-WROOM-1-N8R8, entrada auxiliar aislada de 12 V, reset, depuración y UART.
Incluye entrada aislada de 12 V protegida, buck de 3,3 V, corte del frontal y
acondicionamiento de NTC, caudalímetro, nivel de agua, tres contactos y un
DRV8876 para el motor del grupo y una etapa low-side para la válvula, alimentados
desde una entrada aislada de 24 V con ramas protegidas por separado.
Un TPS3828 externo supervisa el STM32 y una AND doble bloquea ambas salidas
durante reset o timeout.
138 posiciones; 134 con MPN y código JLC/LCSC, más el puente de cobre J111.
Hay 135 huellas importadas a la PCB; faltan las huellas mecánicas de JP19 y los
dos FASTON de PE. J105–J109 usan cabeceras JST XH/PH candidatas a partir de las fotos con
calibre; falta comprobar el acoplamiento con una muestra.
Hay [proyecto KiCad, ERC y netlist nativos](../kicad-workflow.md), contorno,
taladros aceptados y [colocación mecánica/funcional reproducible](layout.md), con
el bloque USB ya encaminado y la primera etapa de carga sin ensayar. El DRC no
presenta infracciones de reglas; quedan 299 conexiones sin rutear, caracterizar la
salida del nivel de agua y completar las demás etapas de potencia.
Dos divisores permiten leer por ADC las entradas de 12 V y 24 V y J114 facilita
su medida directa durante las pruebas.
El [contrato del frontal](front-panel-interface.md) propone un ESP32-S3-WROOM-1-N8R8
y asigna sus GPIO de pantalla, botones, UART y USB. J110 implementa USB-C de
servicio con ESD y alimentación de banco opcional; routing y ensayos siguen
pendientes. La placa final incluirá también JP17, fuente aislada/transformador y
los drivers de calentador, bomba y molino en las posiciones de la original; su
[arquitectura](../power/power-architecture.md) ya forma parte del alcance de esta
misma PCB.
JP8, JP24 y JP17 ya están en el esquema y en la PCB como JST VH candidatos, en
sus posiciones originales. JP19, JP1 y JP9 están en el esquema sin huella para
evitar fijar una geometría no confirmada.
Se aplica la [estrategia de suministro y montaje JLCPCB](../assembly/README.md).
El [perfil de fabricación y clases de red](manufacturing.md) configura dos
capas y reglas conservadoras para lógica, USB, alimentación y actuadores.
Entregables: esquema jerárquico, PCB, BOM trazable, ERC/DRC y planos de montaje.
No trasladar pines de una placa de desarrollo al arnés sin verificación.
