# Validación nativa — controller-core-reva

KiCad 10.0.6. ERC: 0 errores y 0 avisos, sin exclusiones.
Netlist nativa cotejada: 132 componentes, 457 pines.

Configuración estándar de KiCad: no se ejecutan los controles opcionales
footprint_filter, four_way_junction, simulation_model_issue, single_global_label. No se han añadido supresiones.

Alcance: esquema parcial. La principal incluye el núcleo lógico, USB-C de servicio, entrada protegida de 12 V aislados, buck de 3,3 V, corte del frontal, acondicionamiento de NTC, caudalímetro, nivel de agua, tres contactos y un puente H DRV8876 para el motor del grupo, más una etapa low-side para la electroválvula de 24 V. Un supervisor externo reinicia el STM32 y bloquea ambas salidas mediante lógica AND. Dos divisores miden las entradas de 12/24 V y J114 las expone para contraste en banco. No valida la fuente AC/DC, el routing ni las cargas.
No valida mecánica completa, selección eléctrica completa ni fabricación.
Los GPIO sin asignar llevan NC. J105–J109 y J112–J113 usan huellas candidatas XH/PH cotejadas con fotos. JP16 V1/V2 llegan al puente H y JP3.1/JP3.2 a la etapa de válvula. J112 requiere una fuente de 24 V aislada limitada; corriente, frenado, térmica, liberación de válvula y la salida de JP22 requieren ensayo. El watchdog y sus tiempos también requieren firmware y prueba de banco.

La colocación mecánica sitúa J104, J108, J107, J113, J109, J105 y J106 en las
zonas fotografiadas de JP21, JP16, JP14, JP3, JP22, JP13 y JP5. El error estimado
es ±1,5 mm y debe comprobarse con una impresión 1:1 o una PCB sin montar. Las
envolventes originales de JP8, JP19, JP24, JP17, JP1 y JP9 son áreas de regla
reservadas. DRC de la colocación: 0 infracciones, 307 conexiones abiertas y tres
diferencias de paridad intencionales por MH1–MH3.
Regenerar con `python3 tools/validate_kicad.py` desde la raíz.
