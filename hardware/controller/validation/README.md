# Validación nativa — controller-core-reva

KiCad 10.0.6. ERC: 0 errores y 0 avisos, sin exclusiones.
Netlist nativa cotejada: 123 componentes, 435 pines.

Configuración estándar de KiCad: no se ejecutan los controles opcionales
footprint_filter, four_way_junction, simulation_model_issue, single_global_label. No se han añadido supresiones.

Alcance: esquema parcial. La principal incluye el núcleo lógico, USB-C de servicio, entrada protegida de 12 V aislados, buck de 3,3 V, corte del frontal, acondicionamiento de NTC, caudalímetro, nivel de agua, tres contactos y un puente H DRV8876 para el motor del grupo, más una etapa low-side para la electroválvula de 24 V. Un supervisor externo reinicia el STM32 y bloquea ambas salidas mediante lógica AND. No valida la fuente AC/DC, el routing ni las cargas.
No valida mecánica completa, selección eléctrica completa ni fabricación.
Los GPIO sin asignar llevan NC. J105–J109 y J112–J113 usan huellas candidatas XH/PH cotejadas con fotos. JP16 V1/V2 llegan al puente H y JP3.1/JP3.2 a la etapa de válvula. J112 requiere una fuente de 24 V aislada limitada; corriente, frenado, térmica, liberación de válvula y la salida de JP22 requieren ensayo. El watchdog y sus tiempos también requieren firmware y prueba de banco.
Regenerar con `python3 tools/validate_kicad.py` desde la raíz.
