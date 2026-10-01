# Proyectos KiCad — estado y edición

Los dos proyectos se han cargado con KiCad CLI 10.0.6. Para abrirlos en el gestor:

- [Principal](controller/kicad/controller-core-reva.kicad_pro),
  [esquema](controller/kicad/controller-core-reva.kicad_sch),
  [PCB de trabajo](controller/kicad/controller-core-reva.kicad_pcb).
- [Frontal](front-panel/kicad/front-panel-reva.kicad_pro),
  [esquema](front-panel/kicad/front-panel-reva.kicad_sch),
  [PCB de trabajo](front-panel/kicad/front-panel-reva.kicad_pcb).

Cada carpeta incluye `OpenSaeco.kicad_sym`, `sym-lib-table` y `fp-lib-table`.
Los símbolos son locales al proyecto. Las huellas vienen de las bibliotecas
estándar de KiCad 10, mediante `KICAD10_FOOTPRINT_DIR`, o de la biblioteca local
`OpenSaeco.pretty` de cada proyecto (conectores identificados, fuente, relé,
optos con ranura, fusible del molinillo, USB-C vertical y pulsadores). No dependen
de una ruta absoluta del equipo de desarrollo.

## Qué contienen las PCB

Las huellas y sus redes vienen de la netlist **nativa** de KiCad, con los UUID de
los símbolos para poder actualizar desde el esquema, y con fabricante, MPN y
código JLC como campos ocultos. Los scripts guardan cada PCB y la vuelven a
cargar con `pcbnew`, cotejando cada pad y su red.

| Proyecto | Componentes en esquema | Huellas en PCB | Sin huella |
|---|---:|---:|---|
| Principal | 187 | 187 (más MH1–MH3) | — |
| Frontal | 42 | 42 | — |

- **Principal**: [colocada y ruteada](controller/layout.md) sobre el
  [contorno y los tres taladros aceptados](../docs/HD8911/main-board-mechanics.md),
  con los conectores de mazo en sus posiciones originales. Cuatro capas, todas
  las redes conectadas, rellenos de masa en el lado SELV y serigrafía. **No es
  fabricable**: no generar Gerbers, BOM de fabricación ni CPL hasta la
  comprobación 1:1, la identificación de JP14/JP16/JP22 y la revisión de
  aislamiento.
- **Frontal**: [colocado y ruteado](front-panel/layout.md) sobre el
  [contorno aceptado](front-panel/mechanical.md), con paquete JLCPCB candidato
  pendiente de las [comprobaciones previas al pedido](front-panel/layout.md#pendiente-antes-de-pedir).

## Validación

ERC nativo: cero errores y cero avisos en ambos esquemas, sin excluir
infracciones. Se mantiene la configuración estándar de KiCad; los cuatro
controles opcionales desactivados por defecto figuran en cada informe. Los
PWR_FLAG declaran las fuentes aisladas de J101/J112 y los nodos de potencia
separados por elementos pasivos; en el frontal, J1 declara su alimentación
externa. Los tipos de pin genéricos de los GPIO no comprueban la configuración
del firmware.

La netlist XML de KiCad coincide con los 612 pines de la principal y los 118 del
frontal.

| Resultado del DRC (todas las severidades) | Principal | Frontal |
|---|---:|---:|
| Infracciones geométricas/de reglas | 0 | 0 |
| Conexiones pendientes de rutear | 0 | 0 |
| Huellas ausentes respecto al esquema | 0 | 0 |
| Diferencias adicionales de paridad | 3 taladros mecánicos intencionales | 0 |

Las reglas de la principal (`controller-core-reva.kicad_dru`, escritas por
`configure_controller_rules.py`) incluyen la barrera de 8 mm de separación y
creepage entre red y SELV, 2,5 mm entre redes de red distintas y las
excepciones por pieza de optos y triacs; ver [manufacturing.md](controller/manufacturing.md).
El pad expuesto del ESP32 usa doce vías térmicas de 0,20 mm, el mínimo de taladro
del proyecto y el preferido por JLCPCB para placas rígidas.

Informes y vistas:

- [Validación principal](controller/validation/README.md),
  [DRC principal](controller/validation/drc-staging.json),
  [esquema principal renderizado por KiCad](controller/validation/controller-core-reva.svg).
- [Validación frontal](front-panel/validation/README.md),
  [DRC frontal](front-panel/validation/drc-staging.json),
  [esquema frontal renderizado por KiCad](front-panel/validation/front-panel-reva.svg).

## Cómo continuar

Abrir los `.kicad_pro` con KiCad 10. El esquema actual sigue generado por Python;
antes de editarlo manualmente, dejar de regenerarlo o trasladar los cambios al
generador. La PCB ya es editable: `tools/create_pcb_staging.py` se niega a sobrescribir
un archivo existente. `tools/sync_controller_pcb.py` actualiza las redes y huellas
de la principal sin tocar el contorno ni los taladros. `tools/sync_front_panel_pcb.py`
hace lo mismo para nuevas huellas del frontal; `tools/apply_front_panel_mechanics.py`
aplica su contorno sin necesitar KiCad y `tools/layout_front_panel_pcb.py` coloca y
rutea el frontal con Freerouting (el script es la fuente del layout). También se puede usar
«Actualizar PCB desde esquema» en KiCad conservando las posiciones revisadas.
`tools/layout_controller_pcb.py` es la fuente reproducible de la colocación de la
principal; el sincronizador ya no mueve huellas existentes. Tras el ruteo,
`tools/silkscreen_controller_pcb.py` dibuja la serigrafía (logo, título y
nombre de cada conector) y `tools/export_controller_print.py` saca la copia
1:1 en PDF para comprobar en papel. El logo se vectoriza una vez con
`tools/trace_silkscreen_logo.py`, que necesita Pillow, NumPy, scikit-image y
Shapely fuera del Python de KiCad.

Desde la raíz del repositorio (en Windows, con `PYTHONUTF8=1`: los scripts
leen JSON y CSV con texto en español):

```sh
python3 tools/generate_controller_core.py
python3 tools/check_front_panel.py
python3 tools/check_controller_core.py
python3 tools/validate_kicad.py
python3 tools/apply_front_panel_mechanics.py
<python de KiCad> tools/sync_controller_pcb.py
<python de KiCad> tools/layout_controller_pcb.py
<python de KiCad> tools/configure_controller_stackup.py
python3 tools/configure_controller_rules.py
<python de KiCad> tools/route_controller_pcb.py
<python de KiCad> tools/silkscreen_controller_pcb.py
<python de KiCad> tools/make_controller_3d_models.py
<python de KiCad> tools/export_controller_print.py
python3 tools/render_main_connector_map.py
<python de KiCad> tools/sync_front_panel_pcb.py
<python de KiCad> tools/layout_front_panel_pcb.py
kicad-cli pcb drc --schematic-parity --severity-all --format json -o hardware/controller/validation/drc-staging.json hardware/controller/kicad/controller-core-reva.kicad_pcb
kicad-cli pcb drc --schematic-parity --format json -o hardware/controller/validation/pcb/drc.json hardware/controller/kicad/controller-core-reva.kicad_pcb
kicad-cli pcb drc --schematic-parity --severity-all --format json -o hardware/front-panel/validation/drc-staging.json hardware/front-panel/kicad/front-panel-reva.kicad_pcb
python3 tools/export_front_panel_fab.py
```

Si el ejecutable no está en PATH, `validate_kicad.py` y `export_controller_print.py`
admiten `KICAD_CLI` y detectan la instalación habitual de macOS y de Windows. La
vista `controller/preview/pcb-staging-top.png` se renderiza con
`kicad-cli pcb render --side top`. Los detalles del enlace del frontal salen
con `--width 1600 --height 900 --quality high` y: `--zoom 5 --pan "5.4,-5.8,0"`
para `controller/preview/j104-wr-mm-top.png` (más `--rotate "-35,0,0"
--perspective` para `j104-wr-mm-3d.png`) y `--zoom 4 --pan "-6.2,2.2,0"` para
`front-panel/preview/j1-wr-mm-top.png`. Las piezas sin modelo 3D en KiCad 10.0 llevan
[cuerpos de sustitución](controller/kicad/OpenSaeco.3dshapes/README.md) que
genera `make_controller_3d_models.py`: valen para los renders y para ver
holguras a ojo, no para CAD mecánico, encaje en la carcasa ni distancias de
aislamiento. Los scripts de PCB requieren el Python incluido en KiCad y sus
bibliotecas.

Siguiente trabajo eléctrico: comprobar la principal impresa 1:1 contra la placa
original y los mazos, identificar JP14, JP16 y JP22, cerrar F701/F702/RV701 y el
filtro EMI, revisar J101 frente a la salida de U303, y ensayar USB, watchdog,
motor del grupo, válvula y etapas de red según el
[plan de caracterización](../docs/HD8911/characterization-plan.md). Siguiente
trabajo mecánico: cerrar las comprobaciones previas al pedido del frontal
([layout.md](front-panel/layout.md#pendiente-antes-de-pedir)) y el adaptador de pantalla.
