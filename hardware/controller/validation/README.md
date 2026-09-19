# Validación nativa — controller-core-reva

KiCad 10.0.6. ERC: 0 errores y 0 avisos, sin exclusiones.
Netlist nativa cotejada: 158 componentes, 528 pines.

Configuración estándar de KiCad: no se ejecutan los controles opcionales
footprint_filter, four_way_junction, simulation_model_issue, single_global_label. No se han añadido supresiones.

Alcance: esquema parcial. La principal incluye el núcleo lógico, USB-C de servicio, fuente aislada IRM-30-24, selección de 24 V internos/externos, buck AP63200 de 24 V a 12 V, buck de 3,3 V, sensores, puente H DRV8876 y etapa low-side de válvula. Un relé G5RL normalmente abierto corta la fase de las cargas y solo se arma mediante reset válido y orden explícita. Todavía no valida los drivers de calentador, bomba o molino.
No valida mecánica completa, selección eléctrica completa ni fabricación.
Los GPIO sin asignar llevan NC. J105–J109 y J112–J113 usan huellas candidatas XH/PH cotejadas con fotos. JP16 V1/V2 llegan al puente H y JP3.1/JP3.2 a la etapa de válvula. J112 requiere una fuente de 24 V aislada limitada; corriente, frenado, térmica, liberación de válvula y la salida de JP22 requieren ensayo. El watchdog y sus tiempos también requieren firmware y prueba de banco.

La colocación alinea J104, J108, J107, J113, J109, J105 y J106 con JP21, JP16, JP14, JP3, JP22, JP13 y JP5. JP8, JP19, JP24, JP17, JP1 y JP9 son conectores obligatorios y mantienen áreas temporales hasta incorporar sus huellas. El routing reproducible cubre USB, la alimentación y el desacoplo del STM32, la entrada de red hasta PS701, K701 y RV701, la salida de 24 V y un plano GND_UI en B.Cu: 152 segmentos y 23 vías. Las fases de carga van duplicadas en las dos caras con cobre de 1 oz. La barrera de 8 mm red/SELV es una regla DRC y una banda sin cobre; el dominio de red es contiguo, reserva el disipador de calentador y bomba, y el DRC de esta etapa tiene 0 infracciones. Quedan 273 conexiones abiertas y seis diferencias de paridad: MH1–MH3 y las huellas aún desconocidas de JP19/JP1/JP9.

La principal usa dos capas y clases explícitas para red, USB, alimentación, conmutación y actuadores. La geometría USB sigue pendiente de verificar con el stack-up de fabricación.
Regenerar con `python3 tools/validate_kicad.py` desde la raíz.
