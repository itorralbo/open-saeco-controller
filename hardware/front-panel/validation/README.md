# Validación nativa — front-panel-reva

KiCad 10.0.6. ERC: 0 errores y 0 avisos, sin exclusiones.
Netlist nativa cotejada: 44 componentes, 122 pines.

Configuración estándar de KiCad: no se ejecutan los controles opcionales
footprint_filter, four_way_junction, simulation_model_issue, single_global_label. No se han añadido supresiones.

Alcance: esquema parcial. El frontal declara alimentación externa por J1; no valida la fuente ni la mecánica.
No valida mecánica completa, selección eléctrica completa ni fabricación.
J1 ya tiene huella IDC. Contorno y taladros Ø8,4 aplicados desde mechanical-source.json; J2 y SW1–SW8 siguen sin huella, con las posiciones de pulsador como referencia en Dwgs.User.
Regenerar con `python3 tools/validate_kicad.py` desde la raíz.
