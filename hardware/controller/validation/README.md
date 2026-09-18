# Validación nativa — controller-core-reva

KiCad 10.0.6. ERC: 0 errores y 0 avisos, sin exclusiones.
Netlist nativa cotejada: 83 componentes, 324 pines.

Configuración estándar de KiCad: no se ejecutan los controles opcionales
footprint_filter, four_way_junction, simulation_model_issue, single_global_label. No se han añadido supresiones.

Alcance: esquema parcial. La principal incluye el núcleo lógico, USB-C de servicio, entrada protegida de 12 V aislados, buck de 3,3 V, corte del frontal y acondicionamiento de NTC, caudalímetro, nivel de agua y tres contactos. No valida la fuente AC/DC, el routing USB ni las cargas.
No valida mecánica completa, selección eléctrica completa ni fabricación.
Los GPIO sin asignar llevan NC. J105–J109 usan huellas candidatas XH/PH cotejadas con fotos; las dos vías de motor de JP16 permanecen NC hasta incorporar el puente H. La salida de JP22 requiere ensayo.
Regenerar con `python3 tools/validate_kicad.py` desde la raíz.
