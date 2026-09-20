# Proyectos KiCad — estado y edición

Los dos proyectos se han cargado con KiCad CLI 10.0.6. Para abrirlos en el gestor:

- [Principal](controller/kicad/controller-core-reva.kicad_pro),
  [esquema](controller/kicad/controller-core-reva.kicad_sch),
  [PCB de trabajo](controller/kicad/controller-core-reva.kicad_pcb).
- [Frontal](front-panel/kicad/front-panel-reva.kicad_pro),
  [esquema](front-panel/kicad/front-panel-reva.kicad_sch),
  [PCB de trabajo](front-panel/kicad/front-panel-reva.kicad_pcb).

Cada carpeta incluye `OpenSaeco.kicad_sym`, `sym-lib-table` y `fp-lib-table`.
Los símbolos son locales al proyecto; las huellas proceden de las bibliotecas
estándar de KiCad 10 mediante `KICAD10_FOOTPRINT_DIR`. No dependen de una ruta
absoluta del equipo de desarrollo.

## Qué contienen las PCB

Se han importado las huellas seleccionadas y sus redes desde la netlist **nativa**
de KiCad, conservando los UUID de los símbolos para actualizar desde el esquema.
También se han conservado fabricante, MPN y código JLC como campos ocultos.
Las PCB se han guardado y vuelto a cargar con `pcbnew`, cotejando cada pad/red.

| Proyecto | Componentes en esquema | Huellas en PCB | Sin huella |
|---|---:|---:|---|
| Principal | 138 | 135 | J116/JP19 y J119–J120/PE |
| Frontal | 42 | 42 | — |

Las coordenadas actuales forman una [colocación funcional completa](controller/layout.md),
todavía sujeta a ajustes de routing y acoplamiento. **No es una colocación liberada
para fabricación.** La principal incorpora un [contorno y tres taladros aceptados para
la Rev A a partir de las fotos](../docs/HD8911/main-board-mechanics.md); el resto de la colocación
sigue siendo de trabajo. Los desacoplos se han agrupado con sus circuitos y el módulo
ESP32 está en el borde con su keepout libre. En la principal están ruteados el USB, la entrada de red, los 24 V, el puente H,
el supervisor y el relé, la válvula, los sensores y el buck de 12 V, y
JP8/JP24/JP17 ya están colocados; la distribución de 3V3 y 12 V, las señales del
STM32 y las etapas de calentador, bomba y molinillo siguen pendientes. El **frontal está
colocado y ruteado** sobre el [contorno aceptado](front-panel/mechanical.md), con DRC
limpio y paquete JLCPCB candidato: ver [layout del frontal](front-panel/layout.md). J101–J104 y J1 tienen huellas
seleccionadas; J105–J109 y J112–J113 usan candidatas JST XH/PH según las fotos con calibre; J110 es USB-C
y queda colocado provisionalmente en el borde superior junto a JP21. U501 y su
etapa de 24 V para el grupo, U502/Q501 para la válvula y U601/U602 para supervisión están colocados solo para comprobar cabida; no generar
Gerbers/BOM de fabricación/CPL de la principal todavía. J114 y los divisores de
12/24 V permiten contrastar por multímetro la telemetría que enviará el STM32.

## Validación actualizada el 2026-09-19

ERC nativo: cero errores y cero avisos en ambos esquemas, sin excluir infracciones.
Se mantiene la configuración estándar de KiCad; los cuatro controles opcionales
desactivados por defecto figuran en cada informe. En la principal, los PWR_FLAG
declaran las fuentes aisladas de J101/J112 y los nodos de potencia separados por elementos
pasivos; U301/U302 implementan la regulación y el corte del frontal, U501 el
puente H del grupo, U502/Q501 la válvula y U601/U602 el watchdog/interlock. En el
frontal, J1 sigue declarando su alimentación externa.
Los GPIO aún sin asignar permanecen NC. Los tipos de pin de GPIO genéricos no
comprueban las futuras funciones alternativas o la configuración de firmware.

La netlist XML de KiCad coincide con los 457 pines de la principal y los 118 del
frontal. Se revisaron las exportaciones SVG nativas y se corrigió la orientación
del texto de las etiquetas del lado izquierdo.

**DRC ejecutado; diseño aún no liberado:**

| Resultado | Principal | Frontal |
|---|---:|---:|
| Infracciones geométricas/de reglas | 0 | 0 |
| Conexiones pendientes de rutear | 155 | 0 |
| Huellas ausentes respecto al esquema | 0 | 0 |
| Contorno ausente | 0 | 0 |
| Diferencias adicionales de paridad | 3 taladros mecánicos intencionales | 0 |

El pad expuesto del ESP32 usa doce vías térmicas de 0,20 mm. Se ha fijado 0,20 mm
como mínimo de taladro del proyecto: coincide con el mínimo preferido publicado
por JLCPCB para placas rígidas. Esto elimina la discrepancia del footprint sin
modificarlo. Las reglas siguen sin cubrir aislamiento de red ni constituir un
perfil de fabricación completo.

La paridad de la principal solo informa las tres huellas de montaje adicionales
al esquema. Son intencionales y proceden del registro mecánico; no se han excluido.
El frontal, ruteado el 2026-09-18, pasa el DRC de KiCad 10.0.6 con paridad y todas
las severidades sin infracciones, conexiones pendientes ni diferencias con el esquema.

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
principal; el sincronizador ya no mueve huellas existentes.

Desde la raíz del repositorio:

```sh
python3 tools/check_front_panel.py
python3 tools/check_controller_core.py
python3 tools/validate_kicad.py
python3 tools/apply_front_panel_mechanics.py
<python de KiCad> tools/sync_controller_pcb.py
<python de KiCad> tools/layout_controller_pcb.py
python3 tools/configure_controller_rules.py
<python de KiCad> tools/route_controller_pcb.py
<python de KiCad> tools/sync_front_panel_pcb.py
<python de KiCad> tools/layout_front_panel_pcb.py
kicad-cli pcb drc --schematic-parity --format json -o hardware/controller/validation/drc-staging.json hardware/controller/kicad/controller-core-reva.kicad_pcb
kicad-cli pcb drc --schematic-parity --format json -o hardware/controller/validation/pcb/drc.json hardware/controller/kicad/controller-core-reva.kicad_pcb
kicad-cli pcb drc --schematic-parity --severity-all --format json -o hardware/front-panel/validation/drc-staging.json hardware/front-panel/kicad/front-panel-reva.kicad_pcb
python3 tools/export_front_panel_fab.py
```

Si el ejecutable no está en PATH, `validate_kicad.py` admite `KICAD_CLI` y detecta
la instalación habitual de macOS y de Windows. La creación inicial de PCB requiere el Python
incluido en KiCad y sus bibliotecas; no es necesario regenerarlas para editarlas.

Siguiente trabajo eléctrico: rutear y ensayar USB, probar el acoplamiento de J105–J109/J112–J113,
medir los niveles lleno/vacío de JP22, ensayar el motor del grupo con J112 limitado,
seleccionar el módulo AC/DC aislado, cerrar el presupuesto de corriente y completar
el watchdog y la válvula, y completar los drivers de red/molino. Siguiente
trabajo mecánico: cerrar las comprobaciones previas al pedido del frontal
([layout.md](front-panel/layout.md#pendiente-antes-de-pedir)) y el adaptador de pantalla.
