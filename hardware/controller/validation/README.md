# Validación nativa — controller-core-reva

KiCad 10.0.6. ERC: 0 errores y 0 avisos, sin exclusiones.
Netlist nativa cotejada: 48 componentes, 227 pines.

Configuración estándar de KiCad: no se ejecutan los controles opcionales
footprint_filter, four_way_junction, simulation_model_issue, single_global_label. No se han añadido supresiones.

Alcance: esquema parcial. La principal incluye el núcleo lógico, entrada protegida de 12 V aislados, buck de 3,3 V y corte del frontal. No valida la fuente AC/DC ni las cargas.
No valida mecánica completa, selección eléctrica completa ni fabricación.
Los GPIO sin asignar llevan NC. J101–J104 ya tienen huella; aún no se han añadido los conectores de sensores y cargas de la máquina.
Regenerar con `python3 tools/validate_kicad.py` desde la raíz.
