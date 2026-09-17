# Verificación de esta base

2026-09-15, Windows, Visual Studio 2022 / MSVC 19.34:
- Comprobación Python de enlaces y receta inactiva: PASS.
- Configuración CMake y compilación host Debug: PASS.
- CTest controller_lockout: 1/1 PASS.
- Páginas PDF 34–37 del manual renderizadas y cotejadas visualmente.
- Fotografías JPEG de la conversación revisadas según docs/HD8911/photos.md.

ESP-IDF no está disponible como comando en esta sesión: build ESP32 no ejecutado.
No se ha compilado para STM32, flasheado placas ni ensayado hardware.
La CI se incluye pero no se ha ejecutado en GitHub.

## Iteración de hardware, 2026-09-16

macOS / AppleClang 21.0.0:
- `python3 tools/check_scaffold.py`: PASS.
- `python3 tools/check_front_panel.py`: PASS; 44 componentes, pinout del TCA9534,
  conectores, filtros, polarización y correspondencia con BOM/netlist prevista.
- CMake/build/CTest: PASS, `controller_lockout` 1/1.
- `git diff --check`: PASS.

El SDK seleccionado por defecto (CommandLineTools/MacOSX27.0) no era compatible
con el linker de Xcode activo. La compilación pasó seleccionando explícitamente
el SDK de ese Xcode, sin cambiar la configuración global del equipo:

```
cmake -S firmware/stm32 -B build/host -DCMAKE_OSX_SYSROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.4.sdk
cmake --build build/host
ctest --test-dir build/host --output-on-failure
```

El comprobador del frontal lee las conexiones del archivo `.kicad_sch` usando
un parser limitado propio. No acredita que el archivo haya sido abierto por
KiCad ni sustituye su ERC. En esa iteración no se había localizado KiCad/kicad-cli; apertura,
exportación nativa de netlist y ERC quedan pendientes. No hay PCB ni DRC.
El SVG auxiliar se revisó como ayuda visual; no es un render nativo de KiCad.
No se ha montado, alimentado o ensayado el circuito.

## Núcleo principal y suministro, 2026-09-16

- Primera hoja de la principal: 32 componentes, STM32G431RBT6 + ESP32-S3-WROOM-1-N8R8.
- `python3 tools/check_controller_core.py`: PASS. Comprueba conexiones de
  alimentación, depuración, arranque, UART y frontal leyendo el esquema generado.
- Coincidencia MPN/código/huella con el catálogo: 28/32 posiciones de la hoja
  principal y 34/44 del frontal. Las restantes son mecánicas sin seleccionar.
- Catálogo: 14 referencias con stock observado en la web renderizada de JLCPCB;
  incluye AP63203 como candidato aún no instanciado. Fecha y fuente por referencia.
- `python3 tools/check_front_panel.py`, enlaces locales y `git diff --check`: PASS.
- Vista SVG auxiliar del núcleo renderizada y revisada. No es exportación de KiCad.

Sigue sin ejecutarse ERC/DRC nativo. No se han generado archivos de fabricación,
hecho pedidos ni reservado componentes. No se repitieron las pruebas del firmware,
que no ha cambiado respecto a la verificación anterior.

## Validación nativa y proyectos KiCad, 2026-09-16 (posterior)

Esta revisión sustituye el estado pendiente de KiCad de los apartados anteriores.
Se ha localizado KiCad 10.0.6 en `/Applications/KiCad`; no estaba en PATH.

- Proyectos `.kicad_pro`, bibliotecas locales y PCB `.kicad_pcb` creados.
- ERC nativo de ambos esquemas: 0 errores y 0 avisos, sin exclusiones añadidas.
  Se documentan los controles opcionales desactivados por defecto.
- Se corrigieron extremos fuera de rejilla, biblioteca ausente y declaración
  de las fuentes externas. La revisión del SVG nativo detectó y corrigió
  etiquetas izquierdas que invadían los símbolos.
- Netlist nativa XML frente a conexiones previstas: 32 componentes / 188 pines
  principal y 44 / 122 frontal, coincidencia completa.
- PCB guardadas y recargadas con `pcbnew`: 28 y 34 huellas respectivamente;
  numeración de pads y conexiones verificadas. Posiciones de trabajo, sin rutas.
- DRC nativo **no aprobado**: principal 60 conexiones, 4 huellas, contorno y 12
  taladros pendientes; frontal 58 conexiones, 10 huellas y contorno pendientes.
  [Detalle e informes](../hardware/kicad-workflow.md).
- El CLI DRC dentro del sandbox abortaba al registrar la aplicación en macOS;
  fuera del sandbox se ejecutó y produjo los informes. No era un DRC aprobado.
- Fotografías IMG_1085/1086/1089 revisadas directamente; tipos constructivos
  registrados, sin asignar referencias comerciales ni cotas a partir de perspectiva.

## Mecánica recuperada de IMG_1098–IMG_1101, 2026-09-17

- Calibre: contorno principal 141,6 × 135,2 mm, incertidumbre estimada ±0,15 mm.
- Fotogrametría calibrada: tres taladros NPTH de aproximadamente 3,5 mm; centros
  registrados con ±0,6 mm en [mecánica de la principal](HD8911/main-board-mechanics.md).
- Contorno y taladros incorporados al `.kicad_pcb`; archivo guardado y recargado
  para verificar las coordenadas. La vista mecánica SVG fue renderizada y revisada.
- DRC posterior: ya no informa contorno ausente. Conserva 12 taladros del pad
  térmico ESP32 fuera de regla, 60 conexiones sin ruta, cuatro conectores sin
  huella y tres huellas mecánicas adicionales al esquema.
- Las fotos no proporcionan espesor o alturas fiables ni tolerancia suficiente
  para fabricar huellas de conectores. Esos campos continúan pendientes.
- El propietario aceptó el 2026-09-17 el contorno y los centros de taladro como
  línea base mecánica de Rev A. La aceptación no libera el resto del diseño.

Sin ampliación de firmware ni ensayos eléctricos. Supervisión, sensores y potencia
de cargas siguen pendientes en el esquema principal.

## Alimentación de baja tensión y conectores internos, 2026-09-17

- La principal pasa de 32 a 48 componentes; los 48 tienen MPN, código JLC/LCSC y huella.
- Entrada J101 de 12 V DC aislados con fusible 1 A, bloqueo de polaridad SS34 y
  TVS SMAJ18A. La fuente AC/DC aislada y certificada aún no está seleccionada.
- U301 AP63203WU-7 implementado a 3,3 V/2 A con 3,9 µH, 10 µF de entrada,
  2×22 µF de salida y bootstrap de 100 nF según la tabla 2 del fabricante.
- U302 TPS22918DBVR implementado para `3V3_UI`, controlado por PB0, con pull-up,
  CT de 1 nF y descarga QOD. Falta medirlo con el display definitivo.
- Existencias observadas y registradas para las nuevas referencias; el inductor
  seleccionado tiene 3,3 A nominales y 3,9 A de saturación.
- Comprobador propio: PASS. ERC KiCad 10.0.6: 0 infracciones; netlist nativa:
  48 componentes y 227 pines, coincidencia completa.
- J101 seleccionado como JST XH lateral de 2 vías; J102/J103 como 1×6 de 2,54 mm;
  J104 y J1 frontal como IDC polarizado 2×8 de 2,54 mm. Stock observado y registrado.
- PCB principal: 48 huellas eléctricas, 16 nuevas de alimentación y cuatro
  conectores colocados provisionalmente;
  contorno y los tres taladros aceptados conservados y verificados tras recargar.
- DRC de la principal: 0 infracciones geométricas/de reglas, 122 conexiones sin
  rutear y 3 avisos de paridad esperados (MH1–MH3 adicionales al esquema).
- PCB frontal: J1 incorporado; 35 huellas, 70 conexiones sin rutear. El DRC solo
  marca el contorno ausente y las nueve huellas mecánicas aún pendientes.
- El mínimo de taladro se fija en 0,20 mm para las vías térmicas del ESP32, valor
  preferido publicado por JLCPCB. No equivale a liberar el stack-up ni la fabricación.
