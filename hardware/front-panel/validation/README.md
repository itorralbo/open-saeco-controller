# Validación nativa — front-panel-reva

KiCad 10.0.6. ERC: 0 errores y 0 avisos, sin exclusiones.
Netlist nativa cotejada: 42 componentes, 118 pines.

Configuración estándar de KiCad: no se ejecutan los controles opcionales
footprint_filter, four_way_junction, simulation_model_issue, single_global_label. No se han añadido supresiones.

Alcance: esquema parcial. El frontal declara alimentación externa por J1; no valida la fuente ni la mecánica.
No valida mecánica completa, selección eléctrica completa ni fabricación.
Todas las posiciones tienen huella: SW1–SW7 HRO K2-1102SP-A4SC-04 (OpenSaeco.pretty), J2 JST PH 8 y LED STBY en P7. Contorno y taladros Ø8,4 desde mechanical-source.json.
Regenerar con `python3 tools/validate_kicad.py` desde la raíz.
