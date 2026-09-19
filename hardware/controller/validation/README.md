# Validación nativa — controller-core-reva

KiCad 10.0.6. ERC: 0 errores y 0 avisos, sin exclusiones.
Netlist nativa cotejada: 138 componentes, 471 pines.

Configuración estándar de KiCad: no se ejecutan los controles opcionales
footprint_filter, four_way_junction, simulation_model_issue, single_global_label. No se han añadido supresiones.

Alcance: esquema parcial. La principal incluye el núcleo lógico, USB-C de servicio, entrada protegida de 12 V aislados, buck de 3,3 V, corte del frontal, acondicionamiento de NTC, caudalímetro, nivel de agua, tres contactos y un puente H DRV8876 para el motor del grupo, más una etapa low-side para la electroválvula de 24 V. Un supervisor externo reinicia el STM32 y bloquea ambas salidas mediante lógica AND. No valida todavía la fuente AC/DC integrada ni las cargas.
No valida mecánica completa, selección eléctrica completa ni fabricación.
Los GPIO sin asignar llevan NC. J105–J109 y J112–J113 usan huellas candidatas XH/PH cotejadas con fotos. JP16 V1/V2 llegan al puente H y JP3.1/JP3.2 a la etapa de válvula. J112 requiere una fuente de 24 V aislada limitada; corriente, frenado, térmica, liberación de válvula y la salida de JP22 requieren ensayo. El watchdog y sus tiempos también requieren firmware y prueba de banco.

La colocación alinea J104, J108, J107, J113, J109, J105 y J106 con JP21, JP16, JP14, JP3, JP22, JP13 y JP5. JP8, JP19, JP24, JP17, JP1 y JP9 son conectores obligatorios y mantienen áreas temporales hasta incorporar sus huellas. El routing USB reproducible contiene 39 segmentos y 7 vías; el DRC de esta etapa tiene 0 infracciones, 299 conexiones abiertas y seis diferencias de paridad: MH1–MH3 y las huellas aún desconocidas de JP19/JP1/JP9.

La principal usa dos capas y clases explícitas para USB, alimentación, conmutación y actuadores. La geometría USB sigue pendiente de verificar con el stack-up de fabricación.
Regenerar con `python3 tools/validate_kicad.py` desde la raíz.
