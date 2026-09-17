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
| Principal | 48 | 48 | — |
| Frontal | 44 | 35 | J2, SW1–SW8 |

Las coordenadas actuales son una distribución de trabajo para seleccionar y mover
componentes. **No representan colocación eléctrica definitiva ni dimensiones de
la máquina.** La principal incorpora un [contorno y tres taladros aceptados para
la Rev A a partir de las fotos](../docs/HD8911/main-board-mechanics.md); el resto de la colocación
sigue siendo de trabajo. Los desacoplos todavía deben situarse junto a sus pines y el módulo
ESP32 requiere resolver borde y zona libre de antena. No hay pistas, zonas de cobre,
ni conectores de la máquina original. J101–J104 y J1 ya tienen huellas seleccionadas;
no generar Gerbers/BOM de fabricación/CPL desde aquí.

## Validación actualizada el 2026-09-17

ERC nativo: cero errores y cero avisos en ambos esquemas, sin excluir infracciones.
Se mantiene la configuración estándar de KiCad; los cuatro controles opcionales
desactivados por defecto figuran en cada informe. En la principal, los PWR_FLAG
declaran la fuente aislada de J101 y los nodos de potencia separados por elementos
pasivos; U301 y U302 implementan la regulación y el corte del frontal. En el
frontal, J1 sigue declarando su alimentación externa.
Los GPIO aún sin asignar permanecen NC. Los tipos de pin de GPIO genéricos no
comprueban las futuras funciones alternativas o la configuración de firmware.

La netlist XML de KiCad coincide con los 227 pines de la principal y los 122 del
frontal. Se revisaron las exportaciones SVG nativas y se corrigió la orientación
del texto de las etiquetas del lado izquierdo.

**DRC ejecutado; diseño aún no liberado:**

| Resultado | Principal | Frontal |
|---|---:|---:|
| Infracciones geométricas/de reglas | 0 | 1: contorno todavía ausente |
| Conexiones pendientes de rutear | 122 | 70 |
| Huellas ausentes respecto al esquema | 0 | 9 |
| Contorno ausente | 0 | 1 |
| Diferencias adicionales de paridad | 3 taladros mecánicos intencionales | 0 |

El pad expuesto del ESP32 usa doce vías térmicas de 0,20 mm. Se ha fijado 0,20 mm
como mínimo de taladro del proyecto: coincide con el mínimo preferido publicado
por JLCPCB para placas rígidas. Esto elimina la discrepancia del footprint sin
modificarlo. Las reglas siguen sin cubrir aislamiento de red ni constituir un
perfil de fabricación completo.

La paridad de la principal solo informa las tres huellas de montaje adicionales
al esquema. Son intencionales y proceden del registro mecánico; no se han excluido.
El frontal informa J2 y SW1–SW8 sin huella, además del contorno todavía ausente.

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
hace lo mismo para nuevas huellas del frontal. También se puede usar
«Actualizar PCB desde esquema» en KiCad conservando las posiciones revisadas.

Desde la raíz del repositorio:

```sh
python3 tools/check_front_panel.py
python3 tools/check_controller_core.py
python3 tools/validate_kicad.py
<python de KiCad> tools/sync_controller_pcb.py
<python de KiCad> tools/sync_front_panel_pcb.py
kicad-cli pcb drc --schematic-parity --format json -o hardware/controller/validation/drc-staging.json hardware/controller/kicad/controller-core-reva.kicad_pcb
kicad-cli pcb drc --schematic-parity --format json -o hardware/front-panel/validation/drc-staging.json hardware/front-panel/kicad/front-panel-reva.kicad_pcb
```

Si el ejecutable no está en PATH, `validate_kicad.py` admite `KICAD_CLI` y detecta
la instalación habitual de macOS. La creación inicial de PCB requiere el Python
incluido en KiCad y sus bibliotecas; no es necesario regenerarlas para editarlas.

Siguiente trabajo eléctrico: añadir conectores y acondicionamiento de sensores,
seleccionar el módulo AC/DC aislado, cerrar el
presupuesto de corriente y completar supervisión, sensores y drivers. Siguiente
trabajo mecánico: copiar contorno y centros de pulsadores del frontal.
