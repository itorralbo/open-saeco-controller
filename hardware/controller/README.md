# Controladora lógica

Primer [diseño de la principal en KiCad](core-design.md): STM32G431RBT6 y
ESP32-S3-WROOM-1U-N8R8 con antena externa U.FL, alimentación integrada, reset, depuración y UART.
Incluye IRM-30-24 aislado, buck de 24 V a 12 V, buck de 3,3 V, corte del frontal y
acondicionamiento de NTC, caudalímetro, nivel de agua, tres contactos y un
DRV8876 para el motor del grupo y una etapa low-side para la válvula, alimentados
desde una entrada aislada de 24 V con ramas protegidas por separado.
Un TPS3828 externo supervisa el STM32; la lógica AND bloquea los actuadores y
un segundo interlock gobierna el relé general de fase.
159 posiciones; 151 con MPN y código JLC/LCSC, más los puentes de cobre J111/J121.
Hay 156 huellas importadas a la PCB; faltan las huellas mecánicas de JP19 y los
dos FASTON de PE. J105–J109 usan cabeceras JST XH/PH candidatas a partir de las fotos con
calibre; falta comprobar el acoplamiento con una muestra.
Hay [proyecto KiCad, ERC y netlist nativos](../kicad-workflow.md), contorno,
taladros aceptados y [colocación mecánica/funcional reproducible](layout.md), con
el USB, la alimentación del STM32, la entrada de red, los 24 V, el puente H del
grupo, el supervisor con sus interlocks y el relé, la válvula, el lado de mazo de
los sensores y el buck de 12 V ya ruteados, y la primera etapa de carga sin
ensayar. El DRC, con la barrera red/SELV de 8 mm como regla, no presenta
infracciones; quedan 154 conexiones sin rutear, la distribución de 3V3 y 12 V,
las señales del STM32, caracterizar la salida del nivel
de agua y completar las demás etapas de potencia.
Dos divisores permiten leer por ADC las entradas de 12 V y 24 V y J114 facilita
su medida directa durante las pruebas.
El [contrato del frontal](front-panel-interface.md) usa un ESP32-S3-WROOM-1U-N8R8
y asigna sus GPIO de pantalla, botones, UART y USB. J110 implementa USB-C de
servicio con ESD y alimentación de banco opcional; routing y ensayos siguen
pendientes. La placa ya incluye JP17, fuente aislada y relé general; faltan los
drivers de calentador, bomba y molino en las posiciones de la original. Su
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
